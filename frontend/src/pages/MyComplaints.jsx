import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import StatusBadge from '../components/StatusBadge';

export default function MyComplaints() {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');

  useEffect(() => {
    const fetchComplaints = async () => {
      try {
        setLoading(true);
        const res = await api.get('/complaints/');
        setComplaints(Array.isArray(res) ? res : (res.results || []));
      } catch (err) {
        setError(err.data?.detail || err.message || 'Failed to load complaints.');
      } finally {
        setLoading(false);
      }
    };
    fetchComplaints();
  }, []);

  const categories = useMemo(() => {
    const cats = new Set(complaints.map(c => c.category_name).filter(Boolean));
    return ['All', ...Array.from(cats).sort()];
  }, [complaints]);

  const filteredComplaints = useMemo(() => {
    return complaints.filter(c => {
      if (statusFilter !== 'All' && c.status !== statusFilter) {
        return false;
      }
      if (categoryFilter !== 'All' && c.category_name !== categoryFilter) {
        return false;
      }
      if (search) {
        const query = search.toLowerCase();
        const matchNumber = c.complaint_number?.toLowerCase().includes(query);
        const matchCategory = c.category_name?.toLowerCase().includes(query);
        const matchDistrict = c.district?.toLowerCase().includes(query) || c.location_address?.toLowerCase().includes(query);
        if (!matchNumber && !matchCategory && !matchDistrict) return false;
      }
      return true;
    });
  }, [complaints, search, statusFilter, categoryFilter]);

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner"></div>
        <p>Loading complaints...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  if (complaints.length === 0) {
    return (
      <div className="empty-state">
        <p className="empty-state-title">No complaints found</p>
        <p>You haven't reported any civic issues yet.</p>
        <button className="btn btn-primary" style={{ marginTop: 'var(--sp-sm)' }} onClick={() => navigate('/complaints/new')}>
          Report an Issue
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">My Complaints</h2>
          <p className="page-subtitle">Track and manage the issues you've reported.</p>
        </div>
        <div className="page-header-right">
          <button className="btn btn-primary" onClick={() => navigate('/complaints/new')}>
            Report an Issue
          </button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
        <div style={{ display: 'flex', gap: 'var(--sp-md)', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 200px' }}>
            <label className="form-label" style={{ fontSize: 12 }}>Search</label>
            <input 
              type="text" 
              className="form-control" 
              placeholder="Number, Category, District..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div style={{ flex: '0 0 180px' }}>
            <label className="form-label" style={{ fontSize: 12 }}>Status</label>
            <select className="form-control" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="All">All Statuses</option>
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
          <div style={{ flex: '0 0 180px' }}>
            <label className="form-label" style={{ fontSize: 12 }}>Category</label>
            <select className="form-control" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {/* Desktop Table View */}
        <div className="table-container desktop-only">
          <table className="table" style={{ width: '100%' }}>
            <thead>
              <tr>
                <th>Complaint</th>
                <th>Category</th>
                <th>Status</th>
                <th>District</th>
                <th>Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredComplaints.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: 'var(--sp-xl)', color: 'var(--text-muted)' }}>
                    No complaints match your filters.
                  </td>
                </tr>
              ) : (
                filteredComplaints.map(c => (
                  <tr key={c.id}>
                    <td style={{ fontWeight: 500 }}>{c.complaint_number || 'N/A'}</td>
                    <td>{c.category_name || 'Issue'}</td>
                    <td><StatusBadge status={c.status} /></td>
                    <td>{c.district || c.location_address || 'N/A'}</td>
                    <td>{new Date(c.submitted_at).toLocaleDateString()}</td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/complaints/${c.id}`)}>
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile Card View */}
        <div className="mobile-only" style={{ padding: 'var(--sp-md)' }}>
          {filteredComplaints.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 'var(--sp-xl)', color: 'var(--text-muted)' }}>
              No complaints match your filters.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
              {filteredComplaints.map(c => (
                <div 
                  key={c.id} 
                  style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 'var(--sp-md)', cursor: 'pointer' }}
                  onClick={() => navigate(`/complaints/${c.id}`)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ fontWeight: 'bold' }}>{c.complaint_number || 'N/A'}</span>
                    <StatusBadge status={c.status} />
                  </div>
                  <p style={{ fontWeight: 500 }}>{c.category_name || 'Issue'}</p>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>
                    {c.district || c.location_address || 'N/A'}
                  </p>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {new Date(c.submitted_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
