'use strict';
Object.defineProperty(exports, '__esModule', { value: true });
const ethers_1 = require('ethers');
const addresses = [
  '0x357D51124f59836DeD84c8a1730D72B749d8BC23', // Aave Pool
  '0x8954AfA98594b838bda56FE4C12a09D7739D179b', // Uniswap Router
  '0x0C8b5D4Bf676BD283c4F343c260bC668aa07aF49', // Sushiswap Router
  '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889', // WMATIC
];
async function main() {
  console.log('Checksummed addresses:');
  for (const address of addresses) {
    try {
      const checksummed = ethers_1.ethers.getAddress(address);
      console.log(`Original:    ${address}`);
      console.log(`Checksummed: ${checksummed}\n`);
    } catch (error) {
      console.error(`Error with address ${address}:`, error?.message || String(error));
    }
  }
}
main().catch(error => {
  console.error('Script failed:', error?.message || String(error));
  process.exit(1);
});
