 // frontend/src/components/Chat/ChatInput.js
import React, { useState } from 'react';

const ChatInput = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleInputChange = (e) => {
    setMessage(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage(''); // Clear input after sending
    }
  };

   const handleKeyDown = (e) => {
    // Submit on Enter, allow Shift+Enter for newline
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
    }
};


  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-gray-300 bg-gray-50">
      <div className="flex items-center space-x-2">
        <textarea
          value={message}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your data..."
          rows="2" // Start with 2 rows, expands automatically if needed
          className="flex-grow p-2 border border-gray-300 rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-200"
          disabled={isLoading}
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed"
          disabled={isLoading || !message.trim()}
        >
          {isLoading ? 'Asking...' : 'Send'}
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
