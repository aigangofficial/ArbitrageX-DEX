import { Wallet } from 'ethers';

async function main() {
  // Create a new random wallet
  const wallet = Wallet.createRandom();

  console.log('\n=== New Wallet Generated ===');
  console.log('Address:', wallet.address);
  console.log('Private Key:', wallet.privateKey);
  console.log('\n⚠️ IMPORTANT: Save these details securely!');
  console.log('Never share your private key with anyone!');
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
