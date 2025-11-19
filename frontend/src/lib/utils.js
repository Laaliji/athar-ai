import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatProcessingTime(time) {
  return time < 1 ? `${Math.round(time * 1000)}ms` : `${time.toFixed(1)}s`;
}

export function truncateText(text, maxLength = 100) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

export function getStatusColor(status) {
  switch (status) {
    case "ready":
      return "text-emerald-600 bg-emerald-50 border-emerald-200";
    case "partial":
      return "text-gold-600 bg-gold-50 border-gold-200";
    case "not_initialized":
      return "text-blue-600 bg-blue-50 border-blue-200";
    default:
      return "text-red-600 bg-red-50 border-red-200";
  }
}
