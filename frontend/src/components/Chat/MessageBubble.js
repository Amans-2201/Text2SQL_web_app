 // frontend/src/components/Chat/MessageBubble.js
import React from 'react';

const MessageBubble = ({ message }) => {
  const { sender, text } = message;
  const isUser = sender === 'user';

  return (
    <div className={`flex mb-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`py-2 px-4 rounded-lg max-w-lg lg:max-w-xl shadow ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-white text-gray-800 border border-gray-200'
        }`}
      >
        {/* Simple text display - could add markdown support later */}
         <div style={{ whiteSpace: 'pre-wrap' }}>{text}</div>
      </div>
    </div>
  );
};

export default MessageBubble;
