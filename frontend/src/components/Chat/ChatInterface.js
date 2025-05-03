import React, { useState, useEffect, useRef, useCallback } from 'react';
import ChatInput from './ChatInput';
import MessageList from './MessageList';
import ResultsDisplay from '../Results/ResultsDisplay';
import apiClient, { createVisualization } from '../../services/api';
import { useAuth } from '../../hooks/useAuth';
import './ChatInterface.css';
import DatabaseInfo from '../Sidebar/DatabaseInfo';
import ThemeToggle from '../Common/ThemeToggle';
import ErrorBoundary from '../../components/ErrorBoundary';
import { debounce } from 'lodash';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const { logout } = useAuth();
  const [abortController, setAbortController] = useState(null);
  const [isSuggestionsMinimized, setSuggestionsMinimized] = useState(false);
  const [refreshingSuggestions, setRefreshingSuggestions] = useState(false);

  // Load chat history from localStorage on component mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('chatHistory');
    const savedResult = localStorage.getItem('lastResult');
    
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages));
      } catch (e) {
        console.error("Error parsing saved messages:", e);
        setMessages([{ sender: 'bot', text: 'Hello! How can I help you with your data today?' }]);
      }
    } else {
      setMessages([{ sender: 'bot', text: 'Hello! How can I help you with your data today?' }]);
    }
    
    if (savedResult) {
      try {
        setCurrentResult(JSON.parse(savedResult));
      } catch (e) {
        console.error("Error parsing saved result:", e);
      }
    }
    
    fetchSuggestions();
  }, []);

  // Add debounced message update
  const debouncedMessageUpdate = debounce((messages) => {
    localStorage.setItem('chatHistory', JSON.stringify(messages));
  }, 1000);

  // Update useEffect for messages
  useEffect(() => {
    if (messages.length > 0) {
      debouncedMessageUpdate(messages);
    }
    return () => {
      debouncedMessageUpdate.cancel();
    };
  }, [messages]);

  // Save last result to localStorage
  useEffect(() => {
    if (currentResult) {
      localStorage.setItem('lastResult', JSON.stringify(currentResult));
    }
  }, [currentResult]);

  // Fetch suggestions
  const fetchSuggestions = useCallback(async (forceRefresh = false) => {
    try {
      setRefreshingSuggestions(true);
      
      // Add timestamp and force parameter to prevent caching
      const timestamp = Date.now();
      const url = forceRefresh 
        ? `/chat/suggestions?t=${timestamp}&force=true` 
        : `/chat/suggestions?t=${timestamp}`;
      
      console.log("Fetching AI-generated suggestions...");
      const response = await apiClient.get(url);
      
      console.log("AI Suggestions response:", response.data);
      
      if (Array.isArray(response.data)) {
        setSuggestions(response.data);
      } else if (response.data && Array.isArray(response.data.suggestions)) {
        setSuggestions(response.data.suggestions);
      } else {
        console.warn("Unexpected suggestions format:", response.data);
        setSuggestions([]);
      }
    } catch (error) {
      console.error('Failed to fetch AI suggestions:', error);
      setSuggestions([]);
    } finally {
      setRefreshingSuggestions(false);
    }
  }, []);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const handleVisualizationRequest = async (text, signal) => {
    if (!currentResult?.data || !currentResult?.columns) {
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'No data available for visualization. Please run a query first.'
      }]);
      return;
    }

    // Extract chart type from user message
    const chartTypes = {
      bar: text.toLowerCase().includes('bar'),
      pie: text.toLowerCase().includes('pie'),
      line: text.toLowerCase().includes('line'),
      scatter: text.toLowerCase().includes('scatter')
    };

    // Preprocess data for visualization
    const processedData = preprocessDataForVisualization(currentResult.data, currentResult.columns);

    const requestedType = Object.entries(chartTypes)
                               .find(([_, exists]) => exists)?.[0] || 'bar';

    try {
      console.log('Creating visualization of type:', requestedType);
      const response = await createVisualization(
        processedData,
        currentResult.columns,
        requestedType
      );

      if (response.visualization) {
        // Update current result with processed data and visualization config
        setCurrentResult(prev => ({
          ...prev,
          data: processedData,
          visualization: {
            ...response.visualization,
            processedData: processedData
          }
        }));

        setMessages(prev => [...prev, {
          sender: 'bot',
          text: `I've created a ${requestedType} chart for your data. ${response.visualization.description || ''}`
        }]);
      } else {
        throw new Error('No visualization data received');
      }
    } catch (error) {
      console.error('Visualization error:', error);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: `Sorry, I couldn't create the visualization: ${error.message}`
      }]);
    }
  };

  // Add this helper function to process data for visualization
  const preprocessDataForVisualization = (data, columns) => {
    if (!data || !columns) return [];

    // Convert string numbers to actual numbers
    return data.map(row => {
        const processedRow = { ...row };
        columns.forEach(col => {
            const value = row[col];
            if (typeof value === 'string') {
                // Try to convert string numbers
                const numberValue = Number(value.replace(/[^0-9.-]+/g, ''));
                if (!isNaN(numberValue)) {
                    processedRow[col] = numberValue;
                }
            }
            // Handle null/undefined values
            if (value === null || value === undefined) {
                processedRow[col] = 0;
            }
        });
        return processedRow;
    });
  };

  const handleSendMessage = async (text) => {
    setMessages(prev => [...prev, { sender: 'user', text }]);
    setLoading(true);

    const controller = new AbortController();
    setAbortController(controller);

    try {
      // Check if it's a visualization request with more specific conditions
      const isVisualizationRequest = 
        text.toLowerCase().match(/plot|create.*chart|show.*chart|make.*chart|draw.*graph|visualize|generate.*chart/);

      if (isVisualizationRequest) {
        console.log('Handling visualization request:', text);
        await handleVisualizationRequest(text, controller.signal);
        setLoading(false);
        return;
      }

      // Regular query handling
      const response = await apiClient.post('/chat/ask', 
        { question: text },
        { signal: controller.signal }
      );
      
      let botMessage = response.data.error 
        ? `Error: ${response.data.error}`
        : response.data.summary || 'Here are the results:';

      setMessages(prev => [...prev, { sender: 'bot', text: botMessage }]);
      setCurrentResult(response.data);
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request cancelled');
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: 'Query cancelled by user.'
        }]);
      } else {
        console.error('Failed to send message:', error);
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: `Error: ${error.response?.data?.detail || error.message || 'Something went wrong'}`
        }]);
      }
    } finally {
      setLoading(false);
      setAbortController(null);
    }
  };

  const clearHistory = () => {
    localStorage.removeItem('chatHistory');
    localStorage.removeItem('lastResult');
    setMessages([{ sender: 'bot', text: 'Hello! How can I help you with your data today?' }]);
    setCurrentResult(null);
  };

  const handleCancel = () => {
    if (abortController) {
      abortController.abort();
      setLoading(false);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'Query cancelled by user.'
      }]);
    }
  };

  // Add suggestion click handler
  const handleSuggestionClick = (suggestion) => {
    handleSendMessage(suggestion);
  };

  // Add this handler
  const toggleSuggestions = () => {
    setSuggestionsMinimized(!isSuggestionsMinimized);
  };

  // Update refresh button to force a refresh
  const handleRefreshSuggestions = () => {
    fetchSuggestions(true); // Pass true to force refresh
  };

  return (
    <div className="flex h-screen">
      <ErrorBoundary>
        <DatabaseInfo />
      </ErrorBoundary>
      <div className="flex-grow flex flex-col dark:bg-gray-900">
        <header className="chat-header">
          <h1 className="chat-title">Data Chatbot</h1>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <button 
              onClick={clearHistory}
              className="px-3 py-1 bg-gray-500 hover:bg-gray-700 text-white rounded text-sm"
            >
              Clear History
            </button>
            <button 
              onClick={logout}
              className="px-3 py-1 bg-red-500 hover:bg-red-700 text-white rounded text-sm"
            >
              Logout
            </button>
          </div>
        </header>

        <div className={`suggestions-wrapper ${isSuggestionsMinimized ? 'collapsed' : ''}`}>
          <div className="suggestions-header">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Suggested Questions
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRefreshSuggestions}
                className="refresh-button"
                title="Generate new AI suggestions"
                disabled={refreshingSuggestions}
              >
                <svg
                  className={`w-4 h-4 text-gray-500 hover:text-blue-500 ${refreshingSuggestions ? 'animate-spin' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </button>
              <button
                onClick={toggleSuggestions}
                className="minimize-button"
                title={isSuggestionsMinimized ? "Expand" : "Minimize"}
              >
                <svg
                  className={`w-4 h-4 transform transition-transform ${
                    isSuggestionsMinimized ? '-rotate-90' : 'rotate-0'
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>
            </div>
          </div>
          <div className="suggestions-container" style={{ display: isSuggestionsMinimized ? 'none' : 'flex' }}>
            {refreshingSuggestions ? (
              <div className="flex justify-center items-center w-full py-2">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 rounded-full border-t-transparent"></div>
                <span className="ml-2 text-sm text-gray-500">Generating AI questions...</span>
              </div>
            ) : suggestions.length > 0 ? (
              <>
                <div className="w-full mb-2 px-1">
                  <span className="text-xs text-blue-500 italic">AI-generated based on your database schema</span>
                </div>
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="suggestion-chip"
                  >
                    {suggestion}
                  </button>
                ))}
              </>
            ) : (
              <span className="text-sm text-gray-500 italic">No AI suggestions available</span>
            )}
          </div>
        </div>

        <div className="flex-grow overflow-y-auto dark:bg-gray-800">
          <MessageList messages={messages} />
          {currentResult && <ResultsDisplay result={currentResult} isLoading={loading} />}
        </div>

        <ChatInput 
          onSendMessage={handleSendMessage} 
          isLoading={loading} 
          onCancel={handleCancel}
        />
      </div>
    </div>
  );
};

export default ChatInterface;