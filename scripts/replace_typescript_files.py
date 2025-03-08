#!/usr/bin/env python3
"""
Script to replace TypeScript files with Python versions.
This is part of the transition from TypeScript to Python.
"""

import os
import shutil
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def replace_file(source_path, target_path):
    """Replace a file with another file."""
    try:
        # Create backup of the target file if it exists
        if os.path.exists(target_path):
            backup_path = f"{target_path}.bak"
            shutil.copy2(target_path, backup_path)
            logger.info(f"Created backup of {target_path} at {backup_path}")
        
        # Copy the source file to the target path
        shutil.copy2(source_path, target_path)
        logger.info(f"Replaced {target_path} with {source_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error replacing {target_path} with {source_path}: {e}")
        return False

def update_shell_scripts():
    """Update shell scripts to reference Python files instead of TypeScript files."""
    logger.info("Updating shell scripts to reference Python files")
    
    # Shell scripts that need to be updated
    shell_scripts = [
        "monitor_services.sh",
        "stop_arbitragex.sh"
    ]
    
    # Replacements to make
    replacements = [
        ("api/server.ts", "api/server.py"),
        ("bot.ts", "bot.py")
    ]
    
    for script in shell_scripts:
        if not os.path.exists(script):
            logger.warning(f"Shell script {script} not found")
            continue
        
        try:
            # Create backup
            backup_path = f"{script}.bak"
            shutil.copy2(script, backup_path)
            logger.info(f"Created backup of {script} at {backup_path}")
            
            # Read the script
            with open(script, 'r') as f:
                content = f.read()
            
            # Make replacements
            for old, new in replacements:
                content = content.replace(old, new)
            
            # Write the updated script
            with open(script, 'w') as f:
                f.write(content)
            
            logger.info(f"Updated shell script: {script}")
        except Exception as e:
            logger.error(f"Error updating shell script {script}: {e}")

def update_package_json():
    """Update package.json to remove TypeScript-specific scripts and add Python ones."""
    logger.info("Updating package.json")
    
    package_json_path = "package.json"
    if not os.path.exists(package_json_path):
        logger.warning(f"package.json not found")
        return
    
    try:
        # Create backup
        backup_path = f"{package_json_path}.bak"
        shutil.copy2(package_json_path, backup_path)
        logger.info(f"Created backup of {package_json_path} at {backup_path}")
        
        # Read package.json
        import json
        with open(package_json_path, 'r') as f:
            package_json = json.load(f)
        
        # Update scripts
        if "scripts" in package_json:
            scripts = package_json["scripts"]
            
            # Remove TypeScript-specific scripts
            ts_scripts = [
                "lint:ts",
                "build:backend",
                "build:frontend",
                "test:backend",
                "test:frontend"
            ]
            
            for script in ts_scripts:
                if script in scripts:
                    del scripts[script]
            
            # Add Python-specific scripts
            python_scripts = {
                "start:backend": "cd backend && python api/server.py",
                "start:scanner": "cd backend && python bot/network_scanner.py",
                "test:python": "pytest",
                "lint:python": "flake8 backend && mypy backend"
            }
            
            for script, command in python_scripts.items():
                scripts[script] = command
        
        # Write updated package.json
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        logger.info(f"Updated package.json")
    except Exception as e:
        logger.error(f"Error updating package.json: {e}")

def main():
    """Main function to replace TypeScript files with Python versions."""
    logger.info("Starting replacement of TypeScript files with Python versions")
    
    # Define the files to replace
    replacements = [
        {
            "source": "backend/api/server_new.py",
            "target": "backend/api/server.py"
        },
        {
            "source": "backend/bot/database_connector_new.py",
            "target": "backend/bot/database_connector.py"
        }
    ]
    
    # Perform replacements
    for replacement in replacements:
        source_path = replacement["source"]
        target_path = replacement["target"]
        
        if os.path.exists(source_path):
            replace_file(source_path, target_path)
        else:
            logger.error(f"Source file {source_path} does not exist")
    
    # Remove TypeScript files
    typescript_files = [
        "backend/api/server.ts",
        "backend/api/websocket/server.ts"
    ]
    
    for ts_file in typescript_files:
        if os.path.exists(ts_file):
            try:
                # Create backup
                backup_path = f"{ts_file}.bak"
                shutil.copy2(ts_file, backup_path)
                logger.info(f"Created backup of {ts_file} at {backup_path}")
                
                # Remove the file
                os.remove(ts_file)
                logger.info(f"Removed TypeScript file: {ts_file}")
            except Exception as e:
                logger.error(f"Error removing {ts_file}: {e}")
    
    # Update shell scripts
    update_shell_scripts()
    
    # Update package.json
    update_package_json()
    
    logger.info("Replacement of TypeScript files with Python versions completed")
    logger.info("Note: You may need to update other files or scripts that reference TypeScript files.")

if __name__ == "__main__":
    main() 