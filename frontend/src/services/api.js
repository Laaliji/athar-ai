import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Axios instance for regular requests
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

// Request/response logging
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail || error.message;
    if (error.code === "ECONNABORTED") throw new Error("Request timed out.");
    if (error.response?.status === 503) throw new Error("AI system initializing — please wait.");
    if (error.response?.status === 503) throw new Error("Knowledge base empty. Run ingestion first.");
    throw new Error(detail || "Unexpected error.");
  }
);

// ── API Service ─────────────────────────────────────────────────────────────

export const apiService = {
  async healthCheck() {
    const { data } = await api.get("/api/health");
    return data;
  },

  async getSystemStatus() {
    const { data } = await api.get("/api/status");
    return data;
  },

  async queryRAG(question, conversationId = null, maxSources = 3) {
    const { data } = await api.post("/api/query", {
      question,
      conversation_id: conversationId,
      max_sources: maxSources,
    });
    return data;
  },

  async getSampleQuestions() {
    const { data } = await api.get("/api/sample-questions");
    return data;
  },

  async getConversation(conversationId) {
    const { data } = await api.get(`/api/conversations/${conversationId}`);
    return data;
  },

  async clearConversation(conversationId) {
    const { data } = await api.delete(`/api/conversations/${conversationId}`);
    return data;
  },

  // Admin
  async getMetrics() {
    const { data } = await api.get("/api/admin/metrics");
    return data;
  },

  async getKBStats() {
    const { data } = await api.get("/api/admin/kb/stats");
    return data;
  },

  async triggerIngestion(options = {}) {
    const { data } = await api.post("/api/admin/ingest", {
      max_articles: options.maxArticles || 40,
      overwrite: options.overwrite || false,
      topics: options.topics || null,
    });
    return data;
  },

  async getIngestionStatus() {
    const { data } = await api.get("/api/admin/ingest/status");
    return data;
  },
};

// ── SSE Streaming ─────────────────────────────────────────────────────────────

/**
 * Stream a RAG query using Server-Sent Events.
 * 
 * @param {string} question - User question
 * @param {string|null} conversationId - Session ID
 * @param {Object} callbacks - {onSources, onToken, onDone, onError}
 * @returns {Function} - Abort function to cancel the stream
 */
export function streamQuery(question, conversationId, callbacks) {
  const { onSources, onToken, onDone, onError } = callbacks;
  const controller = new AbortController();

  fetch(`${BASE_URL}/api/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      conversation_id: conversationId,
      stream: true,
    }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        onError?.(err.detail || "Stream failed.");
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ") && line.length > 6) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "sources") onSources?.(data.sources, data.retrieval_ms);
              else if (data.type === "token") onToken?.(data.content);
              else if (data.type === "done") onDone?.(data.metadata, data.conversation_id);
              else if (data.type === "error") onError?.(data.content);
            } catch {
              // Ignore malformed SSE lines
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onError?.(err.message);
      }
    });

  return () => controller.abort();
}

export default api;
