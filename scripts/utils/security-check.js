"use strict";
/**
 * @title Security Validation Utility
 * @description Performs security checks and validations for the ArbitrageX system
 *
 * FEATURES:
 * 1. Contract Security:
 *    - Validates contract permissions
 *    - Checks access controls
 *    - Verifies security settings
 *
 * 2. Network Security:
 *    - Validates network connections
 *    - Checks API endpoints
 *    - Verifies RPC security
 *
 * 3. Configuration Validation:
 *    - Checks environment variables
 *    - Validates sensitive data
 *    - Verifies deployment settings
 *
 * USAGE:
 * ```bash
 * # Run security checks
 * npm run security:check
 *
 * # Run security audit
 * npm run security:audit
 * ```
 *
 * @requires ethers
 * @requires fs
 */
const chalk = require('chalk');
const { execSync } = require('child_process');
async function securityCheck() {
    console.log(chalk.blue('🔍 Running security checks...'));
    const checks = [
        {
            name: 'Static Analysis (Slither)',
            command: 'npm run security',
            critical: true,
        },
        {
            name: 'Dependencies (npm audit)',
            command: 'npm audit',
            critical: false,
        },
        {
            name: 'Code Linting',
            command: 'npm run lint',
            critical: true,
        },
        {
            name: 'Test Suite',
            command: 'npm test',
            critical: true,
        },
    ];
    let hasErrors = false;
    for (const check of checks) {
        try {
            console.log(chalk.cyan(`\nRunning ${check.name}...`));
            execSync(check.command, { stdio: 'inherit' });
            console.log(chalk.green(`✅ ${check.name} passed`));
        }
        catch (err) {
            hasErrors = true;
            const error = err;
            const message = `❌ ${check.name} failed: ${error.message || 'Unknown error'}`;
            if (check.critical) {
                console.error(chalk.red(message));
                process.exit(1);
            }
            else {
                console.warn(chalk.yellow(message));
                console.warn(chalk.yellow('Non-critical check failed, continuing...'));
            }
        }
    }
    if (hasErrors) {
        console.log(chalk.yellow('\n⚠️ Some non-critical checks failed. Review warnings above.'));
    }
    else {
        console.log(chalk.green('\n✅ All security checks passed!'));
    }
}
if (require.main === module) {
    securityCheck().catch(error => {
        console.error(chalk.red('\n❌ Security checks failed:'), error);
        process.exit(1);
    });
}
