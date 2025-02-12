import { resolve } from 'path';
import { existsSync, copyFileSync } from 'fs';
import { config } from 'dotenv';
import chalk from 'chalk';

async function main() {
  const configDir = resolve(__dirname, '../config');
  const envExample = resolve(configDir, '.env.example');
  const envFile = resolve(configDir, '.env');

  // Check if .env already exists
  if (existsSync(envFile)) {
    console.log(chalk.yellow('⚠️  A .env file already exists in the config directory'));
    console.log(
      chalk.yellow('Please manually update it if needed using .env.example as a template')
    );
    return;
  }

  // Copy .env.example to .env
  try {
    copyFileSync(envExample, envFile);
    console.log(chalk.green('✅ Created new .env file from template'));
  } catch (error) {
    console.error(chalk.red('❌ Failed to create .env file:'), error);
    process.exit(1);
  }

  // Load and validate environment
  config({ path: envFile });

  const requiredVars = ['SEPOLIA_RPC', 'MAINNET_RPC', 'DEPLOYER_PRIVATE_KEY', 'ETHERSCAN_API_KEY'];

  const missingVars = requiredVars.filter(varName => !process.env[varName]);

  if (missingVars.length > 0) {
    console.log(chalk.yellow('\n⚠️  Missing required environment variables:'));
    missingVars.forEach(varName => {
      console.log(chalk.yellow(`   - ${varName}`));
    });
    console.log(chalk.blue('\nPlease update config/.env with your values'));
  }

  console.log(chalk.green('\n✨ Environment setup complete!'));
  console.log(chalk.blue('Next steps:'));
  console.log(chalk.blue('1. Update config/.env with your private values'));
  console.log(chalk.blue('2. Run npm install to install dependencies'));
  console.log(chalk.blue('3. Run npm test to verify your setup'));
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
