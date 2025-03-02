/**
 * ArbitrageX Test Name Updater
 * 
 * This script helps update test names in ArbitrageExecutor test files to clarify their purpose.
 * It reads the test files, identifies the test descriptions, and suggests updated names.
 */

const fs = require('fs');
const path = require('path');

// File paths
const integrationTestPath = path.join(__dirname, '..', 'tests', 'contracts', 'ArbitrageExecutor.test.ts');
const unitTestPath = path.join(__dirname, '..', 'tests', 'unit', 'contracts', 'ArbitrageExecutor.test.ts');

// Function to read a file and extract test descriptions
function extractTestDescriptions(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    const descriptions = [];
    const describeRegex = /describe\(['"](.+)['"]/;
    const itRegex = /it\(['"](.+)['"]/;
    
    let currentDescribe = null;
    
    for (const line of lines) {
      const describeMatch = line.match(describeRegex);
      if (describeMatch) {
        currentDescribe = describeMatch[1];
      }
      
      const itMatch = line.match(itRegex);
      if (itMatch && currentDescribe) {
        descriptions.push({
          describe: currentDescribe,
          it: itMatch[1],
          line: line.trim()
        });
      }
    }
    
    return descriptions;
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error.message);
    return [];
  }
}

// Function to suggest updated test names
function suggestUpdatedNames(descriptions, testType) {
  const prefix = testType === 'integration' ? '[Integration]' : '[Unit]';
  
  return descriptions.map(desc => {
    // Only add prefix if it doesn't already have one
    if (!desc.describe.includes('[Integration]') && !desc.describe.includes('[Unit]')) {
      return {
        ...desc,
        updatedDescribe: `${prefix} ${desc.describe}`
      };
    }
    return {
      ...desc,
      updatedDescribe: desc.describe
    };
  });
}

// Main function
function main() {
  console.log('ArbitrageX Test Name Updater');
  console.log('============================\n');
  
  // Process integration tests
  console.log('Integration Tests:');
  console.log('-----------------');
  const integrationTests = extractTestDescriptions(integrationTestPath);
  const updatedIntegrationTests = suggestUpdatedNames(integrationTests, 'integration');
  
  updatedIntegrationTests.forEach(test => {
    console.log(`Original: describe('${test.describe}') -> it('${test.it}')`);
    console.log(`Suggested: describe('${test.updatedDescribe}') -> it('${test.it}')`);
    console.log('');
  });
  
  // Process unit tests
  console.log('Unit Tests:');
  console.log('-----------');
  const unitTests = extractTestDescriptions(unitTestPath);
  const updatedUnitTests = suggestUpdatedNames(unitTests, 'unit');
  
  updatedUnitTests.forEach(test => {
    console.log(`Original: describe('${test.describe}') -> it('${test.it}')`);
    console.log(`Suggested: describe('${test.updatedDescribe}') -> it('${test.it}')`);
    console.log('');
  });
  
  console.log('\nManual Update Instructions:');
  console.log('1. Open each test file in your editor');
  console.log('2. Update the describe statements with the suggested prefixes');
  console.log('3. Save the files');
  console.log('4. Run the tests to ensure everything still works');
}

// Run the script
main(); 