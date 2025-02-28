#!/usr/bin/env python3

import os
import json
import re
from typing import Dict, List
import shutil

# Define the replacements for outdated terms
REPLACEMENTS = {
    "6+ months of real trade data": "6+ months of real trade data",
    "AI-driven arbitrage with competitor analysis": "AI-driven arbitrage with competitor analysis",
    "multi-chain flash loan with AI optimization": "multi-chain flash loan with AI optimization",
    "dynamic gas optimization with competitor tracking": "dynamic gas optimization with competitor tracking",
    "AI-based profit prediction with risk assessment": "AI-based profit prediction with risk assessment"
}

# File patterns to update
FILE_PATTERNS = [
    "*.md",
    "*.json",
    "*.ts",
    "*.py",
    "*.sol"
]

def ensure_directory_exists(path: str) -> None:
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)

def update_file_content(content: str) -> str:
    """Update content with new terminology"""
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)
    return content

def process_file(file_path: str) -> None:
    """Process a single file"""
    print(f"Processing {file_path}...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        updated_content = update_file_content(content)

        if content != updated_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Updated {file_path}")
        else:
            print(f"ℹ️ No changes needed in {file_path}")

    except Exception as e:
        print(f"❌ Error processing {file_path}: {str(e)}")

def create_required_directories() -> None:
    """Create required project directories"""
    directories = [
        "docs",
        "config",
        "backend/bot",
        "backend/ai",
        "frontend/components",
        "frontend/pages",
        "frontend/services"
    ]

    for directory in directories:
        ensure_directory_exists(directory)
        print(f"✅ Ensured directory exists: {directory}")

def update_project_files() -> None:
    """Update all project files"""
    for root, _, files in os.walk("."):
        for file in files:
            if any(file.endswith(pattern.replace("*", "")) for pattern in FILE_PATTERNS):
                file_path = os.path.join(root, file)
                process_file(file_path)

def verify_configuration_files() -> None:
    """Verify and update configuration files"""
    config_files = {
        "network_settings.json": {
            "networks": {},
            "globalSettings": {},
            "aiSettings": {}
        },
        "competitor_analysis.json": {
            "competitorTracking": {},
            "decoyStrategies": {},
            "mempoolMonitoring": {}
        },
        "trading_limits.json": {
            "globalLimits": {},
            "networkSpecificLimits": {},
            "aiRiskManagement": {}
        }
    }

    for file_name, template in config_files.items():
        file_path = os.path.join("config", file_name)
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2)
            print(f"✅ Created {file_name}")

def main() -> None:
    """Main execution function"""
    print("🚀 Starting project update process...")

    # Create required directories
    create_required_directories()

    # Verify configuration files
    verify_configuration_files()

    # Update project files
    update_project_files()

    print("\n✨ Project update completed!")
    print("\nNext steps:")
    print("1. Review updated files")
    print("2. Run tests to verify functionality")
    print("3. Commit changes to version control")

if __name__ == "__main__":
    main()
