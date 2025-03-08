#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ArbitrageX Backtest Results Analyzer ===${NC}"

# Directories to analyze
RESULTS_DIR="backend/ai/results"
REALISTIC_DIR="backend/ai/results/realistic_backtest"

# Check if realistic backtest directory exists
if [ ! -d "$REALISTIC_DIR" ]; then
    echo -e "${RED}Error: Realistic backtest directory not found at $REALISTIC_DIR${NC}"
    echo "Has the backtest completed successfully?"
    exit 1
fi

# Count files in the realistic backtest directory
file_count=$(ls -1 $REALISTIC_DIR 2>/dev/null | wc -l | tr -d ' ')
if [ "$file_count" -eq "0" ]; then
    echo -e "${RED}Error: No result files found in $REALISTIC_DIR${NC}"
    echo "The backtest may not have completed successfully."
    exit 1
fi

echo -e "${GREEN}Found $file_count result files in the realistic backtest directory.${NC}"

# List all files in the realistic backtest directory
echo -e "\n${BLUE}=== Backtest Result Files ===${NC}"
ls -la $REALISTIC_DIR

# Check for JSON result files
json_files=$(find $REALISTIC_DIR -name "*.json" | wc -l | tr -d ' ')
if [ "$json_files" -gt "0" ]; then
    echo -e "\n${GREEN}Found $json_files JSON result files.${NC}"
    
    # Display summary of the most recent JSON file - macOS compatible version
    latest_json=$(find $REALISTIC_DIR -name "*.json" -type f -exec stat -f "%m %N" {} \; | sort -n | tail -1 | cut -f2- -d" ")
    if [ ! -z "$latest_json" ]; then
        echo -e "\n${BLUE}=== Latest JSON Result File ===${NC}"
        echo "File: $latest_json"
        echo -e "${CYAN}Content Summary:${NC}"
        
        # Try to extract key information from the JSON file
        if command -v jq &> /dev/null; then
            # If jq is available, use it for better JSON parsing
            echo -e "\n${YELLOW}Profit Summary:${NC}"
            jq -r 'if has("total_profit_usd") then "Total Profit (USD): \(.total_profit_usd)" else "" end' "$latest_json" 2>/dev/null
            jq -r 'if has("roi_percentage") then "ROI: \(.roi_percentage)%" else "" end' "$latest_json" 2>/dev/null
            jq -r 'if has("successful_trades") then "Successful Trades: \(.successful_trades)" else "" end' "$latest_json" 2>/dev/null
            
            echo -e "\n${YELLOW}Trade Details:${NC}"
            jq -r 'if has("trades") then "Total Trades: \(.trades | length)" else "" end' "$latest_json" 2>/dev/null
            
            # Extract the first few trades if available
            jq -r 'if has("trades") and (.trades | length > 0) then "Sample Trade: \(.trades[0] | tostring)" else "" end' "$latest_json" 2>/dev/null
        else
            # If jq is not available, use grep for basic extraction
            echo "For detailed JSON analysis, please install 'jq'"
            echo -e "\n${YELLOW}Basic Content (first 10 lines):${NC}"
            head -n 10 "$latest_json"
        fi
    fi
fi

# Check for PNG visualization files
png_files=$(find $REALISTIC_DIR -name "*.png" | wc -l | tr -d ' ')
if [ "$png_files" -gt "0" ]; then
    echo -e "\n${GREEN}Found $png_files visualization files.${NC}"
    echo "Visualization files are available for viewing in: $REALISTIC_DIR"
    find $REALISTIC_DIR -name "*.png" -type f | sort
fi

# Check for log files
log_file="logs/realistic_backtest.log"
if [ -f "$log_file" ]; then
    echo -e "\n${BLUE}=== Backtest Log Analysis ===${NC}"
    
    # Count lines in log file
    log_lines=$(wc -l < "$log_file" | tr -d ' ')
    echo "Log file contains $log_lines lines."
    
    # Check for errors in the log
    error_count=$(grep -i "error" "$log_file" | wc -l | tr -d ' ')
    warning_count=$(grep -i "warning" "$log_file" | wc -l | tr -d ' ')
    
    if [ "$error_count" -gt "0" ]; then
        echo -e "${RED}Found $error_count error messages in the log.${NC}"
        echo -e "${YELLOW}Last 5 error messages:${NC}"
        grep -i "error" "$log_file" | tail -n 5
    else
        echo -e "${GREEN}No error messages found in the log.${NC}"
    fi
    
    if [ "$warning_count" -gt "0" ]; then
        echo -e "${YELLOW}Found $warning_count warning messages in the log.${NC}"
    else
        echo -e "${GREEN}No warning messages found in the log.${NC}"
    fi
    
    # Show the last few lines of the log
    echo -e "\n${BLUE}Last 10 lines of the log:${NC}"
    tail -n 10 "$log_file"
fi

echo -e "\n${GREEN}=== Analysis Complete ===${NC}"
echo "For more detailed analysis, examine the JSON files in $REALISTIC_DIR"
echo "You can visualize the results by opening the PNG files in a viewer." 