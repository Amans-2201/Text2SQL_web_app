 // frontend/src/components/Chat/MessageList.js
import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

const MessageList = ({ messages }) => {
  const messagesEndRef = useRef(null); // Ref to scroll to bottom

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(() => {
    scrollToBottom(); // Scroll down whenever messages change
  }, [messages]);


  return (
    <div className="flex-grow p-4 overflow-y-auto bg-gray-100">
      {messages.map((msg, index) => (
        <MessageBubble key={index} message={msg} />
      ))}
       {/* Dummy div to help scroll to bottom */}
       <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
