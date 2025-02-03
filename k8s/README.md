# Kubernetes Vulnerability Scanner Deployment Guide

## Prerequisites
- Docker
- Kubernetes cluster (EKS/AKS)
- kubectl configured
- Helm (for installing dependencies)
- Container registry access

## Deployment Steps

1. **Build and Push Docker Images**
```bash
# Build images
docker build -f Dockerfile.backend -t your-registry/k8s-vulnerability-scanner-backend:latest .
docker build -f Dockerfile.frontend -t your-registry/k8s-vulnerability-scanner-frontend:latest .

# Push to registry
docker push your-registry/k8s-vulnerability-scanner-backend:latest
docker push your-registry/k8s-vulnerability-scanner-frontend:latest
```

2. **Install NGINX Ingress Controller** (if not already installed)
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx
```

3. **Install cert-manager** (for SSL certificates)
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true
```

4. **Update Configuration**
- Edit `k8s/01-secrets.yaml` with your actual secrets (base64 encoded)
- Update `k8s/04-ingress.yaml` with your domain name
- Update image references in `k8s/02-backend.yaml` and `k8s/03-frontend.yaml`

5. **Deploy the Application**
```bash
# Create namespace and RBAC
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/05-rbac.yaml

# Create secrets
kubectl apply -f k8s/01-secrets.yaml

# Deploy backend and frontend
kubectl apply -f k8s/02-backend.yaml
kubectl apply -f k8s/03-frontend.yaml

# Deploy ingress
kubectl apply -f k8s/04-ingress.yaml
```

6. **Verify Deployment**
```bash
kubectl get pods -n k8s-vulnerability-scanner
kubectl get svc -n k8s-vulnerability-scanner
kubectl get ingress -n k8s-vulnerability-scanner
```

## Environment Variables

### Backend
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `DATABASE_URL`: Database connection string

### Frontend
- Environment variables are built into the container during build time

## Monitoring and Maintenance

- Monitor pod health using:
```bash
kubectl get pods -n k8s-vulnerability-scanner
kubectl logs -f deployment/backend -n k8s-vulnerability-scanner
kubectl logs -f deployment/frontend -n k8s-vulnerability-scanner
```

- Scale the application:
```bash
kubectl scale deployment/backend --replicas=3 -n k8s-vulnerability-scanner
kubectl scale deployment/frontend --replicas=3 -n k8s-vulnerability-scanner
```

## Troubleshooting

1. **Pod Status Issues**
```bash
kubectl describe pod <pod-name> -n k8s-vulnerability-scanner
```

2. **Service Issues**
```bash
kubectl describe service backend-service -n k8s-vulnerability-scanner
kubectl describe service frontend-service -n k8s-vulnerability-scanner
```

3. **Ingress Issues**
```bash
kubectl describe ingress app-ingress -n k8s-vulnerability-scanner
```
