import { AccountBalance, Assessment, LocalGasStation, SwapHoriz } from '@mui/icons-material';
import { Grid, Paper, Typography } from '@mui/material';

interface TradingStatsProps {
  stats: {
    totalTrades: number;
    successRate: number;
    totalProfit: string;
    averageGasUsed: string;
  };
}

const StatCard = ({
  title,
  value,
  icon,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
}) => (
  <Paper
    sx={{
      p: 2,
      display: 'flex',
      flexDirection: 'column',
      height: 140,
      position: 'relative',
      overflow: 'hidden',
    }}
  >
    <div style={{ position: 'absolute', top: 10, right: 10, opacity: 0.2 }}>{icon}</div>
    <Typography component="h2" variant="h6" color="primary" gutterBottom>
      {title}
    </Typography>
    <Typography component="p" variant="h4">
      {value}
    </Typography>
  </Paper>
);

const TradingStats = ({ stats }: TradingStatsProps) => {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard
          title="Total Trades"
          value={stats.totalTrades}
          icon={<SwapHoriz sx={{ fontSize: 40 }} />}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard
          title="Success Rate"
          value={`${stats.successRate.toFixed(2)}%`}
          icon={<Assessment sx={{ fontSize: 40 }} />}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard
          title="Total Profit"
          value={`$${Number(stats.totalProfit).toFixed(2)}`}
          icon={<AccountBalance sx={{ fontSize: 40 }} />}
        />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard
          title="Avg Gas Used"
          value={`${Number(stats.averageGasUsed).toFixed(2)} GWEI`}
          icon={<LocalGasStation sx={{ fontSize: 40 }} />}
        />
      </Grid>
    </Grid>
  );
};

export default TradingStats;
