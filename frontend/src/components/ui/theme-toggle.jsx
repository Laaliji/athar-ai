import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon, Palette } from 'lucide-react';
import { Button } from './button';
import { useTheme } from '../../contexts/ThemeContext';
import { cn } from '../../lib/utils';

export const ThemeToggle = ({ className, size = "default" }) => {
    const { theme, toggleTheme, isTransitioning } = useTheme();

    const iconVariants = {
        initial: { scale: 0, rotate: -180, opacity: 0 },
        animate: {
            scale: 1,
            rotate: 0,
            opacity: 1,
            transition: {
                type: "spring",
                stiffness: 400,
                damping: 20
            }
        },
        exit: {
            scale: 0,
            rotate: 180,
            opacity: 0,
            transition: {
                duration: 0.2
            }
        }
    };

    const buttonVariants = {
        light: {
            background: "linear-gradient(135deg, #fbbf24, #f59e0b)",
            boxShadow: "0 4px 15px rgba(251, 191, 36, 0.3)"
        },
        dark: {
            background: "linear-gradient(135deg, #1e293b, #0f172a)",
            boxShadow: "0 4px 15px rgba(30, 41, 59, 0.5)"
        }
    };

    return (
        <motion.div
            animate={buttonVariants[theme]}
            transition={{ duration: 0.3 }}
        >
            <Button
                variant="ghost"
                size={size}
                onClick={toggleTheme}
                className={cn(
                    "relative overflow-hidden rounded-full transition-all duration-300",
                    "hover:scale-110 active:scale-95",
                    "bg-gradient-to-br from-gold-400 to-gold-600 dark:from-slate-700 dark:to-slate-900",
                    "text-white shadow-lg hover:shadow-xl",
                    "border-2 border-gold-300 dark:border-slate-600",
                    isTransitioning && "animate-pulse",
                    className
                )}
                disabled={isTransitioning}
            >
                {/* Background glow effect */}
                <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                    animate={{
                        x: ['-100%', '100%'],
                    }}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "linear"
                    }}
                />

                {/* Icon container */}
                <div className="relative z-10 flex items-center justify-center">
                    <AnimatePresence mode="wait">
                        {theme === 'light' ? (
                            <motion.div
                                key="sun"
                                variants={iconVariants}
                                initial="initial"
                                animate="animate"
                                exit="exit"
                                className="flex items-center space-x-1"
                            >
                                <Sun className="w-4 h-4" />
                                {size === "lg" && <span className="text-sm font-medium ml-1">Light</span>}
                            </motion.div>
                        ) : (
                            <motion.div
                                key="moon"
                                variants={iconVariants}
                                initial="initial"
                                animate="animate"
                                exit="exit"
                                className="flex items-center space-x-1"
                            >
                                <Moon className="w-4 h-4" />
                                {size === "lg" && <span className="text-sm font-medium ml-1">Dark</span>}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Ripple effect on click */}
                <motion.div
                    className="absolute inset-0 rounded-full"
                    initial={{ scale: 0, opacity: 0.5 }}
                    whileTap={{ scale: 2, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    style={{
                        background: theme === 'light'
                            ? 'radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%)'
                            : 'radial-gradient(circle, rgba(59,130,246,0.3) 0%, transparent 70%)'
                    }}
                />
            </Button>
        </motion.div>
    );
};

export const ThemePalette = ({ className }) => {
    const { theme, setTheme } = useTheme();

    const themes = [
        { name: 'light', icon: Sun, label: 'Light', color: 'from-gold-400 to-gold-600' },
        { name: 'dark', icon: Moon, label: 'Dark', color: 'from-slate-600 to-slate-800' },
    ];

    return (
        <div className={cn("flex items-center space-x-2", className)}>
            <Palette className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            <div className="flex space-x-1">
                {themes.map((themeOption) => (
                    <motion.button
                        key={themeOption.name}
                        onClick={() => setTheme(themeOption.name)}
                        className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200",
                            "border-2 hover:scale-110 active:scale-95",
                            `bg-gradient-to-br ${themeOption.color}`,
                            theme === themeOption.name
                                ? "border-primary-500 shadow-lg"
                                : "border-transparent hover:border-slate-300 dark:hover:border-slate-600"
                        )}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <themeOption.icon className="w-3 h-3 text-white" />
                    </motion.button>
                ))}
            </div>
        </div>
    );
};