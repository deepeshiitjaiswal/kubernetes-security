# Kubernetes Vulnerability Scanner Dashboard

A web-based dashboard for scanning and monitoring security vulnerabilities in your Kubernetes cluster.

## Features

- User Authentication and Authorization
- Real-time Vulnerability Scanning
- Interactive Dashboard
- Detailed Vulnerability Reports
- Kubernetes Cluster Integration

## Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl CLI tool
- Docker
- Python 3.8+
- Node.js 14+
- Helm (optional, for Helm chart installation)

## Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/deepeshiitjaiswal/kubernetes-security.git
cd kubernetes-security
```

2. Set up the backend:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export JWT_SECRET_KEY=your_secret_key

# Run the backend
flask run
```

3. Set up the frontend:
```bash
cd frontend
npm install
npm start
```

## Kubernetes Deployment

### Option 1: Direct Deployment

1. Build and push Docker images:
```bash
# Backend
docker build -t your-registry/k8s-vuln-scanner-backend:latest ./backend
docker push your-registry/k8s-vuln-scanner-backend:latest

# Frontend
docker build -t your-registry/k8s-vuln-scanner-frontend:latest ./frontend
docker push your-registry/k8s-vuln-scanner-frontend:latest
```

2. Create Kubernetes secrets:
```bash
kubectl create secret generic scanner-secrets \
  --from-literal=JWT_SECRET_KEY=your_secret_key \
  --from-literal=DB_PASSWORD=your_db_password
```

3. Apply Kubernetes manifests:
```bash
# Create namespace
kubectl create namespace vuln-scanner

# Apply manifests
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/ingress.yaml
```

### Option 2: Helm Installation

1. Add the Helm repository:
```bash
helm repo add k8s-vuln-scanner https://your-helm-repo.com
helm repo update
```

2. Install the chart:
```bash
helm install vuln-scanner k8s-vuln-scanner/vuln-scanner \
  --namespace vuln-scanner \
  --create-namespace \
  --set backend.image.repository=your-registry/k8s-vuln-scanner-backend \
  --set frontend.image.repository=your-registry/k8s-vuln-scanner-frontend \
  --set backend.secrets.jwtSecret=your_secret_key
```

## Accessing the Dashboard

1. Get the dashboard URL:
```bash
# If using NodePort
kubectl get svc -n vuln-scanner frontend-service

# If using Ingress
kubectl get ingress -n vuln-scanner vuln-scanner-ingress
```

2. Access the dashboard using the provided URL and log in with your credentials.

## Configuration

### Backend Configuration

The backend service can be configured using the following environment variables:

- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `DB_URI`: Database connection URI
- `KUBERNETES_SERVICE_HOST`: Kubernetes API server host
- `KUBERNETES_SERVICE_PORT`: Kubernetes API server port

### Frontend Configuration

The frontend configuration can be modified in `frontend/src/config.js`:

- `API_BASE_URL`: Backend API endpoint
- `SCAN_INTERVAL`: Vulnerability scan interval in minutes

## Security Considerations

1. **RBAC**: Ensure proper RBAC policies are configured for the scanner service account
2. **Network Policies**: Implement network policies to restrict pod communication
3. **Secrets**: Use Kubernetes secrets for sensitive information
4. **TLS**: Enable TLS for ingress and service communication

## Monitoring and Logging

1. **Prometheus Metrics**:
   - Endpoint: `/metrics`
   - Available metrics: scan_duration, vulnerability_count, etc.

2. **Logging**:
   - Backend logs: `kubectl logs -n vuln-scanner deployment/backend`
   - Frontend logs: `kubectl logs -n vuln-scanner deployment/frontend`

## Troubleshooting

1. **Pod Status**:
```bash
kubectl get pods -n vuln-scanner
kubectl describe pod <pod-name> -n vuln-scanner
```

2. **Service Connectivity**:
```bash
kubectl get svc -n vuln-scanner
kubectl describe svc <service-name> -n vuln-scanner
```

3. **Common Issues**:
   - Database connection errors
   - RBAC permission issues
   - Image pull failures
   - Resource constraints

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
