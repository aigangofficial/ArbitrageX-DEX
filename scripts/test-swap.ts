import dotenv from 'dotenv';
import { ethers } from 'ethers';
import path from 'path';

// Force reload environment variables
dotenv.config({ path: path.resolve(process.cwd(), '.env') });

const ROUTER_ABI = [
  'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) returns (uint[] memory amounts)',
  'function getAmountsOut(uint amountIn, address[] calldata path) view returns (uint[] memory amounts)',
  'function WETH() external pure returns (address)'
];

const ERC20_ABI = [
  'function approve(address spender, uint256 amount) returns (bool)',
  'function allowance(address owner, address spender) view returns (uint256)',
  'function balanceOf(address) view returns (uint256)'
];

async function main() {
  console.log('🔄 Testing Uniswap V2 Swaps on Sepolia...');

  // Initialize provider and wallet
  const provider = new ethers.JsonRpcProvider(process.env.SEPOLIA_RPC);
  const wallet = new ethers.Wallet(process.env.WALLET_PRIVATE_KEY!, provider);

  // Token addresses from .env - trim any whitespace or comments
  const WETH = process.env.WETH_TOKEN_ADDRESS!.split('#')[0].trim();
  const USDC = process.env.USDC_TOKEN_ADDRESS!.split('#')[0].trim();
  const UNISWAP_ROUTER = process.env.UNISWAP_V2_ROUTER!.split('#')[0].trim();

  // Debug: Check raw values
  console.log('\n🔍 Debug: Raw Values');
  console.log('WETH:', JSON.stringify(WETH));
  console.log('USDC:', JSON.stringify(USDC));
  console.log('Router:', JSON.stringify(UNISWAP_ROUTER));

  console.log('\n📝 Configuration:');
  console.log('================');
  console.log('Network: Sepolia');
  console.log('Wallet Address:', wallet.address);
  console.log('WETH Address:', WETH);
  console.log('USDC Address:', USDC);
  console.log('Router Address:', UNISWAP_ROUTER);

  // Initialize contracts
  const router = new ethers.Contract(UNISWAP_ROUTER, ROUTER_ABI, wallet);
  const wethContract = new ethers.Contract(WETH, ERC20_ABI, wallet);
  const usdcContract = new ethers.Contract(USDC, ERC20_ABI, wallet);

  // Check initial balances
  const initialWethBalance = await wethContract.balanceOf(wallet.address);
  const initialUsdcBalance = await usdcContract.balanceOf(wallet.address);

  console.log('\n💰 Initial Balances:');
  console.log('==================');
  console.log('WETH:', ethers.formatEther(initialWethBalance));
  console.log('USDC:', ethers.formatUnits(initialUsdcBalance, 6));

  // Amount to swap
  const usdcToSwap = ethers.parseUnits('5', 6); // Swap 5 USDC for WETH

  // Get expected WETH output
  const amounts = await router.getAmountsOut(usdcToSwap, [USDC, WETH]);
  const expectedWeth = amounts[1];

  console.log('\n📊 Swap Details:');
  console.log('==============');
  console.log('USDC to swap:', ethers.formatUnits(usdcToSwap, 6));
  console.log('Expected WETH:', ethers.formatEther(expectedWeth));

  const priceImpact = Number(ethers.formatUnits(usdcToSwap, 6)) / Number(ethers.formatEther(expectedWeth));
  console.log('Price Impact:', priceImpact.toFixed(2), 'USDC per WETH');

  // Check and set allowance if needed
  const usdcAllowance = await usdcContract.allowance(wallet.address, UNISWAP_ROUTER);
  if (usdcAllowance < usdcToSwap) {
    console.log('\n🔓 Approving USDC...');
    const approveTx = await usdcContract.approve(UNISWAP_ROUTER, ethers.MaxUint256);
    await approveTx.wait();
    console.log('USDC approved ✅');
  }

  // Execute swap
  console.log('\n💱 Executing swap...');
  try {
    const deadline = Math.floor(Date.now() / 1000) + 3600; // 1 hour
    const minOutput = expectedWeth - (expectedWeth * BigInt(5) / BigInt(100)); // 5% slippage

    const tx = await router.swapExactTokensForTokens(
      usdcToSwap,
      minOutput,
      [USDC, WETH],
      wallet.address,
      deadline
    );

    console.log('Transaction hash:', tx.hash);
    await tx.wait();
    console.log('Swap completed successfully ✅');

    // Check final balances
    const finalWethBalance = await wethContract.balanceOf(wallet.address);
    const finalUsdcBalance = await usdcContract.balanceOf(wallet.address);

    console.log('\n💰 Final Balances:');
    console.log('================');
    console.log('WETH:', ethers.formatEther(finalWethBalance));
    console.log('USDC:', ethers.formatUnits(finalUsdcBalance, 6));

    // Calculate and display changes
    const wethChange = finalWethBalance - initialWethBalance;
    const usdcChange = finalUsdcBalance - initialUsdcBalance;

    console.log('\n📈 Changes:');
    console.log('=========');
    console.log('WETH:', ethers.formatEther(wethChange));
    console.log('USDC:', ethers.formatUnits(usdcChange, 6));
    console.log('Actual Price:', Math.abs(Number(ethers.formatUnits(usdcChange, 6)) / Number(ethers.formatEther(wethChange))).toFixed(2), 'USDC per WETH');

  } catch (error) {
    console.error('Error executing swap:', error);
    throw error;
  }
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
