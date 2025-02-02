from flask import jsonify
from kubernetes.client.rest import ApiException
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = 'error'
        return rv

def init_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(error):
        logger.error(f"API Error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(ApiException)
    def handle_kubernetes_error(error):
        logger.error(f"Kubernetes API Error: {error.reason}")
        response = jsonify({
            'status': 'error',
            'message': f'Kubernetes API Error: {error.reason}',
            'code': error.status
        })
        response.status_code = error.status
        return response

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        logger.error(f"Database Error: {str(error)}")
        response = jsonify({
            'status': 'error',
            'message': 'Database operation failed',
            'details': str(error)
        })
        response.status_code = 500
        return response

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        logger.error(f"HTTP Error: {error}")
        response = jsonify({
            'status': 'error',
            'message': error.description,
            'code': error.code
        })
        response.status_code = error.code
        return response

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        logger.error(f"Unexpected Error: {str(error)}")
        response = jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(error)
        })
        response.status_code = 500
        return response

class ValidationError(APIError):
    """Raised when input validation fails"""
    def __init__(self, message):
        super().__init__(message, status_code=400)

class AuthenticationError(APIError):
    """Raised when authentication fails"""
    def __init__(self, message):
        super().__init__(message, status_code=401)

class AuthorizationError(APIError):
    """Raised when authorization fails"""
    def __init__(self, message):
        super().__init__(message, status_code=403)

class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found"""
    def __init__(self, message):
        super().__init__(message, status_code=404)

class KubernetesError(APIError):
    """Raised when Kubernetes operations fail"""
    def __init__(self, message, original_error=None):
        super().__init__(message, status_code=500)
        if original_error:
            logger.error(f"Kubernetes Error Details: {str(original_error)}")
