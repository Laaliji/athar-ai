import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  X,
  History,
  BookOpen,
  Settings,
  Info,
  Github,
  ExternalLink,
  Zap,
  Database,
  Brain,
} from "lucide-react";

const Sidebar = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState("about");

  const tabs = [
    { id: "about", label: "About", icon: Info },
    { id: "features", label: "Features", icon: Zap },
    { id: "tech", label: "Technology", icon: Brain },
  ];

  const features = [
    "🆓 100% Free - No API costs",
    "🧠 Advanced RAG System",
    "📚 Rich Islamic Heritage Dataset",
    "🔍 Source Citations",
    "🌍 Multilingual Ready",
    "⚡ Fast Local Processing",
  ];

  const techStack = [
    { name: "Language Models", value: "FLAN-T5, DialoGPT, DistilGPT2" },
    { name: "Embeddings", value: "Multilingual Sentence Transformers" },
    { name: "Vector Database", value: "ChromaDB" },
    { name: "Backend", value: "FastAPI + Python" },
    { name: "Frontend", value: "React + Tailwind CSS" },
    { name: "Framework", value: "LangChain" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 flex flex-col transition-colors duration-300"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700 transition-colors duration-300">
        <h2 className="text-lg font-display font-semibold text-slate-800 dark:text-slate-100 transition-colors duration-300">
          Athar.AI
        </h2>
        <button
          onClick={onClose}
          className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors duration-200"
        >
          <X className="w-5 h-5 text-slate-500 dark:text-slate-400" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-700 transition-colors duration-300">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 text-sm font-medium transition-colors duration-200 ${
              activeTab === tab.id
                ? "text-primary-600 dark:text-primary-400 border-b-2 border-primary-600 dark:border-primary-400 bg-primary-50 dark:bg-primary-900/20"
                : "text-slate-600 dark:text-slate-300 hover:text-slate-800 dark:hover:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === "about" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-3 transition-colors duration-300">
                About Athar.AI
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed transition-colors duration-300">
                Athar.AI is an advanced Retrieval-Augmented Generation (RAG)
                system designed to help users explore the rich heritage of
                Islamic civilization. Built with cutting-edge AI technology and
                powered entirely by free, open-source models.
              </p>
            </div>

            <div>
              <h4 className="font-medium text-slate-800 dark:text-slate-100 mb-2 transition-colors duration-300">
                What you can explore:
              </h4>
              <ul className="text-sm text-slate-600 dark:text-slate-300 space-y-1 transition-colors duration-300">
                <li>• Islamic history and civilizations</li>
                <li>• Architecture and monuments</li>
                <li>• Art, calligraphy, and culture</li>
                <li>• Scholars and scientific contributions</li>
                <li>• Heritage sites and landmarks</li>
              </ul>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4 transition-colors duration-300">
              <h4 className="font-medium text-slate-800 dark:text-slate-100 mb-2 flex items-center space-x-2 transition-colors duration-300">
                <Info className="w-4 h-4" />
                <span>Important Notice</span>
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed transition-colors duration-300">
                This system provides educational and cultural information only.
                It does not interpret religious texts or provide theological
                guidance.
              </p>
            </div>
          </motion.div>
        )}

        {activeTab === "features" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-4 transition-colors duration-300">
              Key Features
            </h3>

            <div className="space-y-3">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center space-x-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg transition-colors duration-300"
                >
                  <span className="text-sm text-slate-700 dark:text-slate-300 transition-colors duration-300">
                    {feature}
                  </span>
                </motion.div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg transition-colors duration-300">
              <h4 className="font-medium text-emerald-800 dark:text-emerald-300 mb-2 transition-colors duration-300">
                Performance
              </h4>
              <div className="space-y-2 text-sm text-emerald-700 dark:text-emerald-400 transition-colors duration-300">
                <div className="flex justify-between">
                  <span>Response Time:</span>
                  <span className="font-medium">&lt; 2s</span>
                </div>
                <div className="flex justify-between">
                  <span>Accuracy:</span>
                  <span className="font-medium">Source-grounded</span>
                </div>
                <div className="flex justify-between">
                  <span>Cost:</span>
                  <span className="font-medium">$0.00</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === "tech" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-4 transition-colors duration-300">
              Technology Stack
            </h3>

            <div className="space-y-3">
              {techStack.map((tech, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3 transition-colors duration-300"
                >
                  <div className="text-sm font-medium text-slate-800 dark:text-slate-100 mb-1 transition-colors duration-300">
                    {tech.name}
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-300 transition-colors duration-300">
                    {tech.value}
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="mt-6 space-y-3">
              <h4 className="font-medium text-slate-800 dark:text-slate-100 transition-colors duration-300">
                Open Source
              </h4>
              <p className="text-sm text-slate-600 dark:text-slate-300 transition-colors duration-300">
                Built with open-source technologies and free models. No API keys
                or subscriptions required.
              </p>

              <a
                href="https://github.com/your-repo/athar-ai"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-2 text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                <Github className="w-4 h-4" />
                <span>View on GitHub</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </motion.div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-slate-200 dark:border-slate-700 p-4 transition-colors duration-300">
        <div className="text-center">
          <p className="text-xs text-slate-500 dark:text-slate-400 transition-colors duration-300">
            Athar.AI v2.0.0
          </p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1 transition-colors duration-300">
            Built with ❤️ for Islamic heritage
          </p>
        </div>
      </div>
    </motion.div>
  );
};

export default Sidebar;
