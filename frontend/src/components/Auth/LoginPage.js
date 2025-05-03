import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import DatabaseConfig from '../Config/DatabaseConfig';
import LoadingSpinner from '../Common/LoadingSpinner';

const LoginPage = () => {
  const [username, setUsername] = useState('chatbot_user');  // Updated default username
  const [password, setPassword] = useState('');  // Leave password empty for security
  const savedConfig = JSON.parse(localStorage.getItem('dbConfig') || '{}');
  const [dbType, setDbType] = useState(savedConfig.dbType || 'postgresql');
  const [dbName, setDbName] = useState(savedConfig.name || '');
  const [showDbFields, setShowDbFields] = useState(!savedConfig.dbType || !savedConfig.name);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showDbConfig, setShowDbConfig] = useState(true);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Pass dbName if dbType is postgresql
      await login(username, password, dbType === 'postgresql' ? dbName : undefined);
      navigate('/', { replace: true });
    } catch (error) {
      console.error('Login error:', error);
      setError(
        error.response?.data?.detail || 
        error.response?.data?.message ||
        'Failed to login. Please check your credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  // Update the handleConfigComplete function:
  const handleConfigComplete = (config) => {
    // Store database configuration
    localStorage.setItem('dbConfig', JSON.stringify(config));
    setShowDbConfig(false);
  };

  if (showDbConfig) {
    return <DatabaseConfig onConfigComplete={handleConfigComplete} />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Login to your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
              {error}
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            {showDbFields && (
              <>
                {/* Database Type Selector */}
                <div>
                  <label htmlFor="dbType" className="sr-only">Database Type</label>
                  <select
                    id="dbType"
                    name="dbType"
                    value={dbType}
                    onChange={e => setDbType(e.target.value)}
                    className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    disabled={loading}
                  >
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                  </select>
                </div>
                {/* Database Name Input (only for PostgreSQL) */}
                {dbType === 'postgresql' && (
                  <div>
                    <label htmlFor="dbName" className="sr-only">Database Name</label>
                    <input
                      id="dbName"
                      name="dbName"
                      type="text"
                      required
                      value={dbName}
                      onChange={e => setDbName(e.target.value)}
                      className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                      placeholder="Database Name"
                      disabled={loading}
                    />
                  </div>
                )}
              </>
            )}
            <div>
              <label htmlFor="username" className="sr-only">Username</label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Username"
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                disabled={loading}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
                loading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
              } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
