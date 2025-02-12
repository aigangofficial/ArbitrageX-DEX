import { execSync } from 'child_process';
import chalk from 'chalk';

async function main() {
  console.log(chalk.blue('🔍 Running security checks...'));

  try {
    // Run Slither
    console.log(chalk.cyan('\nRunning static analysis (Slither)...'));
    execSync('npm run security', { stdio: 'inherit' });

    // Run dependency audit
    console.log(chalk.cyan('\nChecking dependencies (npm audit)...'));
    execSync('npm audit', { stdio: 'inherit' });

    // Run linter
    console.log(chalk.cyan('\nRunning code linter...'));
    execSync('npm run lint', { stdio: 'inherit' });

    // Run tests
    console.log(chalk.cyan('\nRunning test suite...'));
    execSync('npm test', { stdio: 'inherit' });

    console.log(chalk.green('\n✅ All security checks passed!'));
  } catch (error) {
    console.error(chalk.red('\n❌ Security checks failed:'));
    process.exit(1);
  }
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
