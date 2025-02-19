import dotenv from 'dotenv';
import { ethers } from 'ethers';
import path from 'path';

// Force reload environment variables
dotenv.config({ path: path.resolve(process.cwd(), '.env') });

// Debug: Log environment loading
console.log('Loading environment from:', path.resolve(process.cwd(), '.env'));

// WETH ABI for wrapping/unwrapping ETH
const WETH_ABI = [
  'function deposit() payable',
  'function withdraw(uint256 amount)',
  'function balanceOf(address) view returns (uint256)',
  'function approve(address spender, uint256 amount) returns (bool)'
];

// Add USDC ABI for token interactions
const ERC20_ABI = [
  'function balanceOf(address) view returns (uint256)',
  'function approve(address spender, uint256 amount) returns (bool)',
  'function mint(address to, uint256 amount)',
  'function transfer(address to, uint256 amount) returns (bool)'
];

interface WalletSetupConfig {
  rpcUrl: string;
  chainId: number;
  privateKey?: string;
  wethAddress: string;
  usdcAddress: string;
}

class SepoliaWalletManager {
  private provider: ethers.JsonRpcProvider;
  private wallet?: ethers.Wallet;
  private wethContract?: ethers.Contract;
  private usdcContract?: ethers.Contract;

  constructor(config: WalletSetupConfig) {
    this.provider = new ethers.JsonRpcProvider(config.rpcUrl);

    if (config.privateKey) {
      this.wallet = new ethers.Wallet(config.privateKey, this.provider);
      this.wethContract = new ethers.Contract(config.wethAddress, WETH_ABI, this.wallet);
      this.usdcContract = new ethers.Contract(config.usdcAddress, ERC20_ABI, this.wallet);
    }
  }

  getWalletAddress(): string | undefined {
    return this.wallet?.address;
  }

  async getNetwork() {
    const network = await this.provider.getNetwork();
    return {
      name: network.name,
      chainId: network.chainId
    };
  }

  async getBalances(address: string) {
    const ethBalance = await this.provider.getBalance(address);
    let wethBalance = BigInt(0);
    let usdcBalance = BigInt(0);

    if (this.wethContract) {
      try {
        wethBalance = await this.wethContract.balanceOf(address);
      } catch (error) {
        console.warn('Failed to fetch WETH balance:', error);
      }
    }

    if (this.usdcContract) {
      try {
        usdcBalance = await this.usdcContract.balanceOf(address);
      } catch (error) {
        console.warn('Failed to fetch USDC balance:', error);
      }
    }

    return {
      eth: ethers.formatEther(ethBalance),
      weth: ethers.formatEther(wethBalance),
      usdc: ethers.formatUnits(usdcBalance, 6) // USDC uses 6 decimals
    };
  }

  async wrapEth(amount: string) {
    if (!this.wallet || !this.wethContract) {
      throw new Error('Wallet not initialized with private key');
    }

    const tx = await this.wethContract.deposit({
      value: ethers.parseEther(amount)
    });

    console.log('Wrapping ETH...');
    console.log('Transaction hash:', tx.hash);
    await tx.wait();
    console.log('ETH wrapped successfully!');
  }

  async validateConnection() {
    try {
      const network = await this.getNetwork();
      console.log('Connected to network:', {
        name: network.name,
        chainId: network.chainId
      });

      // Get sanitized RPC URL
      const displayRpcUrl = process.env.SEPOLIA_RPC?.replace(/\/v3\/[^/]+/, '/v3/****') || 'https://sepolia.infura.io/v3/****';

      if (this.wallet) {
        const balances = await this.getBalances(this.wallet.address);
        console.log('\nWallet balances:', {
          ETH: balances.eth,
          WETH: balances.weth,
          USDC: balances.usdc
        });
        console.log('Wallet address:', this.wallet.address);
      }

      return {
        isConnected: true,
        displayRpcUrl
      };
    } catch (error) {
      console.error('Failed to validate connection:', error);
      return {
        isConnected: false,
        displayRpcUrl: ''
      };
    }
  }

  async mintTestUSDC(amount: string) {
    if (!this.wallet || !this.usdcContract) {
      throw new Error('Wallet not initialized with private key');
    }

    try {
      // For test USDC, we can directly mint if the contract allows
      const tx = await this.usdcContract.mint(
        this.wallet.address,
        ethers.parseUnits(amount, 6) // USDC uses 6 decimals
      );

      console.log('Minting USDC...');
      console.log('Transaction hash:', tx.hash);
      await tx.wait();
      console.log('USDC minted successfully!');
    } catch (error) {
      console.error('Failed to mint USDC. Using Uniswap faucet instead...');
      console.log('\nPlease get test USDC from:');
      console.log('1. Uniswap Sepolia Faucet: https://faucet.uniswap.org/');
      console.log('2. Request USDC for address:', this.wallet.address);
      throw error;
    }
  }
}

