import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function AdminDepartments() {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [modalError, setModalError] = useState(null);

  useEffect(() => {
    fetchDepts();
  }, []);

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

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      setCreating(true);
      setModalError(null);
      await api.post('/departments/create/', {
        name: name.trim(),
        description: description.trim()
      });
      setName('');
      setDescription('');
      setShowModal(false);
      fetchDepts();
    } catch (err) {
      setModalError(err.message || 'Failed to create department');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleActive = async (dept) => {
    const action = dept.is_active ? 'deactivate' : 'activate';
    if (!window.confirm(`Are you sure you want to ${action} the "${dept.name}" department?`)) {
      return;
    }
    try {
      setError(null);
      await api.patch(`/departments/${dept.id}/`, {
        is_active: !dept.is_active
      });
      fetchDepts();
    } catch (err) {
      const errorMsg = err.message || '';
      if (dept.is_active && errorMsg.includes('Cannot deactivate department')) {
        const cleanMsg = errorMsg.replace(/^API Error \d+ at [^:]+: /, '').replace(/^\["|"\]$/g, '').replace(/\\"/g, '"');
        const confirmForce = window.confirm(
          `${cleanMsg}\n\nDo you want to FORCE DEACTIVATE this department anyway?\n\n(This will automatically deactivate active routing rules for this department).`
        );
        if (confirmForce) {
          try {
            await api.patch(`/departments/${dept.id}/`, {
              is_active: false,
              force: true
            });
            fetchDepts();
          } catch (forceErr) {
            alert(forceErr.message || 'Failed to force deactivate department');
          }
        }
      } else {
        alert(errorMsg || `Failed to ${action} department`);
      }
    }
  };

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
                  <th>Description</th>
                  <th>Employees</th>
                  <th>Assigned Complaints</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {departments.map((d) => (
                  <tr key={d.id}>
                    <td><strong>{d.name}</strong></td>
                    <td>{d.description || <em className="text-muted">No description</em>}</td>
                    <td>{d.employee_count !== undefined ? d.employee_count : 0}</td>
                    <td>{d.complaint_count !== undefined ? d.complaint_count : 0}</td>
                    <td>
                      <span className={`status-badge status-${d.is_active ? 'verified' : 'invalid'}`}>
                        {d.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button 
                        className={`btn btn-sm ${d.is_active ? 'btn-danger' : 'btn-ghost'}`}
                        onClick={() => handleToggleActive(d)}
                      >
                        {d.is_active ? 'Deactivate' : 'Activate'}
                      </button>
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
            <form onSubmit={handleCreate}>
              <div className="modal-header">
                <h3 className="modal-title">Add Department</h3>
                <button type="button" className="modal-close" onClick={() => setShowModal(false)}>×</button>
              </div>
              <div className="modal-body">
                {modalError && (
                  <div className="alert alert-danger" style={{ marginBottom: '1rem', color: 'var(--error)' }}>
                    {modalError}
                  </div>
                )}
                <div className="form-group" style={{ marginBottom: '1rem' }}>
                  <label className="form-label">Department Name</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    placeholder="e.g. Health Department" 
                    value={name} 
                    onChange={e => setName(e.target.value)}
                    required 
                    autoFocus
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea 
                    className="form-control" 
                    placeholder="Describe department responsibilities..." 
                    value={description} 
                    onChange={e => setDescription(e.target.value)}
                    rows={3}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Close</button>
                <button type="submit" className="btn btn-primary" disabled={creating || !name.trim()}>
                  {creating ? 'Creating...' : 'Create Department'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
