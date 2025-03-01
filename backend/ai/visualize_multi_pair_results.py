#!/usr/bin/env python3
"""
ArbitrageX Multi-Pair Results Visualization

This script generates visualizations from the multi-pair test results.
"""

import os
import sys
import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime
import numpy as np

def parse_summary_file(file_path):
    """Parse the multi-pair summary markdown file into a DataFrame."""
    if not os.path.exists(file_path):
        print(f"Error: Summary file not found at {file_path}")
        return None
    
    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Extract the table rows (skip header and separator)
    table_rows = []
    table_started = False
    for line in lines:
        if '|--' in line:
            table_started = True
            continue
        if table_started and '|' in line and not line.strip().startswith('##'):
            table_rows.append(line.strip())
    
    # Parse each row
    data = []
    for row in table_rows:
        columns = [col.strip() for col in row.split('|')[1:-1]]
        if len(columns) >= 7:  # Ensure we have all columns
            try:
                token_pair = columns[0]
                total_predictions = int(columns[1])
                profitable_predictions = int(columns[2])
                success_rate = float(columns[3].replace('%', ''))
                total_profit = float(columns[4].replace('$', ''))
                avg_confidence = float(columns[5])
                avg_execution_time = float(columns[6].split()[0])
                
                data.append({
                    'Token Pair': token_pair,
                    'Total Predictions': total_predictions,
                    'Profitable Predictions': profitable_predictions,
                    'Success Rate': success_rate,
                    'Total Expected Profit': total_profit,
                    'Avg Confidence': avg_confidence,
                    'Avg Execution Time': avg_execution_time
                })
            except (ValueError, IndexError) as e:
                print(f"Error parsing row: {row}")
                print(f"Error details: {e}")
    
    # Create DataFrame
    return pd.DataFrame(data)

def create_visualizations(df, output_dir):
    """Create visualizations from the DataFrame."""
    if df is None or df.empty:
        print("Error: No data to visualize")
        return False
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set the style
    sns.set(style="whitegrid")
    plt.rcParams.update({'font.size': 12})
    
    # 1. Success Rate by Token Pair
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(x='Token Pair', y='Success Rate', data=df.sort_values('Success Rate', ascending=False))
    plt.title('Success Rate by Token Pair')
    plt.xlabel('Token Pair')
    plt.ylabel('Success Rate (%)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Add value labels
    for i, v in enumerate(df.sort_values('Success Rate', ascending=False)['Success Rate']):
        ax.text(i, v + 0.5, f"{v:.2f}%", ha='center')
    
    plt.savefig(os.path.join(output_dir, 'success_rate_by_pair.png'), dpi=300)
    plt.close()
    
    # 2. Expected Profit by Token Pair
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(x='Token Pair', y='Total Expected Profit', data=df.sort_values('Total Expected Profit', ascending=False))
    plt.title('Expected Profit by Token Pair')
    plt.xlabel('Token Pair')
    plt.ylabel('Expected Profit ($)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Add value labels
    for i, v in enumerate(df.sort_values('Total Expected Profit', ascending=False)['Total Expected Profit']):
        ax.text(i, v - 50 if v < 0 else v + 50, f"${v:.2f}", ha='center')
    
    plt.savefig(os.path.join(output_dir, 'profit_by_pair.png'), dpi=300)
    plt.close()
    
    # 3. Confidence vs Success Rate Scatter Plot
    plt.figure(figsize=(10, 8))
    ax = sns.scatterplot(x='Avg Confidence', y='Success Rate', size='Total Predictions', 
                     hue='Total Expected Profit', data=df, sizes=(100, 500))
    plt.title('Confidence vs Success Rate')
    plt.xlabel('Average Confidence Score')
    plt.ylabel('Success Rate (%)')
    
    # Add token pair labels
    for i, row in df.iterrows():
        plt.text(row['Avg Confidence'], row['Success Rate'], row['Token Pair'], 
                 fontsize=9, ha='center', va='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'confidence_vs_success.png'), dpi=300)
    plt.close()
    
    # 4. Predictions and Profitability
    plt.figure(figsize=(12, 8))
    ax = plt.subplot(111)
    
    # Sort by total predictions
    df_sorted = df.sort_values('Total Predictions', ascending=False)
    
    # Create the bar chart
    x = range(len(df_sorted))
    width = 0.35
    
    ax.bar(x, df_sorted['Total Predictions'], width, label='Total Predictions')
    ax.bar([i + width for i in x], df_sorted['Profitable Predictions'], width, label='Profitable Predictions')
    
    # Add labels and title
    ax.set_xlabel('Token Pair')
    ax.set_ylabel('Number of Predictions')
    ax.set_title('Total vs Profitable Predictions by Token Pair')
    ax.set_xticks([i + width/2 for i in x])
    ax.set_xticklabels(df_sorted['Token Pair'], rotation=45)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'predictions_by_pair.png'), dpi=300)
    plt.close()
    
    # 5. Execution Time by Token Pair
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(x='Token Pair', y='Avg Execution Time', data=df.sort_values('Avg Execution Time', ascending=False))
    plt.title('Average Execution Time by Token Pair')
    plt.xlabel('Token Pair')
    plt.ylabel('Execution Time (ms)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Add value labels
    for i, v in enumerate(df.sort_values('Avg Execution Time', ascending=False)['Avg Execution Time']):
        ax.text(i, v + 0.5, f"{v:.2f} ms", ha='center')
    
    plt.savefig(os.path.join(output_dir, 'execution_time_by_pair.png'), dpi=300)
    plt.close()
    
    # 6. Create a correlation heatmap (only for numeric columns)
    plt.figure(figsize=(10, 8))
    # Select only numeric columns for correlation
    numeric_df = df.select_dtypes(include=['float64', 'int64'])
    correlation = numeric_df.corr()
    mask = np.triu(correlation)
    sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm", mask=mask)
    plt.title('Correlation Between Metrics')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'correlation_heatmap.png'), dpi=300)
    plt.close()
    
    print(f"Visualizations saved to {output_dir}")
    return True

def main():
    """Main entry point for the visualization script."""
    parser = argparse.ArgumentParser(description="ArbitrageX Multi-Pair Results Visualization")
    parser.add_argument("--summary", type=str, help="Path to the multi-pair summary markdown file")
    parser.add_argument("--output", type=str, default="results/visualizations", help="Directory to save visualizations")
    args = parser.parse_args()
    
    # If no summary file is provided, find the most recent one
    if not args.summary:
        results_dir = "results"
        if os.path.exists(results_dir):
            summary_files = [f for f in os.listdir(results_dir) if f.startswith("multi_pair_summary_") and f.endswith(".md")]
            if summary_files:
                # Sort by modification time (newest first)
                summary_files.sort(key=lambda x: os.path.getmtime(os.path.join(results_dir, x)), reverse=True)
                args.summary = os.path.join(results_dir, summary_files[0])
                print(f"Using most recent summary file: {args.summary}")
            else:
                print("Error: No summary files found in the results directory")
                return 1
        else:
            print(f"Error: Results directory not found: {results_dir}")
            return 1
    
    # Parse the summary file
    df = parse_summary_file(args.summary)
    
    # Create visualizations
    if df is not None:
        # Create a timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(args.output, f"viz_{timestamp}")
        
        success = create_visualizations(df, output_dir)
        if success:
            print(f"Visualizations created successfully in {output_dir}")
            return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main()) 