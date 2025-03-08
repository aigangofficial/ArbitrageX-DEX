#!/bin/bash

# Run Monitored Comprehensive Test for ArbitrageX
# This script runs a comprehensive test for the ArbitrageX system with enhanced monitoring.

# Set default values
DURATION=3600
NETWORKS="ethereum"
TOKEN_PAIRS="WETH-USDC"
DEXES="uniswap_v3,sushiswap"
FORK_CONFIG="backend/ai/hardhat_fork_config.json"
RESULTS_DIR="backend/ai/results/comprehensive_test"
METRICS_DIR="backend/ai/metrics"
ALERT_CONFIG="backend/ai/config/alert_config.json"
SAVE_INTERVAL=300
MONITOR_INTERVAL=60

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --networks)
            NETWORKS="$2"
            shift 2
            ;;
        --token-pairs)
            TOKEN_PAIRS="$2"
            shift 2
            ;;
        --dexes)
            DEXES="$2"
            shift 2
            ;;
        --fork-config)
            FORK_CONFIG="$2"
            shift 2
            ;;
        --results-dir)
            RESULTS_DIR="$2"
            shift 2
            ;;
        --metrics-dir)
            METRICS_DIR="$2"
            shift 2
            ;;
        --alert-config)
            ALERT_CONFIG="$2"
            shift 2
            ;;
        --save-interval)
            SAVE_INTERVAL="$2"
            shift 2
            ;;
        --monitor-interval)
            MONITOR_INTERVAL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --duration SECONDS        Test duration in seconds (default: 3600)"
            echo "  --networks NETWORKS       Comma-separated list of networks to test (default: ethereum)"
            echo "  --token-pairs PAIRS       Comma-separated list of token pairs to test (default: WETH-USDC)"
            echo "  --dexes DEXES             Comma-separated list of DEXes to test (default: uniswap_v3,sushiswap)"
            echo "  --fork-config PATH        Path to fork configuration file (default: backend/ai/hardhat_fork_config.json)"
            echo "  --results-dir DIR         Directory to store test results (default: backend/ai/results/comprehensive_test)"
            echo "  --metrics-dir DIR         Directory to store metrics (default: backend/ai/metrics)"
            echo "  --alert-config PATH       Path to alert configuration file (default: backend/ai/config/alert_config.json)"
            echo "  --save-interval SECONDS   Interval in seconds to save metrics (default: 300)"
            echo "  --monitor-interval SECONDS Interval in seconds to monitor system resources (default: 60)"
            echo "  --help                    Display this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create directories if they don't exist
mkdir -p "$RESULTS_DIR"
mkdir -p "$METRICS_DIR"
mkdir -p "$(dirname "$ALERT_CONFIG")"

# Print test configuration
echo "Running monitored comprehensive test with the following configuration:"
echo "  Duration: $DURATION seconds"
echo "  Networks: $NETWORKS"
echo "  Token pairs: $TOKEN_PAIRS"
echo "  DEXes: $DEXES"
echo "  Fork config: $FORK_CONFIG"
echo "  Results directory: $RESULTS_DIR"
echo "  Metrics directory: $METRICS_DIR"
echo "  Alert config: $ALERT_CONFIG"
echo "  Save interval: $SAVE_INTERVAL seconds"
echo "  Monitor interval: $MONITOR_INTERVAL seconds"

# Install dependencies if needed
echo "Checking dependencies..."
python -c "import psutil" 2>/dev/null || {
    echo "Installing dependencies..."
    python backend/ai/install_monitoring_deps.py
}

# Run the monitored test
echo "Starting monitored comprehensive test..."
python backend/ai/run_monitored_test.py \
    --duration "$DURATION" \
    --networks "$NETWORKS" \
    --token-pairs "$TOKEN_PAIRS" \
    --dexes "$DEXES" \
    --fork-config "$FORK_CONFIG" \
    --results-dir "$RESULTS_DIR" \
    --metrics-dir "$METRICS_DIR" \
    --alert-config "$ALERT_CONFIG" \
    --save-interval "$SAVE_INTERVAL" \
    --monitor-interval "$MONITOR_INTERVAL"

# Check if the test was successful
if [ $? -eq 0 ]; then
    echo "Monitored comprehensive test completed successfully"
    
    # Generate timestamp for report
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    # Generate report
    echo "Generating test report..."
    REPORT_FILE="$RESULTS_DIR/test_report_$TIMESTAMP.md"
    
    echo "# ArbitrageX Monitored Comprehensive Test Report" > "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "## Test Configuration" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "- **Duration:** $DURATION seconds" >> "$REPORT_FILE"
    echo "- **Networks:** $NETWORKS" >> "$REPORT_FILE"
    echo "- **Token pairs:** $TOKEN_PAIRS" >> "$REPORT_FILE"
    echo "- **DEXes:** $DEXES" >> "$REPORT_FILE"
    echo "- **Fork config:** $FORK_CONFIG" >> "$REPORT_FILE"
    echo "- **Results directory:** $RESULTS_DIR" >> "$REPORT_FILE"
    echo "- **Metrics directory:** $METRICS_DIR" >> "$REPORT_FILE"
    echo "- **Alert config:** $ALERT_CONFIG" >> "$REPORT_FILE"
    echo "- **Save interval:** $SAVE_INTERVAL seconds" >> "$REPORT_FILE"
    echo "- **Monitor interval:** $MONITOR_INTERVAL seconds" >> "$REPORT_FILE"
    echo "- **Timestamp:** $TIMESTAMP" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Find the latest metrics file
    LATEST_METRICS=$(find "$METRICS_DIR" -name "metrics_*.json" -type f -printf "%T@ %p\n" | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -n "$LATEST_METRICS" ]; then
        echo "## Test Metrics" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "Metrics file: $LATEST_METRICS" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo '```json' >> "$REPORT_FILE"
        cat "$LATEST_METRICS" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
    fi
    
    echo "Test report generated: $REPORT_FILE"
else
    echo "Monitored comprehensive test failed"
    exit 1
fi 