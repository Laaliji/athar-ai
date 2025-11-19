import React from "react";
import { motion } from "framer-motion";
import { Menu, Moon, Zap, AlertCircle, CheckCircle } from "lucide-react";
import { ThemeToggle } from "./ui/theme-toggle";

const Header = ({ onMenuClick, systemStatus }) => {
  const getStatusIcon = () => {
    if (!systemStatus) return <AlertCircle className="w-4 h-4 text-red-500" />;

    if (systemStatus.status === "ready") {
      return <CheckCircle className="w-4 h-4 text-emerald-500" />;
    } else if (systemStatus.status === "partial") {
      return <AlertCircle className="w-4 h-4 text-gold-500" />;
    } else {
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusText = () => {
    if (!systemStatus) return "Connecting...";

    switch (systemStatus.status) {
      case "ready":
        return "System Ready";
      case "partial":
        return "Partial Load";
      case "not_initialized":
        return "Initializing...";
      default:
        return "System Error";
    }
  };

  return (
    <motion.header
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-700 sticky top-0 z-30 transition-colors duration-300"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left side */}
          <div className="flex items-center space-x-4">
            <button
              onClick={onMenuClick}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200 lg:hidden"
            >
              <Menu className="w-5 h-5 text-slate-600 dark:text-slate-300" />
            </button>

            {/* Logo */}
            <motion.div
              className="flex items-center space-x-3"
              whileHover={{ scale: 1.02 }}
              transition={{ type: "spring", stiffness: 400, damping: 10 }}
            >
              <div className="relative">
                <Moon className="w-8 h-8 text-primary-600" />
                <motion.div
                  className="absolute inset-0 bg-primary-600 rounded-full opacity-20"
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              </div>
              <div>
                <h1 className="text-xl font-display font-semibold gradient-text">
                  Athar.AI
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400 -mt-1 transition-colors duration-300">
                  Islamic Heritage Explorer
                </p>
              </div>
            </motion.div>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {/* System Status */}
            <motion.div
              className="hidden sm:flex items-center space-x-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-full transition-colors duration-300"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
            >
              {getStatusIcon()}
              <span className="text-sm font-medium text-slate-700 dark:text-slate-200 transition-colors duration-300">
                {getStatusText()}
              </span>
            </motion.div>

            {/* Performance Indicator */}
            <motion.div
              className="hidden md:flex items-center space-x-2 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/30 rounded-full"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Zap className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                Free Models
              </span>
            </motion.div>

            {/* Theme Toggle */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
            >
              <ThemeToggle />
            </motion.div>
          </div>
        </div>
      </div>
    </motion.header>
  );
};

export default Header;
