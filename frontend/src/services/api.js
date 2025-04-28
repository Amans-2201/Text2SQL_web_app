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
  // FastAPI's OAuth2PasswordRequestForm expects form data
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await apiClient.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  
  if (response.data.access_token) {
    localStorage.setItem('authToken', response.data.access_token);
  }
  return response.data;
};

export const logoutUser = () => {
    localStorage.removeItem('authToken');
    // Optionally: Call a backend logout endpoint if it exists
}

// --- Chat ---
export const askQuestion = async (question) => {
  try {
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await apiClient.post('/chat/ask', 
      { question },
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error("Ask Question API error:", error);
    if (error.response?.status === 401) {
      window.location.href = '/login';
    }
    throw error;
  }
};

export default apiClient;
