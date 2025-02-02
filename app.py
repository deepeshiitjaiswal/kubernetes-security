from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from datetime import datetime, timedelta
import logging
from kubernetes_scanner import KubernetesScanner
from error_handler import KubernetesError
import os
import json
from models import db, User, ScanResult
from dotenv import load_dotenv
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')  # Change this in production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize extensions
jwt = JWTManager(app)
db.init_app(app)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Create database tables and default user
def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default test user if it doesn't exist
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(
                email='test@example.com',
                username='testuser'
            )
            test_user.set_password('Test@123')
            db.session.add(test_user)
            try:
                db.session.commit()
                logger.info("Created default test user")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating default user: {str(e)}")

# Initialize database
init_db()

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        logger.info(f"Login attempt with data: {data}")
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400
        
        user = User.query.filter_by(email=email).first()
        logger.info(f"Found user: {user is not None}")
        
        if not user or not user.check_password(password):
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401
        
        access_token = create_access_token(identity=user.id)
        logger.info(f"User logged in successfully: {email}")
        
        return jsonify({
            'status': 'success',
            'access_token': access_token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during login'
        }), 500

# Valid users for development
VALID_USERS = {
    'admin@example.com': 'admin123',
    'user@example.com': 'user123'
}

@app.route('/login', methods=['POST'])
def login_dev():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Check if user exists and password matches
        if email not in VALID_USERS or VALID_USERS[email] != password:
            return jsonify({'error': 'Invalid email or password'}), 401

        # Create access token
        access_token = create_access_token(identity=email)
        return jsonify({
            'access_token': access_token,
            'user': {
                'email': email,
                'name': email.split('@')[0]
            }
        })
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 401

@app.route('/api/verify-auth', methods=['GET'])
@jwt_required()
def verify_auth():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        return jsonify({
            'status': 'success',
            'user': user.to_dict()
        })
    except Exception as e:
        logger.error(f"Error verifying auth: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to verify authentication'
        }), 500

@app.route('/verify-auth', methods=['GET'])
@jwt_required()
def verify_auth_dev():
    try:
        current_user = get_jwt_identity()
        return jsonify({
            'user': {
                'email': current_user,
                'name': current_user.split('@')[0]
            }
        })
    except Exception as e:
        logger.error(f"Auth verification error: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 401

@app.route('/api/scan', methods=['POST'])
@jwt_required()
def start_scan():
    logger.info('Scan started')
    try:
        # Start scan in a separate thread
        def run_scan():
            scanner = KubernetesScanner()
            logger.info('Running scan...')
            scanner.scan_cluster()
            logger.info('Scan completed')

        thread = threading.Thread(target=run_scan)
        thread.start()

        return jsonify({
            'status': 'started',
            'message': 'Scan started successfully'
        }), 200
    except Exception as e:
        logger.error(f"Error starting scan: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/scan/status', methods=['GET'])
@jwt_required()
def get_scan_status():
    try:
        scanner = KubernetesScanner()
        status = scanner.get_scan_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/resources', methods=['GET'])
# Temporarily disable authentication for development
# @jwt_required()
def get_resources():
    try:
        scanner = KubernetesScanner()
        resources = scanner.get_resources()
        return jsonify(resources)
    except Exception as e:
        logger.error(f"Error in get_resources: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        
        if not email or not password or not username:
            return jsonify({
                'status': 'error',
                'message': 'Email, password and username are required'
            }), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            return jsonify({
                'status': 'error',
                'message': 'Email already exists'
            }), 400
        
        new_user = User(
            email=email,
            username=username
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"New user registered: {email}")
        return jsonify({
            'status': 'success',
            'message': 'User created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during registration'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'success',
        'message': 'Service is healthy'
    })

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
