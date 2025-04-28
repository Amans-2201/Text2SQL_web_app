// frontend/src/hooks/useAuth.js
import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext'; // Import AuthContext

export const useAuth = () => {
  return useContext(AuthContext);
};