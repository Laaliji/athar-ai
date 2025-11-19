import React from 'react';
import { MessageSquare, Plus, Settings, History } from 'lucide-react';

const ConversationSidebar = ({ conversations = [], activeConversation, onSelectConversation, onNewChat }) => {
  // Default conversations if none provided
  const defaultConversations = [
    { id: 1, title: 'Golden Age of Islam', preview: 'Tell me about the Golden Age...', timestamp: '2 hours ago' },
    { id: 2, title: 'The story of Ibn Sina', preview: 'Who was Ibn Sina?', timestamp: '1 day ago' },
    { id: 3, title: 'Architecture of the Alhambra', preview: 'Explain the architecture...', timestamp: '2 days ago' },
  ];

  const displayConversations = conversations.length > 0 ? conversations : defaultConversations;

  return (
    <div className="sidebar flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: 'var(--border-color)' }}>
        <div className="flex items-center gap-3 mb-4">
          <MessageSquare size={24} style={{ color: 'var(--accent-primary)' }} />
          <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            Athar AI
          </h2>
        </div>
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Islamic Heritage Explorer
        </p>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-2">
        <div className="mb-2 px-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
            Recent Conversations
          </h3>
        </div>
        {displayConversations.map((conversation) => (
          <div
            key={conversation.id}
            className={`sidebar-item ${activeConversation === conversation.id ? 'active' : ''}`}
            onClick={() => onSelectConversation && onSelectConversation(conversation.id)}
          >
            <MessageSquare size={16} />
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm truncate">{conversation.title}</div>
              <div className="text-xs truncate" style={{ color: 'var(--text-tertiary)' }}>
                {conversation.preview}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t" style={{ borderColor: 'var(--border-color)' }}>
        <button className="sidebar-item w-full">
          <Settings size={18} />
          <span>Settings</span>
        </button>
      </div>
    </div>
  );
};

export default ConversationSidebar;
