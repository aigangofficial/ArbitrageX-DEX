// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.MONGODB_URI = 'mongodb://localhost:27017/test';
process.env.REDIS_URL = 'redis://localhost:6379';
process.env.JWT_SECRET = 'test-secret';

// Global test timeout
jest.setTimeout(30000);

// Suppress console.log during tests
global.console = {
  ...console,
  // Uncomment to ignore console.log during tests
  // log: jest.fn(),
  error: console.error,
  warn: console.warn,
  info: console.info,
  debug: console.debug,
};
