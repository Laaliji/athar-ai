import React, { useState, useEffect, useRef } from 'react';
import {
  BarChart2, Database, Zap, Clock, AlertCircle,
  RefreshCw, BookOpen, CheckCircle, XCircle, Loader2,
  Activity
} from 'lucide-react';
import { apiService } from '../services/api';

// ── Sub-components ─────────────────────────────────────────────────────────────

const StatCard = ({ icon: Icon, label, value, sub, color = 'accent' }) => (
  <div className="stat-card">
    <div className={`stat-icon stat-icon--${color}`}>
      <Icon size={20} />
    </div>
    <div className="stat-body">
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value ?? '—'}</p>
      {sub && <p className="stat-sub">{sub}</p>}
    </div>
  </div>
);

const StatusDot = ({ ok, label }) => (
  <div className="status-row">
    {ok
      ? <CheckCircle size={14} className="status-ok" />
      : <XCircle size={14} className="status-err" />}
    <span className={ok ? 'status-label--ok' : 'status-label--err'}>{label}</span>
  </div>
);

const TopicTag = ({ name }) => (
  <span className="topic-tag">{name}</span>
);

const SectionHeader = ({ children }) => (
  <h3 className="admin-section-header">{children}</h3>
);

// ── Main Component ─────────────────────────────────────────────────────────────

