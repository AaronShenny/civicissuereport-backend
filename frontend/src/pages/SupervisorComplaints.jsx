import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import StatusBadge from '../components/StatusBadge';

export default function SupervisorComplaints() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadComplaints();
  }, []);

  async function loadComplaints() {
    try {
      const res = await api.get('/supervisor/complaints/');
      setComplaints(Array.isArray(res) ? res : (res.results || []));
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
        <p>Loading department complaints...</p>
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
          <h2 className="page-title">Department Complaints</h2>
          <p className="page-subtitle">View all civic issues routed to your department.</p>
        </div>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Category</th>
              <th>Address</th>
              <th>Assigned To</th>
              <th>Status</th>
              <th>Submitted At</th>
            </tr>
          </thead>
          <tbody>
            {complaints.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <div className="empty-state" style={{ padding: 'var(--sp-3xl)' }}>
                    <p className="empty-state-title">No complaints found</p>
                    <p className="empty-state-desc">There are no issues for your department.</p>
                  </div>
                </td>
              </tr>
            ) : (
              complaints.map((c) => (
                <tr key={c.id}>
                  <td>
                    <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)', background: 'var(--surface-muted)', padding: '2px 6px', borderRadius: 4 }}>
                      {c.complaint_number || c.id.substring(0, 8)}
                    </span>
                  </td>
                  <td style={{ fontWeight: 500 }}>{c.category_name || 'Category'}</td>
                  <td style={{ maxWidth: 200, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {c.location_address || 'No address provided'}
                  </td>
                  <td>{c.assigned_employee_name || <span style={{color: 'var(--text-muted)'}}>Unassigned</span>}</td>
                  <td><StatusBadge status={c.status} /></td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {new Date(c.submitted_at).toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
