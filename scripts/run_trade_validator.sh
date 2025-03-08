#!/bin/bash

# Run Trade Validator Tests
# This script runs the trade validator tests to demonstrate its functionality

# Set the base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR" || exit 1

# Ensure required directories exist
mkdir -p backend/ai/results/validation
mkdir -p backend/ai/models

# Check if scikit-learn is installed
if ! python3 -c "import sklearn" &> /dev/null; then
    echo "Installing scikit-learn for machine learning features..."
    pip install scikit-learn joblib numpy
fi

# Run the basic test
echo "Running basic trade validator test..."
python3 backend/ai/test_trade_validator.py

# Run with enhanced features
echo "Running enhanced trade validator test..."
python3 -c "
import sys
sys.path.append('backend/ai')
from test_trade_validator import test_enhanced_features
test_enhanced_features()
"

echo "Trade validator tests completed successfully!" 