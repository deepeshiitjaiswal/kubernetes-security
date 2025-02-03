import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Grid,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  AppBar,
  Toolbar,
  Button,
  Alert,
  useTheme
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import LogoutIcon from '@mui/icons-material/Logout';
import DashboardIcon from '@mui/icons-material/Dashboard';
import StorageIcon from '@mui/icons-material/Storage';
import MemoryIcon from '@mui/icons-material/Memory';
import DnsIcon from '@mui/icons-material/Dns';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import MonitorIcon from '@mui/icons-material/Monitor';

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatCPU = (cpu) => {
  return `${(cpu * 100).toFixed(1)}%`;
};

const MetricCard = ({ title, value, icon: Icon, color }) => (
  <Paper 
    elevation={3} 
    sx={{ 
      p: 2,
      background: `linear-gradient(45deg, ${color}22 30%, ${color}11 90%)`,
      border: `1px solid ${color}33`,
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'transform 0.2s',
      '&:hover': {
        transform: 'scale(1.02)',
      }
    }}
  >
    <Icon sx={{ fontSize: 40, color: color, mb: 1 }} />
    <Typography variant="subtitle2" color="textSecondary" gutterBottom>
      {title}
    </Typography>
    <Typography variant="h4" sx={{ color: color }}>
      {value}
    </Typography>
  </Paper>
);

