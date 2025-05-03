import React, { useState } from 'react';
import apiClient from '../../services/apiClient';

const [isRefreshing, setIsRefreshing] = useState(false);

const refreshSuggestions = async () => {
  setIsRefreshing(true);
  try {
    // Add timestamp to prevent caching
    const timestamp = Date.now();
    const response = await apiClient.get(`/chat/suggestions?t=${timestamp}`);
    if (response.data && Array.isArray(response.data)) {
      setSuggestions(response.data);
    }
  } catch (error) {
    console.error('Failed to refresh suggestions:', error);
  } finally {
    setIsRefreshing(false);
  }
};

<div className="flex justify-between items-center mb-4">
  <h3 className="text-lg font-medium">Suggested Questions</h3>
  <button 
    onClick={refreshSuggestions}
    disabled={isRefreshing}
    className="text-xs text-blue-400 hover:text-blue-300 flex items-center"
  >
    {isRefreshing ? (
      <span className="inline-block animate-spin mr-1">⟳</span>
    ) : (
      <span>⟳</span>
    )}
    <span className="ml-1">Refresh</span>
  </button>
</div>
