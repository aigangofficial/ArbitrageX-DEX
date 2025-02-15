interface Config {
  mongodbUri: string;
  redisHost: string;
  port: number;
  wsPort: number;
  contracts: {
    flashLoanService: string;
    arbitrageExecutor: string;
    aavePool: string;
    quickswapRouter: string;
    sushiswapRouter: string;
    wmatic: string;
  };
}

export const config: Config = {
  mongodbUri: process.env.MONGODB_URI || 'mongodb://mongodb:27017/arbitragex',
  redisHost: process.env.REDIS_HOST || 'redis',
  port: Number(process.env.PORT) || 3001,
  wsPort: Number(process.env.WS_PORT) || 8080,
  contracts: {
    flashLoanService: '0x3e8C85Dbb5B4C910B91fbf61B542b874aDBfC9FE',
    arbitrageExecutor: '0x8eeEEdf7B807A4B12B37AaDDF8FE86FfFfcEdeF1',
    aavePool: '0x357D51124f59836DeD84c8a1730D72B749d8BC23',
    quickswapRouter: '0x8954AfA98594b838bda56FE4C12a09D7739D179b',
    sushiswapRouter: '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
    wmatic: '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889',
  },
};
