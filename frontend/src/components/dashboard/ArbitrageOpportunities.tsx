import {
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';

interface Opportunity {
  id: string;
  tokenA: string;
  tokenB: string;
  spread: number;
  profit: string;
  route: string;
  timestamp: string;
}

interface ArbitrageOpportunitiesProps {
  opportunities: Opportunity[];
}

const ArbitrageOpportunities = ({ opportunities }: ArbitrageOpportunitiesProps) => {
  const handleExecute = (opportunity: Opportunity) => {
    // TODO: Implement trade execution
    console.log('Executing trade:', opportunity);
  };

  return (
    <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
      <Typography component="h2" variant="h6" color="primary" gutterBottom>
        Arbitrage Opportunities
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Pair</TableCell>
              <TableCell align="right">Spread</TableCell>
              <TableCell align="right">Profit</TableCell>
              <TableCell align="right">Route</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {opportunities.map(opportunity => (
              <TableRow key={opportunity.id}>
                <TableCell>
                  {opportunity.tokenA}/{opportunity.tokenB}
                </TableCell>
                <TableCell align="right">{opportunity.spread.toFixed(2)}%</TableCell>
                <TableCell align="right">${Number(opportunity.profit).toFixed(2)}</TableCell>
                <TableCell align="right">{opportunity.route}</TableCell>
                <TableCell align="right">
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => handleExecute(opportunity)}
                  >
                    Execute
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {opportunities.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No opportunities available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default ArbitrageOpportunities;
