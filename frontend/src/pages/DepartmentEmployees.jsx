import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../auth/AuthProvider';

export default function DepartmentEmployees() {
  const { role } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [jurisdictions, setJurisdictions] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showLocModal, setShowLocModal] = useState(null);
  const [formError, setFormError] = useState(null);
  const [formLoading, setFormLoading] = useState(false);

  // Forms
  const [addForm, setAddForm] = useState({ full_name: '', email: '', role_id: '', jurisdiction_id: '' });
  const [locForm, setLocForm] = useState({ jurisdiction_id: '' });

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const [res, jRes, rRes] = await Promise.all([
        api.get('/users/department-members/'),
        api.get('/departments/jurisdictions/'),
        api.get('/users/roles/')
      ]);
      setEmployees(Array.isArray(res) ? res : (res.results || []));
      setJurisdictions(Array.isArray(jRes) ? jRes : (jRes.results || []));
      setRoles(Array.isArray(rRes) ? rRes : (rRes.results || []));
    } catch (err) {
      setError(err.message || 'Failed to load department members');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const isDeptAdmin = role === 'department_admin';

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError(null);
    try {
      await api.post('/users/employees/', addForm);
      setShowAddModal(false);
      setAddForm({ full_name: '', email: '', role_id: '', jurisdiction_id: '' });
      fetchEmployees();
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
      fetchEmployees();
    } catch (err) {
      setFormError(err.message || 'Failed to transfer location');
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Department Team</h2>
          <p className="page-subtitle">View employees and supervisors within your department.</p>
        </div>
        {isDeptAdmin && (
          <div className="page-header-actions">
            <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>+ Add Employee</button>
          </div>
        )}
      </div>

      <div className="card">
        {loading && (
          <div className="empty-state">
            <div className="spinner"></div>
            <p>Loading team members...</p>
          </div>
        )}

        {error && (
          <div className="empty-state">
            <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
            <p>{error}</p>
            <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry</button>
          </div>
        )}

        {!loading && !error && employees.length === 0 && (
          <div className="empty-state">
            <p className="empty-state-title">No Team Members Found</p>
            <p>There are currently no employees assigned to this department.</p>
          </div>
        )}

        {!loading && !error && employees.length > 0 && (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Email</th>
                  <th>Status</th>
                  {isDeptAdmin && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {employees.map(emp => (
                  <tr key={emp.id}>
                    <td><strong>{emp.full_name || 'Unknown'}</strong></td>
                    <td style={{ textTransform: 'capitalize' }}>
                      {emp.role_name?.replace(/_/g, ' ') || 'Unknown'}
                    </td>
                    <td>{emp.email || 'N/A'}</td>
                    <td>
                      <StatusBadge status={emp.account_status || 'active'} />
                    </td>
                    {isDeptAdmin && (
                      <td>
                        <button className="btn btn-secondary btn-sm" onClick={() => {
                          setLocForm({ jurisdiction_id: '' });
                          setShowLocModal(emp);
                        }}>Transfer Loc</button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

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
                    {roles.filter(r => r.role_name !== 'system_admin').map(r => <option key={r.id} value={r.id}>{r.role_name.replace(/_/g, ' ')}</option>)}
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
    </div>
  );
}
