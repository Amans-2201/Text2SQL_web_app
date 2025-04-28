// frontend/src/components/Auth/LoginPage.js
import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import LoadingSpinner from '../Common/LoadingSpinner';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, loginError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Use the loginUser function from api.js instead of direct login
      await login(username, password);
      // No need to redirect here as AuthContext handles it
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="px-8 py-6 mt-4 text-left bg-white shadow-lg rounded-lg">
        <h3 className="text-2xl font-bold text-center">Login to your account</h3>
        <form onSubmit={handleSubmit}>
          <div className="mt-4">
            <div>
              <label className="block" htmlFor="username">Username</label>
              <input
                type="text"
                placeholder="Username"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                required
              />
            </div>
            <div className="mt-4">
              <label className="block" htmlFor="password">Password</label>
              <input
                type="password"
                placeholder="Password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                required
              />
            </div>
            {loginError && (
                <div className="mt-4 text-xs text-red-600">{loginError}</div>
            )}
            <div className="flex items-baseline justify-between">
              <button
                type="submit"
                className="w-full px-6 py-2 mt-4 text-white bg-blue-600 rounded-lg hover:bg-blue-900 flex items-center justify-center"
                disabled={isLoading}
              >
                 {isLoading ? <LoadingSpinner size="w-5 h-5" /> : 'Login'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
