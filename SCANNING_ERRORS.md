# ArbitrageX Scanning Errors Guide

## Overview

This document provides information about common scanning errors that may occur in the ArbitrageX bot and how to fix them. The scanning process is a critical component of the arbitrage bot, as it identifies potential trading opportunities across different decentralized exchanges (DEXes).

## Common Scanning Errors

### 1. "Error scanning pair"

This error occurs when the bot encounters an issue while scanning a trading pair for arbitrage opportunities.

#### Possible Causes:

- **RPC Node Connection Issues**: The bot cannot connect to the Ethereum node.
- **Invalid Token Addresses**: The token addresses in the pair are invalid or not recognized.
- **Liquidity Pool Issues**: The liquidity pool for the pair does not exist or has insufficient liquidity.
- **Rate Limiting**: The RPC provider is rate-limiting requests.
- **Gas Price Fluctuations**: Sudden changes in gas prices affecting profitability calculations.

#### How to Fix:

1. **Check RPC Connection**:
   ```
   curl -X GET http://localhost:3001/api/v1/blockchain/health
   ```
   Ensure the response indicates a healthy connection.

2. **Verify Token Addresses**:
   Check that the token addresses in the pair configuration are correct and exist on the blockchain.

3. **Increase Timeout Settings**:
   In `backend/execution/arbitrageScanner.ts`, increase the timeout for scanning operations:
   ```typescript
   // Increase timeout for scanning operations
   private readonly scanTimeout = 10000; // 10 seconds
   ```

4. **Implement Retry Logic**:
   Modify the `scanPair` method to include retry logic:
   ```typescript
   async scanPair(tokenA: string, tokenB: string, maxRetries = 3): Promise<void> {
     let retries = 0;
     while (retries < maxRetries) {
       try {
         // Existing scanning logic
         return;
       } catch (error) {
         retries++;
         if (retries >= maxRetries) {
           logger.error(`Error scanning pair ${tokenA}/${tokenB} after ${maxRetries} attempts: ${error.message}`);
           throw error;
         }
         logger.warn(`Retry ${retries}/${maxRetries} for pair ${tokenA}/${tokenB}`);
         await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retrying
       }
     }
   }
   ```

5. **Use Fallback RPC Providers**:
   Configure multiple RPC providers and switch between them if one fails:
   ```typescript
   private readonly rpcProviders = [
     process.env.PRIMARY_RPC_URL,
     process.env.SECONDARY_RPC_URL,
     process.env.TERTIARY_RPC_URL
   ];
   
   private async getWorkingProvider(): Promise<string> {
     for (const provider of this.rpcProviders) {
       try {
         // Test the provider
         const web3 = new Web3(provider);
         await web3.eth.getBlockNumber();
         return provider;
       } catch (error) {
         logger.warn(`RPC provider ${provider} failed: ${error.message}`);
       }
     }
     throw new Error('No working RPC provider found');
   }
   ```

### 2. "Invalid token address" or "Token not found"

This error occurs when the bot tries to scan a pair with an invalid or non-existent token address.

#### Possible Causes:

- **Misconfigured Token List**: The token list contains incorrect addresses.
- **Network Mismatch**: The token exists on a different network than the one being scanned.
- **Contract Deployment Issues**: The token contract may have been deployed incorrectly.

#### How to Fix:

1. **Validate Token Addresses**:
   Implement a validation function to check token addresses before scanning:
   ```typescript
   async isValidToken(address: string): Promise<boolean> {
     try {
       const web3 = new Web3(this.rpcUrl);
       const tokenContract = new web3.eth.Contract(ERC20_ABI, address);
       await tokenContract.methods.symbol().call();
       return true;
     } catch (error) {
       logger.warn(`Invalid token address ${address}: ${error.message}`);
       return false;
     }
   }
   ```

2. **Update Token List**:
   Regularly update the token list with valid addresses:
   ```
   curl -X POST http://localhost:3001/api/v1/tokens/update
   ```

3. **Filter Pairs Before Scanning**:
   Modify the scanning process to filter out pairs with invalid tokens:
   ```typescript
   async scanValidPairs(): Promise<void> {
     const pairs = await this.getPairsToScan();
     const validPairs = [];
     
     for (const pair of pairs) {
       const isTokenAValid = await this.isValidToken(pair.tokenA);
       const isTokenBValid = await this.isValidToken(pair.tokenB);
       
       if (isTokenAValid && isTokenBValid) {
         validPairs.push(pair);
       } else {
         logger.warn(`Skipping invalid pair ${pair.tokenA}/${pair.tokenB}`);
       }
     }
     
     for (const pair of validPairs) {
       await this.scanPair(pair.tokenA, pair.tokenB);
     }
   }
   ```

### 3. "Error calculating price" or "Price calculation failed"

This error occurs when the bot cannot calculate the price of a token pair across different DEXes.

#### Possible Causes:

- **Insufficient Liquidity**: The liquidity pool has insufficient liquidity for accurate price calculation.
- **Price Impact Too High**: The trade size would cause a significant price impact.
- **DEX Router Issues**: The DEX router contract is not responding correctly.
- **Token Decimals Mismatch**: Incorrect handling of token decimals in price calculations.

#### How to Fix:

1. **Implement Minimum Liquidity Checks**:
   Skip pairs with insufficient liquidity:
   ```typescript
   async hasMinimumLiquidity(tokenA: string, tokenB: string, minLiquidity = '1000'): Promise<boolean> {
     try {
       const liquidity = await this.getLiquidityDepth(tokenA, tokenB);
       return new BigNumber(liquidity).isGreaterThanOrEqualTo(minLiquidity);
     } catch (error) {
       logger.warn(`Error checking liquidity for ${tokenA}/${tokenB}: ${error.message}`);
       return false;
     }
   }
   ```

