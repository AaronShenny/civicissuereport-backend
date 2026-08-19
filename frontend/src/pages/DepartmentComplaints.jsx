import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';

export default function DepartmentComplaints() {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters state
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [category, setCategory] = useState('');

  // Fetch categories on mount
  useEffect(() => {
    async function loadCategories() {
      try {
        const res = await api.get('/categories/');
        setCategories(Array.isArray(res) ? res : (res.results || []));
      } catch (err) {
        console.error('Failed to load categories', err);
      }
    }
    loadCategories();
  }, []);

  // Fetch complaints on filter change
  const fetchComplaints = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (status) params.status = status;
      if (priority) params.priority = priority;
      if (category) params.category = category;

      const queryString = new URLSearchParams(params).toString();
      const endpoint = `/admin/department/complaints/${queryString ? `?${queryString}` : ''}`;
      const res = await api.get(endpoint);
      setComplaints(Array.isArray(res) ? res : (res.results || []));
    } catch (err) {
      setError(err.message || 'Failed to load department complaints');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchComplaints();
    }, search ? 300 : 0);

    return () => clearTimeout(delayDebounceFn);
  }, [search, status, priority, category]);

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Department Complaints</h2>
          <p className="page-subtitle">View and manage all issues routed to your department.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
        <div style={{ display: 'flex', gap: 'var(--sp-md)', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: 2, minWidth: '200px' }}>
            <label className="form-label">Search</label>
            <input 
              type="text" 
              className="form-control" 
              placeholder="Search ID, address, description..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ flex: 1, minWidth: '150px' }}>
            <label className="form-label">Status</label>
            <select className="form-control" value={status} onChange={e => setStatus(e.target.value)}>
              <option value="">All Statuses</option>
              <option value="submitted">Submitted</option>
              <option value="under_verification">Under Verification</option>
              <option value="assigned">Assigned</option>
              <option value="verified">Verified</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
              <option value="invalid">Invalid</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1, minWidth: '150px' }}>
            <label className="form-label">Priority</label>
            <select className="form-control" value={priority} onChange={e => setPriority(e.target.value)}>
              <option value="">All Priorities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1, minWidth: '150px' }}>
            <label className="form-label">Category</label>
            <select className="form-control" value={category} onChange={e => setCategory(e.target.value)}>
              <option value="">All Categories</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div className="empty-state" style={{ padding: 'var(--sp-xl)' }}>
            <div className="spinner"></div>
            <p>Loading complaints...</p>
          </div>
        ) : error ? (
          <div className="empty-state" style={{ padding: 'var(--sp-xl)' }}>
            <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
            <p>{error}</p>
            <button className="btn btn-primary" onClick={fetchComplaints}>Retry</button>
          </div>
        ) : complaints.length === 0 ? (
          <div className="empty-state" style={{ padding: 'var(--sp-xl)' }}>
            <p className="empty-state-title">No complaints found</p>
            <p>No issues match the selected filter criteria.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Complaint ID</th>
                  <th>Category</th>
                  <th>District</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Assigned To</th>
                  <th>Submitted</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {complaints.map(c => (
                  <tr key={c.id}>
                    <td>
                      <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-secondary)', background: 'var(--surface-muted)', padding: '2px 6px', borderRadius: 4 }}>
                        {c.complaint_number || c.id.substring(0, 8)}
                      </span>
                    </td>
                    <td><strong>{c.category_name}</strong></td>
                    <td>{c.district || 'N/A'}</td>
                    <td><PriorityBadge priority={c.priority_category} /></td>
                    <td><StatusBadge status={c.status} /></td>
                    <td>{c.assigned_employee_name || <span style={{ color: 'var(--text-muted)' }}>Unassigned</span>}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>
                      {new Date(c.submitted_at).toLocaleDateString()}
                    </td>
                    <td>
                      <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/complaints/${c.id}`)}>
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
