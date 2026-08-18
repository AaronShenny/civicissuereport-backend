import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuth } from '../auth/AuthProvider';
import StatusBadge from '../components/StatusBadge';

export default function ComplaintDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { role } = useAuth();

  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [rejectMode, setRejectMode] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  const fetchComplaint = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/complaints/${id}/`);
      setComplaint(res);
    } catch (err) {
      setError(err.data?.detail || err.message || 'Failed to load complaint details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaint();
  }, [id]);

  const handleConfirmResolution = async () => {
    if (!window.confirm("Are you sure you want to confirm the resolution? This will close the complaint.")) {
      return;
    }
    try {
      setActionLoading(true);
      setActionError(null);
      await api.post(`/complaints/${id}/confirm/`, {});
      setActionSuccess('Resolution confirmed successfully.');
      await fetchComplaint();
    } catch (err) {
      setActionError(err.data?.detail || err.message || 'Failed to confirm resolution.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectResolution = async () => {
    if (rejectionReason.trim().length < 5) {
      setActionError('Please provide a reason (at least 5 characters).');
      return;
    }
    try {
      setActionLoading(true);
      setActionError(null);
      await api.post(`/complaints/${id}/reject/`, { rejection_reason: rejectionReason });
      setActionSuccess('Your feedback has been submitted.');
      setRejectMode(false);
      setRejectionReason('');
      await fetchComplaint();
    } catch (err) {
      setActionError(err.data?.detail || err.message || 'Failed to reject resolution.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner"></div>
        <p>Loading complaint details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
        <p>{error}</p>
        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>Back to Dashboard</button>
      </div>
    );
  }

  if (!complaint) return null;

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <div className="page-header" style={{ marginBottom: 'var(--sp-md)' }}>
        <div className="page-header-left">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-md)' }}>
            <h2 className="page-title" style={{ margin: 0 }}>Complaint {complaint.complaint_number}</h2>
            <StatusBadge status={complaint.status} />
          </div>
        </div>
      </div>

      {actionSuccess && (
        <div className="alert alert-success" style={{ marginBottom: 'var(--sp-md)' }}>
          {actionSuccess}
        </div>
      )}
      
      {actionError && (
        <div className="alert alert-error" style={{ marginBottom: 'var(--sp-md)' }}>
          {actionError}
        </div>
      )}

      {/* Resolution Confirmation Block */}
      {role === 'citizen' && complaint.status === 'resolved' && complaint.closure_confirmation === null && (
        <div className="card" style={{ marginBottom: 'var(--sp-lg)', borderLeft: '4px solid var(--primary)' }}>
          <h3 style={{ fontSize: 18, marginBottom: 'var(--sp-sm)' }}>Has this issue been resolved satisfactorily?</h3>
          
          {!rejectMode ? (
            <div style={{ display: 'flex', gap: 'var(--sp-md)', marginTop: 'var(--sp-md)' }}>
              <button 
                className="btn btn-primary" 
                onClick={handleConfirmResolution}
                disabled={actionLoading}
              >
                Yes, Confirm Resolution
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={() => setRejectMode(true)}
                disabled={actionLoading}
              >
                No, Report a Problem
              </button>
            </div>
          ) : (
            <div style={{ marginTop: 'var(--sp-md)' }}>
              <p style={{ fontSize: 14, marginBottom: 'var(--sp-sm)' }}>Please tell us why the issue is not resolved:</p>
              <textarea 
                className="form-control" 
                rows={3} 
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                disabled={actionLoading}
                placeholder="The pothole was not filled completely..."
              />
              <div style={{ display: 'flex', gap: 'var(--sp-sm)', marginTop: 'var(--sp-sm)' }}>
                <button className="btn btn-ghost" onClick={() => setRejectMode(false)} disabled={actionLoading}>Cancel</button>
                <button className="btn btn-primary" onClick={handleRejectResolution} disabled={actionLoading}>
                  {actionLoading ? 'Submitting...' : 'Submit Feedback'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid-2">
        <div>
          <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
            <p className="section-title">Issue Details</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
              <div>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Category</p>
                <p style={{ fontWeight: 500 }}>{complaint.category?.name || 'N/A'}</p>
              </div>
              <div>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Description</p>
                <p style={{ whiteSpace: 'pre-wrap' }}>{complaint.description}</p>
              </div>
              {complaint.inconvenience_details && (
                <div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Inconvenience Caused</p>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{complaint.inconvenience_details}</p>
                </div>
              )}
              {complaint.expected_solution && (
                <div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Expected Solution</p>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{complaint.expected_solution}</p>
                </div>
              )}
            </div>
          </div>

          <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
            <p className="section-title">Location</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-md)' }}>
              <div>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>District</p>
                <p>{complaint.district || 'N/A'}</p>
              </div>
              {complaint.taluk && (
                <div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Taluk</p>
                  <p>{complaint.taluk}</p>
                </div>
              )}
              {complaint.local_body && (
                <div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Local Body</p>
                  <p>{complaint.local_body}</p>
                </div>
              )}
              {complaint.ward && (
                <div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Ward</p>
                  <p>{complaint.ward}</p>
                </div>
              )}
            </div>
            
            {(complaint.location_address || (complaint.location_lat && complaint.location_lng)) && (
              <div style={{ marginTop: 'var(--sp-md)', paddingTop: 'var(--sp-md)', borderTop: '1px solid var(--border)' }}>
                {complaint.location_address && (
                  <div style={{ marginBottom: 'var(--sp-sm)' }}>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Address/Landmark</p>
                    <p>{complaint.location_address}</p>
                  </div>
                )}
                {complaint.location_lat && complaint.location_lng && (
                  <div>
                    <a 
                      href={`https://maps.google.com/?q=${complaint.location_lat},${complaint.location_lng}`} 
                      target="_blank" 
                      rel="noreferrer"
                      className="btn btn-secondary btn-sm"
                    >
                      View on Google Maps
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
          
          {complaint.attachments && complaint.attachments.length > 0 && (
            <div className="card">
              <p className="section-title">Attachments</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-sm)' }}>
                {complaint.attachments.map(att => (
                  <a 
                    key={att.id} 
                    href={att.file_url} 
                    target="_blank" 
                    rel="noreferrer"
                    style={{ 
                      display: 'flex', alignItems: 'center', padding: 'var(--sp-sm)', 
                      background: 'var(--bg-default)', borderRadius: 'var(--radius)',
                      textDecoration: 'none', color: 'var(--text)' 
                    }}
                  >
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {att.file_url.split('/').pop()}
                    </span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        <div>
          <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
            <p className="section-title">Administration</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
              <div>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Submitted Date</p>
                <p>{new Date(complaint.submitted_at).toLocaleString()}</p>
              </div>
              {complaint.assigned_department && (
                <div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Department</p>
                  <p>{complaint.assigned_department.name}</p>
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <p className="section-title">Complaint Progress</p>
            {complaint.status_history && complaint.status_history.length > 0 ? (
              <div className="timeline">
                <div className="timeline-item">
                  <div className="timeline-dot" style={{ background: 'var(--primary)' }}></div>
                  <div className="timeline-content">
                    <p style={{ fontWeight: 500 }}>Submitted</p>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {new Date(complaint.submitted_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                {(() => {
                  const filteredHistory = complaint.status_history.filter(sh => sh.new_status !== 'submitted');
                  return filteredHistory.map((sh, idx) => (
                    <div className="timeline-item" key={sh.id}>
                      <div className="timeline-line"></div>
                      <div className="timeline-dot" style={{ background: idx === filteredHistory.length - 1 ? 'var(--primary)' : 'var(--text-muted)' }}></div>
                    <div className="timeline-content">
                      <p style={{ fontWeight: 500, textTransform: 'capitalize' }}>
                        {sh.new_status.replace('_', ' ')}
                      </p>
                      <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        {new Date(sh.changed_at).toLocaleString()}
                      </p>
                      {sh.change_reason && (
                        <p style={{ fontSize: 13, marginTop: 4 }}>{sh.change_reason}</p>
                      )}
                    </div>
                  </div>
                ))
                })()}
              </div>
            ) : (
              <div className="timeline">
                <div className="timeline-item">
                  <div className="timeline-dot" style={{ background: 'var(--primary)' }}></div>
                  <div className="timeline-content">
                    <p style={{ fontWeight: 500, textTransform: 'capitalize' }}>{complaint.status.replace('_', ' ')}</p>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {new Date(complaint.submitted_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
