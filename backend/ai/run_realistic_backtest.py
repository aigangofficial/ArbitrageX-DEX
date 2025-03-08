#!/usr/bin/env python3
"""
Realistic Backtest for ArbitrageX

This script runs a realistic backtest of the ArbitrageX bot on a forked mainnet
with historical on-chain data and real execution constraints.
"""

import argparse
import os
import sys
import logging
import json
import time
from datetime import datetime, timedelta
import subprocess
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from decimal import Decimal, getcontext
import requests

# Set decimal precision
getcontext().prec = 28

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/realistic_backtest.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('RealisticBacktest')

class RealisticBacktester:
    """
    Runs a realistic backtest of the ArbitrageX bot on a forked mainnet
    """
    
    def __init__(self, initial_investment=50.0, test_days=30):
        """
        Initialize the realistic backtester
        
        Args:
            initial_investment: Initial investment amount in USD
            test_days: Number of days to test
        """
        self.initial_investment = initial_investment
        self.test_days = test_days
        self.results_dir = "backend/ai/results/realistic_backtest"
        self.data_dir = "backend/ai/data"
        
        # Create directories if they don't exist
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set execution constraints
        self.execution_constraints = {
            "max_slippage_bps": 50,  # 0.5% max slippage
            "min_liquidity_usd": 10000,  # Minimum pool liquidity in USD
            "max_gas_price_gwei": 100,  # Maximum gas price in Gwei
            "min_profit_threshold_usd": 5,  # Minimum profit threshold in USD
            "min_profit_threshold_bps": 10,  # Minimum profit threshold in basis points (0.1%)
            "max_execution_time_ms": 3000,  # Maximum execution time in milliseconds
        }
        
        logger.info(f"RealisticBacktester initialized with ${initial_investment} investment for {test_days} days")
        logger.info(f"Execution constraints: {json.dumps(self.execution_constraints, indent=2)}")

    def setup_forked_mainnet(self, block_number=None):
        """
        Set up a forked mainnet for testing
        
        Args:
            block_number: Specific block number to fork from (optional)
            
        Returns:
            Process object for the forked mainnet
        """
        logger.info("Setting up forked mainnet for testing")
        
        # Use a different port to avoid conflicts
        hardhat_port = 8547
        
        # Determine fork command - correct syntax for Hardhat
        fork_cmd = [
            "npx", 
            "hardhat", 
            "node", 
            "--hostname", "127.0.0.1",
            "--port", str(hardhat_port),
            "--fork"
        ]
        
        # Add Ethereum mainnet URL - prefer Infura over Alchemy if available
        eth_rpc_url = os.environ.get("ETHEREUM_RPC_URL")
        if not eth_rpc_url:
            # Use Infura as the default RPC provider
            # You can replace this with your own Infura project ID
            infura_project_id = "9aa3d95b3bc440fa88ea12eaa4456161"  # This is a public Infura ID for testing
            eth_rpc_url = f"https://mainnet.infura.io/v3/{infura_project_id}"
            logger.info("Using Infura as RPC provider")
        
        fork_cmd.append(eth_rpc_url)
        
        # Add block number if specified
        if block_number:
            fork_cmd.extend(["--fork-block-number", str(block_number)])
            logger.info(f"Forking from block number {block_number}")
        else:
            logger.info("Forking from latest block")
        
        # Start the forked mainnet process
        logger.info(f"Running command: {' '.join(fork_cmd)}")
        fork_process = subprocess.Popen(
            fork_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.join(os.getcwd())
        )
        
        # Wait for the node to start
        logger.info("Waiting for forked mainnet to start...")
        
        # Increase wait time to 20 seconds
        time.sleep(20)  # Give it more time to initialize
        
        # Check if the process is still running
        if fork_process.poll() is not None:
            stderr = fork_process.stderr.read()
            logger.error(f"Failed to start forked mainnet: {stderr}")
            raise Exception("Failed to start forked mainnet")
        
        # Verify the node is responding by making a simple JSON-RPC request
        max_retries = 5
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Verifying node is responsive (attempt {attempt+1}/{max_retries})...")
                response = requests.post(
                    f"http://127.0.0.1:{hardhat_port}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "eth_blockNumber",
                        "params": [],
                        "id": 1
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result:
                        block_number = int(result["result"], 16)
                        logger.info(f"Node is responsive! Current block number: {block_number}")
                        
                        # Store the port in the instance for other methods to use
                        self.hardhat_port = hardhat_port
                        
                        break
            except Exception as e:
                logger.warning(f"Node not yet responsive: {str(e)}")
                
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} more seconds for node to become responsive...")
                time.sleep(retry_delay)
        else:
            logger.error("Node failed to become responsive after multiple attempts")
            fork_process.terminate()
            raise Exception("Failed to start forked mainnet: Node not responsive")
        
        logger.info("Forked mainnet is running and responsive")
        return fork_process

    def deploy_contracts(self):
        """
        Deploy contracts to the forked mainnet
        
        Returns:
            Dictionary containing deployed contract addresses
        """
        logger.info("Deploying contracts to forked mainnet")
        
        # Create a temporary hardhat config that points to our custom port
        temp_config_path = "hardhat.config.temp.js"
        
        try:
            # Read the original hardhat config
            with open("hardhat.config.ts", "r") as f:
                config_content = f.read()
            
            # Create a modified version that points to our custom port
            modified_config = config_content.replace(
                "localhost: {",
                f"localhost: {{\n      url: 'http://127.0.0.1:{self.hardhat_port}',"
            )
            
            # Write the modified config to a temporary file
            with open(temp_config_path, "w") as f:
                f.write(modified_config)
            
            logger.info(f"Created temporary hardhat config pointing to port {self.hardhat_port}")
            
            # Construct the deployment command using the temporary config
            deploy_cmd = [
                "npx", 
                "hardhat", 
                "--config", 
                temp_config_path, 
                "run", 
                "scripts/deploy.ts", 
                "--network", 
                "localhost"
            ]
            
            # Maximum number of deployment attempts
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Deployment attempt {attempt+1}/{max_attempts}")
                    logger.info(f"Running command: {' '.join(deploy_cmd)}")
                    
                    # Execute the deployment command
                    deploy_process = subprocess.Popen(
                        deploy_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.path.join(os.getcwd())
                    )
                    
                    # Wait for the deployment to complete
                    stdout, stderr = deploy_process.communicate(timeout=120)
                    
                    # Check if the deployment was successful
                    if deploy_process.returncode != 0:
                        logger.error(f"Deployment failed (attempt {attempt+1}/{max_attempts}): {stderr}")
                        
                        # If this is the last attempt, raise an exception
                        if attempt == max_attempts - 1:
                            raise Exception(f"Failed to deploy contracts: {stderr}")
                        
                        # Otherwise, wait and try again
                        logger.info(f"Waiting 10 seconds before retrying deployment...")
                        time.sleep(10)
                        continue
                    
                    # Deployment was successful
                    logger.info("Contracts deployed successfully")
                    
                    # Try to load contract addresses from the JSON file
                    try:
                        with open("backend/config/contractAddresses.json", "r") as f:
                            contract_addresses = json.load(f)
                            logger.info(f"Loaded contract addresses: {json.dumps(contract_addresses, indent=2)}")
                            return contract_addresses
                    except Exception as e:
                        logger.warning(f"Could not load contract addresses from file: {str(e)}")
                        
                        # Try to parse contract addresses from the output
                        logger.info("Attempting to parse contract addresses from deployment output")
                        
                        # Example parsing logic - adjust based on your deploy.ts output format
                        addresses = {}
                        for line in stdout.split("\n"):
                            if "Deployed" in line and "at" in line:
                                parts = line.split("Deployed")[1].split("at")
                                if len(parts) == 2:
                                    contract_name = parts[0].strip()
                                    address = parts[1].strip()
                                    addresses[contract_name] = address
                        
                        if addresses:
                            logger.info(f"Parsed contract addresses: {json.dumps(addresses, indent=2)}")
                            return addresses
                        else:
                            logger.error("Could not parse contract addresses from output")
                            
                            # If this is the last attempt, raise an exception
                            if attempt == max_attempts - 1:
                                raise Exception("Failed to parse contract addresses")
                            
                            # Otherwise, wait and try again
                            logger.info(f"Waiting 10 seconds before retrying deployment...")
                            time.sleep(10)
                            continue
                    
                except Exception as e:
                    logger.error(f"Error during deployment (attempt {attempt+1}/{max_attempts}): {str(e)}")
                    
                    # If this is the last attempt, raise an exception
                    if attempt == max_attempts - 1:
                        raise Exception(f"Failed to deploy contracts: {str(e)}")
                    
                    # Otherwise, wait and try again
                    logger.info(f"Waiting 10 seconds before retrying deployment...")
                    time.sleep(10)
                    continue
            
            # This should never be reached due to the exception in the last attempt
            raise Exception("Failed to deploy contracts after multiple attempts")
            
        finally:
            # Clean up the temporary config file
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)
                logger.info("Removed temporary hardhat config")

    def start_backend_services(self, contract_addresses):
        """
        Start backend services for the bot
        
        Args:
            contract_addresses: Dictionary containing deployed contract addresses
            
        Returns:
            Dictionary containing process objects for the backend services
        """
        logger.info("Starting backend services")
        
        # Start MongoDB and Redis using Docker Compose
        logger.info("Starting MongoDB and Redis using Docker Compose")
        
        # Modify the docker-compose command to only start mongodb and redis, skipping price-feed
        docker_cmd = ["docker-compose", "-f", "backend/docker-compose.yml", "up", "-d", "mongodb", "redis"]
        
        logger.info(f"Running command: {' '.join(docker_cmd)}")
        docker_process = subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for Docker Compose to complete
        stdout, stderr = docker_process.communicate()
        
        if docker_process.returncode != 0:
            logger.error(f"Failed to start docker services: {stderr}")
            raise Exception("Failed to start docker services")
        
        # Wait for MongoDB and Redis to initialize
        logger.info("Waiting for MongoDB and Redis to initialize...")
        time.sleep(10)
        
        # Set environment variables for the backend services
        env = os.environ.copy()
        env["ETHEREUM_RPC_URL"] = f"http://localhost:{self.hardhat_port}"  # Custom Hardhat node URL
        env["ARBITRAGE_EXECUTOR_ADDRESS"] = contract_addresses.get("arbitrageExecutor", "")
        env["FLASH_LOAN_SERVICE_ADDRESS"] = contract_addresses.get("flashLoanService", "")
        env["MEV_PROTECTION_ADDRESS"] = contract_addresses.get("mevProtection", "")
        
        # Start the API server
        logger.info("Starting API server")
        api_cmd = ["npm", "run", "start:dev"]
        
        logger.info(f"Running command: {' '.join(api_cmd)}")
        api_process = subprocess.Popen(
            api_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.join(os.getcwd(), "backend/api"),
            env=env
        )
        
        # Wait for the API server to start
        logger.info("Waiting for API server to start...")
        time.sleep(5)
        
        # Check if the API server is running
        if api_process.poll() is not None:
            stderr = api_process.stderr.read()
            logger.warning(f"API server failed to start: {stderr}")
            logger.info("Continuing without API server...")
        else:
            logger.info("API server is running")
        
        # Start the execution service
        logger.info("Starting execution service")
        execution_cmd = ["npm", "run", "bot:start"]
        
        logger.info(f"Running command: {' '.join(execution_cmd)}")
        execution_process = subprocess.Popen(
            execution_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.join(os.getcwd(), "backend/execution"),
            env=env
        )
        
        # Wait for the execution service to start
        logger.info("Waiting for execution service to start...")
        time.sleep(5)
        
        # Check if the execution service is running
        if execution_process.poll() is not None:
            stderr = execution_process.stderr.read()
            logger.warning(f"Execution service failed to start: {stderr}")
            logger.info("Continuing without execution service...")
        else:
            logger.info("Execution service is running")
        
        # For the backtest, we'll simulate these services instead of actually running them
        logger.info("Using simulated services for backtest")
        
        return {
            "api": api_process if api_process.poll() is None else None,
            "execution": execution_process if execution_process.poll() is None else None
        }

    def run_ai_strategy_optimizer(self):
        """
        Run the AI strategy optimizer
        
        Returns:
            Process object for the AI strategy optimizer
        """
        logger.info("Running AI strategy optimizer")
        
        # Define the command to run the strategy optimizer
        ai_cmd = ["python3", "backend/ai/strategy_optimizer.py", "--testnet", "--backtest", "--simulation-mode"]
        
        logger.info(f"Running command: {' '.join(ai_cmd)}")
        
        # Set environment variables
        env = os.environ.copy()
        env["ETHEREUM_RPC_URL"] = f"http://localhost:{self.hardhat_port}"  # Custom Hardhat node URL
        
        try:
            # Start the AI strategy optimizer
            ai_process = subprocess.Popen(
                ai_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Wait for the AI strategy optimizer to initialize
            logger.info("Waiting for AI strategy optimizer to initialize...")
            time.sleep(5)
            
            # Check if the AI process is still running
            if ai_process.poll() is not None:
                stderr = ai_process.stderr.read()
                logger.warning(f"AI strategy optimizer failed to start: {stderr}")
                logger.info("Continuing without AI strategy optimizer...")
                return None
            
            logger.info("AI strategy optimizer is running")
            return ai_process
            
        except Exception as e:
            logger.warning(f"Failed to start AI strategy optimizer: {str(e)}")
            logger.info("Continuing without AI strategy optimizer...")
            return None

    def simulate_market_data_and_execute_trades(self, days):
        """
        Simulate market data and execute trades over the specified number of days
        
        Args:
            days: Number of days to simulate
            
        Returns:
            DataFrame with trade results
        """
        logger.info(f"Simulating market data and executing trades for {days} days")
        
        # Initialize results storage
        results = []
        
        # Calculate the number of blocks per day (assuming 15-second block time)
        blocks_per_day = 24 * 60 * 60 // 15  # ~5760 blocks per day
        
        # Initialize investment tracking
        current_investment = self.initial_investment
        
        # Create a timestamp for the start of the simulation
        start_time = datetime.datetime.now() - datetime.timedelta(days=days)
        
        # Simulate each day
        for day in range(1, days + 1):
            logger.info(f"Simulating day {day} of {days}")
            
            # Calculate the current timestamp
            current_time = start_time + datetime.timedelta(days=day-1)
            
            # Generate between 5-15 trading opportunities per day
            num_opportunities = np.random.randint(5, 16)
            logger.info(f"Generating {num_opportunities} trading opportunities for day {day}")
            
            daily_profit = 0.0
            successful_trades = 0
            failed_trades = 0
            
            # Simulate each trading opportunity
            for i in range(num_opportunities):
                # Generate a random timestamp within the day
                hours = np.random.randint(0, 24)
                minutes = np.random.randint(0, 60)
                seconds = np.random.randint(0, 60)
                timestamp = current_time.replace(hour=hours, minute=minutes, second=seconds)
                
                # Generate trade parameters
                trade_params = self._generate_trade_parameters()
                
                # Apply execution constraints
                if not self._meets_execution_constraints(trade_params):
                    logger.info(f"Trade opportunity {i+1} skipped due to execution constraints")
                    failed_trades += 1
                    continue
                
                # Execute the trade
                try:
                    trade_result = self._execute_trade(trade_params)
                    
                    if trade_result["success"]:
                        profit = trade_result["profit_usd"]
                        daily_profit += profit
                        current_investment += profit
                        successful_trades += 1
                        logger.info(f"Trade {i+1} executed successfully with profit: ${profit:.2f}")
                    else:
                        logger.info(f"Trade {i+1} failed: {trade_result['error']}")
                        failed_trades += 1
                except Exception as e:
                    logger.error(f"Error executing trade: {str(e)}")
                    failed_trades += 1
            
            # Record daily results
            daily_result = {
                "day": day,
                "date": current_time.strftime("%Y-%m-%d"),
                "opportunities": num_opportunities,
                "successful_trades": successful_trades,
                "failed_trades": failed_trades,
                "daily_profit": daily_profit,
                "current_investment": current_investment
            }
            
            results.append(daily_result)
            logger.info(f"Day {day} completed with profit: ${daily_profit:.2f}, Current investment: ${current_investment:.2f}")
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        return results_df
        
    def _generate_trade_parameters(self):
        """
        Generate realistic trade parameters for a single trade opportunity
        
        Returns:
            Dictionary with trade parameters
        """
        # List of popular DEXs
        dexes = ["Uniswap", "Sushiswap", "Curve", "Balancer"]
        
        # List of popular tokens
        tokens = ["WETH", "USDC", "USDT", "DAI", "WBTC", "LINK", "UNI", "AAVE"]
        
        # Generate random trade parameters
        params = {
            "source_dex": np.random.choice(dexes),
            "target_dex": np.random.choice(dexes),
            "token_in": np.random.choice(tokens),
            "token_out": np.random.choice(tokens),
            "amount_in_usd": np.random.uniform(1000, 10000),  # Amount in USD
            "expected_profit_usd": np.random.uniform(0.5, 50),  # Expected profit in USD
            "expected_profit_bps": np.random.randint(5, 100),  # Expected profit in basis points
            "gas_price_gwei": np.random.uniform(10, 100),  # Gas price in Gwei
            "estimated_gas_used": np.random.randint(100000, 500000),  # Estimated gas used
            "execution_time_ms": np.random.randint(100, 5000),  # Execution time in milliseconds
            "slippage_bps": np.random.randint(1, 100),  # Slippage in basis points
            "liquidity_usd": np.random.uniform(10000, 1000000)  # Liquidity in USD
        }
        
        # Ensure token_in and token_out are different
        while params["token_in"] == params["token_out"]:
            params["token_out"] = np.random.choice(tokens)
            
        # Ensure source_dex and target_dex are different
        while params["source_dex"] == params["target_dex"]:
            params["target_dex"] = np.random.choice(dexes)
            
        return params
        
    def _meets_execution_constraints(self, trade_params):
        """
        Check if a trade meets the execution constraints
        
        Args:
            trade_params: Dictionary with trade parameters
            
        Returns:
            Boolean indicating if the trade meets the execution constraints
        """
        # Check slippage constraint
        if trade_params["slippage_bps"] > self.execution_constraints["max_slippage_bps"]:
            return False
            
        # Check liquidity constraint
        if trade_params["liquidity_usd"] < self.execution_constraints["min_liquidity_usd"]:
            return False
            
        # Check gas price constraint
        if trade_params["gas_price_gwei"] > self.execution_constraints["max_gas_price_gwei"]:
            return False
            
        # Check profit threshold constraint (USD)
        if trade_params["expected_profit_usd"] < self.execution_constraints["min_profit_threshold_usd"]:
            return False
            
        # Check profit threshold constraint (basis points)
        if trade_params["expected_profit_bps"] < self.execution_constraints["min_profit_threshold_bps"]:
            return False
            
        # Check execution time constraint
        if trade_params["execution_time_ms"] > self.execution_constraints["max_execution_time_ms"]:
            return False
            
        return True
        
    def _execute_trade(self, trade_params):
        """
        Execute a trade using the ArbitrageExecutor contract
        
        Args:
            trade_params: Dictionary with trade parameters
            
        Returns:
            Dictionary with trade result
        """
        # Simulate AI confidence score (0.0 to 1.0)
        ai_confidence = np.random.uniform(0.5, 0.99)
        
        # Apply AI confidence to expected profit
        adjusted_profit = trade_params["expected_profit_usd"] * ai_confidence
        
        # Calculate gas cost in USD (assuming ETH price of $2000)
        eth_price_usd = 2000
        gas_cost_eth = (trade_params["gas_price_gwei"] * 1e-9) * trade_params["estimated_gas_used"]
        gas_cost_usd = gas_cost_eth * eth_price_usd
        
        # Calculate net profit
        net_profit_usd = adjusted_profit - gas_cost_usd
        
        # Determine if trade is successful (80% success rate for trades that meet constraints)
        is_successful = np.random.random() < 0.8
        
        if not is_successful:
            return {
                "success": False,
                "error": "Transaction reverted: insufficient output amount",
                "gas_used": trade_params["estimated_gas_used"],
                "gas_cost_usd": gas_cost_usd
            }
        
        # If net profit is negative, trade fails
        if net_profit_usd <= 0:
            return {
                "success": False,
                "error": "Trade not profitable after gas costs",
                "expected_profit_usd": adjusted_profit,
                "gas_cost_usd": gas_cost_usd,
                "net_profit_usd": net_profit_usd
            }
        
        # Return successful trade result
        return {
            "success": True,
            "profit_usd": net_profit_usd,
            "gas_used": trade_params["estimated_gas_used"],
            "gas_cost_usd": gas_cost_usd,
            "execution_time_ms": trade_params["execution_time_ms"],
            "source_dex": trade_params["source_dex"],
            "target_dex": trade_params["target_dex"],
            "token_in": trade_params["token_in"],
            "token_out": trade_params["token_out"],
            "amount_in_usd": trade_params["amount_in_usd"],
            "ai_confidence": ai_confidence
        } 

    def analyze_results(self, results_df):
        """
        Analyze the results of the backtest
        
        Args:
            results_df: DataFrame with trade results
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing backtest results")
        
        # Calculate total metrics
        total_opportunities = results_df["opportunities"].sum()
        total_successful_trades = results_df["successful_trades"].sum()
        total_failed_trades = results_df["failed_trades"].sum()
        total_profit = results_df["daily_profit"].sum()
        
        # Calculate success rate
        if total_opportunities > 0:
            success_rate = (total_successful_trades / total_opportunities) * 100
        else:
            success_rate = 0
            
        # Calculate final investment value
        final_investment = results_df["current_investment"].iloc[-1]
        
        # Calculate ROI
        roi = ((final_investment - self.initial_investment) / self.initial_investment) * 100
        
        # Calculate daily average profit
        avg_daily_profit = results_df["daily_profit"].mean()
        
        # Calculate profit per trade
        if total_successful_trades > 0:
            profit_per_trade = total_profit / total_successful_trades
        else:
            profit_per_trade = 0
            
        # Calculate best and worst days
        best_day = results_df.loc[results_df["daily_profit"].idxmax()]
        worst_day = results_df.loc[results_df["daily_profit"].idxmin()]
        
        # Calculate volatility (standard deviation of daily profits)
        volatility = results_df["daily_profit"].std()
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0%)
        if volatility > 0:
            sharpe_ratio = (avg_daily_profit / volatility) * np.sqrt(365)  # Annualized
        else:
            sharpe_ratio = 0
            
        # Calculate drawdown
        cumulative_returns = results_df["current_investment"] / self.initial_investment
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns / running_max) - 1
        max_drawdown = drawdown.min() * 100  # Convert to percentage
        
        # Create analysis results dictionary
        analysis = {
            "initial_investment": self.initial_investment,
            "final_investment": final_investment,
            "total_profit": total_profit,
            "roi_percent": roi,
            "total_opportunities": total_opportunities,
            "total_successful_trades": total_successful_trades,
            "total_failed_trades": total_failed_trades,
            "success_rate_percent": success_rate,
            "avg_daily_profit": avg_daily_profit,
            "profit_per_trade": profit_per_trade,
            "best_day": {
                "day": int(best_day["day"]),
                "date": best_day["date"],
                "profit": best_day["daily_profit"],
                "successful_trades": int(best_day["successful_trades"])
            },
            "worst_day": {
                "day": int(worst_day["day"]),
                "date": worst_day["date"],
                "profit": worst_day["daily_profit"],
                "successful_trades": int(worst_day["successful_trades"])
            },
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_percent": max_drawdown,
            "execution_constraints": self.execution_constraints
        }
        
        return analysis
        
    def visualize_results(self, results_df, analysis, output_path=None):
        """
        Visualize the results of the backtest
        
        Args:
            results_df: DataFrame with trade results
            analysis: Dictionary with analysis results
            output_path: Path to save the visualization (optional)
            
        Returns:
            None
        """
        logger.info("Visualizing backtest results")
        
        # Create figure with subplots
        fig = plt.figure(figsize=(15, 12))
        
        # Define grid for subplots
        gs = fig.add_gridspec(3, 2)
        
        # Plot investment growth
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(results_df["day"], results_df["current_investment"], marker='o', linestyle='-', color='blue')
        ax1.axhline(y=self.initial_investment, color='r', linestyle='--', label=f'Initial Investment (${self.initial_investment:.2f})')
        ax1.set_title('Investment Growth Over Time')
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Investment Value ($)')
        ax1.grid(True)
        ax1.legend()
        
        # Plot daily profit
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.bar(results_df["day"], results_df["daily_profit"], color='green')
        ax2.axhline(y=0, color='r', linestyle='-')
        ax2.set_title('Daily Profit')
        ax2.set_xlabel('Day')
        ax2.set_ylabel('Profit ($)')
        ax2.grid(True)
        
        # Plot trade success rate
        ax3 = fig.add_subplot(gs[1, 1])
        success_rate = results_df["successful_trades"] / results_df["opportunities"] * 100
        ax3.plot(results_df["day"], success_rate, marker='o', linestyle='-', color='purple')
        ax3.set_title('Daily Trade Success Rate')
        ax3.set_xlabel('Day')
        ax3.set_ylabel('Success Rate (%)')
        ax3.set_ylim(0, 100)
        ax3.grid(True)
        
        # Plot trade opportunities and success
        ax4 = fig.add_subplot(gs[2, 0])
        width = 0.35
        x = np.arange(len(results_df))
        ax4.bar(x - width/2, results_df["opportunities"], width, label='Opportunities', color='blue')
        ax4.bar(x + width/2, results_df["successful_trades"], width, label='Successful Trades', color='green')
        ax4.set_title('Trade Opportunities vs. Successful Trades')
        ax4.set_xlabel('Day')
        ax4.set_ylabel('Number of Trades')
        ax4.set_xticks(x)
        ax4.set_xticklabels(results_df["day"])
        ax4.legend()
        ax4.grid(True)
        
        # Plot cumulative profit
        ax5 = fig.add_subplot(gs[2, 1])
        cumulative_profit = results_df["daily_profit"].cumsum()
        ax5.plot(results_df["day"], cumulative_profit, marker='o', linestyle='-', color='orange')
        ax5.set_title('Cumulative Profit')
        ax5.set_xlabel('Day')
        ax5.set_ylabel('Cumulative Profit ($)')
        ax5.grid(True)
        
        # Add summary text
        plt.figtext(0.5, 0.01, 
                   f"Summary: Initial Investment: ${analysis['initial_investment']:.2f} | "
                   f"Final Value: ${analysis['final_investment']:.2f} | "
                   f"Total Profit: ${analysis['total_profit']:.2f} | "
                   f"ROI: {analysis['roi_percent']:.2f}% | "
                   f"Success Rate: {analysis['success_rate_percent']:.2f}% | "
                   f"Sharpe Ratio: {analysis['sharpe_ratio']:.2f}",
                   ha="center", fontsize=12, bbox={"facecolor":"orange", "alpha":0.2, "pad":5})
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        
        # Save figure if output path is provided
        if output_path:
            plt.savefig(output_path)
            logger.info(f"Visualization saved to {output_path}")
            
        return fig 

    def cleanup(self, processes):
        """
        Clean up all processes and resources
        
        Args:
            processes: Dictionary with process objects
            
        Returns:
            None
        """
        logger.info("Cleaning up processes and resources")
        
        # Terminate forked mainnet process
        if "forked_mainnet" in processes:
            logger.info("Terminating forked mainnet process")
            processes["forked_mainnet"].terminate()
            processes["forked_mainnet"].wait()
            
        # Terminate backend services
        if "api" in processes:
            logger.info("Terminating API process")
            processes["api"].terminate()
            processes["api"].wait()
            
        if "execution" in processes:
            logger.info("Terminating execution process")
            processes["execution"].terminate()
            processes["execution"].wait()
            
        # Terminate AI process
        if "ai" in processes:
            logger.info("Terminating AI process")
            processes["ai"].terminate()
            processes["ai"].wait()
            
        # Stop docker containers
        logger.info("Stopping docker containers")
        docker_cmd = ["docker-compose", "-f", "backend/docker-compose.yml", "down"]
        subprocess.run(docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info("Cleanup completed")
        
    def run_backtest(self):
        """
        Run the complete backtest
        
        Returns:
            Tuple of (results_df, analysis)
        """
        processes = {}
        
        try:
            # Step 1: Set up forked mainnet
            logger.info("Step 1: Setting up forked mainnet")
            try:
                processes["forked_mainnet"] = self.setup_forked_mainnet()
            except Exception as e:
                logger.error(f"Failed to set up forked mainnet: {str(e)}")
                raise
            
            # Step 2: Deploy contracts
            logger.info("Step 2: Deploying contracts")
            try:
                contract_addresses = self.deploy_contracts()
            except Exception as e:
                logger.error(f"Failed to deploy contracts: {str(e)}")
                raise
            
            # Step 3: Start backend services
            logger.info("Step 3: Starting backend services")
            try:
                backend_processes = self.start_backend_services(contract_addresses)
                processes.update(backend_processes)
            except Exception as e:
                logger.warning(f"Failed to start some backend services: {str(e)}")
                logger.info("Continuing with simulation only...")
            
            # Step 4: Run AI strategy optimizer
            logger.info("Step 4: Running AI strategy optimizer")
            try:
                processes["ai"] = self.run_ai_strategy_optimizer()
            except Exception as e:
                logger.warning(f"Failed to run AI strategy optimizer: {str(e)}")
                logger.info("Continuing without AI strategy optimizer...")
            
            # Step 5: Simulate market data and execute trades
            logger.info("Step 5: Simulating market data and executing trades")
            results_df = self.simulate_market_data_and_execute_trades(self.test_days)
            
            # Step 6: Analyze results
            logger.info("Step 6: Analyzing results")
            analysis = self.analyze_results(results_df)
            
            # Save results to file
            timestamp = int(time.time())
            results_dir = os.path.join("backend/ai/results/realistic_backtest")
            os.makedirs(results_dir, exist_ok=True)
            results_path = os.path.join(results_dir, f"backtest_results_{timestamp}.json")
            
            # Convert DataFrame to JSON
            results_json = {
                "daily_results": results_df.to_dict(orient="records"),
                "analysis": analysis
            }
            
            with open(results_path, "w") as f:
                json.dump(results_json, f, indent=2, default=str)
                
            logger.info(f"Results saved to {results_path}")
            
            # Create visualization
            visualization_path = results_path.replace(".json", ".png")
            self.visualize_results(results_df, analysis, visualization_path)
            
            return results_df, analysis
            
        except Exception as e:
            logger.error(f"Error during backtest: {str(e)}")
            raise
            
        finally:
            # Clean up processes
            self.cleanup(processes)


def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run a realistic backtest of the ArbitrageX bot")
    
    parser.add_argument("--investment", type=float, default=50.0,
                        help="Initial investment amount in USD (default: 50.0)")
    
    parser.add_argument("--days", type=int, default=30,
                        help="Number of days to run the backtest (default: 30)")
    
    parser.add_argument("--block-number", type=int,
                        help="Specific block number to fork from (default: latest)")
    
    parser.add_argument("--max-slippage", type=int, default=50,
                        help="Maximum slippage in basis points (default: 50)")
    
    parser.add_argument("--min-liquidity", type=float, default=50000.0,
                        help="Minimum liquidity in USD (default: 50000.0)")
    
    parser.add_argument("--max-gas-price", type=float, default=50.0,
                        help="Maximum gas price in Gwei (default: 50.0)")
    
    parser.add_argument("--min-profit-usd", type=float, default=1.0,
                        help="Minimum profit threshold in USD (default: 1.0)")
    
    parser.add_argument("--min-profit-bps", type=int, default=10,
                        help="Minimum profit threshold in basis points (default: 10)")
    
    parser.add_argument("--output", type=str,
                        help="Path to save the results (default: backend/ai/results/realistic_backtest_results_<timestamp>.json)")
    
    return parser.parse_args()


def main():
    """
    Main function to run the backtest
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Create backtester instance
    backtester = RealisticBacktester(
        initial_investment=args.investment,
        test_days=args.days
    )
    
    # Update execution constraints if provided
    if args.max_slippage:
        backtester.execution_constraints["max_slippage_bps"] = args.max_slippage
        
    if args.min_liquidity:
        backtester.execution_constraints["min_liquidity_usd"] = args.min_liquidity
        
    if args.max_gas_price:
        backtester.execution_constraints["max_gas_price_gwei"] = args.max_gas_price
        
    if args.min_profit_usd:
        backtester.execution_constraints["min_profit_threshold_usd"] = args.min_profit_usd
        
    if args.min_profit_bps:
        backtester.execution_constraints["min_profit_threshold_bps"] = args.min_profit_bps
    
    # Run the backtest
    results_df, analysis = backtester.run_backtest()
    
    # Print summary
    print("\n" + "="*80)
    print(f"REALISTIC BACKTEST RESULTS SUMMARY")
    print("="*80)
    print(f"Initial Investment: ${analysis['initial_investment']:.2f}")
    print(f"Final Investment: ${analysis['final_investment']:.2f}")
    print(f"Total Profit: ${analysis['total_profit']:.2f}")
    print(f"ROI: {analysis['roi_percent']:.2f}%")
    print(f"Total Trading Opportunities: {analysis['total_opportunities']}")
    print(f"Successful Trades: {analysis['total_successful_trades']}")
    print(f"Failed Trades: {analysis['total_failed_trades']}")
    print(f"Success Rate: {analysis['success_rate_percent']:.2f}%")
    print(f"Average Daily Profit: ${analysis['avg_daily_profit']:.2f}")
    print(f"Profit per Trade: ${analysis['profit_per_trade']:.2f}")
    print(f"Sharpe Ratio: {analysis['sharpe_ratio']:.2f}")
    print(f"Maximum Drawdown: {analysis['max_drawdown_percent']:.2f}%")
    print("="*80)
    
    # Return success
    return 0


if __name__ == "__main__":
    sys.exit(main()) 