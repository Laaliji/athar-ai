import React from "react";
import { motion, useMotionValue, useTransform, useSpring } from "framer-motion";
import {
  BookOpen,
  Landmark,
  Palette,
  GraduationCap,
  MapPin,
  Sparkles,
  ArrowRight,
  Shield,
  Zap,
  Globe,
  Heart,
  Star,
} from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { cn, getStatusColor } from "../lib/utils";

const EnhancedWelcomeScreen = ({
  sampleQuestions,
  onQuestionClick,
  systemStatus,
}) => {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const rotateX = useTransform(mouseY, [-300, 300], [10, -10]);
  const rotateY = useTransform(mouseX, [-300, 300], [-10, 10]);

  const springConfig = { damping: 25, stiffness: 400 };
  const x = useSpring(mouseX, springConfig);
  const y = useSpring(mouseY, springConfig);

  const features = [
    {
      icon: BookOpen,
      title: "Historical Knowledge",
      description: "Explore centuries of Islamic civilization and heritage",
      color: "from-blue-500 to-primary-600",
      delay: 0.1,
    },
    {
      icon: Landmark,
      title: "Architecture & Art",
      description: "Discover architectural marvels and artistic traditions",
      color: "from-emerald-500 to-teal-600",
      delay: 0.2,
    },
    {
      icon: GraduationCap,
      title: "Scholars & Science",
      description: "Learn about great minds and scientific contributions",
      color: "from-gold-500 to-orange-600",
      delay: 0.3,
    },
    {
      icon: MapPin,
      title: "Heritage Sites",
      description: "Visit famous monuments and cultural landmarks",
      color: "from-purple-500 to-pink-600",
      delay: 0.4,
    },
  ];

  const stats = [
    { label: "Topics Covered", value: "10+", icon: Globe },
    { label: "Free Models", value: "3", icon: Zap },
    { label: "Response Time", value: "<2s", icon: Star },
    { label: "Cost", value: "$0", icon: Heart },
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
    hidden: { opacity: 0, y: 30, scale: 0.9 },
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

  const floatingVariants = {
    animate: {
      y: [-10, 10, -10],
      rotate: [-5, 5, -5],
      transition: {
        duration: 6,
        repeat: Infinity,
        ease: "easeInOut",
      },
    },
  };

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    mouseX.set(e.clientX - rect.left - rect.width / 2);
    mouseY.set(e.clientY - rect.top - rect.height / 2);
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-6xl mx-auto text-center py-12 relative"
      onMouseMove={handleMouseMove}
    >
      {/* Floating Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-32 h-32 rounded-full bg-gradient-to-r from-primary-200/20 to-emerald-200/20 blur-xl"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            variants={floatingVariants}
            animate="animate"
            transition={{ delay: i * 0.5 }}
          />
        ))}
      </div>

      {/* Hero Section */}
      <motion.div variants={itemVariants} className="mb-16 relative z-10">
        <motion.div
          className="relative inline-block mb-8"
          style={{ rotateX, rotateY, transformPerspective: 1000 }}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-primary-600 via-gold-500 to-emerald-600 rounded-full blur-2xl opacity-30"
            animate={{
              scale: [1, 1.2, 1],
              rotate: [0, 180, 360],
            }}
            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
          />
          <Card className="relative bg-white/80 backdrop-blur-xl border-white/20 shadow-2xl">
            <CardContent className="p-8">
              <motion.div
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles className="w-16 h-16 text-gold-500 mx-auto" />
              </motion.div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.h1
          className="text-5xl md:text-7xl font-display font-bold mb-6"
          variants={itemVariants}
        >
          Welcome to{" "}
          <motion.span
            className="gradient-text inline-block"
            whileHover={{ scale: 1.05 }}
            transition={{ type: "spring", stiffness: 400, damping: 10 }}
          >
            Athar.AI
          </motion.span>
        </motion.h1>

        <motion.p
          className="text-xl md:text-2xl text-slate-600 max-w-3xl mx-auto leading-relaxed mb-8"
          variants={itemVariants}
        >
          Your AI companion for exploring the rich heritage of Islamic
          civilization. Ask questions about history, architecture, art, and
          culture.
        </motion.p>

        {/* Stats Row */}
        <motion.div
          className="flex flex-wrap justify-center gap-4 mb-12"
          variants={itemVariants}
        >
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              whileHover={{ scale: 1.05, y: -5 }}
              transition={{ type: "spring", stiffness: 400, damping: 10 }}
            >
              <Badge variant="islamic" className="px-4 py-2 text-sm">
                <stat.icon className="w-4 h-4 mr-2" />
                <span className="font-bold">{stat.value}</span>
                <span className="ml-1 opacity-90">{stat.label}</span>
              </Badge>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>

      {/* Features Grid */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16"
      >
        {features.map((feature, index) => (
          <motion.div
            key={index}
            variants={itemVariants}
            whileHover={{
              scale: 1.05,
              y: -10,
              rotateY: 5,
            }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 20,
              delay: feature.delay,
            }}
          >
            <Card className="h-full bg-white/60 backdrop-blur-xl border-white/20 shadow-xl hover:shadow-2xl transition-all duration-500 group">
              <CardContent className="p-6 text-center h-full flex flex-col">
                <motion.div
                  className={cn(
                    "w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 bg-gradient-to-br",
                    feature.color
                  )}
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.6 }}
                >
                  <feature.icon className="w-8 h-8 text-white" />
                </motion.div>
                <h3 className="font-display font-semibold text-slate-800 mb-3 text-lg group-hover:text-primary-700 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed flex-1">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Sample Questions */}
      {sampleQuestions.length > 0 && (
        <motion.div variants={itemVariants} className="mb-16">
          <motion.h2
            className="text-3xl font-display font-semibold text-slate-800 mb-8"
            whileHover={{ scale: 1.02 }}
          >
            Try asking about...
          </motion.h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
            {sampleQuestions.slice(0, 6).map((question, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                whileHover={{ scale: 1.02, y: -2 }}
                whileTap={{ scale: 0.98 }}
              >
                <Button
                  onClick={() => onQuestionClick(question)}
                  variant="outline"
                  className="w-full text-left p-6 h-auto bg-white/60 backdrop-blur-xl border-white/30 hover:bg-white/80 hover:border-primary-300 hover:shadow-lg transition-all duration-300 group"
                  disabled={systemStatus?.status !== "ready"}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="text-slate-700 group-hover:text-slate-900 font-medium text-sm leading-relaxed">
                      {question}
                    </span>
                    <motion.div
                      whileHover={{ x: 5 }}
                      transition={{
                        type: "spring",
                        stiffness: 400,
                        damping: 10,
                      }}
                    >
                      <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-primary-600 transition-colors duration-200 flex-shrink-0 ml-3" />
                    </motion.div>
                  </div>
                </Button>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Disclaimer */}
      <motion.div variants={itemVariants}>
        <Card className="bg-gradient-to-r from-slate-50 to-primary-50 border-primary-200 max-w-3xl mx-auto">
          <CardContent className="p-8">
            <div className="flex items-start space-x-4">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 4, repeat: Infinity }}
              >
                <Shield className="w-6 h-6 text-primary-600 mt-1 flex-shrink-0" />
              </motion.div>
              <div className="text-left">
                <h3 className="font-display font-semibold text-slate-800 mb-3 text-lg">
                  Important Notice
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Athar.AI provides historical and cultural information about
                  Islamic civilization. It does not interpret religious texts or
                  provide theological advice. All responses are based on
                  academic and public heritage sources.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* System Status */}
      {systemStatus?.status !== "ready" && (
        <motion.div variants={itemVariants} className="mt-8">
          <Card
            className={cn(
              "max-w-md mx-auto",
              getStatusColor(systemStatus?.status)
            )}
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-center space-x-3">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="w-5 h-5" />
                </motion.div>
                <span className="font-medium">
                  System is initializing... Please wait a moment.
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
};

export default EnhancedWelcomeScreen;
