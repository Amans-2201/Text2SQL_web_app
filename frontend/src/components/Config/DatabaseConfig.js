import React, { useState } from 'react';
import apiClient from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';

const DatabaseConfig = ({ onConfigComplete }) => {
  const [dbConfig, setDbConfig] = useState({
    dbType: 'mysql',
    host: 'localhost',
    port: '3306',
    name: '',
    user: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [databases, setDatabases] = useState([]);

  const dbTypes = [
    { value: 'mysql', label: 'MySQL', defaultPort: '3306' },
    { value: 'postgresql', label: 'PostgreSQL', defaultPort: '5432' }
  ];

  const handleDbTypeChange = (e) => {
    const selectedType = e.target.value;
    const defaultPort = dbTypes.find(type => type.value === selectedType)?.defaultPort;
    
    setDbConfig(prev => ({
      ...prev,
      dbType: selectedType,
      port: defaultPort
    }));
  };

  const handleInputChange = (e) => {
    setDbConfig(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  // Update the testConnection function
  const testConnection = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);
    
    try {
        const response = await apiClient.post('/config/test-connection', dbConfig);
        if (response.data.status === 'success') {
            setSuccess(true);
            setDatabases(response.data.databases || []);
        }
    } catch (err) {
        setError(err.response?.data?.detail || 'Failed to connect to database');
        setSuccess(false);
    } finally {
        setLoading(false);
    }
  };

  const handleDatabaseSelect = async (selectedDb) => {
    setDbConfig(prev => ({
        ...prev,
        name: selectedDb
    }));
  };

  const handleSaveConfig = async () => {
    setLoading(true);
    setError('');
    
    try {
        const response = await apiClient.post('/config/save', dbConfig);
        if (response.data.status === 'success') {
            setSuccess(true);
            // Force reload to reflect new database
            window.location.reload();
        }
    } catch (err) {
        setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
        setLoading(false);
    }
  };

  // Save configuration
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await apiClient.post('/config/save', dbConfig);
      onConfigComplete(dbConfig);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6">Database Configuration</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            Connection successful!
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700">Database Type</label>
          <select
            name="dbType"
            value={dbConfig.dbType}
            onChange={handleDbTypeChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            {dbTypes.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Host</label>
          <input
            type="text"
            name="host"
            value={dbConfig.host}
            onChange={handleInputChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Port</label>
          <input
            type="text"
            name="port"
            value={dbConfig.port}
            onChange={handleInputChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Username</label>
          <input
            type="text"
            name="user"
            value={dbConfig.user}
            onChange={handleInputChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Password</label>
          <input
            type="password"
            name="password"
            value={dbConfig.password}
            onChange={handleInputChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div className="flex gap-4">
          <button
            type="button"
            onClick={testConnection}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2"
          >
            {loading ? <LoadingSpinner size="w-4 h-4" /> : null}
            {loading ? 'Testing...' : 'Test Connection'}
          </button>
          
          <button
            type="submit"
            disabled={loading || !success}
            className={`px-4 py-2 text-white rounded ${
              success ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-400'
            }`}
          >
            Save Configuration
          </button>
        </div>

        {databases.length > 0 && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">
              Select Database
            </label>
            <select
              name="name"
              value={dbConfig.name}
              onChange={(e) => handleDatabaseSelect(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            >
              <option value="">Select a database</option>
              {databases.map(db => (
                <option key={db} value={db}>{db}</option>
              ))}
            </select>
          </div>
        )}
      </form>
    </div>
  );
};

export default DatabaseConfig;