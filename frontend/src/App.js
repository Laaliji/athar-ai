import React, { useState, useEffect, useCallback } from 'react';
import { Toaster } from 'react-hot-toast';
import { v4 as uuidv4 } from 'uuid';
import ConversationSidebar from './components/ConversationSidebar';
import ChatInterface from './components/ChatInterface';
import AdminDashboard from './components/AdminDashboard';
import LoadingScreen from './components/LoadingScreen';
import { apiService } from './services/api';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [showAdmin, setShowAdmin] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        await apiService.getSystemStatus();
      } catch {
        // Backend may not be up yet — that's fine, the UI still works
      } finally {
        setTimeout(() => setIsLoading(false), 1400);
      }
    };
    init();
  }, []);

  const handleNewChat = useCallback(() => {
    const newId = uuidv4();
    setConversations(prev => [{
      id: newId,
      title: 'New Conversation',
      preview: '',
      createdAt: new Date(),
    }, ...prev]);
    setActiveConvId(newId);
  }, []);

  // Start the first conversation once loading is done
  useEffect(() => {
    if (!isLoading && activeConvId === null) {
      handleNewChat();
    }
  }, [isLoading, activeConvId, handleNewChat]);

  const handleConversationUpdate = useCallback((convId, firstQuestion) => {
    setConversations(prev =>
      prev.map(c =>
        c.id === convId
          ? {
              ...c,
              title: firstQuestion.length > 42
                ? firstQuestion.slice(0, 42) + '…'
                : firstQuestion,
              preview: firstQuestion,
            }
          : c
      )
    );
  }, []);

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <ConversationSidebar
          conversations={conversations}
          activeConversation={activeConvId}
          onSelectConversation={id => setActiveConvId(id)}
          onNewChat={handleNewChat}
          onOpenAdmin={() => setShowAdmin(true)}
        />
      </aside>

      <main className="app-main">
        {activeConvId && (
          <ChatInterface
            key={activeConvId}
            conversationId={activeConvId}
            onConversationUpdate={handleConversationUpdate}
          />
        )}
      </main>

      {showAdmin && (
        <AdminDashboard onClose={() => setShowAdmin(false)} />
      )}

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            fontSize: '14px',
          },
        }}
      />
    </div>
  );
}

export default App;
