# Cloud Deployment Instructions

This guide explains how to deploy the Kubernetes Vulnerability Scanner to any cloud provider (EKS, AKS, GKE).

## Prerequisites

1. Docker installed
2. kubectl configured with your cluster
3. Container registry access (ECR, ACR, or GCR)
4. Helm (for installing dependencies)
5. Domain name for the application

## Step 1: Prepare the Environment

1. Install NGINX Ingress Controller:
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx
```

2. Install cert-manager for SSL:
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true
```

## Step 2: Build and Push Docker Images

1. Set your registry URL:
```bash
export REGISTRY=your-registry-url  # e.g., 123456789.dkr.ecr.region.amazonaws.com
```

2. Build and push backend:
```bash
docker build -t $REGISTRY/vuln-scanner-backend:latest -f backend.Dockerfile .
docker push $REGISTRY/vuln-scanner-backend:latest
```

3. Build and push frontend:
```bash
docker build -t $REGISTRY/vuln-scanner-frontend:latest -f frontend.Dockerfile .
docker push $REGISTRY/vuln-scanner-frontend:latest
```

## Step 3: Configure Secrets

1. Generate a JWT secret:
```bash
JWT_SECRET=$(openssl rand -base64 32)
```

2. Create base64 encoded secret:
```bash
echo -n "$JWT_SECRET" | base64
```

3. Update k8s-cloud/secrets.yaml with the base64 encoded secret

## Step 4: Update Configuration

1. Update the domain in ingress.yaml:
   - Replace scanner.example.com with your actual domain

2. Update image registry in deployment files:
   - Replace ${REGISTRY} with your actual registry URL in both deployment files

## Step 5: Deploy the Application

1. Create namespace:
```bash
kubectl apply -f k8s-cloud/namespace.yaml
```

2. Apply secrets:
```bash
kubectl apply -f k8s-cloud/secrets.yaml
```

3. Deploy backend:
```bash
kubectl apply -f k8s-cloud/backend-deployment.yaml
```

4. Deploy frontend:
```bash
kubectl apply -f k8s-cloud/frontend-deployment.yaml
```

5. Deploy ingress:
```bash
kubectl apply -f k8s-cloud/ingress.yaml
```

## Step 6: Verify Deployment

1. Check all resources:
```bash
kubectl get all -n vuln-scanner
```

2. Check ingress status:
```bash
kubectl get ingress -n vuln-scanner
```

3. Wait for SSL certificate:
```bash
kubectl get certificate -n vuln-scanner
```

## Cloud-Specific Instructions

### AWS EKS

1. Create ECR repositories:
```bash
aws ecr create-repository --repository-name vuln-scanner-frontend
aws ecr create-repository --repository-name vuln-scanner-backend
```

2. Login to ECR:
```bash
aws ecr get-login-password --region region | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
```

### Azure AKS

1. Create ACR repositories:
```bash
az acr repository create --name YourRegistryName --repository vuln-scanner-frontend
az acr repository create --name YourRegistryName --repository vuln-scanner-backend
```

2. Login to ACR:
```bash
az acr login --name YourRegistryName
```

## Monitoring and Maintenance

1. View logs:
```bash
kubectl logs -f deployment/vuln-scanner-backend -n vuln-scanner
kubectl logs -f deployment/vuln-scanner-frontend -n vuln-scanner
```

2. Scale deployments:
```bash
kubectl scale deployment/vuln-scanner-backend -n vuln-scanner --replicas=3
kubectl scale deployment/vuln-scanner-frontend -n vuln-scanner --replicas=3
```

## Security Considerations

1. Always use HTTPS in production
2. Regularly update the JWT secret
3. Implement proper network policies
4. Use resource quotas and limits
5. Regular security audits
6. Enable audit logging

## Troubleshooting

1. Check pod status:
```bash
kubectl get pods -n vuln-scanner
kubectl describe pod <pod-name> -n vuln-scanner
```

2. Check service status:
```bash
kubectl get svc -n vuln-scanner
kubectl describe svc <service-name> -n vuln-scanner
```

3. Check ingress status:
```bash
kubectl describe ingress vuln-scanner-ingress -n vuln-scanner
```

4. View container logs:
```bash
kubectl logs <pod-name> -n vuln-scanner
```
