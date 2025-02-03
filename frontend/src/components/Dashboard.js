import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Paper,
  Grid,
  CircularProgress,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Chip
} from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  IconButton,
  Alert,
  LinearProgress,
  Collapse,
  styled
} from '@mui/material';
import axios from 'axios';
import LogoutIcon from '@mui/icons-material/Logout';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const Item = styled(Paper)(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
  ...theme.typography.body2,
  padding: theme.spacing(2),
  textAlign: 'center',
  color: theme.palette.text.secondary,
}));

const getSeverityColor = (severity) => {
  const colors = {
    'CRITICAL': '#dc3545',
    'HIGH': '#fd7e14',
    'MEDIUM': '#ffc107',
    'LOW': '#28a745'
  };
  return colors[severity] || '#6c757d';
};

const Dashboard = () => {
  const [scanData, setScanData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');
        if (!token) {
          setError('No authentication token found');
          return;
        }

        const response = await axios.get('/api/scan/status', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        setScanData(response.data);
        if (response.data.status === 'running') {
          setScanning(true);
        } else {
          setScanning(false);
        }
      } catch (err) {
        setError('Failed to fetch scan data: ' + (err.response?.data?.message || err.message));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Poll for updates every second while scanning
    const interval = setInterval(() => {
      if (scanning) {
        fetchData();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [scanning]);

  const startScan = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('No authentication token found');
        return;
      }

      setScanning(true);
      setError(null);
      setScanData(prev => ({
        ...prev,
        progress: 0,
        message: 'Initializing scan...'
      }));

      // Start the scan
      const scanResponse = await axios.post('/api/scan', {}, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (scanResponse.data.status === 'success') {
        // Poll for scan status
        const pollInterval = setInterval(async () => {
          try {
            const statusResponse = await axios.get('/api/scan/status', {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });

            const newData = statusResponse.data;
            setScanData(prev => ({
              ...prev,
              ...newData,
              progress: Math.max(prev?.progress || 0, newData.progress || 0)
            }));

            if (newData.status === 'completed') {
              clearInterval(pollInterval);
              setScanning(false);
            } else if (newData.status === 'error') {
              clearInterval(pollInterval);
              setScanning(false);
              setError('Scan failed: ' + newData.message);
            }
          } catch (err) {
            clearInterval(pollInterval);
            setScanning(false);
            setError('Error checking scan status: ' + (err.response?.data?.message || err.message));
          }
        }, 1000); // Poll every second for smoother updates

        // Clean up interval after 5 minutes (timeout)
        setTimeout(() => {
          clearInterval(pollInterval);
          if (scanning) {
            setScanning(false);
            setError('Scan timed out after 5 minutes');
          }
        }, 300000);
      } else {
        setError('Failed to start scan: ' + scanResponse.data.message);
        setScanning(false);
      }
    } catch (err) {
      console.error('Scan error:', err);
      setError('Failed to start scan: ' + (err.response?.data?.message || err.message));
      setScanning(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const vulnerabilityData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      data: [
        scanData?.vulnerability_stats?.by_severity?.CRITICAL || 0,
        scanData?.vulnerability_stats?.by_severity?.HIGH || 0,
        scanData?.vulnerability_stats?.by_severity?.MEDIUM || 0,
        scanData?.vulnerability_stats?.by_severity?.LOW || 0
      ],
      backgroundColor: ['#dc3545', '#fd7e14', '#ffc107', '#28a745'],
      hoverBackgroundColor: ['#c82333', '#e96b02', '#e0a800', '#218838']
    }]
  };

  const podSecurityData = {
    labels: ['Secure', 'Vulnerable'],
    datasets: [{
      data: [
        scanData?.pod_stats?.secure || 0,
        scanData?.pod_stats?.vulnerable || 0
      ],
      backgroundColor: ['#28a745', '#dc3545'],
      hoverBackgroundColor: ['#218838', '#c82333']
    }]
  };

  if (loading) return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
      <CircularProgress />
    </Box>
  );

  if (error) return (
    <Box sx={{ p: 3 }}>
      <Alert severity="error">{error}</Alert>
    </Box>
  );

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Kubernetes Vulnerability Scanner
          </Typography>
          <Button
            color="inherit"
            component={Link}
            to="/monitoring"
            sx={{ mr: 2 }}
          >
            Cluster Monitoring
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/resources"
            sx={{ mr: 2 }}
          >
            Resource Monitor
          </Button>
          <Button
            color="inherit"
            startIcon={<RefreshIcon />}
            onClick={startScan}
            disabled={scanning}
            sx={{ mr: 2 }}
          >
            {scanning ? 'Scanning...' : 'Start Scan'}
          </Button>
          <IconButton color="inherit" onClick={handleLogout}>
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Scan Progress Section */}
      {scanning && (
        <Box sx={{ width: '100%', p: 3 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Scan Progress
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Box sx={{ width: '100%', mr: 1 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={scanData?.progress || 0}
                  sx={{
                    height: 10,
                    borderRadius: 5,
                    backgroundColor: '#e0e0e0',
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 5,
                      backgroundColor: '#2196f3',
                      transition: 'transform 0.3s ease'
                    }
                  }}
                />
              </Box>
              <Box sx={{ minWidth: 60 }}>
                <Typography variant="body2" color="text.secondary">
                  {`${Math.round(scanData?.progress || 0)}%`}
                </Typography>
              </Box>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {scanData?.message || 'Scanning in progress...'}
            </Typography>
          </Paper>
        </Box>
      )}

      {/* Error Alert */}
      {error && (
        <Box sx={{ p: 3 }}>
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </Box>
      )}

      {/* Dashboard Content */}
      {scanData?.latest_scan && (
        <Box sx={{ p: 3 }}>
          {/* Summary Cards */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom>
                  Total Pods
                </Typography>
                <Typography variant="h4">
                  {scanData.pod_stats?.total || 0}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#dc3545', color: 'white' }}>
                <Typography variant="h6" gutterBottom>
                  Vulnerable Pods
                </Typography>
                <Typography variant="h4">
                  {scanData.pod_stats?.vulnerable || 0}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#28a745', color: 'white' }}>
                <Typography variant="h6" gutterBottom>
                  Secure Pods
                </Typography>
                <Typography variant="h4">
                  {scanData.pod_stats?.secure || 0}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom>
                  Total CVEs
                </Typography>
                <Typography variant="h4">
                  {scanData.vulnerability_stats?.total || 0}
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Charts */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Vulnerabilities by Severity
                </Typography>
                <Box sx={{ height: 300 }}>
                  <Doughnut data={vulnerabilityData} options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'right'
                      }
                    }
                  }} />
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Pod Security Status
                </Typography>
                <Box sx={{ height: 300 }}>
                  <Doughnut data={podSecurityData} options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'right'
                      }
                    }
                  }} />
                </Box>
              </Paper>
            </Grid>
          </Grid>

          {/* CVE Table */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Detected CVEs
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>CVE ID</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>Affected Pods</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scanData.latest_scan.cves.map((cve) => (
                    <TableRow key={cve.id}>
                      <TableCell>{cve.id}</TableCell>
                      <TableCell>
                        <Chip 
                          label={cve.severity}
                          sx={{ 
                            bgcolor: getSeverityColor(cve.severity),
                            color: 'white'
                          }}
                        />
                      </TableCell>
                      <TableCell>{cve.description}</TableCell>
                      <TableCell>
                        {scanData.latest_scan.pods
                          .filter(pod => pod.vulnerabilities?.some(v => v.cves?.includes(cve.id)))
                          .map(pod => pod.name)
                          .join(', ')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Box>
      )}
    </Box>
  );
};

export default Dashboard;
