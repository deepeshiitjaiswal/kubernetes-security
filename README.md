# Kubernetes Vulnerability Scanner

A modern web application for scanning and monitoring Kubernetes clusters for vulnerabilities. Features include:
- User authentication and authorization
- Real-time vulnerability scanning of Kubernetes pods and services
- Beautiful and responsive dashboard built with React and Material-UI
- Detailed vulnerability reports and analytics

## Features
- Scan Kubernetes pods and services for vulnerabilities
- User authentication system
- Beautiful dashboard with real-time updates
- Comprehensive vulnerability reporting
- Easy-to-use interface

## Tech Stack
- Backend: Python Flask
- Frontend: React.js with Material-UI
- Database: PostgreSQL
- Authentication: JWT
- Kubernetes: Official Python K8s client

## Setup Instructions

### Backend Setup
1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configurations
```

### Frontend Setup
1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm start
```

### Running the Application
1. Start the backend server:
```bash
python app.py
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

## Security Note
Make sure to properly configure your Kubernetes RBAC permissions and keep your credentials secure.
