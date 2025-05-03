 // frontend/src/components/Chat/ChatInterface.js
 import React, { useState, useEffect } from 'react';
 import ChatInput from './ChatInput';
 import MessageList from './MessageList';
 import ResultsDisplay from '../Results/ResultsDisplay';
 import { askQuestion } from '../../services/api';
 import { useAuth } from '../../hooks/useAuth'; // Import useAuth
 
 const ChatInterface = () => {
   const [messages, setMessages] = useState([]); // Stores { sender: 'user'/'bot', text: '...' }
   const [currentResult, setCurrentResult] = useState(null); // Stores the backend response { query?, data?, columns?, summary?, viz?, error? }
   const [isLoading, setIsLoading] = useState(false);
   const { logout } = useAuth(); // Get logout function
 
   // Optional: Add an initial welcome message from the bot
   useEffect(() => {
         setMessages([{ sender: 'bot', text: 'Hello! How can I help you with your data today?' }]);
     }, []);
 
 
   const handleSendMessage = async (userQuestion) => {
     // Add user message to chat
     const newUserMessage = { sender: 'user', text: userQuestion };
     setMessages(prevMessages => [...prevMessages, newUserMessage]);
 
     setIsLoading(true);
     setCurrentResult(null); // Clear previous results immediately
 
     try {
       const response = await askQuestion(userQuestion);
       setCurrentResult(response); // Store the full response object
 
       // Add bot's response message (either summary, data indicator, or error)
       let botResponseText = '';
       if (response.error) {
          botResponseText = `Sorry, I encountered an error: ${response.error}`;
       } else if (response.summary) {
          botResponseText = response.summary; // Use the summary as the main text response
       } else if (response.data && response.data.length > 0) {
          botResponseText = `Okay, I found ${response.data.length} results. See the table/chart below.`;
       } else if (response.query) {
          botResponseText = "The query ran successfully, but returned no data.";
       } else {
          botResponseText = "I received a response, but couldn't process it fully."; // Fallback
       }
 
       const newBotMessage = { sender: 'bot', text: botResponseText };
        setMessages(prevMessages => [...prevMessages, newBotMessage]);
 
 
     } catch (error) {
        // This catch block handles errors *during* the API call itself (e.g., network error)
        console.error("Failed to send message:", error);
        const errorMessage = { sender: 'bot', text: `Sorry, I couldn't reach the server. ${error.message || ''}` };
         setCurrentResult({ error: `Network or API call error: ${error.message || 'Unknown error'}` }); // Set error state
         setMessages(prevMessages => [...prevMessages, errorMessage]);
     } finally {
       setIsLoading(false);
     }
   };
 
   return (
      <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white shadow-xl rounded-lg overflow-hidden relative"> {/* Added relative positioning */}
          {/* Header with Logout */}
         <header className="p-4 bg-blue-600 text-white flex justify-between items-center">
             <h1 className="text-xl font-semibold">Data Chatbot</h1>
             <button
                 onClick={logout}
                 className="px-3 py-1 bg-red-500 hover:bg-red-700 rounded text-sm"
             >
                 Logout
             </button>
         </header>
 
         {/* Main Content Area (Chat History + Results) */}
         <div className="flex-grow overflow-y-auto"> {/* This container will scroll */}
             <MessageList messages={messages} />
             {/* Display Results or Loading Indicator within the scrollable area */}
              <ResultsDisplay result={currentResult} isLoading={isLoading && !currentResult} /> {/* Show loading within results area only when actively fetching */}
         </div>
 
          {/* Fixed Input Area at the Bottom */}
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
     </div>
 
   );
 };
 
 export default ChatInterface;