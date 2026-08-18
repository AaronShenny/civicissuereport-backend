import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import StatusBadge from '../components/StatusBadge';

export default function EmployeeComplaints() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    loadComplaints();
  }, []);

  async function loadComplaints() {
    try {
      const res = await api.get('/employee/complaints/');
      // API might return an array or { results: [] }
      const data = Array.isArray(res) ? res : (res.results || []);
      setComplaints(data);
    } catch (err) {
      setError(err.message || 'Failed to load complaints');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner"></div>
        <p>Loading assigned complaints...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={loadComplaints}>Retry</button>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Assigned to Me</h2>
          <p className="page-subtitle">Manage and resolve civic issues assigned to you.</p>
        </div>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Category</th>
              <th>Address</th>
              <th>Status</th>
              <th>Submitted At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {complaints.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <div className="empty-state" style={{ padding: 'var(--sp-3xl)' }}>
                    <p className="empty-state-title">No assignments found</p>
                    <p className="empty-state-desc">You currently have no issues assigned to you.</p>
                  </div>
                </td>
              </tr>
            ) : (
              complaints.map((c) => (
                <React.Fragment key={c.id}>
                  <tr style={{ cursor: 'pointer', background: expandedId === c.id ? 'var(--surface-muted)' : 'transparent' }} onClick={() => setExpandedId(expandedId === c.id ? null : c.id)}>
                    <td>
                      <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)', background: 'var(--surface-muted)', padding: '2px 6px', borderRadius: 4 }}>
                        {c.complaint_number || c.id.substring(0, 8)}
                      </span>
                    </td>
                    <td style={{ fontWeight: 500 }}>{c.category_name || 'Category'}</td>
                    <td style={{ maxWidth: 200, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {c.location_address || 'No address provided'}
                    </td>
                    <td><StatusBadge status={c.status} /></td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {new Date(c.submitted_at).toLocaleDateString()}
                    </td>
                    <td>
                      <button className="btn btn-ghost btn-sm">
                        {expandedId === c.id ? 'Hide Details' : 'View Action'}
                      </button>
                    </td>
                  </tr>
                  {expandedId === c.id && (
                    <tr>
                      <td colSpan={6} style={{ padding: 0, borderBottom: '1px solid var(--border)' }}>
                        <div style={{ background: 'var(--surface-muted)', padding: 'var(--sp-lg)' }}>
                          <EmployeeActionPanel complaint={c} onActionComplete={loadComplaints} />
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div style={{ marginTop: 'var(--sp-lg)' }}>
         <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>
           <strong>Backend Gap Identified:</strong> The Employee API (`GET /api/v1/employee/complaints/`) only returns minimal details (no full description or media). A detail endpoint like `/api/v1/employee/complaints/&lt;uuid&gt;/` is needed for employees to view the full complaint.
         </p>
      </div>
    </div>
  );
}

function EmployeeActionPanel({ complaint, onActionComplete }) {
  const [activeTab, setActiveTab] = useState(
    complaint.status === 'assigned' ? 'verify' : 'progress'
  );
  
  return (
    <div style={{ display: 'flex', gap: 'var(--sp-lg)' }}>
      {/* Read-Only Details from List API */}
      <div className="card" style={{ flex: 1 }}>
        <p className="section-title">Complaint Summary</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
           <div>
             <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 500, display: 'block' }}>Location</span>
             <span style={{ fontSize: 14 }}>{complaint.location_address || 'N/A'}</span>
           </div>
           {(complaint.location_lat && complaint.location_lng) && (
             <div>
               <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 500, display: 'block' }}>Coordinates</span>
               <span style={{ fontSize: 14 }}>{complaint.location_lat}, {complaint.location_lng}</span>
             </div>
           )}
        </div>
      </div>

      {/* Action Forms */}
      <div className="card" style={{ flex: 2 }}>
        <div className="tabs" style={{ marginBottom: 'var(--sp-md)' }}>
          <button className={`tab${activeTab === 'verify' ? ' active' : ''}`} onClick={() => setActiveTab('verify')}>Verify</button>
          <button className={`tab${activeTab === 'progress' ? ' active' : ''}`} onClick={() => setActiveTab('progress')}>Update Progress</button>
          <button className={`tab${activeTab === 'resolve' ? ' active' : ''}`} onClick={() => setActiveTab('resolve')}>Resolve</button>
        </div>

        {activeTab === 'verify' && <VerifyForm complaintId={complaint.id} onComplete={onActionComplete} />}
        {activeTab === 'progress' && <ProgressForm complaintId={complaint.id} onComplete={onActionComplete} />}
        {activeTab === 'resolve' && <ResolveForm complaintId={complaint.id} onComplete={onActionComplete} />}
      </div>
    </div>
  );
}

function VerifyForm({ complaintId, onComplete }) {
  const [status, setStatus] = useState('verified');
  const [remarks, setRemarks] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = new FormData();
      payload.append('verification_result', status);
      payload.append('verification_remarks', remarks);
      await api.post(`/employee/complaints/${complaintId}/verify/`, payload);
      alert('Verification submitted');
      onComplete();
    } catch (err) {
      alert(err.message || 'Error submitting verification');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
      <div>
        <label className="label">Verification Result *</label>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="select" required style={{ width: '100%' }}>
          <option value="verified">Verified (Valid Issue)</option>
          <option value="invalid">Invalid / Fake Issue</option>
        </select>
      </div>
      <div>
        <label className="label">Remarks *</label>
        <textarea className="input" rows={2} required style={{ width: '100%' }} value={remarks} onChange={(e) => setRemarks(e.target.value)} />
      </div>
      <button type="submit" className="btn btn-primary" disabled={loading} style={{ alignSelf: 'flex-start' }}>
        {loading ? 'Submitting...' : 'Submit Verification'}
      </button>
    </form>
  );
}

function ProgressForm({ complaintId, onComplete }) {
  const [status, setStatus] = useState('in_progress');
  const [remarks, setRemarks] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = new FormData();
      payload.append('progress_update', status);
      payload.append('remarks', remarks);
      await api.post(`/employee/complaints/${complaintId}/progress/`, payload);
      alert('Progress updated');
      onComplete();
    } catch (err) {
      alert(err.message || 'Error updating progress');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
      <div>
        <label className="label">New Status *</label>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="select" required style={{ width: '100%' }}>
          <option value="in_progress">In Progress</option>
          <option value="on_hold">On Hold</option>
          <option value="delayed">Delayed</option>
        </select>
      </div>
      <div>
        <label className="label">Progress Remarks *</label>
        <textarea className="input" rows={2} required style={{ width: '100%' }} value={remarks} onChange={(e) => setRemarks(e.target.value)} />
      </div>
      <button type="submit" className="btn btn-primary" disabled={loading} style={{ alignSelf: 'flex-start' }}>
        {loading ? 'Submitting...' : 'Add Progress Update'}
      </button>
    </form>
  );
}