const ClusterMonitoring = () => {
  const [clusterMetrics, setClusterMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metricsHistory, setMetricsHistory] = useState([]);
  const navigate = useNavigate();
  const theme = useTheme();

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        const response = await axios.get('/api/cluster/metrics', {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data.status === 'success') {
          setClusterMetrics(response.data.data);
          
          // Add to history with timestamp
          setMetricsHistory(prev => {
            const newHistory = [...prev, {
              timestamp: new Date().toLocaleTimeString(),
              cpuUsage: response.data.data.cluster_cpu_usage,
              memoryUsage: response.data.data.cluster_memory_usage
            }].slice(-20); // Keep last 20 data points
            return newHistory;
          });
          
          setError(null);
        } else {
          setError(response.data.message || 'Failed to fetch metrics');
        }
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.message || err.message);
        setLoading(false);
      }
    };

    // Initial fetch
    fetchMetrics();

    // Set up polling every 10 seconds
    const interval = setInterval(fetchMetrics, 10000);

    return () => clearInterval(interval);
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  if (loading) {
    return (
      <Box>
        <AppBar 
          position="static" 
          sx={{ 
            background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
            boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)'
          }}
        >
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Cluster Monitoring
            </Typography>
          </Toolbar>
        </AppBar>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
          <CircularProgress sx={{ color: '#2196F3' }} />
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <AppBar 
        position="static" 
        sx={{ 
          background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
          boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)'
        }}
      >
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Cluster Monitoring
          </Typography>
          <Button
            color="inherit"
            component={Link}
            to="/resources"
            startIcon={<MonitorIcon />}
            sx={{ 
              mr: 2,
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)'
              }
            }}
          >
            Resource Monitor
          </Button>
          <Button
            color="inherit"
            component={Link}
            to="/dashboard"
            startIcon={<DashboardIcon />}
            sx={{ 
              mr: 2,
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)'
              }
            }}
          >
            Dashboard
          </Button>
          <Button
            color="inherit"
            onClick={handleLogout}
            startIcon={<LogoutIcon />}
            sx={{
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)'
              }
            }}
          >
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            mt: 2, 
            mx: 3,
            backgroundColor: '#ff000015',
            color: '#d32f2f'
          }}
        >
          {error}
        </Alert>
      )}

      <Box p={3}>
        <Grid container spacing={3}>
          {/* Cluster Overview */}
          <Grid item xs={12}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <MetricCard
                  title="Total Nodes"
                  value={clusterMetrics?.total_nodes || 0}
                  icon={DnsIcon}
                  color="#2196F3"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <MetricCard
                  title="Total Pods"
                  value={clusterMetrics?.total_pods || 0}
                  icon={StorageIcon}
                  color="#4CAF50"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <MetricCard
                  title="Total Namespaces"
                  value={clusterMetrics?.total_namespaces || 0}
                  icon={AccountTreeIcon}
                  color="#FF9800"
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <MetricCard
                  title="Total Services"
                  value={clusterMetrics?.total_services || 0}
                  icon={MemoryIcon}
                  color="#E91E63"
                />
              </Grid>
            </Grid>
          </Grid>

          {/* Resource Usage Charts */}
          {metricsHistory.length > 0 && (
            <Grid item xs={12}>
              <Paper 
                elevation={3} 
                sx={{ 
                  p: 3,
                  background: '#ffffff',
                  boxShadow: '0 3px 5px 2px rgba(0, 0, 0, .03)',
                  borderRadius: 2
                }}
              >
                <Typography variant="h6" gutterBottom sx={{ color: '#1976D2' }}>
                  Resource Usage Over Time
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={metricsHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="timestamp" stroke="#666" />
                    <YAxis yAxisId="left" stroke="#8884d8" />
                    <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: '#fff',
                        border: '1px solid #ccc',
                        borderRadius: '4px'
                      }}
                    />
                    <Legend />
                    <Line 
                      yAxisId="left"
                      type="monotone"
                      dataKey="cpuUsage"
                      stroke="#8884d8"
                      name="CPU Usage (%)"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="memoryUsage"
                      stroke="#82ca9d"
                      name="Memory Usage (GB)"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
          )}

          {/* Node Details */}
          {clusterMetrics?.nodes && (
            <Grid item xs={12}>
              <Paper 
                elevation={3} 
                sx={{ 
                  p: 3,
                  background: '#ffffff',
                  boxShadow: '0 3px 5px 2px rgba(0, 0, 0, .03)',
                  borderRadius: 2
                }}
              >
                <Typography variant="h6" gutterBottom sx={{ color: '#1976D2' }}>
                  Node Details
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold', color: '#1976D2' }}>Node Name</TableCell>
                        <TableCell sx={{ fontWeight: 'bold', color: '#1976D2' }}>Status</TableCell>
                        <TableCell sx={{ fontWeight: 'bold', color: '#1976D2' }}>CPU Usage</TableCell>
                        <TableCell sx={{ fontWeight: 'bold', color: '#1976D2' }}>Memory Usage</TableCell>
                        <TableCell sx={{ fontWeight: 'bold', color: '#1976D2' }}>Pods Running</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {clusterMetrics.nodes.map((node) => (
                        <TableRow 
                          key={node.name}
                          sx={{
                            '&:nth-of-type(odd)': {
                              backgroundColor: '#f8f9fa'
                            },
                            '&:hover': {
                              backgroundColor: '#f5f5f5'
                            }
                          }}
                        >
                          <TableCell>{node.name}</TableCell>
                          <TableCell>
                            <Chip
                              label={node.status}
                              color={node.status === 'Ready' ? 'success' : 'error'}
                              size="small"
                              sx={{
                                '& .MuiChip-label': {
                                  fontWeight: 'bold'
                                }
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Box sx={{ width: '100%', mr: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={node.cpu_usage * 100}
                                  sx={{
                                    height: 10,
                                    borderRadius: 5,
                                    backgroundColor: '#e9ecef',
                                    '& .MuiLinearProgress-bar': {
                                      backgroundColor: node.cpu_usage > 0.8 ? '#f44336' : 
                                                     node.cpu_usage > 0.6 ? '#ff9800' : '#4caf50',
                                      transition: 'transform .4s linear'
                                    }
                                  }}
                                />
                              </Box>
                              <Box sx={{ minWidth: 35 }}>
                                <Typography variant="body2" color="textSecondary">
                                  {formatCPU(node.cpu_usage)}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Box sx={{ width: '100%', mr: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={(node.memory_usage / node.memory_capacity) * 100}
                                  sx={{
                                    height: 10,
                                    borderRadius: 5,
                                    backgroundColor: '#e9ecef',
                                    '& .MuiLinearProgress-bar': {
                                      backgroundColor: (node.memory_usage / node.memory_capacity) > 0.8 ? '#f44336' :
                                                     (node.memory_usage / node.memory_capacity) > 0.6 ? '#ff9800' : '#4caf50',
                                      transition: 'transform .4s linear'
                                    }
                                  }}
                                />
                              </Box>
                              <Box sx={{ minWidth: 35 }}>
                                <Typography variant="body2" color="textSecondary">
                                  {formatBytes(node.memory_usage)} / {formatBytes(node.memory_capacity)}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography 
                              sx={{ 
                                color: node.pods_running > 20 ? '#f44336' : 
                                      node.pods_running > 10 ? '#ff9800' : '#4caf50',
                                fontWeight: 'bold'
                              }}
                            >
                              {node.pods_running}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>
          )}
        </Grid>
      </Box>
    </Box>
  );
};

export default ClusterMonitoring;