2. **Adjust Trade Size Based on Liquidity**:
   Dynamically adjust the trade size based on available liquidity:
   ```typescript
   calculateOptimalTradeSize(liquidity: string): string {
     // Use at most 10% of available liquidity
     return new BigNumber(liquidity).multipliedBy(0.1).toString();
   }
   ```

3. **Handle Token Decimals Correctly**:
   Ensure token decimals are handled correctly in price calculations:
   ```typescript
   async getTokenDecimals(tokenAddress: string): Promise<number> {
     try {
       const web3 = new Web3(this.rpcUrl);
       const tokenContract = new web3.eth.Contract(ERC20_ABI, tokenAddress);
       const decimals = await tokenContract.methods.decimals().call();
       return parseInt(decimals);
     } catch (error) {
       logger.warn(`Error getting decimals for token ${tokenAddress}: ${error.message}`);
       return 18; // Default to 18 decimals
     }
   }
   
   async normalizeAmount(amount: string, tokenAddress: string): Promise<string> {
     const decimals = await this.getTokenDecimals(tokenAddress);
     return new BigNumber(amount).dividedBy(new BigNumber(10).pow(decimals)).toString();
   }
   ```

### 4. "Gas estimation failed" or "Cannot estimate gas"

This error occurs when the bot cannot estimate the gas required for a transaction.

#### Possible Causes:

- **Complex Transaction Path**: The transaction path is too complex for accurate gas estimation.
- **Blockchain Congestion**: The network is congested, affecting gas estimation.
- **Contract Reverts**: The transaction would revert if executed.
- **Insufficient Funds**: The account does not have enough funds to cover gas costs.

#### How to Fix:

1. **Use Conservative Gas Estimates**:
   Implement conservative gas estimation with a safety margin:
   ```typescript
   estimateGasWithBuffer(baseEstimate: number, bufferPercentage = 20): number {
     return Math.ceil(baseEstimate * (1 + bufferPercentage / 100));
   }
   ```

2. **Implement Fallback Gas Limits**:
   Use fallback gas limits when estimation fails:
   ```typescript
   async estimateGasOrFallback(txObject: any, fallbackLimit = 300000): Promise<number> {
     try {
       const gasEstimate = await web3.eth.estimateGas(txObject);
       return this.estimateGasWithBuffer(gasEstimate);
     } catch (error) {
       logger.warn(`Gas estimation failed: ${error.message}. Using fallback limit.`);
       return fallbackLimit;
     }
   }
   ```

3. **Monitor Network Congestion**:
   Skip transactions during high congestion periods:
   ```typescript
   async isNetworkCongested(): Promise<boolean> {
     try {
       const gasPrice = await web3.eth.getGasPrice();
       const gasPriceGwei = web3.utils.fromWei(gasPrice, 'gwei');
       return parseFloat(gasPriceGwei) > this.maxGasPriceGwei;
     } catch (error) {
       logger.warn(`Error checking network congestion: ${error.message}`);
       return true; // Assume congested if check fails
     }
   }
   ```

## Monitoring and Debugging

### Real-time Monitoring

Monitor scanning errors in real-time using the WebSocket service:

```javascript
const ws = new WebSocket('ws://localhost:3002/ws');

ws.on('message', (data) => {
  const message = JSON.parse(data);
  if (message.type === 'scanning_error') {
    console.log('Scanning Error:', message.data);
  }
});
```

### Logging

Enable detailed logging for scanning operations:

1. **Set Log Level**:
   In `backend/api/utils/logger.ts`, set the log level to 'debug' for detailed logs:
   ```typescript
   const logger = winston.createLogger({
     level: 'debug',
     // Other configuration
   });
   ```

2. **Add Debug Logs**:
   Add detailed debug logs in the scanning process:
   ```typescript
   async scanPair(tokenA: string, tokenB: string): Promise<void> {
     logger.debug(`Starting scan for pair ${tokenA}/${tokenB}`);
     // Existing scanning logic
     logger.debug(`Completed scan for pair ${tokenA}/${tokenB}`);
   }
   ```

### Performance Metrics

Track scanning performance metrics:

```typescript
class ScanningMetrics {
  private totalScans = 0;
  private successfulScans = 0;
  private failedScans = 0;
  private scanTimes: number[] = [];
  
  recordScan(success: boolean, timeMs: number): void {
    this.totalScans++;
    if (success) {
      this.successfulScans++;
    } else {
      this.failedScans++;
    }
    this.scanTimes.push(timeMs);
  }
  
  getMetrics(): any {
    const avgTime = this.scanTimes.length > 0 
      ? this.scanTimes.reduce((a, b) => a + b, 0) / this.scanTimes.length 
      : 0;
    
    return {
      totalScans: this.totalScans,
      successfulScans: this.successfulScans,
      failedScans: this.failedScans,
      successRate: this.totalScans > 0 ? (this.successfulScans / this.totalScans) * 100 : 0,
      averageScanTimeMs: avgTime,
    };
  }
}
```

## Conclusion

By understanding and addressing these common scanning errors, you can improve the reliability and performance of the ArbitrageX bot. Regular monitoring, proper error handling, and implementing the fixes described in this document will help minimize scanning errors and ensure the bot operates efficiently. 