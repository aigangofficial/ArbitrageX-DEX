# ArbitrageX Duplicate Files Analysis and Cleanup Plan

## 1. Duplicate Solidity Contract Files

### Analysis

We've identified that there are duplicate Solidity files in the project. The main issue is that the same contract files appear in both:

- `contracts/` directory (source files)
- `artifacts/contracts/` directory (compiled artifacts)

The `artifacts/` directory contains compiled contract data (JSON files) that are generated during the build process. These are not source files but compilation outputs.

### Cleanup Plan for Contract Files

1. **Keep only the source files in the `contracts/` directory**
2. **Do not manually delete files in the `artifacts/` directory** as these are generated during compilation
3. **Add `artifacts/` to `.gitignore` if not already present** to avoid committing compiled artifacts

## 2. Duplicate Test Files

### Analysis

We've identified several duplicate test files:

1. **FlashLoanArbitrage.test.ts**:

   - `test/FlashLoanArbitrage.test.ts`
   - `tests/contracts/FlashLoanArbitrage.test.ts`

   These files have different content and testing approaches:

   - The file in `test/` uses a more basic setup with direct contract interactions
   - The file in `tests/contracts/` uses a more comprehensive fixture-based approach with better test isolation

2. **ArbitrageExecutor.test.ts**:

   - `tests/contracts/ArbitrageExecutor.test.ts`
   - `tests/unit/contracts/ArbitrageExecutor.test.ts`

   These files have different content and testing scopes:

   - The file in `tests/contracts/` is more comprehensive with detailed DEX interaction tests
   - The file in `tests/unit/contracts/` is more focused on unit testing with simpler test cases

### Cleanup Plan for Test Files

1. **FlashLoanArbitrage.test.ts**:

   - Keep `tests/contracts/FlashLoanArbitrage.test.ts` as it's more comprehensive
   - Move any unique test cases from `test/FlashLoanArbitrage.test.ts` to the kept file
   - Delete `test/FlashLoanArbitrage.test.ts` after migration

2. **ArbitrageExecutor.test.ts**:

   - Keep `tests/contracts/ArbitrageExecutor.test.ts` as the main integration test
   - Keep `tests/unit/contracts/ArbitrageExecutor.test.ts` as it serves a different purpose (unit tests)
   - Ensure test names clearly indicate their purpose (integration vs unit)

3. **Test Directory Structure**:
   - Standardize on the `tests/` directory (plural) for all tests
   - Move any remaining tests from `test/` (singular) to the appropriate location in `tests/`
   - Delete the `test/` directory after migration

## 3. Implementation Steps

1. **Contract Files**:

   - No action needed for source files in `contracts/`
   - Ensure `.gitignore` includes `artifacts/`

2. **Test Files**:

   - Migrate unique tests from `test/FlashLoanArbitrage.test.ts` to `tests/contracts/FlashLoanArbitrage.test.ts`
   - Delete `test/FlashLoanArbitrage.test.ts`
   - Update test names in both ArbitrageExecutor test files to clarify their purpose
   - Move any other tests from `test/` to `tests/`
   - Delete the `test/` directory

3. **Verification**:
   - Run all tests to ensure they still pass after migration
   - Verify that no functionality is lost

## 4. Future Prevention

1. **Documentation**:

   - Document the test directory structure and naming conventions
   - Clarify the purpose of different test directories (unit, integration, etc.)

2. **CI/CD**:
   - Add a check in CI to detect duplicate test files
   - Enforce consistent test naming and location
