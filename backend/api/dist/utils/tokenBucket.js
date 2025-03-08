"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TokenBucket = void 0;
class TokenBucket {
    constructor(config) {
        this.capacity = config.capacity;
        this.fillRate = config.fillRate;
        this.tokens = config.initialTokens ?? this.capacity;
        this.lastFill = Date.now();
    }
    fill() {
        const now = Date.now();
        const timePassed = (now - this.lastFill) / 1000; // Convert to seconds
        const tokensToAdd = timePassed * this.fillRate;
        this.tokens = Math.min(this.capacity, this.tokens + tokensToAdd);
        this.lastFill = now;
    }
    tryConsume(tokens = 1) {
        this.fill();
        if (this.tokens >= tokens) {
            this.tokens -= tokens;
            return true;
        }
        return false;
    }
    getTokenCount() {
        this.fill();
        return Math.floor(this.tokens);
    }
    getTimeUntilNextToken() {
        if (this.tokens >= this.capacity) {
            return 0;
        }
        const tokensNeeded = 1;
        const timeNeeded = (tokensNeeded / this.fillRate) * 1000; // Convert to milliseconds
        return Math.ceil(timeNeeded);
    }
}
exports.TokenBucket = TokenBucket;
//# sourceMappingURL=tokenBucket.js.map