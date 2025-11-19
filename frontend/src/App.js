import React, { useState, useEffect } from "react";
import { Toaster } from "react-hot-toast";
import ConversationSidebar from "./components/ConversationSidebar";
import DarkChatInterface from "./components/DarkChatInterface";
import LearnMorePanel from "./components/LearnMorePanel";
import LoadingScreen from "./components/LoadingScreen";
import { apiService } from "./services/api";

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState(null);
  const [activeConversation, setActiveConversation] = useState(1);
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    // Initialize app and check system status
    const initializeApp = async () => {
      try {
        const status = await apiService.getSystemStatus();
        setSystemStatus(status);
      } catch (error) {
        console.error("Failed to get system status:", error);
        setSystemStatus({
          status: "error",
          model_loaded: false,
          database_ready: false,
        });
      } finally {
        // Minimum loading time for smooth UX
        setTimeout(() => setIsLoading(false), 2000);
      }
    };

    initializeApp();
  }, []);

  const handleNewChat = () => {
    const newId = conversations.length + 1;
    setConversations([
      {
        id: newId,
        title: 'New Conversation',
        preview: 'Start a new conversation...',
        timestamp: 'Just now',
      },
      ...conversations,
    ]);
    setActiveConversation(newId);
  };

  const handleSelectConversation = (id) => {
    setActiveConversation(id);
  };

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Left Sidebar - Conversations */}
      <div className="w-64 flex-shrink-0 hidden lg:block">
        <ConversationSidebar
          conversations={conversations}
          activeConversation={activeConversation}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <DarkChatInterface />
      </div>

      {/* Right Panel - Learn More */}
      <div className="w-80 flex-shrink-0 hidden xl:block border-l" style={{ borderColor: 'var(--border-color)' }}>
        <LearnMorePanel />
      </div>

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
          },
          success: {
            iconTheme: {
              primary: 'var(--accent-primary)',
              secondary: 'white',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: 'white',
            },
          },
        }}
      />
    </div>
  );
}

export default App;
