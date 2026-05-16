// src/components/LoadingSpinner.jsx
import React from 'react';
import { CircularProgress } from '@mui/material';

const LoadingSpinner = ({ size = 20 }) => (
  <CircularProgress size={size} thickness={4} sx={{ color: '#7c5cfc' }} />
);

export default LoadingSpinner;
