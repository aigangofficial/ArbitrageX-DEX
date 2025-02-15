const mockTrades = [
  { id: '1', tokenA: 'ETH', tokenB: 'USDT', timestamp: new Date() },
  { id: '2', tokenA: 'BTC', tokenB: 'USDT', timestamp: new Date() },
];

export const ArbitrageTrade = {
  find: jest.fn().mockReturnValue({
    sort: jest.fn().mockReturnValue({
      limit: jest.fn().mockImplementation(limit => {
        console.log('Mock database: Fetching trades with limit:', limit);
        const trades = mockTrades.slice(0, limit);
        console.log('Mock database: Returning trades:', trades);
        return Promise.resolve(trades);
      }),
    }),
  }),
  findById: jest.fn().mockImplementation(id => {
    console.log('Mock database: Finding trade by id:', id);
    const trade = mockTrades.find(t => t.id === id);
    console.log('Mock database: Found trade:', trade);
    return Promise.resolve(trade || null);
  }),
  findByIdAndUpdate: jest.fn().mockImplementation((id, update) => {
    console.log('Mock database: Updating trade:', id, update);
    const trade = mockTrades.find(t => t.id === id);
    if (!trade) {
      console.log('Mock database: Trade not found');
      return Promise.resolve(null);
    }
    const updatedTrade = { ...trade, ...update };
    console.log('Mock database: Updated trade:', updatedTrade);
    return Promise.resolve(updatedTrade);
  }),
};
