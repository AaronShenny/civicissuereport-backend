import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function AdminDepartments() {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    async function fetchDepts() {
      try {
        setLoading(true);
        const res = await api.get('/departments/');
        const deptList = Array.isArray(res) ? res : (res.results || []);
        setDepartments(deptList);
      } catch (err) {
        setError(err.message || 'Failed to load departments');
      } finally {
        setLoading(false);
      }
    }
    fetchDepts();
  }, []);

  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Departments</h2>
          <p className="page-subtitle">Manage structural departments and jurisdictions</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + Add Department
          </button>
        </div>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="spinner"></div>
          <p>Loading departments...</p>
        </div>
      ) : error ? (
        <div className="empty-state">
          <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
          <p>{error}</p>
        </div>
      ) : departments.length === 0 ? (
        <div className="empty-state">
          <p className="empty-state-title">No Departments Found</p>
          <p>There are no departments available in the system.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Department Name</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {departments.map((d) => (
                  <tr key={d.id}>
                    <td><strong>{d.name}</strong></td>
                    <td>
                      <span className={`status-badge status-${d.is_active ? 'verified' : 'invalid'}`}>
                        {d.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Add Department</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                <strong>Pending Backend API:</strong> Department creation via the frontend 
                is currently disabled because the backend returns a <code>501 Not Implemented</code>. 
                Departments must currently be managed via the Supabase admin panel.
              </p>
              <div className="form-group">
                <label className="form-label">Department Name</label>
                <input type="text" className="form-control" placeholder="e.g. Traffic Police" disabled />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Close</button>
              <button className="btn btn-primary" disabled>Create Department</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
