import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Box,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Button,
  AppBar,
  Toolbar,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Collapse,
} from '@mui/material';
import { styled } from '@mui/material/styles';
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
  switch (severity.toUpperCase()) {
    case 'CRITICAL':
      return '#dc3545';
    case 'HIGH':
      return '#fd7e14';
    case 'MEDIUM':
      return '#ffc107';
    case 'LOW':
      return '#28a745';
    default:
      return '#6c757d';
  }
};

const Dashboard = () => {
  const [scanData, setScanData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [expandedCVE, setExpandedCVE] = useState(null);
  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('No authentication token found. Please login again.');
        setLoading(false);
        return;
      }

      const response = await axios.get('/api/scan/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data) {
        setScanData(response.data);
        setError(null);
      }
    } catch (err) {
      console.error('Error fetching scan data:', err);
      setError(err.response?.data?.message || 'Error fetching scan data');
    } finally {
      setLoading(false);
    }
  };

  const startScan = async () => {
    try {
      setScanning(true);
      const token = localStorage.getItem('token');
      await axios.post('/api/scan', {}, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      await fetchData();
    } catch (err) {
      setError('Failed to start scan: ' + (err.response?.data?.message || err.message));
    } finally {
      setScanning(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const vulnerabilityData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      data: [
        scanData?.latest_scan?.vulnerabilities?.CRITICAL?.length || 0,
        scanData?.latest_scan?.vulnerabilities?.HIGH?.length || 0,
        scanData?.latest_scan?.vulnerabilities?.MEDIUM?.length || 0,
        scanData?.latest_scan?.vulnerabilities?.LOW?.length || 0
      ],
      backgroundColor: ['#dc3545', '#fd7e14', '#ffc107', '#28a745'],
    }]
  };

  const podSecurityData = {
    labels: ['Secure', 'Vulnerable', 'Unknown'],
    datasets: [{
      data: [
        scanData?.latest_scan?.pods?.filter(pod => pod.vulnerabilities.length === 0)?.length || 0,
        scanData?.latest_scan?.pods?.filter(pod => pod.vulnerabilities.length > 0)?.length || 0,
        0
      ],
      backgroundColor: ['#28a745', '#dc3545', '#6c757d'],
    }]
  };

  const timelineData = {
    labels: scanData?.latest_scan?.pods?.map((_, index) => `Scan ${index + 1}`) || [],
    datasets: [{
      label: 'Vulnerabilities',
      data: scanData?.latest_scan?.pods?.map(pod => pod.vulnerabilities.length) || [],
      borderColor: '#2196f3',
      tension: 0.1
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

      <Box sx={{ p: 3 }}>
        <Grid container spacing={3}>
          {/* Summary Cards */}
          <Grid item xs={12} md={3}>
            <Item>
              <Typography variant="h6">Total Vulnerabilities</Typography>
              <Typography variant="h4" color="error">
                {Object.values(scanData?.latest_scan?.vulnerabilities || {}).reduce((acc, curr) => acc + (curr?.length || 0), 0)}
              </Typography>
            </Item>
          </Grid>
          <Grid item xs={12} md={3}>
            <Item>
              <Typography variant="h6">Critical Issues</Typography>
              <Typography variant="h4" color="error">
                {scanData?.latest_scan?.vulnerabilities?.CRITICAL?.length || 0}
              </Typography>
            </Item>
          </Grid>
          <Grid item xs={12} md={3}>
            <Item>
              <Typography variant="h6">Pods Scanned</Typography>
              <Typography variant="h4">
                {scanData?.latest_scan?.pods?.length || 0}
              </Typography>
            </Item>
          </Grid>
          <Grid item xs={12} md={3}>
            <Item>
              <Typography variant="h6">Scan Status</Typography>
              <Typography variant="h4" color={scanData?.status === 'completed' ? 'success' : 'warning'}>
                {scanData?.status || 'Unknown'}
              </Typography>
            </Item>
          </Grid>

          {/* Charts */}
          <Grid item xs={12} md={6}>
            <Item>
              <Typography variant="h6">Vulnerability Distribution</Typography>
              <Box sx={{ height: 300 }}>
                <Doughnut data={vulnerabilityData} options={{ maintainAspectRatio: false }} />
              </Box>
            </Item>
          </Grid>
          <Grid item xs={12} md={6}>
            <Item>
              <Typography variant="h6">Pod Security Status</Typography>
              <Box sx={{ height: 300 }}>
                <Doughnut data={podSecurityData} options={{ maintainAspectRatio: false }} />
              </Box>
            </Item>
          </Grid>
          <Grid item xs={12}>
            <Item>
              <Typography variant="h6">Vulnerability Trend</Typography>
              <Box sx={{ height: 300 }}>
                <Line data={timelineData} options={{ maintainAspectRatio: false }} />
              </Box>
            </Item>
          </Grid>

          {/* CVE List */}
          <Grid item xs={12}>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>CVE ID</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Affected Components</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scanData?.latest_scan?.cves?.map((cve) => (
                    <React.Fragment key={cve.id}>
                      <TableRow>
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
                        <TableCell>{cve.affected_components.join(', ')}</TableCell>
                        <TableCell>{cve.description}</TableCell>
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={() => setExpandedCVE(expandedCVE === cve.id ? null : cve.id)}
                          >
                            {expandedCVE === cve.id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={5}>
                          <Collapse in={expandedCVE === cve.id} timeout="auto" unmountOnExit>
                            <Box sx={{ margin: 1 }}>
                              <Typography variant="h6" gutterBottom component="div">
                                Details
                              </Typography>
                              <Table size="small">
                                <TableBody>
                                  <TableRow>
                                    <TableCell component="th" scope="row">Attack Vector</TableCell>
                                    <TableCell>{cve.attack_vector}</TableCell>
                                  </TableRow>
                                  <TableRow>
                                    <TableCell component="th" scope="row">Fix Version</TableCell>
                                    <TableCell>{cve.fix_version}</TableCell>
                                  </TableRow>
                                  <TableRow>
                                    <TableCell component="th" scope="row">Mitigation</TableCell>
                                    <TableCell>{cve.mitigation}</TableCell>
                                  </TableRow>
                                  <TableRow>
                                    <TableCell component="th" scope="row">Published Date</TableCell>
                                    <TableCell>{new Date(cve.published_date).toLocaleDateString()}</TableCell>
                                  </TableRow>
                                  <TableRow>
                                    <TableCell component="th" scope="row">Reference</TableCell>
                                    <TableCell>
                                      <a href={cve.link} target="_blank" rel="noopener noreferrer">
                                        View on NVD
                                      </a>
                                    </TableCell>
                                  </TableRow>
                                </TableBody>
                              </Table>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default Dashboard;
