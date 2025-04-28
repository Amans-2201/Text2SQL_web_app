import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/Auth/LoginPage';
import ChatInterface from './components/Chat/ChatInterface';
import ErrorBoundary from './components/ErrorBoundary';
import './index.css';

function App() {
  const styles = {
    padding: '40px',
    fontSize: '24px',
    fontWeight: 'bold',
    color: 'blue',
    border: '2px solid red',
    height: '200px',
    width: '400px',
    margin: '50px'
  };

  function AppContent() {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
      return <div style={styles}>Loading...</div>;
    }

    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <ChatInterface />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    );
  }

  return (
    <Router>
      <AuthProvider>
        <ErrorBoundary>
          <AppContent />
        </ErrorBoundary>
      </AuthProvider>
    </Router>
  );
}

export default App;