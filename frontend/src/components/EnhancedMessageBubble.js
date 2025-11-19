import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  User,
  Bot,
  ExternalLink,
  Clock,
  Zap,
  AlertTriangle,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { toast } from "react-hot-toast";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader } from "./ui/card";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { cn, formatTime, formatProcessingTime } from "../lib/utils";

const EnhancedMessageBubble = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const [sourcesExpanded, setSourcesExpanded] = useState(false);

  const isUser = message.type === "user";
  const isError = message.type === "error";
  const isAI = message.type === "ai";

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success("Copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error("Failed to copy");
    }
  };

  const messageVariants = {
    hidden: { opacity: 0, y: 20, scale: 0.95 },
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
  };

  const avatarVariants = {
    hidden: { scale: 0, rotate: -180 },
    visible: {
      scale: 1,
      rotate: 0,
      transition: {
        type: "spring",
        damping: 15,
        stiffness: 400,
        delay: 0.1,
      },
    },
  };

  const contentVariants = {
    hidden: { opacity: 0, x: isUser ? 20 : -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        type: "spring",
        damping: 25,
        stiffness: 200,
        delay: 0.2,
      },
    },
  };

  return (
    <motion.div
      variants={messageVariants}
      initial="hidden"
      animate="visible"
      className={cn(
        "flex max-w-5xl mx-auto",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "flex space-x-4 max-w-4xl",
          isUser ? "flex-row-reverse space-x-reverse" : "flex-row"
        )}
      >
        {/* Enhanced Avatar */}
        <motion.div variants={avatarVariants}>
          <Avatar
            className={cn(
              "w-12 h-12 shadow-lg ring-2 ring-white",
              isUser && "ring-primary-200",
              isError && "ring-red-200",
              isAI && "ring-emerald-200"
            )}
          >
            <AvatarFallback
              className={cn(
                "text-white font-semibold",
                isUser && "bg-gradient-to-br from-primary-500 to-primary-700",
                isError && "bg-gradient-to-br from-red-500 to-red-700",
                isAI &&
                  "bg-gradient-to-br from-emerald-500 via-primary-600 to-gold-500"
              )}
            >
              {isUser ? (
                <User className="w-6 h-6" />
              ) : isError ? (
                <AlertTriangle className="w-6 h-6" />
              ) : (
                <motion.div
                  animate={{ rotate: [0, 360] }}
                  transition={{
                    duration: 20,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                >
                  <Sparkles className="w-6 h-6" />
                </motion.div>
              )}
            </AvatarFallback>
          </Avatar>
        </motion.div>

        {/* Message Content */}
        <motion.div variants={contentVariants} className="flex-1 min-w-0">
          {/* Message Card */}
          <Card
            className={cn(
              "shadow-lg hover:shadow-xl transition-all duration-300",
              isUser &&
                "bg-gradient-to-br from-primary-500 to-primary-600 text-white border-primary-300",
              isError &&
                "bg-gradient-to-br from-red-50 to-red-100 border-red-200",
              isAI &&
                "bg-gradient-to-br from-white to-slate-50 border-slate-200 hover:border-primary-200"
            )}
          >
            <CardContent className="p-6">
              {/* Message Text */}
              <div
                className={cn(
                  "prose prose-sm max-w-none",
                  isUser && "prose-invert",
                  isAI && "prose-slate"
                )}
              >
                {isUser ? (
                  <p className="text-white/95 leading-relaxed font-medium">
                    {message.content}
                  </p>
                ) : (
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => (
                        <p className="mb-3 last:mb-0 leading-relaxed text-slate-700">
                          {children}
                        </p>
                      ),
                      strong: ({ children }) => (
                        <strong className="font-semibold text-slate-900">
                          {children}
                        </strong>
                      ),
                      em: ({ children }) => (
                        <em className="italic text-slate-600">{children}</em>
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                )}
              </div>

              {/* Action Buttons */}
              {!isUser && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
                  <div className="flex items-center space-x-3 text-xs text-slate-500">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{formatTime(message.timestamp)}</span>
                    </div>

                    {message.processingTime && (
                      <>
                        <span>•</span>
                        <div className="flex items-center space-x-1">
                          <Zap className="w-3 h-3" />
                          <span>
                            {formatProcessingTime(message.processingTime)}
                          </span>
                        </div>
                      </>
                    )}

                    {message.modelUsed && (
                      <>
                        <span>•</span>
                        <Badge
                          variant="secondary"
                          className="text-xs py-0 px-2"
                        >
                          {message.modelUsed}
                        </Badge>
                      </>
                    )}
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(message.content)}
                    className="h-8 px-3"
                  >
                    <motion.div
                      animate={{ scale: copied ? 1.2 : 1 }}
                      transition={{
                        type: "spring",
                        stiffness: 400,
                        damping: 10,
                      }}
                    >
                      {copied ? (
                        <Check className="w-3 h-3 text-emerald-600" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </motion.div>
                    <span className="ml-1 text-xs">
                      {copied ? "Copied!" : "Copy"}
                    </span>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Enhanced Sources Section */}
          {!isUser &&
            !isError &&
            message.sources &&
            message.sources.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                transition={{ delay: 0.3, duration: 0.4 }}
                className="mt-4"
              >
                <Card className="bg-gradient-to-r from-slate-50 to-primary-50 border-primary-200">
                  <CardHeader className="pb-3">
                    <Button
                      variant="ghost"
                      onClick={() => setSourcesExpanded(!sourcesExpanded)}
                      className="w-full justify-between p-0 h-auto font-semibold text-slate-700 hover:text-primary-700"
                    >
                      <div className="flex items-center space-x-2">
                        <ExternalLink className="w-4 h-4" />
                        <span>Sources ({message.sources.length})</span>
                      </div>
                      <motion.div
                        animate={{ rotate: sourcesExpanded ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ChevronDown className="w-4 h-4" />
                      </motion.div>
                    </Button>
                  </CardHeader>

                  <AnimatePresence>
                    {sourcesExpanded && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <CardContent className="pt-0 space-y-3">
                          {message.sources.map((source, index) => (
                            <motion.div
                              key={index}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="bg-white rounded-lg p-4 border border-slate-200 hover:border-primary-300 hover:shadow-md transition-all duration-200 group"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1 min-w-0">
                                  <h5 className="font-semibold text-slate-800 text-sm mb-2 group-hover:text-primary-700 transition-colors">
                                    {source.title}
                                  </h5>
                                  <p className="text-xs text-slate-600 leading-relaxed mb-3 line-clamp-2">
                                    {source.excerpt}
                                  </p>
                                  {source.url && (
                                    <motion.a
                                      href={source.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center space-x-1 text-xs text-primary-600 hover:text-primary-700 font-medium group-hover:underline"
                                      whileHover={{ scale: 1.05 }}
                                      whileTap={{ scale: 0.95 }}
                                    >
                                      <ExternalLink className="w-3 h-3" />
                                      <span>Read more on Wikipedia</span>
                                    </motion.a>
                                  )}
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </CardContent>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              </motion.div>
            )}
        </motion.div>
      </div>
    </motion.div>
  );
};

export default EnhancedMessageBubble;
