// frontend/src/components/Chat/MessageBubble.js
import React from 'react';

const MessageBubble = ({ message }) => {
  const { sender, text } = message;
  const isUser = sender === 'user';

  return (
    <div 
      className={`flex mb-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`py-2 px-4 rounded-lg max-w-lg lg:max-w-xl shadow ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-white dark:bg-gray-700 text-gray-800 dark:text-white border border-gray-200 dark:border-gray-600'
        }`}
      >
        <div className="whitespace-pre-wrap">{text}</div>
      </div>
    </div>
  );
};

export default MessageBubble;
