import dotenv from 'dotenv';
import { ethers } from 'ethers';
import path from 'path';

// Force reload environment variables
dotenv.config({ path: path.resolve(process.cwd(), '.env') });

const ROUTER_ABI = [
  'function addLiquidity(address tokenA, address tokenB, uint amountADesired, uint amountBDesired, uint amountAMin, uint amountBMin, address to, uint deadline) returns (uint amountA, uint amountB, uint liquidity)',
  'function factory() external pure returns (address)',
];

const ERC20_ABI = [
  'function approve(address spender, uint256 amount) returns (bool)',
  'function allowance(address owner, address spender) view returns (uint256)',
  'function balanceOf(address) view returns (uint256)'
];

async function main() {
  console.log('🚀 Deploying test pools on Sepolia...');

  // Initialize provider and wallet
  const provider = new ethers.JsonRpcProvider(process.env.SEPOLIA_RPC);
  const wallet = new ethers.Wallet(process.env.WALLET_PRIVATE_KEY!, provider);

  // Token addresses from .env
  const WETH = process.env.WETH_TOKEN_ADDRESS!;
  const USDC = process.env.USDC_TOKEN_ADDRESS!;
  const UNISWAP_ROUTER = process.env.UNISWAP_V2_ROUTER!;

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

  // Check balances
  const wethBalance = await wethContract.balanceOf(wallet.address);
  const usdcBalance = await usdcContract.balanceOf(wallet.address);

  console.log('\n💰 Current Balances:');
  console.log('==================');
  console.log('WETH:', ethers.formatEther(wethBalance));
  console.log('USDC:', ethers.formatUnits(usdcBalance, 6));

  // Amount of tokens to add as liquidity
  const wethAmount = ethers.parseEther('0.1'); // 0.1 WETH
  const usdcAmount = ethers.parseUnits('20', 6); // 20 USDC

  console.log('\n🔍 Checking allowances...');

  // Check and set allowances if needed
  const wethAllowance = await wethContract.allowance(wallet.address, UNISWAP_ROUTER);
  const usdcAllowance = await usdcContract.allowance(wallet.address, UNISWAP_ROUTER);

  if (wethAllowance < wethAmount) {
    console.log('Approving WETH...');
    const approveTx1 = await wethContract.approve(UNISWAP_ROUTER, ethers.MaxUint256);
    await approveTx1.wait();
    console.log('WETH approved ✅');
  }

  if (usdcAllowance < usdcAmount) {
    console.log('Approving USDC...');
    const approveTx2 = await usdcContract.approve(UNISWAP_ROUTER, ethers.MaxUint256);
    await approveTx2.wait();
    console.log('USDC approved ✅');
  }

  console.log('\n💧 Adding liquidity to Uniswap V2...');
  try {
    const tx = await router.addLiquidity(
      WETH,
      USDC,
      wethAmount,
      usdcAmount,
      0, // amountAMin
      0, // amountBMin
      wallet.address,
      Math.floor(Date.now() / 1000) + 3600 // 1 hour deadline
    );
    console.log('Transaction hash:', tx.hash);
    await tx.wait();
    console.log('Added liquidity successfully ✅');

    // Check final balances
    const finalWethBalance = await wethContract.balanceOf(wallet.address);
    const finalUsdcBalance = await usdcContract.balanceOf(wallet.address);

    console.log('\n💰 Final Balances:');
    console.log('================');
    console.log('WETH:', ethers.formatEther(finalWethBalance));
    console.log('USDC:', ethers.formatUnits(finalUsdcBalance, 6));
  } catch (error) {
    console.error('Error adding liquidity:', error);
    throw error;
  }
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
