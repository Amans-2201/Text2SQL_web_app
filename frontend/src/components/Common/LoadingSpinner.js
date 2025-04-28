// frontend/src/components/Common/LoadingSpinner.js
import React from 'react';

const LoadingSpinner = ({ size = 'w-8 h-8' }) => {
  return (
    <div className={`animate-spin rounded-full ${size} border-t-2 border-b-2 border-blue-500`}></div>
  );
};

export default LoadingSpinner; 
