import React, { useState } from 'react';
import { MessageSquare, Plus, Settings, Trash2, LayoutDashboard } from 'lucide-react';

const ConversationSidebar = ({
  conversations = [],
  activeConversation,
  onSelectConversation,
  onNewChat,
  onOpenAdmin,
}) => {
  const [hoveredId, setHoveredId] = useState(null);

  return (
    <div className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <span>أ</span>
        </div>
        <div>
          <h2 className="sidebar-logo-name">Athar AI</h2>
          <p className="sidebar-logo-tagline">Islamic Heritage</p>
        </div>
      </div>

      {/* New Chat */}
      <div className="sidebar-new-chat">
        <button className="btn-primary sidebar-new-btn" onClick={onNewChat}>
          <Plus size={16} />
          New Conversation
        </button>
      </div>

      {/* Conversations */}
      <div className="sidebar-conversations">
        {conversations.length > 0 && (
          <p className="sidebar-section-label">Recent</p>
        )}

        {conversations.length === 0 ? (
          <div className="sidebar-empty">
            <MessageSquare size={28} className="sidebar-empty-icon" />
            <p>No conversations yet.</p>
            <p>Ask your first question!</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`sidebar-item ${activeConversation === conv.id ? 'sidebar-item--active' : ''}`}
              onClick={() => onSelectConversation?.(conv.id)}
              onMouseEnter={() => setHoveredId(conv.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <MessageSquare size={14} className="sidebar-item-icon" />
              <div className="sidebar-item-content">
                <p className="sidebar-item-title">{conv.title}</p>
                {conv.preview && (
                  <p className="sidebar-item-preview">{conv.preview}</p>
                )}
              </div>
              {hoveredId === conv.id && (
                <button
                  className="sidebar-item-delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Parent handles delete
                  }}
                  aria-label="Delete conversation"
                >
                  <Trash2 size={12} />
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <button className="sidebar-footer-btn" onClick={onOpenAdmin}>
          <LayoutDashboard size={16} />
          <span>Admin Dashboard</span>
        </button>
        <button className="sidebar-footer-btn" onClick={() => {}}>
          <Settings size={16} />
          <span>Settings</span>
        </button>
      </div>
    </div>
  );
};

export default ConversationSidebar;
