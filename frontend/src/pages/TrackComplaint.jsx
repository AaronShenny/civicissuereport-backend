import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../lib/api';

export default function TrackComplaint() {
  const [searchParams] = useSearchParams();
  const initialId = searchParams.get('id') || '';
  
  const [complaintId, setComplaintId] = useState(initialId);
  const [searchStatus, setSearchStatus] = useState('idle'); // idle, loading, success, not_found, error
  const [complaintData, setComplaintData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (initialId) {
      performSearch(initialId);
    }
  }, [initialId]);

  const performSearch = async (id) => {
    setSearchStatus('loading');
    setComplaintData(null);
    try {
      const res = await api.get(`/api/v1/complaints/public/${id}/`);
      setComplaintData(res.data);
      setSearchStatus('success');
    } catch (err) {
      if (err.response && err.response.status === 404) {
        setSearchStatus('not_found');
      } else {
        setSearchStatus('error');
      }
    }
  };

  const handleTrack = (e) => {
    e.preventDefault();
    if (!complaintId.trim()) return;
    performSearch(complaintId.trim());
  };

  const formatStatus = (s) => {
    if (!s) return '';
    return s.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  return (
    <div className="app-shell" style={{ display: 'block', minHeight: '100vh', background: 'var(--surface-muted)' }}>
      {/* Simple Public Header */}
      <header className="top-header" style={{ position: 'relative', borderBottom: '1px solid var(--border)', background: 'var(--surface)', padding: '0 var(--sp-xl)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-sm)', flex: 1, cursor: 'pointer' }} onClick={() => navigate('/')}>
          <div className="sidebar-logo-mark" style={{ background: 'var(--primary)', color: 'var(--surface)' }}>C</div>
          <span className="sidebar-logo-text" style={{ color: 'var(--text-primary)' }}>CivicConnect</span>
        </div>
        <div className="top-header-actions">
          <button className="btn btn-ghost" onClick={() => navigate('/login')}>Login</button>
          <button className="btn btn-primary" onClick={() => navigate('/register')}>Register</button>
        </div>
      </header>

      <main style={{ maxWidth: '800px', margin: '0 auto', padding: 'var(--sp-3xl) var(--sp-md)' }}>
        <div style={{ textAlign: 'center', marginBottom: 'var(--sp-2xl)' }}>
          <h1 className="t-display-xl" style={{ fontSize: '42px', marginBottom: 'var(--sp-md)' }}>Track Your Complaint</h1>
          <p className="t-body-lg" style={{ color: 'var(--text-secondary)' }}>
            Enter your Complaint ID to see its progress and current status.
          </p>
        </div>

        <div className="card-elevated" style={{ marginBottom: 'var(--sp-2xl)' }}>
          <form onSubmit={handleTrack} style={{ display: 'flex', gap: 'var(--sp-sm)', flexWrap: 'wrap' }}>
            <input
              type="text"
              className="input"
              placeholder="e.g., CMP-2026-000123"
              value={complaintId}
              onChange={(e) => setComplaintId(e.target.value)}
              style={{ flex: 1, minWidth: '250px', padding: '12px 16px', fontSize: '16px' }}
            />
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={!complaintId.trim() || searchStatus === 'loading'}
              style={{ padding: '0 var(--sp-xl)', fontSize: '16px' }}
            >
              {searchStatus === 'loading' ? 'Tracking...' : 'Track'}
            </button>
          </form>
        </div>

        {searchStatus === 'not_found' && (
          <div className="card" style={{ textAlign: 'center', padding: 'var(--sp-2xl)' }}>
            <AlertCircleIcon size={48} style={{ margin: '0 auto var(--sp-md)', color: 'var(--text-secondary)' }} />
            <h3 className="t-heading-lg">Complaint not found</h3>
            <p className="t-body-md" style={{ color: 'var(--text-secondary)', marginTop: 'var(--sp-sm)' }}>
              We couldn't find a complaint with the ID "{complaintId}". Please check the ID and try again.
            </p>
          </div>
        )}

        {searchStatus === 'error' && (
          <div className="alert alert-danger" style={{ textAlign: 'center', padding: 'var(--sp-xl)' }}>
            <AlertCircleIcon size={32} style={{ margin: '0 auto var(--sp-sm)', display: 'block' }} />
            <h3 className="t-heading-md">Unable to retrieve complaint status. Please try again later.</h3>
          </div>
        )}

        {searchStatus === 'success' && complaintData && (
          <div className="card" style={{ padding: 'var(--sp-xl)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--sp-xl)' }}>
              <div>
                <div className="t-label" style={{ color: 'var(--text-secondary)', marginBottom: 'var(--sp-xs)' }}>
                  COMPLAINT ID
                </div>
                <h2 className="t-heading-lg">{complaintData.complaint_number}</h2>
                <div className="t-body-md" style={{ color: 'var(--text-secondary)', marginTop: 'var(--sp-xs)' }}>
                  Submitted on {new Date(complaintData.submitted_at).toLocaleDateString()}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className={`badge badge-${complaintData.status === 'resolved' || complaintData.status === 'closed' ? 'success' : 'primary'}`} style={{ fontSize: '14px', padding: '6px 12px' }}>
                  {formatStatus(complaintData.status)}
                </span>
                <div className="t-body-sm" style={{ color: 'var(--text-secondary)', marginTop: 'var(--sp-xs)' }}>
                  Category: {complaintData.category || 'N/A'}
                </div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 'var(--sp-xl)' }}>
              <h3 className="t-heading-md" style={{ marginBottom: 'var(--sp-lg)' }}>Status Timeline</h3>
              <div style={{ position: 'relative', paddingLeft: '24px' }}>
                <div style={{ position: 'absolute', left: '7px', top: '8px', bottom: '8px', width: '2px', background: 'var(--border)' }}></div>
                {complaintData.status_history && complaintData.status_history.map((h, i) => (
                  <div key={i} style={{ position: 'relative', marginBottom: i === complaintData.status_history.length - 1 ? 0 : 'var(--sp-lg)' }}>
                    <div style={{ position: 'absolute', left: '-24px', top: '4px', width: '16px', height: '16px', borderRadius: '50%', background: 'var(--surface)', border: '2px solid var(--primary)', zIndex: 1 }}></div>
                    <div className="t-heading-sm">{formatStatus(h.status)}</div>
                    <div className="t-body-sm" style={{ color: 'var(--text-secondary)' }}>
                      {new Date(h.changed_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {complaintData.resolution && (
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 'var(--sp-xl)', marginTop: 'var(--sp-xl)' }}>
                <h3 className="t-heading-md" style={{ marginBottom: 'var(--sp-sm)' }}>Resolution Details</h3>
                <div className="card-muted" style={{ padding: 'var(--sp-md)' }}>
                  <p className="t-body-md">{complaintData.resolution.details}</p>
                  <p className="t-body-sm" style={{ color: 'var(--text-secondary)', marginTop: 'var(--sp-xs)' }}>
                    Resolved on {new Date(complaintData.resolution.resolved_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

      </main>
    </div>
  );
}

function AlertCircleIcon({ size = 24, style }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={style}>
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="12" y1="8" x2="12" y2="12"></line>
      <line x1="12" y1="16" x2="12.01" y2="16"></line>
    </svg>
  );
}