async function main() {
  try {
    console.log('🔄 Initializing Sepolia wallet setup...');

    // Debug: Check environment variables
    console.log('\n🔍 Checking configuration...');
    const privateKey = process.env.WALLET_PRIVATE_KEY;
    if (!privateKey) {
      console.log('❌ No private key found in environment variables');
    } else {
      console.log('✅ Private key found (first 6 characters):', privateKey.substring(0, 6) + '...');
    }

    const walletConfig: WalletSetupConfig = {
      rpcUrl: process.env.SEPOLIA_RPC || 'https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID',
      chainId: Number(process.env.SEPOLIA_CHAIN_ID) || 11155111,
      privateKey: process.env.WALLET_PRIVATE_KEY,
      wethAddress: process.env.WETH_TOKEN_ADDRESS || '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
      usdcAddress: process.env.USDC_TOKEN_ADDRESS || '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238'
    };

    const walletManager = new SepoliaWalletManager(walletConfig);
    const walletAddress = walletManager.getWalletAddress();

    console.log('\n📝 Step 1: Validating network connection...');
    const connectionStatus = await walletManager.validateConnection();

    if (!connectionStatus.isConnected) {
      throw new Error('Failed to connect to network');
    }

    // Check if --check-balance flag is provided
    if (process.argv.includes('--check-balance')) {
      console.log('\n💰 Checking current balances...');
      if (walletAddress) {
        const balances = await walletManager.getBalances(walletAddress);
        console.log('\nCurrent Wallet Balances:');
        console.log('=======================');
        console.log(`ETH:  ${balances.eth}`);
        console.log(`WETH: ${balances.weth}`);
        console.log(`USDC: ${balances.usdc}`);
        console.log('\nWallet Address:', walletAddress);
      }
      return;
    }

    // Check if --mint-usdc flag is provided
    if (process.argv.includes('--mint-usdc')) {
      console.log('\n💰 Attempting to get test USDC...');
      if (walletAddress) {
        try {
          await walletManager.mintTestUSDC('1000'); // Try to mint 1000 USDC
          const balances = await walletManager.getBalances(walletAddress);
          console.log('\nUpdated Wallet Balances:');
          console.log('=======================');
          console.log(`ETH:  ${balances.eth}`);
          console.log(`WETH: ${balances.weth}`);
          console.log(`USDC: ${balances.usdc}`);
          console.log('\nWallet Address:', walletAddress);
        } catch (error) {
          // Error already handled in mintTestUSDC
        }
      }
      return;
    }

    // Regular setup with ETH wrapping
    if (walletConfig.privateKey) {
      console.log('\n💱 Step 2: Wrapping some ETH to WETH...');
      try {
        await walletManager.wrapEth('0.1');

        // Check updated balances after wrapping
        if (walletAddress) {
          const updatedBalances = await walletManager.getBalances(walletAddress);
          console.log('\nUpdated Wallet Balances:');
          console.log('=======================');
          console.log(`ETH:  ${updatedBalances.eth}`);
          console.log(`WETH: ${updatedBalances.weth}`);
          console.log(`USDC: ${updatedBalances.usdc}`);
        }
      } catch (error) {
        console.warn('Failed to wrap ETH:', error);
      }
    } else {
      console.log('\n⚠️ No private key provided. Skipping ETH wrapping...');
      console.log('To enable automated transactions, add your private key to .env:');
      console.log('WALLET_PRIVATE_KEY=your_private_key_here');
    }

    console.log('\n✅ Setup Complete!');
    console.log(`
    Network Configuration:
    ====================
    Network: Sepolia Testnet
    RPC URL: ${connectionStatus.displayRpcUrl}
    Chain ID: ${walletConfig.chainId}

    Token Addresses:
    ==============
    WETH: ${walletConfig.wethAddress}
    USDC: ${walletConfig.usdcAddress}

    Next Steps:
    ==========
    1. Ensure MetaMask is connected to Sepolia Testnet
    2. Get test ETH from faucet: https://sepoliafaucet.com/
    3. Get test tokens:
       - Wrap ETH to get WETH using the contract
       - Get USDC from Uniswap Sepolia faucet

    To deploy test pools:
    ===================
    npm run deploy-pools
    `);

  } catch (error) {
    if (error instanceof Error) {
      console.error('❌ Setup failed:', error.message);
    } else {
      console.error('❌ Setup failed with unknown error:', error);
    }
    process.exit(1);
  }
}

main();
