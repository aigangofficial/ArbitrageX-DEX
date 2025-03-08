#!/bin/bash
export ETHEREUM_RPC_URL="http://127.0.0.1:8546"
python3 backend/ai/run_realistic_backtest.py --investment 50 --days 3 --min-profit-usd 0.5 --min-liquidity 10000
