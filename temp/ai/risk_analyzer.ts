export class AdaptiveRiskManager {
  private readonly maxDrawdown: number;
  private readonly volatilityWindow: number;
  private readonly liquiditySafety: number;
  private readonly maxExposure: number;
  private readonly minProfitThreshold: number;

  constructor(
    maxDrawdown: number = 0.2, // 20% max drawdown threshold
    volatilityWindow: number = 24, // 24-hour lookback period
    liquiditySafety: number = 0.3, // 30% of observed liquidity
    maxExposure: number = 0.1, // 10% max capital exposure
    minProfitThreshold: number = 0.002 // 0.2% minimum profit threshold
  ) {
    this.maxDrawdown = maxDrawdown;
    this.volatilityWindow = volatilityWindow;
    this.liquiditySafety = liquiditySafety;
    this.maxExposure = maxExposure;
    this.minProfitThreshold = minProfitThreshold;
  }

  public async analyze_market_risk(
    prices: number[],
    liquidities: number[]
  ): Promise<{ isValid: boolean; risk: number; reason?: string }> {
    try {
      // Calculate price volatility
      const volatility = this.calculateVolatility(prices);
      if (volatility > this.maxDrawdown) {
        return {
          isValid: false,
          risk: volatility,
          reason: 'High price volatility',
        };
      }

      // Check liquidity adequacy
      const avgLiquidity = liquidities.reduce((a, b) => a + b, 0) / liquidities.length;
      if (avgLiquidity < this.liquiditySafety) {
        return {
          isValid: false,
          risk: 1 - avgLiquidity / this.liquiditySafety,
          reason: 'Insufficient liquidity',
        };
      }

      // Calculate overall risk score
      const riskScore = this.calculateRiskScore(volatility, avgLiquidity);

      return {
        isValid: riskScore <= this.maxExposure,
        risk: riskScore,
        reason: riskScore > this.maxExposure ? 'High overall risk' : undefined,
      };
    } catch (error) {
      console.error('Error in risk analysis:', error);
      return {
        isValid: false,
        risk: 1,
        reason: 'Risk analysis failed',
      };
    }
  }

  private calculateVolatility(prices: number[]): number {
    if (prices.length < 2) return 0;

    const returns = [];
    for (let i = 1; i < prices.length; i++) {
      returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
    }

    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (returns.length - 1);

    return Math.sqrt(variance);
  }

  private calculateRiskScore(volatility: number, liquidity: number): number {
    // Normalize volatility and liquidity to [0,1] range
    const normalizedVolatility = Math.min(volatility / this.maxDrawdown, 1);
    const normalizedLiquidity = Math.max(0, Math.min(liquidity / this.liquiditySafety, 1));

    // Weight factors (can be adjusted based on risk preference)
    const volatilityWeight = 0.6;
    const liquidityWeight = 0.4;

    return volatilityWeight * normalizedVolatility + liquidityWeight * (1 - normalizedLiquidity);
  }

  public validateTradeSize(tradeSize: number, liquidity: number): boolean {
    return tradeSize <= liquidity * this.liquiditySafety;
  }

  public validateProfitability(expectedProfit: number): boolean {
    return expectedProfit >= this.minProfitThreshold;
  }
}
