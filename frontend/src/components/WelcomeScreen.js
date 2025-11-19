import React from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  Landmark,
  Palette,
  GraduationCap,
  MapPin,
  Sparkles,
  ArrowRight,
  Shield,
} from "lucide-react";

const WelcomeScreen = ({ sampleQuestions, onQuestionClick, systemStatus }) => {
  const features = [
    {
      icon: BookOpen,
      title: "Historical Knowledge",
      description: "Explore centuries of Islamic civilization and heritage",
    },
    {
      icon: Landmark,
      title: "Architecture & Art",
      description: "Discover architectural marvels and artistic traditions",
    },
    {
      icon: GraduationCap,
      title: "Scholars & Science",
      description: "Learn about great minds and scientific contributions",
    },
    {
      icon: MapPin,
      title: "Heritage Sites",
      description: "Visit famous monuments and cultural landmarks",
    },
  ];

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

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: "easeOut" },
    },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-4xl mx-auto text-center py-12"
    >
      {/* Hero Section */}
      <motion.div variants={itemVariants} className="mb-12">
        <div className="relative inline-block">
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-primary-600 via-gold-500 to-emerald-600 rounded-full blur-xl opacity-20"
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 3, repeat: Infinity }}
          />
          <div className="relative bg-white rounded-full p-6 shadow-lg">
            <Sparkles className="w-12 h-12 text-gold-500 mx-auto" />
          </div>
        </div>

        <h1 className="text-4xl md:text-5xl font-display font-bold mt-6 mb-4">
          Welcome to <span className="gradient-text">Athar.AI</span>
        </h1>

        <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed transition-colors duration-300">
          Your AI companion for exploring the rich heritage of Islamic
          civilization. Ask questions about history, architecture, art, and
          culture.
        </p>
      </motion.div>

      {/* Features Grid */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12"
      >
        {features.map((feature, index) => (
          <motion.div
            key={index}
            className="card hover:shadow-md transition-shadow duration-300"
            whileHover={{ y: -5, scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
          >
            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-emerald-500 rounded-lg flex items-center justify-center mx-auto mb-4">
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2 transition-colors duration-300">
                {feature.title}
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 transition-colors duration-300">
                {feature.description}
              </p>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Sample Questions */}
      {sampleQuestions.length > 0 && (
        <motion.div variants={itemVariants} className="mb-12">
          <h2 className="text-2xl font-display font-semibold text-slate-800 dark:text-slate-100 mb-6 transition-colors duration-300">
            Try asking about...
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sampleQuestions.slice(0, 6).map((question, index) => (
              <motion.button
                key={index}
                onClick={() => onQuestionClick(question)}
                className="text-left p-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md transition-all duration-200 group"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={systemStatus?.status !== "ready"}
              >
                <div className="flex items-center justify-between">
                  <span className="text-slate-700 dark:text-slate-200 group-hover:text-slate-900 dark:group-hover:text-slate-50 font-medium transition-colors duration-300">
                    {question}
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-400 dark:text-slate-500 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors duration-200" />
                </div>
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Disclaimer */}
      <motion.div
        variants={itemVariants}
        className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 transition-colors duration-300"
      >
        <div className="flex items-start space-x-3">
          <Shield className="w-5 h-5 text-slate-500 mt-0.5 flex-shrink-0" />
          <div className="text-left">
            <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-2 transition-colors duration-300">
              Important Notice
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed transition-colors duration-300">
              Athar.AI provides historical and cultural information about
              Islamic civilization. It does not interpret religious texts or
              provide theological advice. All responses are based on academic
              and public heritage sources.
            </p>
          </div>
        </div>
      </motion.div>

      {/* System Status */}
      {systemStatus?.status !== "ready" && (
        <motion.div
          variants={itemVariants}
          className="mt-6 p-4 bg-gold-50 dark:bg-gold-900/20 border border-gold-200 dark:border-gold-800 rounded-lg transition-colors duration-300"
        >
          <p className="text-gold-700 dark:text-gold-300 text-sm transition-colors duration-300">
            🔄 System is initializing... Please wait a moment before asking
            questions.
          </p>
        </motion.div>
      )}
    </motion.div>
  );
};

export default WelcomeScreen;
