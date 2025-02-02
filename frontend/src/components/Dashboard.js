import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
  Link,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Backdrop,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import axios from 'axios';
import SecurityIcon from '@mui/icons-material/Security';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorAlert from './ErrorAlert';
import { handleApiError } from '../utils/errorHandler';
import api from '../services/api';

const Dashboard = () => {
  const [resources, setResources] = useState(null);
  const [scanResults, setScanResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [kubeConfigError, setKubeConfigError] = useState(false);

  const fetchResources = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/resources');
      setResources(response.data.data);
    } catch (err) {
      const errorData = handleApiError(err);
      if (errorData.message.includes('kube-config')) {
        setKubeConfigError(true);
      }
      setError(errorData.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, []);

  const startScan = async () => {
    setScanning(true);
    setError(null);
    try {
      const response = await api.post('/scan');
      setScanResults(response.data.data);
    } catch (err) {
      const errorData = handleApiError(err);
      if (errorData.message.includes('kube-config')) {
        setKubeConfigError(true);
      }
      setError(errorData.message);
    } finally {
      setScanning(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      CRITICAL: '#dc3545', // Red
      HIGH: '#fd7e14',    // Orange
      MEDIUM: '#ffc107',  // Yellow
      LOW: '#198754'      // Green
    };
    return colors[severity] || '#6c757d'; // Gray for unknown
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const renderVulnerabilityChart = (vulnerabilities) => {
    if (!vulnerabilities) return null;

    const data = Object.entries(vulnerabilities).map(([severity, count]) => ({
      severity,
      count,
      color: getSeverityColor(severity)
    }));

    return (
      <Box sx={{ width: '100%', height: 400, p: 2 }}>
        <ResponsiveContainer>
          <BarChart
            data={data}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 20,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis
              dataKey="severity"
              tick={{ fill: '#666', fontSize: 14 }}
              tickLine={{ stroke: '#666' }}
              axisLine={{ stroke: '#666' }}
            />
            <YAxis
              tick={{ fill: '#666', fontSize: 14 }}
              tickLine={{ stroke: '#666' }}
              axisLine={{ stroke: '#666' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderRadius: '8px',
                border: '1px solid #ddd',
                boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
              }}
            />
            <Legend
              verticalAlign="top"
              height={36}
              formatter={(value) => (
                <span style={{ color: '#666', fontSize: '14px' }}>{value}</span>
              )}
            />
            <Bar
              dataKey="count"
              name="Vulnerabilities"
              radius={[4, 4, 0, 0]}
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Box>
    );
  };

  const renderCVETable = (cves) => {
    if (!cves || cves.length === 0) return null;

    return (
      <TableContainer component={Paper} sx={{ mt: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>CVE ID</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Fix Version</TableCell>
              <TableCell>Published Date</TableCell>
              <TableCell>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {cves.map((cve) => (
              <TableRow key={cve.id}>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {cve.id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={cve.severity}
                    size="small"
                    sx={{
                      bgcolor: getSeverityColor(cve.severity),
                      color: 'white',
                    }}
                  />
                </TableCell>
                <TableCell>{cve.description}</TableCell>
                <TableCell>{cve.fix_version}</TableCell>
                <TableCell>{formatDate(cve.published_date)}</TableCell>
                <TableCell>
                  <Link href={cve.link} target="_blank" rel="noopener noreferrer">
                    View Details
                  </Link>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderPodVulnerabilities = (pods) => {
    if (!pods || pods.length === 0) return null;

    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Pod Vulnerabilities
        </Typography>
        {pods.map((pod) => (
          <Accordion key={`${pod.namespace}-${pod.name}`}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>
                {pod.namespace}/{pod.name}
                {' - '}
                <Chip
                  label={`${pod.vulnerabilities.length + pod.cves.length} issues`}
                  size="small"
                  color={pod.vulnerabilities.length + pod.cves.length > 0 ? 'error' : 'success'}
                />
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {pod.vulnerabilities.map((vuln, index) => (
                <Alert
                  key={index}
                  severity={vuln.severity.toLowerCase()}
                  sx={{ mb: 1 }}
                >
                  <Typography variant="subtitle2">
                    {vuln.description}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Affected Resource: {vuln.affected_resource}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Recommendation: {vuln.recommendation}
                  </Typography>
                </Alert>
              ))}
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    );
  };

  if (loading) {
    return (
      <Backdrop open={true} sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <CircularProgress color="inherit" />
      </Backdrop>
    );
  }

  return (
    <Container maxWidth="xl">
      <Grid container spacing={3}>
        {/* Header */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h4" component="h1">
              Kubernetes Vulnerability Scanner
            </Typography>
          </Paper>
        </Grid>

        {/* Kubernetes Connection Error */}
        {kubeConfigError && (
          <Grid item xs={12}>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <AlertTitle>Kubernetes Configuration Required</AlertTitle>
              <Typography variant="body1">
                Unable to connect to Kubernetes cluster. Please ensure that:
                <ol>
                  <li>You have a Kubernetes cluster running</li>
                  <li>Your kubeconfig file is properly configured at ~/.kube/config</li>
                  <li>You have the necessary permissions to access the cluster</li>
                </ol>
              </Typography>
            </Alert>
          </Grid>
        )}

        {/* Error Alert */}
        {error && !kubeConfigError && (
          <Grid item xs={12}>
            <ErrorAlert error={error} onClose={() => setError(null)} />
          </Grid>
        )}

        {/* Cluster Overview */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">
                Cluster Overview
              </Typography>
              <Button
                variant="contained"
                color="primary"
                onClick={startScan}
                disabled={scanning}
                startIcon={<SecurityIcon />}
                sx={{
                  background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                  boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
                  color: 'white',
                  padding: '10px 30px',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #1976D2 30%, #00BCD4 90%)',
                  }
                }}
              >
                {scanning ? (
                  <>
                    <CircularProgress size={24} color="inherit" sx={{ mr: 1 }} />
                    Scanning...
                  </>
                ) : (
                  'Start Scan'
                )}
              </Button>
            </Box>
            <Grid container spacing={3}>
              {resources && (
                <>
                  <Grid item xs={12} md={4}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom>
                          Pods
                        </Typography>
                        <Typography variant="h4">{resources.pods}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom>
                          Services
                        </Typography>
                        <Typography variant="h4">{resources.services}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom>
                          Nodes
                        </Typography>
                        <Typography variant="h4">{resources.nodes}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </>
              )}
            </Grid>
          </Paper>
        </Grid>

        {scanResults && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              {/* Scan Summary */}
              <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} md={4}>
                  <Card sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white'
                  }}>
                    <CardContent>
                      <Typography color="white" gutterBottom>
                        Total Pods Scanned
                      </Typography>
                      <Typography variant="h4" color="white">
                        {scanResults.summary.total_pods}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card sx={{
                    background: 'linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%)',
                    color: 'white'
                  }}>
                    <CardContent>
                      <Typography color="white" gutterBottom>
                        Vulnerable Pods
                      </Typography>
                      <Typography variant="h4" color="white">
                        {scanResults.summary.vulnerable_pods}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card sx={{
                    background: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
                    color: 'white'
                  }}>
                    <CardContent>
                      <Typography color="white" gutterBottom>
                        Total CVEs
                      </Typography>
                      <Typography variant="h4" color="white">
                        {scanResults.summary.total_cves}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Vulnerability Chart */}
              <Box sx={{ mb: 4, mt: 2 }}>
                <Typography variant="h6" gutterBottom sx={{
                  borderBottom: '2px solid #eee',
                  paddingBottom: '8px',
                  marginBottom: '24px'
                }}>
                  Vulnerability Distribution
                </Typography>
                {renderVulnerabilityChart(scanResults.vulnerabilities)}
              </Box>

              {/* CVE Table */}
              <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
                CVE Details
              </Typography>
              {renderCVETable(scanResults.cves)}

              {/* Pod Vulnerabilities */}
              {renderPodVulnerabilities(scanResults.pods)}

              {/* Scan Timestamp */}
              <Typography variant="body2" color="textSecondary" sx={{ mt: 3 }}>
                Last scan: {formatDate(scanResults.scan_time)}
              </Typography>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default Dashboard;
