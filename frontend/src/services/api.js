// frontend/src/services/api.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Function to get the token from localStorage
const getToken = () => localStorage.getItem('authToken');

// Add a request interceptor to include the token in headers
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// --- Authentication ---
export const loginUser = async (username, password) => {
  // Simplified login - just return success
  if (username && password) {
    return { access_token: 'dummy_token' };
  }
  throw new Error('Invalid credentials');
};

export const logoutUser = () => {
  localStorage.removeItem('authToken');
};

// --- Chat ---
export const askQuestion = async (question, signal) => {
  try {
    const response = await apiClient.post('/chat/ask', 
      { question },
      { signal }
    );
    return response.data;
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Request aborted');
      throw error;
    }
    console.error("Ask Question API error:", error);
    throw error;
  }
};

// Add this new function
export const createVisualization = async (data, columns, chartType) => {
  try {
    const response = await apiClient.post('/chat/visualize', {
      data,
      columns,
      chartType
    });
    return response.data;
  } catch (error) {
    console.error("Visualization API error:", error);
    throw error;
  }
};

// Add this function to the existing api.js file
export const getDatabaseInfo = async () => {
  try {
    const response = await apiClient.get('/chat/database-info');
    return response.data;
  } catch (error) {
    console.error("Database info fetch error:", error);
    throw error;
  }
};

export default apiClient;
