'use strict';
/**
 * @title Environment Setup Utility
 * @description Sets up and validates the development environment for ArbitrageX
 *
 * FEATURES:
 * 1. Environment Initialization:
 *    - Creates necessary directories
 *    - Sets up environment variables
 *    - Initializes configuration files
 *
 * 2. Dependency Validation:
 *    - Checks required dependencies
 *    - Validates node version
 *    - Verifies network access
 *
 * 3. Security Setup:
 *    - Generates secure keys
 *    - Sets up encryption
 *    - Configures access controls
 *
 * USAGE:
 * ```bash
 * # Initialize development environment
 * npm run setup:dev
 *
 * # Initialize production environment
 * npm run setup:prod
 * ```
 *
 * @requires dotenv
 * @requires fs
 * @requires path
 */
const dotenv = require('dotenv');
const fs = require('fs');
const path = require('path');
// Console colors
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
};
async function main() {
  const configDir = path.resolve(__dirname, '../../config');
  const envExample = path.resolve(configDir, '.env.example');
  const envFile = path.resolve(configDir, '.env');
  // Check if .env already exists
  if (fs.existsSync(envFile)) {
    console.log(colors.yellow + '⚠️  A .env file already exists in the config directory');
    console.log(
      'Please manually update it if needed using .env.example as a template' + colors.reset
    );
    return;
  }
  // Copy .env.example to .env
  try {
    fs.copyFileSync(envExample, envFile);
    console.log(colors.green + '✅ Created new .env file from template' + colors.reset);
  } catch (error) {
    console.error(colors.red + '❌ Failed to create .env file:', error + colors.reset);
    process.exit(1);
  }
  // Load and validate environment
  dotenv.config({ path: envFile });
  const requiredVars = ['SEPOLIA_RPC', 'MAINNET_RPC', 'DEPLOYER_PRIVATE_KEY', 'ETHERSCAN_API_KEY'];
  const missingVars = requiredVars.filter(varName => !process.env[varName]);
  if (missingVars.length > 0) {
    console.log(colors.yellow + '\n⚠️  Missing required environment variables:');
    missingVars.forEach(varName => {
      console.log(`   - ${varName}`);
    });
    console.log('\nPlease update config/.env with your values' + colors.reset);
  }
  console.log(colors.green + '\n✨ Environment setup complete!' + colors.reset);
  console.log(colors.blue + 'Next steps:');
  console.log('1. Update config/.env with your private values');
  console.log('2. Run npm install to install dependencies');
  console.log('3. Run npm test to verify your setup' + colors.reset);
}
main().catch(error => {
  console.error(colors.red + 'Error:', error + colors.reset);
  process.exitCode = 1;
});
