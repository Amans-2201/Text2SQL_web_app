import React, { useState, useEffect } from 'react';
import ChatInput from './ChatInput';
import MessageList from './MessageList';
import ResultsDisplay from '../Results/ResultsDisplay';
import { askQuestion } from '../../services/api';
import { useAuth } from '../../hooks/useAuth';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [currentResult, setCurrentResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const { logout } = useAuth();

  useEffect(() => {
    setMessages([{ sender: 'bot', text: 'Hello! How can I help you with your data today?' }]);
  }, []);

  const handleSendMessage = async (userQuestion) => {
    const newUserMessage = { sender: 'user', text: userQuestion };
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    setIsLoading(true);
    setCurrentResult(null);

    try {
        const response = await askQuestion(userQuestion);
        setCurrentResult(response);

        let botResponseText;
        if (response.error) {
            botResponseText = `Sorry, I encountered an error: ${response.error}`;
        } else if (response.summary) {
            botResponseText = response.summary;
        } else if (response.data && response.data.length > 0) {
            botResponseText = `Found ${response.data.length} results.`;
        } else {
            botResponseText = "No data found for your query.";
        }

        const newBotMessage = { sender: 'bot', text: botResponseText };
        setMessages(prevMessages => [...prevMessages, newBotMessage]);
    } catch (error) {
        console.error("Failed to send message:", error);
        const errorMessage = { 
            sender: 'bot', 
            text: `Sorry, I couldn't process your request. ${error.message || ''}` 
        };
        setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white shadow-xl rounded-lg overflow-hidden relative">
      <header className="p-4 bg-blue-600 text-white flex justify-between items-center">
        <h1 className="text-xl font-semibold">Data Chatbot</h1>
        <button
          onClick={logout}
          className="px-3 py-1 bg-red-500 hover:bg-red-700 rounded text-sm"
        >
          Logout
        </button>
      </header>

      <div className="flex-grow overflow-y-auto">
        <MessageList messages={messages} />
        <ResultsDisplay result={currentResult} isLoading={isLoading && !currentResult} />
      </div>

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};

export default ChatInterface;