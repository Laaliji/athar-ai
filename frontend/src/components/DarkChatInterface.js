import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, User, Sparkles } from 'lucide-react';
import { apiService } from '../services/api';

const DarkChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sampleQuestions, setSampleQuestions] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadSampleQuestions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSampleQuestions = async () => {
    try {
      const response = await apiService.getSampleQuestions();
      setSampleQuestions(response.questions || []);
    } catch (error) {
      console.error('Failed to load sample questions:', error);
    }
  };

  const handleSend = async (question = input) => {
    if (!question.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Add minimum delay for more natural feel (1.5 seconds)
      const startTime = Date.now();
      const response = await apiService.queryRAG(question);
      const elapsedTime = Date.now() - startTime;
      const minimumDelay = 1500; // 1.5 seconds
      
      if (elapsedTime < minimumDelay) {
        await new Promise(resolve => setTimeout(resolve, minimumDelay - elapsedTime));
      }
      
      const botMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again.',
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: 'var(--bg-chat)' }}>
      {/* Chat Header */}
      <div className="p-6 border-b" style={{ borderColor: 'var(--border-color)' }}>
        <h1 className="text-2xl font-bold gradient-text">Athar AI</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
          Explore the rich history and heritage of Islamic civilization
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                <Sparkles size={32} style={{ color: 'var(--accent-primary)' }} />
              </div>
              <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                Athar AI
              </h2>
              <p className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>
                As-salamu alaykum! I am here to help you explore the rich history and heritage of the Islamic world. How may I help you?
              </p>
            </div>

            {/* Suggestion Chips */}
            <div className="flex flex-wrap gap-3 justify-center max-w-2xl">
              {sampleQuestions.slice(0, 4).map((question, index) => (
                <button
                  key={index}
                  className="suggestion-chip"
                  onClick={() => handleSend(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} fade-in`}
              >
                <div className="flex gap-3 max-w-3xl">
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                      <Sparkles size={16} style={{ color: 'var(--accent-primary)' }} />
                    </div>
                  )}
                  <div className={message.role === 'user' ? 'message-user' : 'message-bot'}>
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--border-color)' }}>
                        <p className="text-xs font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>
                          Sources ({message.sources.length})
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {message.sources.map((source, idx) => (
                            <a
                              key={idx}
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs font-medium hover:underline"
                              style={{ color: 'var(--accent-light)' }}
                            >
                              {source.title}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--accent-primary)' }}>
                      <User size={16} color="white" />
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start fade-in">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                    <Sparkles size={16} style={{ color: 'var(--accent-primary)' }} />
                  </div>
                  <div className="message-bot">
                    <div className="flex items-center gap-2">
                      <Loader2 size={16} className="animate-spin" style={{ color: 'var(--accent-primary)' }} />
                      <span className="text-sm">Thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 border-t" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
        <div className="flex gap-3 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="input-field resize-none"
            rows="1"
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="btn-primary flex-shrink-0 px-4 py-3"
            style={{
              opacity: !input.trim() || isLoading ? 0.5 : 1,
              cursor: !input.trim() || isLoading ? 'not-allowed' : 'pointer',
            }}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default DarkChatInterface;
