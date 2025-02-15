import {
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';

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

interface RecentTradesProps {
  trades: Trade[];
}

const RecentTrades = ({ trades }: RecentTradesProps) => {
  const getStatusColor = (status: Trade['status']) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'executing':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatAmount = (amount: string) => {
    return Number(amount).toFixed(6);
  };

  return (
    <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
      <Typography component="h2" variant="h6" color="primary" gutterBottom>
        Recent Trades
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Pair</TableCell>
              <TableCell align="right">Amount In</TableCell>
              <TableCell align="right">Amount Out</TableCell>
              <TableCell align="right">Profit</TableCell>
              <TableCell align="right">Gas Used</TableCell>
              <TableCell align="right">Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {trades.map(trade => (
              <TableRow key={trade.id}>
                <TableCell>{formatTimestamp(trade.timestamp)}</TableCell>
                <TableCell>
                  {trade.tokenA}/{trade.tokenB}
                </TableCell>
                <TableCell align="right">
                  {formatAmount(trade.amountIn)} {trade.tokenA}
                </TableCell>
                <TableCell align="right">
                  {formatAmount(trade.amountOut)} {trade.tokenB}
                </TableCell>
                <TableCell align="right">
                  {trade.profit ? `$${Number(trade.profit).toFixed(2)}` : '-'}
                </TableCell>
                <TableCell align="right">
                  {trade.gasUsed ? `${Number(trade.gasUsed).toFixed(2)} GWEI` : '-'}
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={trade.status}
                    color={getStatusColor(trade.status) as any}
                    size="small"
                  />
                </TableCell>
              </TableRow>
            ))}
            {trades.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No trades available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default RecentTrades;
