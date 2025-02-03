from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from datetime import datetime, timedelta
import logging
import threading
from models import db, User, ScanResult
from kubernetes_scanner import KubernetesScanner
from cluster_monitor import ClusterMonitor
from error_handler import KubernetesError
from resource_monitor import ResourceMonitor
import os
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')  # Change this in production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize extensions
jwt = JWTManager(app)
db.init_app(app)

# Initialize components
scanner = KubernetesScanner()
cluster_monitor = ClusterMonitor()
resource_monitor = ResourceMonitor()

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
            test_user.set_password('test123')
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
        
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'status': 'success',
                'access_token': access_token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during login'
        }), 500

@app.route('/api/scan', methods=['POST'])
@jwt_required()
def start_scan():
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        # Initialize scanner if not exists
        if not hasattr(app, 'scanner'):
            app.scanner = KubernetesScanner()
            
        # Start scan in a new thread
        def run_scan():
            try:
                app.logger.info("Starting Kubernetes cluster scan...")
                scan_result = app.scanner.scan_cluster()
                
                if scan_result:
                    app.logger.info(f"Scan completed. Saving results...")
                    
                    # Save scan result to database
                    result = ScanResult(
                        user_id=current_user_id,
                        vulnerabilities=scan_result.get('vulnerabilities', {}),
                        pods=scan_result.get('pods', []),
                        cves=scan_result.get('cves', []),
                        scan_time=datetime.now()
                    )
                    
                    with app.app_context():
                        try:
                            db.session.add(result)
                            db.session.commit()
                            app.logger.info(f"Scan results saved to database for user {current_user_id}")
                        except Exception as db_error:
                            app.logger.error(f"Database error: {str(db_error)}")
                            db.session.rollback()
                            app.scanner._scan_status['error'] = f"Failed to save scan results: {str(db_error)}"
                            raise
                else:
                    app.logger.error("Scan completed but no results returned")
                    app.scanner._scan_status['error'] = "Scan completed but no results returned"
                    
            except Exception as e:
                error_msg = f"Scan failed: {str(e)}"
                app.logger.error(error_msg)
                app.scanner._scan_status.update({
                    'status': 'error',
                    'error': error_msg,
                    'message': 'Scan failed'
                })
                
        scan_thread = threading.Thread(target=run_scan)
        scan_thread.daemon = True
        scan_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Scan started successfully'
        })
        
    except Exception as e:
        app.logger.error(f"Failed to start scan: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/scan/status', methods=['GET'])
@jwt_required()
def get_scan_status():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        if not hasattr(app, 'scanner'):
            app.scanner = KubernetesScanner()
            
        status = app.scanner._scan_status
        app.logger.info(f"Current scan status: {status}")
        
        # Get the latest scan result
        latest_scan = ScanResult.query.filter_by(user_id=current_user_id).order_by(ScanResult.scan_time.desc()).first()
        
        response = {
            'status': status.get('status', 'unknown'),
            'progress': status.get('progress', 0),
            'message': status.get('message', ''),
            'error': status.get('error'),
            'last_scan': status.get('last_scan')
        }
        
        # Add latest scan data if available
        if latest_scan:
            response['latest_scan'] = {
                'vulnerabilities': latest_scan.vulnerabilities,
                'pods': latest_scan.pods,
                'cves': latest_scan.cves,
                'scan_time': latest_scan.scan_time.isoformat() if latest_scan.scan_time else None
            }
            
            # Calculate vulnerability statistics
            vuln_stats = {
                'total': sum(len(v) for v in latest_scan.vulnerabilities.values()),
                'by_severity': {
                    severity: len(cves) 
                    for severity, cves in latest_scan.vulnerabilities.items()
                }
            }
            response['vulnerability_stats'] = vuln_stats
            
            # Calculate pod statistics
            pod_stats = {
                'total': len(latest_scan.pods),
                'vulnerable': len([p for p in latest_scan.pods if p.get('vulnerabilities', [])]),
                'secure': len([p for p in latest_scan.pods if not p.get('vulnerabilities', [])])
            }
            response['pod_stats'] = pod_stats
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Failed to get scan status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/cluster/metrics', methods=['GET'])
@jwt_required()
def get_cluster_metrics():
    """Get real-time cluster metrics"""
    try:
        metrics = cluster_monitor.get_cluster_metrics()
        if metrics:
            return jsonify({
                'status': 'success',
                'data': metrics
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get cluster metrics'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/resources', methods=['GET'])
@jwt_required()
def get_resources():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
            
        scanner = KubernetesScanner()
        resources = scanner.get_resources()
        
        return jsonify({
            'status': 'success',
            'data': resources
        }), 200
    except Exception as e:
        logger.error(f"Error getting resources: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/resources/metrics', methods=['GET'])
@jwt_required()
def get_resource_metrics():
    """Get real-time resource metrics"""
    try:
        logger.info("Fetching resource metrics...")
        metrics = resource_monitor.get_metrics()
        if metrics:
            logger.info(f"Resource metrics fetched successfully: {metrics}")
            return jsonify({
                'status': 'success',
                'data': metrics
            }), 200
        else:
            logger.error("Failed to get resource metrics")
            return jsonify({
                'status': 'error',
                'message': 'Failed to get resource metrics'
            }), 500
    except Exception as e:
        logger.error(f"Error getting resource metrics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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

if __name__ == '__main__':
    # Enable CORS for all domains in production
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run app on all interfaces (0.0.0.0) for cloud access
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,  # Disable debug mode in production
        threaded=True  # Enable threading for better performance
    )
