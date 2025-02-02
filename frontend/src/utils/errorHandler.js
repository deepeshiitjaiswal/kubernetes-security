export const handleApiError = (error) => {
  console.error('API Error:', error);

  // Network error
  if (!error.response) {
    return {
      message: 'Network error. Please check your internet connection.',
      type: 'network',
    };
  }

  // Server error response
  const { status, data } = error.response;

  // Authentication errors
  if (status === 401 || status === 403) {
    // Clear token if authentication fails
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return {
      message: data.message || 'Authentication failed. Please log in again.',
      type: 'auth',
    };
  }

  // Validation errors
  if (status === 400) {
    return {
      message: data.message || 'Invalid input. Please check your data.',
      type: 'validation',
    };
  }

  // Kubernetes errors
  if (data.message && data.message.includes('kube-config')) {
    return {
      message: 'Kubernetes configuration error. Please check your cluster setup.',
      type: 'kubernetes',
    };
  }

  // Generic server error
  if (status >= 500) {
    return {
      message: 'Server error. Please try again later.',
      type: 'server',
    };
  }

  // Default error
  return {
    message: data.message || 'An unexpected error occurred.',
    type: 'unknown',
  };
};

export const isAuthError = (error) => {
  return error.type === 'auth';
};
