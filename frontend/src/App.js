import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import ErrorBoundary from './components/ErrorBoundary';
import './index.css';

// Lazy load components
const ChatInterface = lazy(() => import('./components/Chat/ChatInterface'));
const LoginPage = lazy(() => import('./components/Auth/LoginPage'));

// Add loading fallback
const LoadingFallback = () => (
  <div className="flex h-screen items-center justify-center bg-gray-100">
    <div className="animate-spin h-12 w-12 border-4 border-blue-500 rounded-full border-t-transparent"></div>
  </div>
);

// Create a separate component that uses useAuth
function ProtectedRoutes() {
  const { isAuthenticated } = useAuth();
  
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

  return (
    <Router>
      <AuthProvider>
        <ThemeProvider>
          <ErrorBoundary>
            <Suspense fallback={<LoadingFallback />}>
              <ProtectedRoutes />
            </Suspense>
          </ErrorBoundary>
        </ThemeProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;