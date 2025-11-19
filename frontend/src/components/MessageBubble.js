import React from "react";
import { motion } from "framer-motion";
import {
  User,
  Bot,
  ExternalLink,
  Clock,
  Zap,
  AlertTriangle,
} from "lucide-react";
import ReactMarkdown from "react-markdown";

const MessageBubble = ({ message }) => {
  const isUser = message.type === "user";
  const isError = message.type === "error";

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatProcessingTime = (time) => {
    return time < 1 ? `${Math.round(time * 1000)}ms` : `${time.toFixed(1)}s`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-6`}
    >
      <div
        className={`flex max-w-4xl ${
          isUser ? "flex-row-reverse" : "flex-row"
        } space-x-3`}
      >
        {/* Avatar */}
        <motion.div
          className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
            isUser
              ? "bg-primary-600"
              : isError
              ? "bg-red-500"
              : "bg-gradient-to-br from-gold-500 to-emerald-500"
          }`}
          whileHover={{ scale: 1.1 }}
          transition={{ type: "spring", stiffness: 400, damping: 10 }}
        >
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : isError ? (
            <AlertTriangle className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </motion.div>

        {/* Message Content */}
        <div className={`flex-1 ${isUser ? "mr-3" : "ml-3"}`}>
          {/* Message Bubble */}
          <motion.div
            className={`rounded-2xl px-4 py-3 transition-colors duration-300 ${
              isUser
                ? "bg-primary-600 dark:bg-primary-700 text-white"
                : isError
                ? "bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300"
                : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100 shadow-sm"
            }`}
            whileHover={{ scale: 1.01 }}
            transition={{ type: "spring", stiffness: 400, damping: 10 }}
          >
            {isUser ? (
              <p className="text-sm leading-relaxed">{message.content}</p>
            ) : (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown
                  components={{
                    p: ({ children }) => (
                      <p className="mb-2 last:mb-0 leading-relaxed">
                        {children}
                      </p>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold text-slate-900 dark:text-slate-50 transition-colors duration-300">
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => (
                      <em className="italic text-slate-700 dark:text-slate-300 transition-colors duration-300">
                        {children}
                      </em>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </motion.div>

          {/* Metadata */}
          <div
            className={`flex items-center mt-2 space-x-3 text-xs text-slate-500 dark:text-slate-400 transition-colors duration-300 ${
              isUser ? "justify-end" : "justify-start"
            }`}
          >
            <span>{formatTime(message.timestamp)}</span>

            {!isUser && !isError && message.processingTime && (
              <>
                <span>•</span>
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>{formatProcessingTime(message.processingTime)}</span>
                </div>
              </>
            )}

            {!isUser && !isError && message.modelUsed && (
              <>
                <span>•</span>
                <div className="flex items-center space-x-1">
                  <Zap className="w-3 h-3" />
                  <span>{message.modelUsed}</span>
                </div>
              </>
            )}
          </div>

          {/* Sources */}
          {!isUser &&
            !isError &&
            message.sources &&
            message.sources.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                transition={{ delay: 0.2, duration: 0.3 }}
                className="mt-4 space-y-2"
              >
                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center space-x-2 transition-colors duration-300">
                  <ExternalLink className="w-4 h-4" />
                  <span>Sources</span>
                </h4>

                <div className="space-y-2">
                  {message.sources.map((source, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 * index }}
                      className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors duration-200"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className="font-medium text-slate-800 dark:text-slate-100 text-sm mb-1 transition-colors duration-300">
                            {source.title}
                          </h5>
                          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed mb-2 transition-colors duration-300">
                            {source.excerpt}
                          </p>
                          {source.url && (
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center space-x-1 text-xs text-primary-600 hover:text-primary-700 font-medium"
                            >
                              <ExternalLink className="w-3 h-3" />
                              <span>Read more</span>
                            </a>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
        </div>
      </div>
    </motion.div>
  );
};

export default MessageBubble;
