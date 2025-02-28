import { BaseContract, BigNumberish } from "ethers";

export interface IERC20 extends BaseContract {
  transfer(to: string, amount: BigNumberish): Promise<boolean>;
  approve(spender: string, amount: BigNumberish): Promise<boolean>;
  balanceOf(account: string): Promise<BigNumberish>;
  allowance(owner: string, spender: string): Promise<BigNumberish>;
  transferFrom(from: string, to: string, amount: BigNumberish): Promise<boolean>;
  connect(signer: any): IERC20;
}

export interface IFlashLoanService extends BaseContract {
  owner(): Promise<string>;
  aavePool(): Promise<string>;
  requestFlashLoan(
    token: string,
    amount: BigNumberish,
    tokenIn: string,
    tokenOut: string,
    router: string
  ): Promise<void>;
  withdraw(token: string, amount: BigNumberish): Promise<void>;
  connect(signer: any): IFlashLoanService;
  getAddress(): Promise<string>;
}

export interface IArbitrageExecutor extends BaseContract {
  owner(): Promise<string>;
  UNISWAP_V2_ROUTER(): Promise<string>;
  SUSHISWAP_V2_ROUTER(): Promise<string>;
  minProfitBps(): Promise<number>;
  setSupportedToken(token: string, supported: boolean): Promise<void>;
  setMinProfitBps(bps: number): Promise<void>;
  setDexRouter(router: string, enabled: boolean): Promise<void>;
  executeArbitrage(
    tokenIn: string,
    tokenOut: string,
    amount: BigNumberish,
    path: string[],
    sourceRouter: string
  ): Promise<BigNumberish>;
  getExpectedReturn(
    tokenA: string,
    tokenB: string,
    amountIn: BigNumberish,
    useFirstDexFirst: boolean
  ): Promise<BigNumberish>;
  withdraw(token: string, amount: BigNumberish): Promise<void>;
  executeTrade(
    router: string,
    path: string[],
    amountIn: BigNumberish,
    minAmountOut: BigNumberish
  ): Promise<BigNumberish>;
  connect(signer: any): IArbitrageExecutor;
  getAddress(): Promise<string>;
}
