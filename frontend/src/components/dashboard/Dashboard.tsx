import {
  AppBar,
  Box,
  Button,
  Container,
  Grid,
  Paper,
  Toolbar,
  Typography,
  useTheme,
} from '@mui/material';
import { useEffect, useState } from 'react';
import TradingViewWidget from '../common/TradingViewWidget';
import ArbitrageOpportunities from './ArbitrageOpportunities';
import RecentTrades from './RecentTrades';
import TradingStats from './TradingStats';

interface DashboardProps {
  isConnected: boolean;
  onConnect: () => void;
}

interface Opportunity {
  id: string;
  tokenA: string;
  tokenB: string;
  spread: number;
  profit: string;
  route: string;
  timestamp: string;
}

interface Trade {
  id: string;
  tokenA: string;
  tokenB: string;
  amountIn: string;
  amountOut: string;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  timestamp: string;
  txHash?: string;
  profit?: string;
  gasUsed?: string;
}

const Dashboard = ({ isConnected, onConnect }: DashboardProps) => {
  const theme = useTheme();
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [stats, setStats] = useState({
    totalTrades: 0,
    successRate: 0,
    totalProfit: '0',
    averageGasUsed: '0',
  });

  useEffect(() => {
    // Fetch initial data
    fetchOpportunities();
    fetchRecentTrades();
    fetchStats();

    // Set up WebSocket connection
    const ws = new WebSocket(`ws://localhost:3001`);

    ws.onmessage = event => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case 'opportunity':
          setOpportunities(prev => [data.data, ...prev].slice(0, 10));
          break;
        case 'trade':
          setRecentTrades(prev => [data.data, ...prev].slice(0, 10));
          break;
        case 'stats':
          setStats(data.data);
          break;
      }
    };

    return () => ws.close();
  }, []);

  const fetchOpportunities = async () => {
    try {
      const response = await fetch('http://localhost:3000/api/arbitrage/opportunities');
      const data = await response.json();
      if (data.success) {
        setOpportunities(data.data);
      }
    } catch (error) {
      console.error('Error fetching opportunities:', error);
    }
  };

  const fetchRecentTrades = async () => {
    try {
      const response = await fetch('http://localhost:3000/api/trades/recent');
      const data = await response.json();
      if (data.success) {
        setRecentTrades(data.data);
      }
    } catch (error) {
      console.error('Error fetching recent trades:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:3000/api/trades/stats');
      const data = await response.json();
      if (data.success) {
        setStats(data.data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ArbitrageX
          </Typography>
          <Button color="inherit" onClick={onConnect} disabled={isConnected}>
            {isConnected ? 'Connected' : 'Connect Wallet'}
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Grid container spacing={3}>
          {/* Trading Stats */}
          <Grid item xs={12}>
            <TradingStats stats={stats} />
          </Grid>

          {/* Trading View Chart */}
          <Grid item xs={12} md={8}>
            <Paper
              sx={{
                p: 2,
                display: 'flex',
                flexDirection: 'column',
                height: 400,
              }}
            >
              <TradingViewWidget />
            </Paper>
          </Grid>

          {/* Arbitrage Opportunities */}
          <Grid item xs={12} md={4}>
            <ArbitrageOpportunities opportunities={opportunities} />
          </Grid>

          {/* Recent Trades */}
          <Grid item xs={12}>
            <RecentTrades trades={recentTrades} />
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default Dashboard;
