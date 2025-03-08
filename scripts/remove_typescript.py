#!/usr/bin/env python3
"""
Script to remove all TypeScript files from the project and clean up related configuration files.
This is part of the transition from TypeScript to Python.
"""

import os
import shutil
import glob
import json
from pathlib import Path

def remove_typescript_files():
    """Remove all TypeScript files from the project."""
    print("Removing TypeScript files...")
    
    # Find all TypeScript files
    ts_files = glob.glob("**/*.ts", recursive=True)
    tsx_files = glob.glob("**/*.tsx", recursive=True)
    
    # Exclude node_modules and typechain-types
    ts_files = [f for f in ts_files if "node_modules" not in f and "typechain-types" not in f]
    tsx_files = [f for f in tsx_files if "node_modules" not in f and "typechain-types" not in f]
    
    # Print summary
    print(f"Found {len(ts_files)} .ts files and {len(tsx_files)} .tsx files to remove")
    
    # Remove files
    for file in ts_files + tsx_files:
        try:
            os.remove(file)
            print(f"Removed: {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")
    
    # Remove TypeScript-specific directories
    ts_dirs = [
        "dist",
        "backend/dist",
        "frontend/.next",
        "typechain-types"
    ]
    
    for dir_path in ts_dirs:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"Removed directory: {dir_path}")
            except Exception as e:
                print(f"Error removing directory {dir_path}: {e}")

def update_gitignore():
    """Update .gitignore file to remove TypeScript-specific entries and add Python-specific ones."""
    print("Updating .gitignore file...")
    
    if not os.path.exists(".gitignore"):
        print("No .gitignore file found. Creating one...")
        with open(".gitignore", "w") as f:
            f.write("")
    
    with open(".gitignore", "r") as f:
        lines = f.readlines()
    
    # Remove TypeScript-specific entries
    ts_entries = [
        "node_modules",
        "dist",
        ".next",
        "typechain-types",
        "coverage",
        "*.tsbuildinfo",
        "next-env.d.ts"
    ]
    
    new_lines = [line for line in lines if not any(entry in line for entry in ts_entries)]
    
    # Add Python-specific entries
    py_entries = [
        "# Python",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "build/",
        "develop-eggs/",
        "dist/",
        "downloads/",
        "eggs/",
        ".eggs/",
        "lib/",
        "lib64/",
        "parts/",
        "sdist/",
        "var/",
        "wheels/",
        "*.egg-info/",
        ".installed.cfg",
        "*.egg",
        "MANIFEST",
        ".env",
        ".venv",
        "env/",
        "venv/",
        "ENV/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".tox/",
        ".nox/",
        ".hypothesis/",
        ".DS_Store"
    ]
    
    # Check if Python entries already exist
    if not any("__pycache__" in line for line in new_lines):
        new_lines.extend([f"{entry}\n" for entry in py_entries])
    
    with open(".gitignore", "w") as f:
        f.writelines(new_lines)
    
    print("Updated .gitignore file")

def create_requirements_file():
    """Create a requirements.txt file based on Python dependencies."""
    print("Creating requirements.txt file...")
    
    requirements = [
        "# Web Framework",
        "flask==2.3.3",
        "flask-cors==4.0.0",
        "gunicorn==21.2.0",
        
        "# Database",
        "pymongo==4.6.1",
        "redis==5.0.1",
        
        "# Blockchain",
        "web3==6.15.1",
        "eth-account==0.10.0",
        
        "# AI/ML",
        "tensorflow==2.15.0",
        "numpy==1.26.3",
        "pandas==2.1.4",
        "scikit-learn==1.4.0",
        
        "# Utilities",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "websockets==12.0",
        "pydantic==2.5.3",
        
        "# Testing",
        "pytest==7.4.3",
        "pytest-cov==4.1.0",
        
        "# Monitoring",
        "prometheus-client==0.19.0",
        "sentry-sdk==1.39.1",
        
        "# Development",
        "black==23.12.0",
        "isort==5.13.2",
        "flake8==6.1.0",
        "mypy==1.7.1"
    ]
    
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    
    print("Created requirements.txt file")

