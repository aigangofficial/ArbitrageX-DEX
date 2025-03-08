#!/usr/bin/env python3
"""
ArbitrageX Setup Script

This script installs the ArbitrageX package, making it importable from anywhere.
"""

from setuptools import setup, find_packages

setup(
    name="arbitragex",
    version="1.0.0",
    description="ArbitrageX - Multi-Chain DEX Arbitrage Platform with AI",
    author="ArbitrageX Team",
    author_email="info@arbitragex.io",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.3.3",
        "flask-cors>=4.0.0",
        "pymongo>=4.6.1",
        "redis>=5.0.1",
        "web3>=6.15.1",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "websockets>=12.0",
        "pydantic>=2.5.3",
    ],
)