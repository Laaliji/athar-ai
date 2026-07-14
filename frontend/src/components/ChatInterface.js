import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, User, Sparkles, Square, RotateCcw, ChevronDown } from 'lucide-react';
import { apiService, streamQuery } from '../services/api';

// Simple markdown-like renderer for bold and line breaks
const renderMarkdown = (text) => {
  if (!text) return null;
  const parts = text.split(/(\*\*[^*]+\*\*|\n)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part === '\n') return <br key={i} />;
    return part;
  });
};

const SourceBadge = ({ source, index }) => (
  <a
    href={source.url || '#'}
    target="_blank"
    rel="noopener noreferrer"
    className="source-badge"
    title={source.excerpt}
  >
    <span className="source-badge-num">{index + 1}</span>
    <span className="source-badge-title">{source.title}</span>
    {source.score > 0 && (
      <span className="source-badge-score">{Math.round(source.score * 100)}%</span>
    )}
  </a>
);

const TypingCursor = () => <span className="typing-cursor" aria-hidden="true" />;

const MetaBadge = ({ label, value }) => (
  <span className="meta-badge">
    <span className="meta-badge-label">{label}</span>
    <span className="meta-badge-value">{value}</span>
  </span>
);

const ChatMessage = ({ message }) => {
  const isUser = message.role === 'user';
  const isStreaming = message.streaming;

  return (
    <div className={`message-row ${isUser ? 'message-row--user' : 'message-row--bot'} fade-in`}>
      {/* Avatar */}
      {!isUser && (
        <div className="message-avatar message-avatar--bot">
          <Sparkles size={14} />
        </div>
      )}

      <div className="message-container">
        {/* Bubble */}
        <div className={`message-bubble ${isUser ? 'message-bubble--user' : 'message-bubble--bot'}`}>
          <div className="message-text">
            {renderMarkdown(message.content)}
            {isStreaming && <TypingCursor />}
          </div>

          {/* Sources */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="message-sources">
              <p className="sources-label">Sources</p>
              <div className="sources-list">
                {message.sources.map((src, i) => (
                  <SourceBadge key={i} source={src} index={i} />
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          {!isUser && message.metadata && !isStreaming && (
            <div className="message-meta">
              {message.metadata.total_ms && (
                <MetaBadge label="⏱" value={`${Math.round(message.metadata.total_ms)}ms`} />
              )}
              {message.metadata.chunks_used && (
                <MetaBadge label="📄" value={`${message.metadata.chunks_used} chunks`} />
              )}
              {message.metadata.confidence !== undefined && (
                <MetaBadge label="✓" value={`${Math.round(message.metadata.confidence * 100)}% conf`} />
              )}
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <div className="message-avatar message-avatar--user">
          <User size={14} />
        </div>
      )}
    </div>
  );
};

const WelcomeScreen = ({ questions, onSelect }) => (
  <div className="welcome-screen">
    <div className="welcome-icon">
      <Sparkles size={32} />
    </div>
    <h2 className="welcome-title">Athar AI</h2>
    <p className="welcome-subtitle">
      As-salamu alaykum! Explore 14 centuries of Islamic civilization — history,
      architecture, science, art, and more.
    </p>
    <div className="welcome-chips">
      {questions.slice(0, 6).map((q, i) => (
        <button key={i} className="chip" onClick={() => onSelect(q)}>
          {q}
        </button>
      ))}
    </div>
  </div>
);

const ScrollToBottomButton = ({ onClick }) => (
  <button className="scroll-btn" onClick={onClick} aria-label="Scroll to bottom">
    <ChevronDown size={18} />
  </button>
);

// ── Main Component ─────────────────────────────────────────────────────────────

const ChatInterface = ({ conversationId, onConversationUpdate }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sampleQuestions, setSampleQuestions] = useState([]);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [currentAbort, setCurrentAbort] = useState(null);

  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const textareaRef = useRef(null);

  // Load sample questions
  useEffect(() => {
    apiService.getSampleQuestions()
      .then(data => setSampleQuestions(data.questions || []))
      .catch(console.error);
  }, []);

  // Auto-scroll
  const scrollToBottom = useCallback((smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
  }, []);

  useEffect(() => {
    if (messages.length > 0) scrollToBottom();
  }, [messages, scrollToBottom]);

  // Show scroll-to-bottom button when not at bottom
  const handleScroll = () => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    setShowScrollBtn(!atBottom);
  };

  // Auto-resize textarea
  const handleInputChange = (e) => {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
    }
  };

  const stopGeneration = () => {
    currentAbort?.();
    setCurrentAbort(null);
    setIsLoading(false);
    // Mark last message as no longer streaming
    setMessages(prev =>
      prev.map((m, i) => i === prev.length - 1 ? { ...m, streaming: false } : m)
    );
  };

  const handleSend = async (question = input) => {
    if (!question.trim() || isLoading) return;
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    const userMsg = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: question.trim(),
    };

    // Placeholder bot message that we'll fill via streaming
    const botMsgId = `a-${Date.now()}`;
    const botMsgPlaceholder = {
      id: botMsgId,
      role: 'assistant',
      content: '',
      streaming: true,
      sources: [],
      metadata: null,
    };

    setMessages(prev => [...prev, userMsg, botMsgPlaceholder]);
    setIsLoading(true);

    const abort = streamQuery(question, conversationId, {
      onSources: (sources) => {
        setMessages(prev =>
          prev.map(m => m.id === botMsgId ? { ...m, sources } : m)
        );
      },
      onToken: (token) => {
        setMessages(prev =>
          prev.map(m => m.id === botMsgId ? { ...m, content: m.content + token } : m)
        );
      },
      onDone: (metadata, convId) => {
        setMessages(prev =>
          prev.map(m => m.id === botMsgId ? { ...m, streaming: false, metadata } : m)
        );
        setIsLoading(false);
        setCurrentAbort(null);
        // Notify parent about conversation update for sidebar
        onConversationUpdate?.(convId, question);
      },
      onError: (err) => {
        setMessages(prev =>
          prev.map(m => m.id === botMsgId ? {
            ...m,
            content: `⚠️ Error: ${err}`,
            streaming: false,
            isError: true,
          } : m)
        );
        setIsLoading(false);
        setCurrentAbort(null);
      },
    });

    setCurrentAbort(() => abort);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = () => {
    if (isLoading) stopGeneration();
    setMessages([]);
  };

  return (
    <div className="chat-wrapper">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="chat-header-icon">
            <Sparkles size={18} />
          </div>
          <div>
            <h1 className="chat-header-title gradient-text">Athar AI</h1>
            <p className="chat-header-subtitle">Islamic Heritage Explorer</p>
          </div>
        </div>
        <div className="chat-header-actions">
          <button
            className="icon-btn"
            onClick={handleReset}
            title="New conversation"
            aria-label="New conversation"
          >
            <RotateCcw size={16} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div
        className="messages-area"
        ref={scrollContainerRef}
        onScroll={handleScroll}
      >
        {messages.length === 0 ? (
          <WelcomeScreen
            questions={sampleQuestions}
            onSelect={handleSend}
          />
        ) : (
          <div className="messages-list">
            {messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        {showScrollBtn && (
          <ScrollToBottomButton onClick={() => scrollToBottom(true)} />
        )}
      </div>

      {/* Input */}
      <div className="input-area">
        <div className="input-row">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Islamic history, art, science, architecture…"
            className="chat-input"
            rows={1}
            disabled={isLoading && !currentAbort}
            aria-label="Message input"
          />

          {isLoading ? (
            <button
              className="send-btn send-btn--stop"
              onClick={stopGeneration}
              aria-label="Stop generation"
            >
              <Square size={18} />
            </button>
          ) : (
            <button
              className="send-btn"
              onClick={() => handleSend()}
              disabled={!input.trim()}
              aria-label="Send message"
            >
              <Send size={18} />
            </button>
          )}
        </div>
        <p className="input-hint">
          Press <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;
