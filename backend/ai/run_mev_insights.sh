#!/bin/bash

# ArbitrageX MEV Protection Insights Runner
# This script runs the MEV Protection Insights demo and dashboard

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${SCRIPT_DIR}"

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}                  ArbitrageX MEV Protection Insights                  ${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo

# Function to check if Python 3 is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
        exit 1
    fi
}

# Function to check if required modules are installed
check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"
    
    # Create a temporary Python script to check imports
    cat > /tmp/check_imports.py << EOF
try:
    import flask
    import flask_socketio
    import web3
    print("All dependencies found.")
except ImportError as e:
    module = str(e).split("'")[1]
    print(f"Error: Module {module} not found.")
    exit(1)
EOF
    
    # Run the script
    if ! python3 /tmp/check_imports.py; then
        echo -e "${RED}Installing missing dependencies...${NC}"
        pip install -r dashboard/requirements.txt
    else
        echo -e "${GREEN}All dependencies are installed.${NC}"
    fi
    
    rm /tmp/check_imports.py
}

# Function to run the demo
run_demo() {
    echo -e "${YELLOW}Running MEV Protection Insights demo...${NC}"
    python3 run_mev_protection_insights.py
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Demo failed to run.${NC}"
        exit 1
    fi
}

# Function to start the dashboard
start_dashboard() {
    echo -e "${YELLOW}Starting MEV Protection Insights dashboard...${NC}"
    echo -e "${GREEN}Dashboard URL: http://localhost:5000/mev_protection${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop the dashboard${NC}"
    
    cd dashboard
    python3 app.py
}

# Main function
main() {
    check_python
    check_requirements
    
    # Parse command line arguments
    case "$1" in
        demo)
            run_demo
            ;;
        dashboard)
            start_dashboard
            ;;
        *)
            echo -e "${YELLOW}Usage:${NC}"
            echo -e "  ${GREEN}./run_mev_insights.sh demo${NC} - Run the MEV Protection Insights demo"
            echo -e "  ${GREEN}./run_mev_insights.sh dashboard${NC} - Start the dashboard"
            echo
            echo -e "${YELLOW}Running demo by default...${NC}"
            run_demo
            
            echo
            echo -e "${YELLOW}Do you want to start the dashboard now? (y/n)${NC}"
            read -r answer
            if [[ "$answer" =~ ^[Yy]$ ]]; then
                start_dashboard
            fi
            ;;
    esac
}

# Run the main function
main "$@" 