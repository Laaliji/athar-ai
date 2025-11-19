import axios from "axios";

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  timeout: 30000, // 30 seconds timeout for RAG queries
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(
      `🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`
    );
    return config;
  },
  (error) => {
    console.error("❌ API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(
      "❌ API Response Error:",
      error.response?.data || error.message
    );

    // Handle different error types
    if (error.code === "ECONNABORTED") {
      throw new Error(
        "Request timeout - the AI system might be processing. Please try again."
      );
    } else if (error.response?.status === 503) {
      throw new Error(
        "AI system is initializing. Please wait a moment and try again."
      );
    } else if (error.response?.status >= 500) {
      throw new Error("Server error. Please try again later.");
    } else if (error.response?.status === 400) {
      throw new Error(
        error.response.data?.detail ||
          "Invalid request. Please check your input."
      );
    } else {
      throw new Error(
        error.response?.data?.detail ||
          error.message ||
          "An unexpected error occurred."
      );
    }
  }
);

// API service methods
export const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get("/api/health");
    return response.data;
  },

  // Get system status
  async getSystemStatus() {
    const response = await api.get("/api/status");
    return response.data;
  },

  // Query the RAG system
  async queryRAG(question, maxSources = 3) {
    const response = await api.post("/api/query", {
      question,
      max_sources: maxSources,
    });
    return response.data;
  },

  // Get sample questions
  async getSampleQuestions() {
    const response = await api.get("/api/sample-questions");
    return response.data;
  },

  // Test connection
  async testConnection() {
    try {
      const response = await api.get("/");
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },
};

// Utility functions for API calls
export const withRetry = async (apiCall, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall();
    } catch (error) {
      if (i === maxRetries - 1) throw error;

      console.log(`🔄 Retry ${i + 1}/${maxRetries} after ${delay}ms`);
      await new Promise((resolve) => setTimeout(resolve, delay));
      delay *= 2; // Exponential backoff
    }
  }
};

// Export default api instance for custom calls
export default api;
