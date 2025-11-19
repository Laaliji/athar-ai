import React, { useState, useRef, useEffect } from "react";
import {
  motion,
  AnimatePresence,
  useScroll,
  useTransform,
  useSpring,
  useMotionValue,
} from "framer-motion";
import {
  Send,
  Loader2,
  BookOpen,
  Clock,
  Sparkles,
  Zap,
  MessageCircle,
  Brain,
  Search,
} from "lucide-react";
import { toast } from "react-hot-toast";
import { apiService } from "../services/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Card, CardContent } from "./ui/card";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { Progress } from "./ui/progress";
import { cn } from "../lib/utils";
import EnhancedMessageBubble from "./EnhancedMessageBubble";
import EnhancedWelcomeScreen from "./EnhancedWelcomeScreen";

const EnhancedChatInterface = ({ systemStatus }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sampleQuestions, setSampleQuestions] = useState([]);
  const [typingProgress, setTypingProgress] = useState(0);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const containerRef = useRef(null);

  // Framer Motion values
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const { scrollY } = useScroll({ container: containerRef });
  const backgroundY = useTransform(scrollY, [0, 500], [0, -50]);
  const springConfig = { damping: 25, stiffness: 700 };
  const x = useSpring(mouseX, springConfig);
  const y = useSpring(mouseY, springConfig);

  useEffect(() => {
    loadSampleQuestions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadSampleQuestions = async () => {
    try {
      const response = await apiService.getSampleQuestions();
      setSampleQuestions(response.questions);
    } catch (error) {
      console.error("Failed to load sample questions:", error);
    }
  };

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
    setTypingProgress(0);

    // Simulate typing progress
    const progressInterval = setInterval(() => {
      setTypingProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 10;
      });
    }, 200);

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
      toast.success("Response generated successfully!");
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: "error",
        content:
          "Sorry, I encountered an error processing your question. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast.error("Failed to process your question");
    } finally {
      clearInterval(progressInterval);
      setIsLoading(false);
      setTypingProgress(0);
    }
  };

  const handleSampleQuestion = (question) => {
    setInputValue(question);
    inputRef.current?.focus();
  };

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    mouseX.set(e.clientX - rect.left);
    mouseY.set(e.clientY - rect.top);
  };

  const isSystemReady = systemStatus?.status === "ready";

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const messageVariants = {
    hidden: { opacity: 0, y: 50, scale: 0.8 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        damping: 20,
        stiffness: 300,
      },
    },
    exit: {
      opacity: 0,
      y: -50,
      scale: 0.8,
      transition: { duration: 0.2 },
    },
  };

  return (
    <div className="flex flex-col h-full relative overflow-hidden">
      {/* Animated Background */}
      <motion.div
        className="absolute inset-0 opacity-30"
        style={{ y: backgroundY }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-gold-50 to-emerald-50" />
        <div className="absolute inset-0 islamic-pattern" />
      </motion.div>

      {/* Chat Messages Area */}
      <motion.div
        ref={containerRef}
        className="flex-1 overflow-y-auto px-4 py-6 relative z-10"
        onMouseMove={handleMouseMove}
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <EnhancedWelcomeScreen
              sampleQuestions={sampleQuestions}
              onQuestionClick={handleSampleQuestion}
              systemStatus={systemStatus}
            />
          ) : (
            <motion.div className="space-y-6" layout>
              <AnimatePresence mode="popLayout">
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    variants={messageVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    layout
                  >
                    <EnhancedMessageBubble message={message} />
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Enhanced Loading Indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="flex flex-col space-y-3"
                >
                  <Card className="max-w-md bg-gradient-to-r from-slate-50 to-primary-50 border-primary-200">
                    <CardContent className="p-4">
                      <div className="flex items-center space-x-3 mb-3">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="bg-gradient-to-r from-primary-500 to-emerald-500 text-white">
                            <motion.div
                              animate={{ rotate: 360 }}
                              transition={{
                                duration: 2,
                                repeat: Infinity,
                                ease: "linear",
                              }}
                            >
                              <Brain className="w-4 h-4" />
                            </motion.div>
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <motion.div
                              animate={{ scale: [1, 1.2, 1] }}
                              transition={{ duration: 1.5, repeat: Infinity }}
                            >
                              <Search className="w-4 h-4 text-primary-600" />
                            </motion.div>
                            <span className="text-sm font-medium text-slate-700">
                              Searching Islamic heritage...
                            </span>
                          </div>
                          <Progress value={typingProgress} className="h-2" />
                        </div>
                      </div>

                      <div className="flex space-x-1">
                        {[0, 1, 2].map((i) => (
                          <motion.div
                            key={i}
                            className="w-2 h-2 bg-primary-500 rounded-full"
                            animate={{
                              scale: [1, 1.5, 1],
                              opacity: [0.5, 1, 0.5],
                            }}
                            transition={{
                              duration: 1.5,
                              repeat: Infinity,
                              delay: i * 0.2,
                            }}
                          />
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )}
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </motion.div>

      {/* Enhanced Input Area */}
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3, type: "spring", damping: 25, stiffness: 200 }}
        className="relative z-20"
      >
        {/* Glassmorphism background */}
        <div className="absolute inset-0 bg-white/80 backdrop-blur-xl border-t border-white/20" />

        <div className="relative p-6">
          <div className="max-w-4xl mx-auto">
            {/* System Status */}
            {!isSystemReady && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="mb-4"
              >
                <Badge
                  variant="warning"
                  className="w-full justify-center py-3 text-sm"
                >
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    className="mr-2"
                  >
                    <Clock className="w-4 h-4" />
                  </motion.div>
                  System is initializing. Please wait a moment...
                </Badge>
              </motion.div>
            )}

            {/* Input Form */}
            <form onSubmit={handleSubmit} className="flex space-x-4">
              <div className="flex-1 relative group">
                <Input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask about Islamic history, architecture, or culture..."
                  className={cn(
                    "pr-12 h-14 text-base transition-all duration-300 bg-white/90 backdrop-blur-sm",
                    "focus:ring-2 focus:ring-primary-500 focus:border-transparent focus:bg-white",
                    "group-hover:border-primary-300 group-hover:shadow-lg",
                    "placeholder:text-slate-400"
                  )}
                  disabled={!isSystemReady || isLoading}
                />

                <motion.div
                  className="absolute right-4 top-1/2 transform -translate-y-1/2"
                  animate={{
                    rotate: inputValue ? 360 : 0,
                    scale: inputValue ? 1.1 : 1,
                  }}
                  transition={{ duration: 0.3, type: "spring" }}
                >
                  <BookOpen
                    className={cn(
                      "w-5 h-5 transition-colors duration-200",
                      inputValue ? "text-primary-500" : "text-slate-400"
                    )}
                  />
                </motion.div>
              </div>

              <Button
                type="submit"
                disabled={!inputValue.trim() || !isSystemReady || isLoading}
                variant="islamic"
                size="lg"
                className="h-14 px-8 shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <motion.div
                  className="flex items-center space-x-2"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {isLoading ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{
                        duration: 1,
                        repeat: Infinity,
                        ease: "linear",
                      }}
                    >
                      <Loader2 className="w-5 h-5" />
                    </motion.div>
                  ) : (
                    <motion.div
                      whileHover={{ x: 3 }}
                      transition={{
                        type: "spring",
                        stiffness: 400,
                        damping: 10,
                      }}
                    >
                      <Send className="w-5 h-5" />
                    </motion.div>
                  )}
                  <span className="hidden sm:inline font-semibold">
                    Ask Athar
                  </span>
                </motion.div>
              </Button>
            </form>

            {/* Quick Actions */}
            {messages.length === 0 && sampleQuestions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="mt-4 flex flex-wrap gap-2"
              >
                {sampleQuestions.slice(0, 3).map((question, index) => (
                  <motion.button
                    key={index}
                    onClick={() => handleSampleQuestion(question)}
                    className={cn(
                      "text-xs px-4 py-2 bg-white/60 backdrop-blur-sm hover:bg-white/80",
                      "text-slate-600 hover:text-slate-800 rounded-full border border-white/30",
                      "transition-all duration-200 hover:shadow-md hover:scale-105"
                    )}
                    disabled={!isSystemReady}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <MessageCircle className="w-3 h-3 inline mr-1" />
                    {question.length > 35
                      ? question.substring(0, 35) + "..."
                      : question}
                  </motion.button>
                ))}
              </motion.div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default EnhancedChatInterface;
