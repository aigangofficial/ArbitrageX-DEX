#!/bin/bash

# Script to generate a trade summary with USD values for all coins

# Set the directory to the project root
cd "$(dirname "$0")/.."

# Create a directory for reports if it doesn't exist
mkdir -p reports

# Fetch the latest data
echo "Fetching latest trade data..."
curl -s http://localhost:3002/api/v1/trades > reports/trades.json
curl -s http://localhost:3002/api/v1/trades/stats > reports/trade_stats.json
curl -s http://localhost:3002/api/v1/market/data > reports/market_data.json

# Copy the generator script to the reports directory
cp generate_trade_summary.js reports/

# Run the generator
echo "Generating trade summary..."
cd reports
node generate_trade_summary.js

# Get the current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create a timestamped copy of the report
cp trade_results_summary.md "trade_results_summary_${TIMESTAMP}.md"

echo "Trade summary generated: reports/trade_results_summary.md"
echo "Timestamped copy saved as: reports/trade_results_summary_${TIMESTAMP}.md"

# Display the summary
echo "Summary:"
echo "----------------------------------------"
cat trade_results_summary.md
echo "----------------------------------------" 