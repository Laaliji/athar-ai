import React, { useState, useRef, useEffect } from "react";
import {
  motion,
  AnimatePresence,
  useScroll,
  useTransform,
} from "framer-motion";
import { Send, Loader2, BookOpen, Clock, Sparkles, Zap } from "lucide-react";
import { toast } from "react-hot-toast";
import { apiService } from "../services/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { cn } from "../lib/utils";
import MessageBubble from "./MessageBubble";
import WelcomeScreen from "./WelcomeScreen";

const ChatInterface = ({ systemStatus }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sampleQuestions, setSampleQuestions] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Load sample questions
    const loadSampleQuestions = async () => {
      try {
        const response = await apiService.getSampleQuestions();
        setSampleQuestions(response.questions);
      } catch (error) {
        console.error("Failed to load sample questions:", error);
      }
    };

    loadSampleQuestions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await apiService.queryRAG(userMessage.content);

      const aiMessage = {
        id: Date.now() + 1,
        type: "ai",
        content: response.answer,
        sources: response.sources,
        processingTime: response.processing_time,
        modelUsed: response.model_used,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: "error",
        content:
          "Sorry, I encountered an error processing your question. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSampleQuestion = (question) => {
    setInputValue(question);
    inputRef.current?.focus();
  };

  const isSystemReady = systemStatus?.status === "ready";

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <WelcomeScreen
              sampleQuestions={sampleQuestions}
              onQuestionClick={handleSampleQuestion}
              systemStatus={systemStatus}
            />
          ) : (
            <div className="space-y-6">
              <AnimatePresence>
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
              </AnimatePresence>

              {/* Loading indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center space-x-3 text-slate-500"
                >
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
                  </div>
                  <div className="loading-dots">
                    <div style={{ "--i": 0 }}></div>
                    <div style={{ "--i": 1 }}></div>
                    <div style={{ "--i": 2 }}></div>
                  </div>
                  <span className="text-sm text-slate-600 dark:text-slate-300 transition-colors duration-300">
                    Searching through Islamic heritage...
                  </span>
                </motion.div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="border-t border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md p-4 transition-colors duration-300"
      >
        <div className="max-w-4xl mx-auto">
          {/* System Status Warning */}
          {!isSystemReady && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mb-4 p-3 bg-gold-50 dark:bg-gold-900/20 border border-gold-200 dark:border-gold-800 rounded-lg flex items-center space-x-2 transition-colors duration-300"
            >
              <Clock className="w-4 h-4 text-gold-600" />
              <span className="text-sm text-gold-700 dark:text-gold-300 transition-colors duration-300">
                System is initializing. Please wait a moment before asking
                questions.
              </span>
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="flex space-x-3">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask about Islamic history, architecture, or culture..."
                className="input-field pr-12"
                disabled={!isSystemReady || isLoading}
              />
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <BookOpen className="w-5 h-5 text-slate-400" />
              </div>
            </div>

            <motion.button
              type="submit"
              disabled={!inputValue.trim() || !isSystemReady || isLoading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">Ask</span>
            </motion.button>
          </form>

          {/* Quick Actions */}
          {messages.length === 0 && sampleQuestions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="mt-3 flex flex-wrap gap-2"
            >
              {sampleQuestions.slice(0, 3).map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSampleQuestion(question)}
                  className="text-xs px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full transition-colors duration-200"
                  disabled={!isSystemReady}
                >
                  {question.length > 40
                    ? question.substring(0, 40) + "..."
                    : question}
                </button>
              ))}
            </motion.div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default ChatInterface;
