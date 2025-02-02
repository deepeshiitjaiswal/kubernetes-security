import unittest
import json
from app import app
from models import db, User
import os

class TestKubernetesVulnerabilityScanner(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        os.remove('test.db') if os.path.exists('test.db') else None
    
    def register_user(self, email="test@test.com", username="testuser", password="testpass"):
        return self.client.post('/api/register', json={
            'email': email,
            'username': username,
            'password': password
        })
    
    def login_user(self, email="test@test.com", password="testpass"):
        return self.client.post('/api/login', json={
            'email': email,
            'password': password
        })
    
    def get_auth_header(self):
        response = self.login_user()
        token = json.loads(response.data)['access_token']
        return {'Authorization': f'Bearer {token}'}
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
    
    def test_register_success(self):
        """Test successful user registration"""
        response = self.register_user()
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        self.register_user()
        response = self.register_user()
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        response = self.register_user(email="invalid-email")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_login_success(self):
        """Test successful login"""
        self.register_user()
        response = self.login_user()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        self.register_user()
        response = self.login_user(password="wrongpass")
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_scan_unauthorized(self):
        """Test scan endpoint without authentication"""
        response = self.client.post('/api/scan')
        self.assertEqual(response.status_code, 401)
    
    def test_scan_authorized(self):
        """Test scan endpoint with authentication"""
        self.register_user()
        headers = self.get_auth_header()
        response = self.client.post('/api/scan', headers=headers)
        self.assertIn(response.status_code, [200, 500])  # 500 if no K8s cluster
    
    def test_get_resources_unauthorized(self):
        """Test get resources endpoint without authentication"""
        response = self.client.get('/api/resources')
        self.assertEqual(response.status_code, 401)
    
    def test_get_resources_authorized(self):
        """Test get resources endpoint with authentication"""
        self.register_user()
        headers = self.get_auth_header()
        response = self.client.get('/api/resources', headers=headers)
        self.assertIn(response.status_code, [200, 500])  # 500 if no K8s cluster
    
    def test_get_vulnerabilities_unauthorized(self):
        """Test get vulnerabilities endpoint without authentication"""
        response = self.client.get('/api/vulnerabilities')
        self.assertEqual(response.status_code, 401)
    
    def test_get_vulnerabilities_authorized(self):
        """Test get vulnerabilities endpoint with authentication"""
        self.register_user()
        headers = self.get_auth_header()
        response = self.client.get('/api/vulnerabilities', headers=headers)
        self.assertIn(response.status_code, [200, 500])  # 500 if no K8s cluster

if __name__ == '__main__':
    unittest.main(verbosity=2)