def create_setup_py():
    """Create a setup.py file for the project."""
    print("Creating setup.py file...")
    
    setup_content = """
from setuptools import setup, find_packages

setup(
    name="arbitragex",
    version="1.0.0",
    description="ArbitrageX - Multi-Chain DEX Arbitrage Platform with AI",
    author="ArbitrageX Team",
    author_email="info@arbitragex.io",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-cors",
        "pymongo",
        "redis",
        "web3",
        "eth-account",
        "tensorflow",
        "numpy",
        "pandas",
        "scikit-learn",
        "python-dotenv",
        "requests",
        "websockets",
        "pydantic",
    ],
    python_requires=">=3.10",
)
"""
    
    with open("setup.py", "w") as f:
        f.write(setup_content.strip())
    
    print("Created setup.py file")

def create_makefile():
    """Create a Makefile for common Python commands."""
    print("Creating Makefile...")
    
    makefile_content = """
.PHONY: setup test lint format clean run

setup:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest

lint:
	flake8 backend
	mypy backend

format:
	black backend
	isort backend

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

run:
	python backend/api/server.py
"""
    
    with open("Makefile", "w") as f:
        f.write(makefile_content.strip())
    
    print("Created Makefile")

def update_readme():
    """Update README.md to reflect Python-based project."""
    print("Updating README.md...")
    
    if not os.path.exists("README.md"):
        print("No README.md file found. Creating one...")
        with open("README.md", "w") as f:
            f.write("# ArbitrageX\n\nMulti-Chain DEX Arbitrage Platform with AI")
    
    with open("README.md", "r") as f:
        content = f.read()
    
    # Replace TypeScript references with Python
    content = content.replace("TypeScript", "Python")
    content = content.replace("Node.js", "Python")
    content = content.replace("npm", "pip")
    content = content.replace("yarn", "pip")
    
    # Update installation instructions
    if "## Installation" in content:
        installation_section = """
## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/arbitragex.git
   cd arbitragex
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```
"""
        
        # Find the installation section and replace it
        start = content.find("## Installation")
        end = content.find("##", start + 1)
        if end == -1:
            end = len(content)
        
        content = content[:start] + installation_section + content[end:]
    
    # Update usage instructions
    if "## Usage" in content:
        usage_section = """
## Usage

1. Start the backend server:
   ```
   python backend/api/server.py
   ```

2. Run the arbitrage scanner:
   ```
   python backend/bot/network_scanner.py
   ```

3. Run AI optimization:
   ```
   python backend/ai/strategy_optimizer.py
   ```
"""
        
        # Find the usage section and replace it
        start = content.find("## Usage")
        end = content.find("##", start + 1)
        if end == -1:
            end = len(content)
        
        content = content[:start] + usage_section + content[end:]
    
    with open("README.md", "w") as f:
        f.write(content)
    
    print("Updated README.md")

def main():
    """Main function to execute the TypeScript removal process."""
    print("Starting TypeScript to Python transition...")
    
    # Create backup directory
    backup_dir = "typescript_backup"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"Created backup directory: {backup_dir}")
    
    # Backup package.json files
    for pkg_file in ["package.json", "backend/package.json", "frontend/package.json"]:
        if os.path.exists(pkg_file):
            backup_path = os.path.join(backup_dir, pkg_file)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(pkg_file, backup_path)
            print(f"Backed up: {pkg_file} to {backup_path}")
    
    # Remove TypeScript files
    remove_typescript_files()
    
    # Update .gitignore
    update_gitignore()
    
    # Create Python-specific files
    create_requirements_file()
    create_setup_py()
    create_makefile()
    
    # Update README
    update_readme()
    
    print("TypeScript to Python transition completed successfully!")
    print("Note: You may need to manually update some Python files or create new ones to replace TypeScript functionality.")

if __name__ == "__main__":
    main() 