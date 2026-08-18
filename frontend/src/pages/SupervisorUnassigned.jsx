import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import StatusBadge from '../components/StatusBadge';

export default function SupervisorUnassigned() {
  const [complaints, setComplaints] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [compRes, empRes] = await Promise.all([
        api.get('/supervisor/complaints/unassigned/'),
        api.get('/users/department-members/')
      ]);
      setComplaints(Array.isArray(compRes) ? compRes : (compRes.results || []));
      
      // Filter out non-ground-level employees if needed, but department-members likely returns everyone.
      // We will let the API enforce this or just show what's available.
      setEmployees(Array.isArray(empRes) ? empRes : (empRes.results || []));
    } catch (err) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  const handleAssign = async (complaintId, employeeId) => {
    if (!employeeId) return;
    try {
      await api.post(`/supervisor/complaints/${complaintId}/assign/`, { employee_id: employeeId });
      alert('Complaint assigned successfully');
      loadData();
    } catch (err) {
      alert(err.message || 'Error assigning complaint');
    }
  };

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner"></div>
        <p>Loading unassigned complaints...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={loadData}>Retry</button>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Unassigned Complaints</h2>
          <p className="page-subtitle">Assign issues to ground-level employees in your department.</p>
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
              <th>Assign To</th>
            </tr>
          </thead>
          <tbody>
            {complaints.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <div className="empty-state" style={{ padding: 'var(--sp-3xl)' }}>
                    <p className="empty-state-title">No unassigned complaints</p>
                    <p className="empty-state-desc">Your department is all caught up!</p>
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
                  <td><StatusBadge status={c.status} /></td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {new Date(c.submitted_at).toLocaleDateString()}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <select 
                        className="select select-sm" 
                        onChange={(e) => handleAssign(c.id, e.target.value)}
                        defaultValue=""
                      >
                        <option value="" disabled>Select Employee...</option>
                        {employees.map(emp => (
                          <option key={emp.id} value={emp.id}>{emp.full_name || emp.email}</option>
                        ))}
                      </select>
                    </div>
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
