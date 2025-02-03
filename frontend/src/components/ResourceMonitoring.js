import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Grid,
  CircularProgress,
  AppBar,
  Toolbar,
  Button,
  Alert,
  Card,
  CardContent,
  useTheme,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import axios from 'axios';
import LogoutIcon from '@mui/icons-material/Logout';
import DashboardIcon from '@mui/icons-material/Dashboard';
import MonitorIcon from '@mui/icons-material/Monitor';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

const ResourceGauge = ({ value, max, title, unit, color }) => {
  const percentage = (value / max) * 100;
  const getColor = (pct) => {
    if (pct > 80) return '#ff4444';
    if (pct > 60) return '#ffa000';
    return '#00C49F';
  };

  return (
    <Card 
      elevation={3}
      sx={{
        height: '100%',
        background: `linear-gradient(45deg, ${color}15 30%, ${color}05 90%)`,
        border: `1px solid ${color}22`,
      }}
    >
      <CardContent>
        <Box sx={{ position: 'relative', display: 'inline-flex', width: '100%', justifyContent: 'center' }}>
          <CircularProgress
            variant="determinate"
            value={100}
            size={160}
            thickness={4}
            sx={{ color: '#f5f5f5', position: 'absolute' }}
          />
          <CircularProgress
            variant="determinate"
            value={percentage}
            size={160}
            thickness={4}
            sx={{ color: getColor(percentage), transform: 'rotate(-90deg)' }}
          />
          <Box
            sx={{
              top: 0,
              left: 0,
              bottom: 0,
              right: 0,
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
            }}
          >
            <Typography variant="h4" component="div" color="text.secondary">
              {value.toFixed(1)}
            </Typography>
            <Typography variant="caption" component="div" color="text.secondary">
              {unit}
            </Typography>
          </Box>
        </Box>
        <Typography variant="h6" align="center" sx={{ mt: 2 }}>
          {title}
        </Typography>
        <Typography variant="body2" align="center" color="text.secondary">
          {percentage.toFixed(1)}% of {max} {unit}
        </Typography>
      </CardContent>
    </Card>
  );
};

const ResourceMonitoring = () => {
  const [resourceMetrics, setResourceMetrics] = useState(null);
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

        const response = await axios.get('/api/resources/metrics', {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data.status === 'success') {
          setResourceMetrics(response.data.data);
          
          // Add to history with timestamp
          setMetricsHistory(prev => {
            const newHistory = [...prev, {
              timestamp: new Date().toLocaleTimeString(),
              cpuUsage: response.data.data.cpu_usage,
              memoryUsage: response.data.data.memory_usage,
              diskUsage: response.data.data.disk_usage
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

    // Set up polling every 5 seconds
    const interval = setInterval(fetchMetrics, 5000);

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
              Resource Monitoring
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
            Resource Monitoring
          </Typography>
          <Button
            color="inherit"
            component={Link}
            to="/monitoring"
            startIcon={<MonitorIcon />}
            sx={{ 
              mr: 2,
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)'
              }
            }}
          >
            Cluster Monitor
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
          {/* Resource Gauges */}
          <Grid item xs={12} md={4}>
            <ResourceGauge
              value={resourceMetrics?.cpu_usage || 0}
              max={resourceMetrics?.cpu_cores || 1}
              title="CPU Usage"
              unit="Cores"
              color="#2196F3"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <ResourceGauge
              value={resourceMetrics?.memory_usage || 0}
              max={resourceMetrics?.memory_total || 1}
              title="Memory Usage"
              unit="GB"
              color="#4CAF50"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <ResourceGauge
              value={resourceMetrics?.disk_usage || 0}
              max={resourceMetrics?.disk_total || 1}
              title="Disk Usage"
              unit="GB"
              color="#FF9800"
            />
          </Grid>

          {/* Resource Usage History */}
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
                  Resource Usage History
                </Typography>
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={metricsHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="timestamp" stroke="#666" />
                    <YAxis stroke="#666" />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: '#fff',
                        border: '1px solid #ccc',
                        borderRadius: '4px'
                      }}
                    />
                    <Legend />
                    <Area 
                      type="monotone"
                      dataKey="cpuUsage"
                      name="CPU Usage (Cores)"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                    <Area
                      type="monotone"
                      dataKey="memoryUsage"
                      name="Memory Usage (GB)"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                    <Area
                      type="monotone"
                      dataKey="diskUsage"
                      name="Disk Usage (GB)"
                      stroke="#ffc658"
                      fill="#ffc658"
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
          )}

          {/* Resource Distribution */}
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
                Resource Distribution
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle1" align="center" gutterBottom>
                    CPU Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Used', value: resourceMetrics?.cpu_usage || 0 },
                          { name: 'Available', value: (resourceMetrics?.cpu_cores || 1) - (resourceMetrics?.cpu_usage || 0) }
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        fill="#8884d8"
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {resourceMetrics && [0, 1].map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle1" align="center" gutterBottom>
                    Memory Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Used', value: resourceMetrics?.memory_usage || 0 },
                          { name: 'Available', value: (resourceMetrics?.memory_total || 1) - (resourceMetrics?.memory_usage || 0) }
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        fill="#82ca9d"
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {resourceMetrics && [0, 1].map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="subtitle1" align="center" gutterBottom>
                    Disk Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Used', value: resourceMetrics?.disk_usage || 0 },
                          { name: 'Available', value: (resourceMetrics?.disk_total || 1) - (resourceMetrics?.disk_usage || 0) }
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        fill="#ffc658"
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {resourceMetrics && [0, 1].map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default ResourceMonitoring;