const AdminDashboard = ({ onClose }) => {
  const [metrics, setMetrics] = useState(null);
  const [kbStats, setKbStats] = useState(null);
  const [sysStatus, setSysStatus] = useState(null);
  const [ingestStatus, setIngestStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestMsg, setIngestMsg] = useState('');
  const pollRef = useRef(null);

  const loadData = async () => {
    try {
      const [m, k, s] = await Promise.all([
        apiService.getMetrics(),
        apiService.getKBStats(),
        apiService.getSystemStatus(),
      ]);
      setMetrics(m);
      setKbStats(k);
      setSysStatus(s);
    } catch (err) {
      console.error('Admin data load failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const checkIngestStatus = async () => {
    try {
      const status = await apiService.getIngestionStatus();
      setIngestStatus(status);
      if (status.running) {
        pollRef.current = setTimeout(checkIngestStatus, 3000);
      } else {
        clearTimeout(pollRef.current);
        if (ingestLoading) {
          setIngestLoading(false);
          setIngestMsg('✅ Ingestion complete! Reload to see updated stats.');
          loadData();
        }
      }
    } catch { /* ignore */ }
  };

  useEffect(() => {
    loadData();
    return () => clearTimeout(pollRef.current);
  }, []);

  const handleIngest = async (overwrite = false) => {
    setIngestLoading(true);
    setIngestMsg('Starting ingestion…');
    try {
      await apiService.triggerIngestion({ overwrite });
      setIngestMsg('⏳ Ingestion running in background…');
      setTimeout(checkIngestStatus, 2000);
    } catch (err) {
      setIngestMsg(`❌ ${err.message}`);
      setIngestLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="admin-loading">
        <Loader2 size={32} className="spin" />
        <p>Loading dashboard…</p>
      </div>
    );
  }

  return (
    <div className="admin-overlay" onClick={onClose}>
      <div className="admin-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="admin-header">
          <div className="admin-header-left">
            <BarChart2 size={22} style={{ color: 'var(--accent-primary)' }} />
            <h2 className="admin-title">Admin Dashboard</h2>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="admin-body">
          {/* System Status */}
          <section className="admin-section">
            <SectionHeader>System Status</SectionHeader>
            <div className="status-grid">
              <StatusDot ok={sysStatus?.vector_db_ready} label="ChromaDB (Semantic)" />
              <StatusDot ok={sysStatus?.bm25_ready} label="BM25 (Keyword)" />
              <StatusDot ok={!!sysStatus?.llm_provider && sysStatus.llm_provider !== 'none'} label="LLM Provider" />
              <StatusDot ok={(sysStatus?.documents_loaded ?? 0) > 0} label="Knowledge Base" />
            </div>
            {sysStatus && (
              <div className="system-info-row">
                <span className="sys-badge">
                  <Zap size={12} /> {sysStatus.llm_provider}/{sysStatus.llm_model?.split('-').slice(0, 3).join('-')}
                </span>
                <span className="sys-badge">
                  <Database size={12} /> {sysStatus.documents_loaded?.toLocaleString()} chunks
                </span>
                <span className="sys-badge">
                  <Clock size={12} /> up {Math.round((sysStatus.uptime_seconds || 0) / 60)}m
                </span>
              </div>
            )}
          </section>

          {/* Performance Metrics */}
          <section className="admin-section">
            <SectionHeader>Query Metrics</SectionHeader>
            <div className="stats-grid">
              <StatCard
                icon={Activity}
                label="Total Queries"
                value={metrics?.total_queries?.toLocaleString()}
                sub={`${metrics?.queries_last_hour ?? 0} in last hour`}
              />
              <StatCard
                icon={Clock}
                label="Avg Response"
                value={metrics?.avg_response_time_ms ? `${Math.round(metrics.avg_response_time_ms)}ms` : '—'}
                sub={`Retrieval: ${Math.round(metrics?.avg_retrieval_time_ms ?? 0)}ms`}
                color="gold"
              />
              <StatCard
                icon={Zap}
                label="Generation"
                value={metrics?.avg_generation_time_ms ? `${Math.round(metrics.avg_generation_time_ms)}ms` : '—'}
                sub="LLM latency"
                color="green"
              />
              <StatCard
                icon={AlertCircle}
                label="Error Rate"
                value={metrics?.error_rate !== undefined ? `${(metrics.error_rate * 100).toFixed(1)}%` : '—'}
                sub="Last 1000 queries"
                color={metrics?.error_rate > 0.05 ? 'red' : 'green'}
              />
            </div>
          </section>

          {/* Knowledge Base */}
          <section className="admin-section">
            <SectionHeader>Knowledge Base</SectionHeader>
            <div className="kb-info">
              <div className="kb-info-row">
                <BookOpen size={16} />
                <span><strong>{kbStats?.total_documents ?? 0}</strong> articles · <strong>{kbStats?.total_chunks?.toLocaleString() ?? 0}</strong> chunks</span>
              </div>
              {kbStats?.last_ingested && (
                <div className="kb-info-row">
                  <Clock size={14} />
                  <span className="text-secondary">Last ingested: {new Date(kbStats.last_ingested).toLocaleDateString()}</span>
                </div>
              )}
              {kbStats?.embedding_model && (
                <div className="kb-info-row">
                  <Database size={14} />
                  <span className="text-secondary">{kbStats.embedding_model}</span>
                </div>
              )}
            </div>

            {kbStats?.topics?.length > 0 && (
              <div className="topics-container">
                <p className="topics-label">Indexed Topics ({kbStats.topics.length})</p>
                <div className="topics-list">
                  {kbStats.topics.map((t, i) => <TopicTag key={i} name={t} />)}
                </div>
              </div>
            )}
          </section>

          {/* Ingestion Controls */}
          <section className="admin-section">
            <SectionHeader>Re-Ingestion</SectionHeader>
            <p className="admin-hint">
              Fetch fresh Wikipedia articles and rebuild the knowledge base.
              This runs in the background — the API remains available.
            </p>
            <div className="ingest-actions">
              <button
                className="btn-primary"
                onClick={() => handleIngest(false)}
                disabled={ingestLoading}
              >
                {ingestLoading
                  ? <><Loader2 size={14} className="spin" /> Running…</>
                  : <><RefreshCw size={14} /> Add New Articles</>}
              </button>
              <button
                className="btn-secondary"
                onClick={() => handleIngest(true)}
                disabled={ingestLoading}
              >
                Full Re-ingest
              </button>
            </div>
            {ingestMsg && <p className="ingest-msg">{ingestMsg}</p>}
            {ingestStatus?.running && (
              <div className="ingest-progress">
                <Loader2 size={12} className="spin" />
                <span>{ingestStatus.chunks_indexed?.toLocaleString() ?? 0} chunks indexed so far…</span>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
