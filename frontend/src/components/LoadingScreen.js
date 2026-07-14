import React from 'react';

const LoadingScreen = () => {
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'var(--bg-primary)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '24px',
      zIndex: 9999,
    }}>
      {/* Logo */}
      <div style={{
        width: 72,
        height: 72,
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #c97d3a, #c9a352)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Amiri', serif",
        fontSize: 36,
        color: 'white',
        fontWeight: 700,
        boxShadow: '0 0 40px rgba(201,125,58,0.35)',
        animation: 'pulse-logo 2.5s ease-in-out infinite',
      }}>
        أ
      </div>

      {/* Title */}
      <div style={{ textAlign: 'center' }}>
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: 28,
          fontWeight: 700,
          background: 'linear-gradient(135deg, #e6b080, #dbbf7a)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          marginBottom: 8,
        }}>
          Athar AI
        </h1>
        <p style={{ color: '#6b7280', fontSize: 14 }}>
          Islamic Heritage Explorer
        </p>
      </div>

      {/* Progress bar */}
      <div style={{
        width: 220,
        height: 3,
        background: 'rgba(255,255,255,0.08)',
        borderRadius: 2,
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          background: 'linear-gradient(90deg, #c97d3a, #c9a352)',
          borderRadius: 2,
          animation: 'progress-bar 1.8s ease-in-out infinite',
        }} />
      </div>

      {/* Status */}
      <p style={{ color: '#4b5563', fontSize: 13 }}>
        Initializing RAG pipeline…
      </p>

      <style>{`
        @keyframes pulse-logo {
          0%, 100% { box-shadow: 0 0 24px rgba(201,125,58,0.3); }
          50%       { box-shadow: 0 0 48px rgba(201,125,58,0.5); }
        }
        @keyframes progress-bar {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
};

export default LoadingScreen;
