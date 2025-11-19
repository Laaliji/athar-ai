import React from "react";
import { motion } from "framer-motion";
import { Moon, Sparkles } from "lucide-react";

const LoadingScreen = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-primary-50 to-emerald-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center islamic-pattern transition-colors duration-300">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-center"
      >
        {/* Logo Animation */}
        <motion.div
          className="relative mb-8"
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        >
          <div className="relative">
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-primary-600 via-gold-500 to-emerald-600 rounded-full blur-xl opacity-30"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <div className="relative w-20 h-20 bg-white dark:bg-slate-800 rounded-full shadow-lg flex items-center justify-center transition-colors duration-300">
              <Moon className="w-10 h-10 text-primary-600 dark:text-primary-400" />
            </div>
          </div>

          {/* Orbiting elements */}
          <motion.div
            className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-2"
            animate={{ rotate: -360 }}
            transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
          >
            <Sparkles className="w-4 h-4 text-gold-500" />
          </motion.div>

          <motion.div
            className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-2"
            animate={{ rotate: -360 }}
            transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
          >
            <div className="w-2 h-2 bg-emerald-500 rounded-full" />
          </motion.div>
        </motion.div>

        {/* Title */}
        <motion.h1
          className="text-4xl font-display font-bold gradient-text mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
        >
          Athar.AI
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          className="text-lg text-slate-600 dark:text-slate-300 mb-8 transition-colors duration-300"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
        >
          Islamic Heritage Explorer
        </motion.p>

        {/* Loading Animation */}
        <motion.div
          className="flex items-center justify-center space-x-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7, duration: 0.6 }}
        >
          <div className="loading-dots">
            <motion.div
              className="w-3 h-3 bg-primary-500 rounded-full"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity, delay: 0 }}
            />
            <motion.div
              className="w-3 h-3 bg-gold-500 rounded-full"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
            />
            <motion.div
              className="w-3 h-3 bg-emerald-500 rounded-full"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
            />
          </div>
        </motion.div>

        {/* Loading Text */}
        <motion.p
          className="text-sm text-slate-500 dark:text-slate-400 mt-4 transition-colors duration-300"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.6 }}
        >
          Initializing AI system...
        </motion.p>

        {/* Progress Indicator */}
        <motion.div
          className="mt-6 w-64 mx-auto"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.2, duration: 0.6 }}
        >
          <div className="bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden transition-colors duration-300">
            <motion.div
              className="h-full bg-gradient-to-r from-primary-500 via-gold-500 to-emerald-500"
              initial={{ width: "0%" }}
              animate={{ width: "100%" }}
              transition={{ duration: 2, ease: "easeInOut" }}
            />
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default LoadingScreen;
