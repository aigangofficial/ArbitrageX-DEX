module.exports = {
    parser: '@typescript-eslint/parser',
    extends: [
        'plugin:@typescript-eslint/recommended',
        'plugin:jest/recommended'
    ],
    plugins: ['@typescript-eslint', 'jest'],
    env: {
        node: true,
        jest: true,
        es6: true
    },
    parserOptions: {
        ecmaVersion: 2020,
        sourceType: 'module'
    },
    rules: {
        '@typescript-eslint/explicit-function-return-type': 'off',
        '@typescript-eslint/no-explicit-any': 'warn',
        '@typescript-eslint/no-unused-vars': ['error', { 'argsIgnorePattern': '^_' }],
        'jest/expect-expect': 'off',
        'jest/no-done-callback': 'off',
        'jest/no-conditional-expect': 'off'
    },
    settings: {
        jest: {
            version: 29
        }
    },
    ignorePatterns: [
        'dist/*',
        '.eslintrc.js',
        'jest.config.js'
    ],
    overrides: [
        {
            files: ['*.ts', '*.tsx'],
            parserOptions: {
                project: './tsconfig.json'
            }
        }
    ]
}; 