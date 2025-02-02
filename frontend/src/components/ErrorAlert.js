import React from 'react';
import { Alert, Collapse, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

const ErrorAlert = ({ error, onClose }) => {
  if (!error) return null;

  return (
    <Collapse in={!!error}>
      <Alert
        severity="error"
        action={
          <IconButton
            aria-label="close"
            color="inherit"
            size="small"
            onClick={onClose}
          >
            <CloseIcon fontSize="inherit" />
          </IconButton>
        }
        sx={{ mb: 2 }}
      >
        {error.message}
        {error.details && (
          <div style={{ fontSize: '0.8em', marginTop: '8px' }}>
            Details: {error.details}
          </div>
        )}
      </Alert>
    </Collapse>
  );
};

export default ErrorAlert;
