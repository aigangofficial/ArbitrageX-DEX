interface TokenBucketConfig {
  capacity: number;
  fillRate: number;
  initialTokens?: number;
}

export class TokenBucket {
  private tokens: number;
  private lastFill: number;
  private readonly capacity: number;
  private readonly fillRate: number;

  constructor(config: TokenBucketConfig) {
    this.capacity = config.capacity;
    this.fillRate = config.fillRate;
    this.tokens = config.initialTokens ?? this.capacity;
    this.lastFill = Date.now();
  }

  private fill(): void {
    const now = Date.now();
    const timePassed = (now - this.lastFill) / 1000; // Convert to seconds
    const tokensToAdd = timePassed * this.fillRate;
    
    this.tokens = Math.min(this.capacity, this.tokens + tokensToAdd);
    this.lastFill = now;
  }

  public tryConsume(tokens: number = 1): boolean {
    this.fill();
    if (this.tokens >= tokens) {
      this.tokens -= tokens;
      return true;
    }
    return false;
  }

  public getTokenCount(): number {
    this.fill();
    return Math.floor(this.tokens);
  }

  public getTimeUntilNextToken(): number {
    if (this.tokens >= this.capacity) {
      return 0;
    }
    
    const tokensNeeded = 1;
    const timeNeeded = (tokensNeeded / this.fillRate) * 1000; // Convert to milliseconds
    return Math.ceil(timeNeeded);
  }
} 