function ResolveForm({ complaintId, onComplete }) {
  const [details, setDetails] = useState('');
  const [remarks, setRemarks] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    if (!file) {
      alert("Resolution proof attachment is required.");
      setLoading(false);
      return;
    }
    if (details.trim().length < 10) {
      alert("Resolution details must be at least 10 characters.");
      setLoading(false);
      return;
    }
    try {
      const payload = new FormData();
      payload.append('resolution_details', details);
      payload.append('remarks', remarks);
      payload.append('attachments', file);
      await api.post(`/employee/complaints/${complaintId}/resolve/`, payload);
      alert('Resolution submitted');
      onComplete();
    } catch (err) {
      alert(err.message || 'Error submitting resolution');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
      <div>
        <label className="label">Resolution Details *</label>
        <textarea className="input" rows={3} required style={{ width: '100%' }} value={details} onChange={(e) => setDetails(e.target.value)} placeholder="Describe how the issue was resolved..." />
      </div>
      <div>
        <label className="label">Additional Remarks (Optional)</label>
        <textarea className="input" rows={2} style={{ width: '100%' }} value={remarks} onChange={(e) => setRemarks(e.target.value)} />
      </div>
      <div>
        <label className="label">Resolution Proof (Required) *</label>
        <input type="file" className="input" required accept="image/*,video/*,.pdf" onChange={(e) => setFile(e.target.files[0])} style={{ width: '100%' }} />
      </div>
      <button type="submit" className="btn btn-secondary" style={{ background: 'var(--secondary)', color: 'white', borderColor: 'var(--secondary)', alignSelf: 'flex-start' }} disabled={loading}>
        {loading ? 'Submitting...' : 'Mark as Resolved'}
      </button>
    </form>
  );
}
