import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function TrackComplaint() {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--surface-muted)',
      padding: 'var(--sp-xl)',
      textAlign: 'center',
      fontFamily: "'Montserrat', sans-serif"
    }}>
      <h1 className="t-heading-xl" style={{ marginBottom: 'var(--sp-md)' }}>Track Complaint</h1>
      <p className="t-body-md" style={{ color: 'var(--text-secondary)', marginBottom: 'var(--sp-xl)', maxWidth: 400 }}>
        This page would securely load the public status of a specific complaint using its tracking ID.
      </p>
      
      <div className="card" style={{ width: '100%', maxWidth: 500, marginBottom: 'var(--sp-xl)' }}>
        <h2 className="t-heading-md" style={{ marginBottom: 'var(--sp-md)' }}>Search Status</h2>
        <div className="form-group" style={{ marginBottom: 'var(--sp-lg)' }}>
          <input type="text" className="input" placeholder="e.g. CMP-2026-XXXXX" />
        </div>
        <button className="btn btn-primary" style={{ width: '100%' }}>Check Status</button>
      </div>

      <button className="btn btn-ghost" onClick={() => navigate('/')}>
        &larr; Back to Home
      </button>
    </div>
  );
}
