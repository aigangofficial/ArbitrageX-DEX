import chalk from 'chalk';
import fs from 'fs';
import path, { dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface DirectoryStructure {
  [key: string]: {
    required: string[];
    optional?: string[];
  };
}

const directoryStructure: DirectoryStructure = {
  'contracts': {
    required: [
      'FlashLoanService.sol',
      'ArbitrageExecutor.sol',
      'SecurityAdmin.sol'
    ],
    optional: [
      'interfaces/',
      'libraries/'
    ]
  },
  'contracts/interfaces': {
    required: [
      'IFlashLoanReceiver.sol',
      'IArbitrageExecutor.sol',
      'IPool.sol',
      'IPoolAddressesProvider.sol'
    ]
  },
  'contracts/libraries': {
    required: [
      'SafeERC20.sol'
    ]
  },
  'scripts': {
    required: [
      'deploy.ts',
      'verify.ts'
    ]
  },
  'tests/contracts': {
    required: [
      'FlashLoanService.test.ts',
      'ArbitrageExecutor.test.ts'
    ]
  }
};

interface ValidationResult {
  missingDirs: string[];
  missingRequiredFiles: string[];
  missingOptionalFiles: string[];
  unexpectedFiles: string[];
  duplicateFiles: string[];
  status: 'success' | 'warning' | 'error';
}

function validateStructure(): ValidationResult {
  const result: ValidationResult = {
    missingDirs: [],
    missingRequiredFiles: [],
    missingOptionalFiles: [],
    unexpectedFiles: [],
    duplicateFiles: [],
    status: 'success',
  };

  Object.entries(directoryStructure).forEach(([dir, { required, optional = [] }]) => {
    const normalizedDir = path.resolve(dir);

    // Check if directory exists
    if (!fs.existsSync(normalizedDir)) {
      result.missingDirs.push(dir);
      result.status = 'error';
      return;
    }

    // Check for required files
    required.forEach(file => {
      const filePath = path.join(normalizedDir, file);
      if (!fs.existsSync(filePath)) {
        result.missingRequiredFiles.push(path.join(dir, file));
        result.status = 'error';
      }
    });

    // Check for optional files
    optional.forEach(file => {
      const filePath = path.join(normalizedDir, file);
      if (!fs.existsSync(filePath)) {
        result.missingOptionalFiles.push(path.join(dir, file));
        if (result.status !== 'error') {
          result.status = 'warning';
        }
      }
    });

    // Check for duplicate files in contracts directory
    if (dir.startsWith('contracts')) {
      const fileMap = new Map<string, number>();
      const files = fs.readdirSync(normalizedDir).filter(file => file.endsWith('.sol'));

      files.forEach(file => {
        fileMap.set(file, (fileMap.get(file) || 0) + 1);
      });

      fileMap.forEach((count, file) => {
        if (count > 1) {
          result.duplicateFiles.push(path.join(dir, file));
          result.status = 'error';
        }
      });
    }

    // Check for unexpected files
    try {
      const actualFiles = fs
        .readdirSync(normalizedDir)
        .filter(file => !file.startsWith('.')) // Ignore hidden files
        .filter(file => fs.statSync(path.join(normalizedDir, file)).isFile());

      actualFiles.forEach(file => {
        if (!required.includes(file) && !optional.includes(file)) {
          result.unexpectedFiles.push(path.join(dir, file));
        }
      });
    } catch (error) {
      console.error(chalk.red(`Error reading directory ${dir}:`, error));
    }
  });

  return result;
}

function printValidationResults(results: ValidationResult): void {
  console.log(chalk.cyan('\n🔍 ArbitrageX Structure Validation Report'));
  console.log(chalk.cyan('====================================='));

  if (results.missingDirs.length > 0) {
    console.log(chalk.red('\n❌ Missing Required Directories:'));
    results.missingDirs.forEach(dir => console.log(chalk.red(`  • ${dir}`)));
  }

  if (results.missingRequiredFiles.length > 0) {
    console.log(chalk.red('\n❌ Missing Required Files:'));
    results.missingRequiredFiles.forEach(file => console.log(chalk.red(`  • ${file}`)));
  }

  if (results.duplicateFiles.length > 0) {
    console.log(chalk.red('\n❌ Duplicate Files Detected:'));
    results.duplicateFiles.forEach(file => console.log(chalk.red(`  • ${file}`)));
  }

  if (results.missingOptionalFiles.length > 0) {
    console.log(chalk.yellow('\n⚠️  Missing Optional Files:'));
    results.missingOptionalFiles.forEach(file => console.log(chalk.yellow(`  • ${file}`)));
  }

  if (results.unexpectedFiles.length > 0) {
    console.log(chalk.blue('\nℹ️  Unexpected Files:'));
    results.unexpectedFiles.forEach(file => console.log(chalk.blue(`  • ${file}`)));
  }

  console.log('\n📊 Validation Status:');
  switch (results.status) {
    case 'success':
      console.log(chalk.green('✅ All required files and directories are in place.'));
      break;
    case 'warning':
      console.log(chalk.yellow('⚠️  Structure valid but some optional files are missing.'));
      break;
    case 'error':
      console.log(
        chalk.red('❌ Critical structure issues detected. Please fix before proceeding.')
      );
      break;
  }
}

function validateBeforeCommand(command: string): boolean {
  console.log(chalk.cyan(`\n🔄 Validating structure before running: ${command}`));
  const results = validateStructure();

  if (results.status === 'error') {
    console.log(chalk.red('\n🚫 Command execution blocked due to structure validation errors.'));
    printValidationResults(results);
    return false;
  }

  if (results.status === 'warning') {
    console.log(chalk.yellow('\n⚠️  Some optional files are missing, but command can proceed.'));
  }

  return true;
}

// Update the main execution part
const main = () => {
  const command = process.argv[2];
  if (command) {
    if (!validateBeforeCommand(command)) {
      process.exit(1);
    }
  } else {
    const results = validateStructure();
    printValidationResults(results);
    process.exit(results.status === 'error' ? 1 : 0);
  }
};

// Run the script if it's the main module
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { printValidationResults, validateBeforeCommand, validateStructure };
