// frontend/src/contexts/AuthContext.js
import React, { createContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/api';

// Create context
export const AuthContext = createContext(null);

// Custom hook for using auth context
export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Provider component
export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();
  
  // Add this useEffect to check for existing tokens when the app loads
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const login = async (username, password) => {
    try {
      // Simplified login
      if (username && password) {
        setIsAuthenticated(true);
        localStorage.setItem('authToken', 'dummy_token');
        navigate('/');
        return { success: true };
      }
      throw new Error('Please provide username and password');
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('authToken');
    navigate('/login');
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      login,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};
