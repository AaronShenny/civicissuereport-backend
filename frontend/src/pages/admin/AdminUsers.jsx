import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function AdminUsers() {
  const [departments, setDepartments] = useState([]);
  const [jurisdictions, setJurisdictions] = useState([]);
  const [roles, setRoles] = useState([]);
  
  const [selectedDept, setSelectedDept] = useState('');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showLocModal, setShowLocModal] = useState(null);
  const [showDeptModal, setShowDeptModal] = useState(null);
  const [formError, setFormError] = useState(null);
  const [formLoading, setFormLoading] = useState(false);

  // Forms
  const [addForm, setAddForm] = useState({ full_name: '', email: '', role_id: '', department_id: '', jurisdiction_id: '' });
  const [locForm, setLocForm] = useState({ jurisdiction_id: '' });
  const [deptForm, setDeptForm] = useState({ department_id: '' });

  useEffect(() => {
    async function fetchMetadata() {
      try {
        const [dRes, jRes, rRes] = await Promise.all([
          api.get('/departments/'),
          api.get('/departments/jurisdictions/'),
          api.get('/users/roles/')
        ]);
        setDepartments(Array.isArray(dRes) ? dRes : (dRes.results || []));
        setJurisdictions(Array.isArray(jRes) ? jRes : (jRes.results || []));
        setRoles(Array.isArray(rRes) ? rRes : (rRes.results || []));
      } catch (err) {
        console.error('Failed to load metadata', err);
      }
    }
    fetchMetadata();
  }, []);

  const fetchUsers = async () => {
    if (!selectedDept) {
      setUsers([]);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/users/department-members/?department_id=${selectedDept}`);
      setUsers(Array.isArray(res) ? res : (res.results || []));
    } catch (err) {
      setError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [selectedDept]);

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);
    try {
      await api.post('/users/employees/', addForm);
      setShowAddModal(false);
      setAddForm({ full_name: '', email: '', role_id: '', department_id: '', jurisdiction_id: '' });
      if (addForm.department_id === selectedDept) fetchUsers();
    } catch (err) {
      setFormError(err.message || 'Failed to create employee');
    } finally {
      setFormLoading(false);
    }
  };

  const handleTransferLocation = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);
    try {
      await api.post(`/users/${showLocModal.id}/transfer-location/`, locForm);
      setShowLocModal(null);
      fetchUsers();
    } catch (err) {
      setFormError(err.message || 'Failed to transfer location');
    } finally {
      setFormLoading(false);
    }
  };

  const handleTransferDepartment = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);
    try {
      await api.post(`/users/${showDeptModal.id}/transfer-department/`, deptForm);
      setShowDeptModal(null);
      fetchUsers();
    } catch (err) {
      setFormError(err.message || 'Failed to transfer department');
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Employees</h2>
          <p className="page-subtitle">Manage department employees across the system</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>+ Add Employee</button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="form-group" style={{ maxWidth: '400px', marginBottom: 0 }}>
          <label className="form-label">Select Department</label>
          <select className="form-control" value={selectedDept} onChange={(e) => setSelectedDept(e.target.value)}>
            <option value="">-- Select a department to view employees --</option>
            {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
      </div>

      {!selectedDept ? (
        <div className="empty-state">
          <p className="empty-state-title">No Department Selected</p>
          <p>Select a department to view or manage its employees.</p>
        </div>
      ) : loading ? (
        <div className="empty-state">
          <div className="spinner"></div>
          <p>Loading employees...</p>
        </div>
      ) : error ? (
        <div className="empty-state">
          <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
          <p>{error}</p>
        </div>
      ) : users.length === 0 ? (
        <div className="empty-state">
          <p className="empty-state-title">No Employees Found</p>
          <p>This department currently has no employees assigned.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td><strong>{u.full_name}</strong></td>
                    <td>{u.email || 'N/A'}</td>
                    <td style={{ textTransform: 'capitalize' }}>{u.role_name?.replace(/_/g, ' ') || 'Unknown'}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => {
                          setLocForm({ jurisdiction_id: '' });
                          setShowLocModal(u);
                        }}>Transfer Loc</button>
                        <button className="btn btn-secondary btn-sm" onClick={() => {
                          setDeptForm({ department_id: '' });
                          setShowDeptModal(u);
                        }}>Transfer Dept</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showAddModal && (
        <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Add Employee</h3>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>×</button>
            </div>
            <form onSubmit={handleAddEmployee}>
              <div className="modal-body">
                {formError && <div className="error-banner">{formError}</div>}
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input type="text" className="form-control" required value={addForm.full_name} onChange={e => setAddForm({...addForm, full_name: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input type="email" className="form-control" required value={addForm.email} onChange={e => setAddForm({...addForm, email: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Role</label>
                  <select className="form-control" required value={addForm.role_id} onChange={e => setAddForm({...addForm, role_id: e.target.value})}>
                    <option value="">Select Role</option>
                    {roles.map(r => <option key={r.id} value={r.id}>{r.role_name.replace(/_/g, ' ')}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Department</label>
                  <select className="form-control" required value={addForm.department_id} onChange={e => setAddForm({...addForm, department_id: e.target.value})}>
                    <option value="">Select Department</option>
                    {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">District / Jurisdiction</label>
                  <select className="form-control" value={addForm.jurisdiction_id} onChange={e => setAddForm({...addForm, jurisdiction_id: e.target.value})}>
                    <option value="">None / Global</option>
                    {jurisdictions.map(j => <option key={j.id} value={j.id}>{j.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={formLoading}>{formLoading ? 'Creating...' : 'Create Employee'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showLocModal && (
        <div className="modal-backdrop" onClick={() => setShowLocModal(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Transfer Location: {showLocModal.full_name}</h3>
              <button className="modal-close" onClick={() => setShowLocModal(null)}>×</button>
            </div>
            <form onSubmit={handleTransferLocation}>
              <div className="modal-body">
                {formError && <div className="error-banner">{formError}</div>}
                <div className="form-group">
                  <label className="form-label">New District / Jurisdiction</label>
                  <select className="form-control" required value={locForm.jurisdiction_id} onChange={e => setLocForm({...locForm, jurisdiction_id: e.target.value})}>
                    <option value="">Select Jurisdiction</option>
                    {jurisdictions.map(j => <option key={j.id} value={j.id}>{j.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowLocModal(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={formLoading}>{formLoading ? 'Transferring...' : 'Transfer Location'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showDeptModal && (
        <div className="modal-backdrop" onClick={() => setShowDeptModal(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Transfer Department: {showDeptModal.full_name}</h3>
              <button className="modal-close" onClick={() => setShowDeptModal(null)}>×</button>
            </div>
            <form onSubmit={handleTransferDepartment}>
              <div className="modal-body">
                {formError && <div className="error-banner">{formError}</div>}
                <div className="form-group">
                  <label className="form-label">New Department</label>
                  <select className="form-control" required value={deptForm.department_id} onChange={e => setDeptForm({...deptForm, department_id: e.target.value})}>
                    <option value="">Select Department</option>
                    {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowDeptModal(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={formLoading}>{formLoading ? 'Transferring...' : 'Transfer Department'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
