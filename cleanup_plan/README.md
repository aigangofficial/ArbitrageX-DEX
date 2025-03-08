# ArbitrageX Duplicate Files Cleanup

This directory contains the analysis and scripts for cleaning up duplicate files in the ArbitrageX project.

## Contents

1. **duplicate_analysis.md** - Detailed analysis of duplicate files and cleanup plan
2. **cleanup_script.sh** - Shell script to implement the cleanup plan
3. **update_test_names.js** - Node.js script to help update test names
4. **README.md** - This file

## Cleanup Process

### Step 1: Review the Analysis

Before starting the cleanup process, review the analysis in `duplicate_analysis.md` to understand the duplicate files and the proposed cleanup plan.

### Step 2: Make a Backup

Always make a backup of your project before running any cleanup scripts. The cleanup script will create a backup automatically, but it's good practice to make your own as well.

```bash
cp -r /Users/sbh/Desktop/arbitragex-new /Users/sbh/Desktop/arbitragex-backup
```

### Step 3: Run the Cleanup Script

Make the script executable and run it:

```bash
chmod +x cleanup_script.sh
./cleanup_script.sh
```

The script will:

- Create a backup of files before deletion
- Add `artifacts/` to `.gitignore` if needed
- Identify unique test cases in duplicate test files
- Guide you through the migration process
- Move tests from `test/` to `tests/` directory
- Clean up temporary files

### Step 4: Update Test Names

Run the test name updater script to get suggestions for updating test names:

```bash
node update_test_names.js
```

Follow the instructions provided by the script to manually update the test names in the files.

### Step 5: Verify the Changes

After completing the cleanup process, run the tests to ensure everything still works correctly:

```bash
cd /Users/sbh/Desktop/arbitragex-new
npm test
```

## Important Notes

1. **Manual Migration Required**: The scripts identify duplicate files and suggest changes, but some steps require manual intervention, such as migrating unique test cases.

2. **Backup**: A backup of the original files is created before any deletion. The backup directory is printed at the end of the cleanup script.

3. **Artifacts Directory**: Do not manually delete files in the `artifacts/` directory as these are generated during compilation.

4. **Test Directory Structure**: After the cleanup, all tests should be in the `tests/` directory (plural), and the `test/` directory (singular) should be deleted.

## Contact

If you encounter any issues during the cleanup process, please contact the project maintainer.
