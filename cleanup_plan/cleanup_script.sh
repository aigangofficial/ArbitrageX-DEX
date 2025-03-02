#!/bin/bash

# ArbitrageX Duplicate Files Cleanup Script
# This script implements the cleanup plan for duplicate files in the ArbitrageX project

# Set the base directory
BASE_DIR="/Users/sbh/Desktop/arbitragex-new"
cd "$BASE_DIR"

echo "=== ArbitrageX Duplicate Files Cleanup ==="
echo "Starting cleanup process..."

# 1. Create backup directory
BACKUP_DIR="$BASE_DIR/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Created backup directory: $BACKUP_DIR"

# 2. Backup files before deletion
echo "Backing up files before deletion..."
mkdir -p "$BACKUP_DIR/test"
cp -r test/* "$BACKUP_DIR/test/" 2>/dev/null || echo "No files to backup in test/"

# 3. Check if .gitignore exists and add artifacts/ if needed
if [ -f .gitignore ]; then
    if ! grep -q "^artifacts/$" .gitignore; then
        echo "Adding artifacts/ to .gitignore..."
        echo "artifacts/" >> .gitignore
    else
        echo "artifacts/ already in .gitignore"
    fi
else
    echo "Creating .gitignore and adding artifacts/..."
    echo "artifacts/" > .gitignore
fi

# 4. Migrate unique tests from test/FlashLoanArbitrage.test.ts to tests/contracts/FlashLoanArbitrage.test.ts
echo "Analyzing test files for unique test cases..."

# Create a temporary directory for migration work
mkdir -p temp_migration

# Extract test case names from both files for comparison
grep -o "it(['\"].*['\"]" test/FlashLoanArbitrage.test.ts | sort > temp_migration/test1_cases.txt
grep -o "it(['\"].*['\"]" tests/contracts/FlashLoanArbitrage.test.ts | sort > temp_migration/test2_cases.txt

# Find unique test cases in the first file
echo "Unique test cases in test/FlashLoanArbitrage.test.ts:"
comm -23 temp_migration/test1_cases.txt temp_migration/test2_cases.txt > temp_migration/unique_cases.txt
cat temp_migration/unique_cases.txt

# Note: Manual migration of test cases is required
# This script identifies the unique tests but doesn't automatically migrate them
echo "NOTE: Please manually migrate the unique test cases listed above to tests/contracts/FlashLoanArbitrage.test.ts"

# 5. Delete duplicate test file after confirming migration
read -p "Have you migrated the unique test cases? (y/n): " confirm
if [ "$confirm" = "y" ]; then
    echo "Deleting test/FlashLoanArbitrage.test.ts..."
    rm test/FlashLoanArbitrage.test.ts
else
    echo "Skipping deletion of test/FlashLoanArbitrage.test.ts"
fi

# 6. Update test names in ArbitrageExecutor test files to clarify their purpose
echo "NOTE: Please manually update test descriptions in ArbitrageExecutor test files to clarify their purpose (integration vs unit)"

# 7. Move any other tests from test/ to tests/
if [ -d test ] && [ "$(ls -A test 2>/dev/null)" ]; then
    echo "Moving remaining tests from test/ to tests/..."
    for file in test/*.test.ts test/*Test.ts; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            echo "Moving $filename to tests/contracts/"
            mkdir -p tests/contracts
            cp "$file" "tests/contracts/$filename"
        fi
    done
    
    # Ask for confirmation before deleting the test directory
    read -p "Delete the test/ directory? (y/n): " confirm
    if [ "$confirm" = "y" ]; then
        echo "Deleting test/ directory..."
        rm -rf test
    else
        echo "Skipping deletion of test/ directory"
    fi
else
    echo "No files in test/ directory or directory doesn't exist"
fi

# 8. Clean up temporary files
rm -rf temp_migration

echo "=== Cleanup process completed ==="
echo "Please run tests to verify that everything still works correctly"
echo "Backup of original files is available at: $BACKUP_DIR" 