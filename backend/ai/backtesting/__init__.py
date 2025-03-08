"""
ArbitrageX Backtesting Package

This package provides tools for backtesting trading strategies
using historical market data.
"""

from .backtester import Backtester, BacktestConfig, BacktestResult

__all__ = ['Backtester', 'BacktestConfig', 'BacktestResult'] 