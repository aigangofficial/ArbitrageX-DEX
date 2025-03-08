
    const express = require('express');
    
    // Create a simple express app with mock endpoints
    async function startServer() {
      try {
        const app = express();
        app.use(express.json());
        
        // Log all requests
        app.use((req, res, next) => {
          console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
          next();
        });
        
        // Add health endpoint
        app.get('/api/v1/health', (req, res) => {
          console.log('Health endpoint called');
          res.json({ status: 'ok' });
        });
        
        // Add blockchain health endpoint
        app.get('/api/v1/blockchain/health', (req, res) => {
          console.log('Blockchain health endpoint called');
          
          res.json({
            status: 'connected',
            provider: {
              url: 'http://127.0.0.1:8546',
              network: 'hardhat',
              chainId: 31337
            },
            contracts: {
              ArbitrageExecutor: '0x5FbDB2315678afecb367f032d93F642f64180aa3',
              FlashLoanService: '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512'
            }
          });
        });
        
        // Add set execution mode endpoint
        app.post('/api/v1/blockchain/set-execution-mode', (req, res) => {
          console.log('Set execution mode endpoint called', req.body);
          
          res.json({
            status: 'success',
            message: `Execution mode set to "${req.body.mode || 'test'}"`,
            mode: req.body.mode || 'test'
          });
        });
        
        // Add execute arbitrage endpoint
        app.post('/api/v1/blockchain/execute-arbitrage', (req, res) => {
          console.log('Execute arbitrage endpoint called', req.body);
          
          res.json({
            status: 'success',
            message: 'Arbitrage executed successfully',
            transaction: {
              hash: '0x' + Math.random().toString(16).substring(2, 42),
              blockNumber: 12345678,
              gasUsed: '250000',
              effectiveGasPrice: '20000000000'
            },
            profit: {
              amount: '0.05',
              token: req.body.targetToken || 'USDC'
            },
            executionMode: 'test'
          });
        });
        
        // Log all registered routes
        console.log('Registered routes:');
        app._router.stack.forEach(r => {
          if (r.route && r.route.path) {
            console.log(`${Object.keys(r.route.methods).join(',')} ${r.route.path}`);
          }
        });
        
        // Start server
        const server = app.listen(3000, () => {
          console.log(`Server started on port 3000`);
        });
        
        process.on('SIGINT', () => {
          server.close();
          process.exit(0);
        });
      } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
      }
    }
    
    startServer();
    