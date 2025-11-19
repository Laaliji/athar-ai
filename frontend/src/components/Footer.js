import React from "react";
import { motion } from "framer-motion";
import { Heart, Github, ExternalLink, Shield } from "lucide-react";

const Footer = () => {
  const links = [
    { name: "Documentation", href: "#", icon: ExternalLink },
    {
      name: "GitHub",
      href: "https://github.com/your-repo/athar-ai",
      icon: Github,
    },
    { name: "Privacy", href: "#", icon: Shield },
  ];

  return (
    <motion.footer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.6 }}
      className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-700 py-6 transition-colors duration-300"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
          {/* Left side */}
          <div className="flex items-center space-x-4">
            <p className="text-sm text-slate-600 dark:text-slate-300 flex items-center space-x-2 transition-colors duration-300">
              <span>Built with</span>
              <Heart className="w-4 h-4 text-red-500" />
              <span>for Islamic heritage exploration</span>
            </p>
          </div>

          {/* Center */}
          <div className="flex items-center space-x-6">
            {links.map((link, index) => (
              <motion.a
                key={index}
                href={link.href}
                target={link.href.startsWith("http") ? "_blank" : "_self"}
                rel={link.href.startsWith("http") ? "noopener noreferrer" : ""}
                className="flex items-center space-x-1 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors duration-200"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <link.icon className="w-4 h-4" />
                <span>{link.name}</span>
              </motion.a>
            ))}
          </div>

          {/* Right side */}
          <div className="text-sm text-slate-500 dark:text-slate-400 transition-colors duration-300">
            <p>© 2024 Athar.AI • v2.0.0</p>
          </div>
        </div>

        {/* Bottom disclaimer */}
        <motion.div
          className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700 transition-colors duration-300"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7, duration: 0.6 }}
        >
          <p className="text-xs text-slate-400 dark:text-slate-500 text-center leading-relaxed transition-colors duration-300">
            Athar.AI provides educational content about Islamic heritage and
            culture. It does not offer religious interpretations or theological
            guidance. All information is sourced from academic and public
            heritage references.
          </p>
        </motion.div>
      </div>
    </motion.footer>
  );
};

export default Footer;
