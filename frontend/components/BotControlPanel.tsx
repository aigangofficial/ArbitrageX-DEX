import React, { useState, useEffect } from 'react';
import { Box, Button, Card, CardContent, Typography, CircularProgress, Snackbar, Alert, FormControl, InputLabel, Select, MenuItem, TextField, Grid } from '@mui/material';
import { styled } from '@mui/system';
import axios from 'axios';
import { API_BASE_URL } from '../config/constants';

// Styled components
const StyledCard = styled(Card)(({ theme }) => ({
  marginBottom: '20px',
  borderRadius: '12px',
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
}));

const CardHeader = styled(Box)(({ theme }) => ({
  padding: '16px',
  borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
}));

const StyledButton = styled(Button)(({ theme }) => ({
  borderRadius: '8px',
  fontWeight: 'bold',
  textTransform: 'none',
  minWidth: '120px',
}));

interface BotControlPanelProps {
  onStatusChange?: (isRunning: boolean) => void;
}

const BotControlPanel: React.FC<BotControlPanelProps> = ({ onStatusChange }) => {
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Bot configuration
  const [runTime, setRunTime] = useState<number>(600);
  const [tokens, setTokens] = useState<string>('WETH,USDC,DAI');
  const [dexes, setDexes] = useState<string>('uniswap_v3,curve,balancer');
  const [gasStrategy, setGasStrategy] = useState<string>('dynamic');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Fetch bot status on component mount
  useEffect(() => {
    fetchBotStatus();
  }, []);

  const fetchBotStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/v1/bot-control/status`);
      setIsRunning(response.data.data.isRunning);
      if (onStatusChange) {
        onStatusChange(response.data.data.isRunning);
      }
    } catch (err) {
      setError('Failed to fetch bot status');
      console.error('Error fetching bot status:', err);
    } finally {
      setLoading(false);
    }
  };

  const startBot = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/v1/bot-control/start`, {
        runTime,
        tokens,
        dexes,
        gasStrategy
      });
      setSuccess('Bot started successfully');
      setIsRunning(true);
      if (onStatusChange) {
        onStatusChange(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to start bot');
      console.error('Error starting bot:', err);
    } finally {
      setLoading(false);
    }
  };

  const stopBot = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/v1/bot-control/stop`);
      setSuccess('Bot stopped successfully');
      setIsRunning(false);
      if (onStatusChange) {
        onStatusChange(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to stop bot');
      console.error('Error stopping bot:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseAlert = () => {
    setError(null);
    setSuccess(null);
  };

  return (
    <StyledCard>
      <CardHeader>
        <Typography variant="h6" fontWeight="bold">
          Bot Control
        </Typography>
        <Button 
          size="small" 
          color="primary" 
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? 'Hide Advanced' : 'Show Advanced'}
        </Button>
      </CardHeader>
      <CardContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="body1" sx={{ mb: 1 }}>
            Status: <span style={{ fontWeight: 'bold', color: isRunning ? 'green' : 'red' }}>
              {isRunning ? 'Running' : 'Stopped'}
            </span>
          </Typography>
          
          {showAdvanced && (
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Run Time (seconds)"
                  type="number"
                  value={runTime}
                  onChange={(e) => setRunTime(Number(e.target.value))}
                  disabled={isRunning}
                  size="small"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Tokens"
                  value={tokens}
                  onChange={(e) => setTokens(e.target.value)}
                  disabled={isRunning}
                  size="small"
                  helperText="Comma-separated list of tokens"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="DEXes"
                  value={dexes}
                  onChange={(e) => setDexes(e.target.value)}
                  disabled={isRunning}
                  size="small"
                  helperText="Comma-separated list of DEXes"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Gas Strategy</InputLabel>
                  <Select
                    value={gasStrategy}
                    label="Gas Strategy"
                    onChange={(e) => setGasStrategy(e.target.value)}
                    disabled={isRunning}
                  >
                    <MenuItem value="dynamic">Dynamic</MenuItem>
                    <MenuItem value="aggressive">Aggressive</MenuItem>
                    <MenuItem value="conservative">Conservative</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          )}
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <StyledButton
              variant="contained"
              color="primary"
              onClick={startBot}
              disabled={isRunning || loading}
              startIcon={loading && !isRunning ? <CircularProgress size={20} /> : null}
            >
              {loading && !isRunning ? 'Starting...' : 'Start Bot'}
            </StyledButton>
            <StyledButton
              variant="outlined"
              color="error"
              onClick={stopBot}
              disabled={!isRunning || loading}
              startIcon={loading && isRunning ? <CircularProgress size={20} /> : null}
            >
              {loading && isRunning ? 'Stopping...' : 'Stop Bot'}
            </StyledButton>
          </Box>
        </Box>
      </CardContent>
      
      <Snackbar open={!!error || !!success} autoHideDuration={6000} onClose={handleCloseAlert}>
        <Alert 
          onClose={handleCloseAlert} 
          severity={error ? 'error' : 'success'} 
          sx={{ width: '100%' }}
        >
          {error || success}
        </Alert>
      </Snackbar>
    </StyledCard>
  );
};

export default BotControlPanel; 