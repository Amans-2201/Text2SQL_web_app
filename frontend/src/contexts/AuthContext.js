// frontend/src/contexts/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken') || null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setAuthToken(storedToken);
    }
    setIsLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await apiClient.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      const token = response.data.access_token;
      if (token) {
        localStorage.setItem('authToken', token);
        setAuthToken(token);
        // Set the token for all future requests
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        navigate('/');
      } else {
        throw new Error('No token received');
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    setAuthToken(null);
    localStorage.removeItem('authToken');
    delete apiClient.defaults.headers.common['Authorization'];
    navigate('/login');
  };

  const isAuthenticated = !!authToken;

  const contextValue = {
    authToken,
    isAuthenticated,
    isLoading,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {!isLoading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};

export { AuthContext };
