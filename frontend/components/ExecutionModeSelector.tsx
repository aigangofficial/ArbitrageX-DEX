import React, { useState, useEffect } from 'react';
import { Box, Button, Card, CardContent, Typography, FormControl, RadioGroup, FormControlLabel, Radio, Snackbar, Alert } from '@mui/material';
import { styled } from '@mui/system';
import axios from 'axios';

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
}));

// Execution mode types
enum ExecutionMode {
  MAINNET = 'mainnet',
  FORK = 'fork'
}

interface ExecutionModeData {
  mode: ExecutionMode;
  lastUpdated?: string;
}

const ExecutionModeSelector: React.FC = () => {
  const [executionMode, setExecutionMode] = useState<ExecutionMode>(ExecutionMode.FORK);
  const [selectedMode, setSelectedMode] = useState<ExecutionMode>(ExecutionMode.FORK);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Fetch current execution mode on component mount
  useEffect(() => {
    fetchExecutionMode();
  }, []);

  const fetchExecutionMode = async () => {
    try {
      setLoading(true);
      const response = await axios.get<{ success: boolean; data: ExecutionModeData }>('/api/v1/execution-mode');
      
      if (response.data.success) {
        setExecutionMode(response.data.data.mode);
        setSelectedMode(response.data.data.mode);
      } else {
        setError('Failed to fetch execution mode');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error fetching execution mode:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleModeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedMode(event.target.value as ExecutionMode);
  };

  const handleSubmit = async () => {
    if (selectedMode === executionMode) {
      setSuccess('Execution mode is already set to ' + selectedMode);
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post<{ success: boolean; data: ExecutionModeData }>('/api/v1/execution-mode', {
        mode: selectedMode,
        updatedBy: 'frontend'
      });
      
      if (response.data.success) {
        setExecutionMode(response.data.data.mode);
        setSuccess(`Execution mode updated to ${response.data.data.mode}`);
      } else {
        setError('Failed to update execution mode');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error updating execution mode:', err);
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
          Network Execution Mode
        </Typography>
      </CardHeader>
      <CardContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Select the execution environment for arbitrage operations.
        </Typography>
        
        <Box sx={{ mt: 2 }}>
          <FormControl component="fieldset">
            <RadioGroup
              aria-label="execution-mode"
              name="execution-mode"
              value={selectedMode}
              onChange={handleModeChange}
            >
              <FormControlLabel 
                value={ExecutionMode.FORK} 
                control={<Radio />} 
                label={
                  <Box>
                    <Typography variant="body1" fontWeight="medium">Fork Mode</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Safe testing environment with simulated transactions
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel 
                value={ExecutionMode.MAINNET} 
                control={<Radio />} 
                label={
                  <Box>
                    <Typography variant="body1" fontWeight="medium">Mainnet Mode</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Live execution with real transactions and assets
                    </Typography>
                  </Box>
                }
              />
            </RadioGroup>
          </FormControl>
        </Box>
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2">
            Current mode: <strong>{executionMode}</strong>
          </Typography>
          <StyledButton
            variant="contained"
            color="primary"
            onClick={handleSubmit}
            disabled={loading || selectedMode === executionMode}
          >
            {loading ? 'Updating...' : 'Update Mode'}
          </StyledButton>
        </Box>
      </CardContent>

      {/* Success and Error alerts */}
      <Snackbar open={!!error} autoHideDuration={6000} onClose={handleCloseAlert}>
        <Alert onClose={handleCloseAlert} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
      
      <Snackbar open={!!success} autoHideDuration={6000} onClose={handleCloseAlert}>
        <Alert onClose={handleCloseAlert} severity="success" sx={{ width: '100%' }}>
          {success}
        </Alert>
      </Snackbar>
    </StyledCard>
  );
};

export default ExecutionModeSelector; 