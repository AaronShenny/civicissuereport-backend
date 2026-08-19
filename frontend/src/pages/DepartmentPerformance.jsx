import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthProvider';
import { api } from '../lib/api';

export default function DepartmentPerformance() {
  const { profile } = useAuth();
  const [performance, setPerformance] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [category, setCategory] = useState('');
  const [district, setDistrict] = useState('');
  const [priority, setPriority] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    async function loadInitialData() {
      try {
        const catRes = await api.get('/categories/');
        setCategories(Array.isArray(catRes) ? catRes : (catRes.results || []));
      } catch (err) {
        console.error('Failed to load categories', err);
      }
    }
    loadInitialData();
  }, []);

  useEffect(() => {
    if (profile?.department_id) {
      fetchPerformance();
    }
  }, [profile, startDate, endDate, category, district, priority, statusFilter]);

  const fetchPerformance = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (category) params.category = category;
      if (district) params.district = district;
      if (priority) params.priority = priority;
      if (statusFilter) params.status = statusFilter;

      const res = await api.get(`/admin/departments/${profile.department_id}/performance/`, params);
      setPerformance(res);
    } catch (err) {
      setError(err.message || 'Failed to load performance metrics');
    } finally {
      setLoading(false);
    }
  };

  // Helper to format duration string
  const formatDuration = (durationStr) => {
    if (!durationStr) return 'N/A';
    // Format "d days, h:mm:ss" or "h:mm:ss" nicely
    const parts = durationStr.split('.');
    let timeStr = parts[0];
    if (timeStr.includes('days') || timeStr.includes('day')) {
      return timeStr;
    }
    const timeParts = timeStr.split(':');
    if (timeParts.length >= 3) {
      const hours = parseInt(timeParts[0], 10);
      const minutes = parseInt(timeParts[1], 10);
      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    }
    return timeStr;
  };

  return (
    <div className="performance-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Department Performance</h2>
          <p className="page-subtitle">Analytics and workload metrics across your department</p>
        </div>
      </div>

      {/* Filters Card */}
      <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
        <p className="section-title">Filters</p>
        <div className="grid-4" style={{ gap: 'var(--sp-md)' }}>
          <div className="form-group">
            <label className="form-label">Start Date</label>
            <input type="date" className="form-control" value={startDate} onChange={e => setStartDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">End Date</label>
            <input type="date" className="form-control" value={endDate} onChange={e => setEndDate(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Category</label>
            <select className="form-control" value={category} onChange={e => setCategory(e.target.value)}>
              <option value="">All Categories</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Priority</label>
            <select className="form-control" value={priority} onChange={e => setPriority(e.target.value)}>
              <option value="">All Priorities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
        <div className="grid-2" style={{ gap: 'var(--sp-md)', marginTop: 'var(--sp-md)' }}>
          <div className="form-group">
            <label className="form-label">District</label>
            <input type="text" className="form-control" placeholder="e.g. Ernakulam" value={district} onChange={e => setDistrict(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Status</label>
            <select className="form-control" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
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
        </div>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="spinner"></div>
          <p>Loading performance statistics...</p>
        </div>
      ) : error ? (
        <div className="empty-state">
          <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
          <p>{error}</p>
        </div>
      ) : !performance ? (
        <div className="empty-state">
          <p>No performance data available.</p>
        </div>
      ) : (
        <>
          {/* Overview Cards */}
          <div className="grid-4" style={{ marginBottom: 'var(--sp-lg)', gap: 'var(--sp-md)' }}>
            <div className="card text-center" style={{ padding: 'var(--sp-md)' }}>
              <p className="sidebar-section-label" style={{ margin: 0 }}>Total Complaints</p>
              <h2 style={{ margin: '0.5rem 0', fontSize: '2rem' }}>{performance.volume.total}</h2>
              <p className="text-muted" style={{ fontSize: '0.75rem', margin: 0 }}>Week: {performance.volume.week} | Month: {performance.volume.month}</p>
            </div>
            <div className="card text-center" style={{ padding: 'var(--sp-md)' }}>
              <p className="sidebar-section-label" style={{ margin: 0 }}>Pending / Active</p>
              <h2 style={{ margin: '0.5rem 0', fontSize: '2rem', color: 'var(--warning)' }}>{performance.volume.pending}</h2>
              <p className="text-muted" style={{ fontSize: '0.75rem', margin: 0 }}>In Progress: {performance.volume.in_progress}</p>
            </div>
            <div className="card text-center" style={{ padding: 'var(--sp-md)' }}>
              <p className="sidebar-section-label" style={{ margin: 0 }}>Successfully Resolved</p>
              <h2 style={{ margin: '0.5rem 0', fontSize: '2rem', color: 'var(--success)' }}>{performance.volume.resolved + performance.volume.closed}</h2>
              <p className="text-muted" style={{ fontSize: '0.75rem', margin: 0 }}>Closed: {performance.volume.closed}</p>
            </div>
            <div className="card text-center" style={{ padding: 'var(--sp-md)' }}>
              <p className="sidebar-section-label" style={{ margin: 0 }}>Invalid / Rejected</p>
              <h2 style={{ margin: '0.5rem 0', fontSize: '2rem', color: 'var(--error)' }}>{performance.volume.invalid}</h2>
              <p className="text-muted" style={{ fontSize: '0.75rem', margin: 0 }}>Excluded from resolution rate</p>
            </div>
          </div>

          {/* Resolution Duration Metrics */}
          <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
            <p className="section-title">Resolution Speed & On-Time Performance</p>
            <div className="grid-4" style={{ gap: 'var(--sp-md)' }}>
              <div style={{ textAlign: 'center' }}>
                <p className="sidebar-section-label">Average Resolution Time</p>
                <h3>{formatDuration(performance.resolution_performance.avg_resolution_time)}</h3>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p className="sidebar-section-label">Fastest Resolution</p>
                <h3 style={{ color: 'var(--success)' }}>{formatDuration(performance.resolution_performance.fastest_resolution)}</h3>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p className="sidebar-section-label">Slowest Resolution</p>
                <h3 style={{ color: 'var(--error)' }}>{formatDuration(performance.resolution_performance.slowest_resolution)}</h3>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p className="sidebar-section-label">Resolved On Time</p>
                <h3>
                  {performance.resolution_performance.total_with_expected > 0 ? (
                    <>
                      {Math.round((performance.resolution_performance.resolved_on_time / performance.resolution_performance.total_with_expected) * 100)}%
                      <span className="text-muted" style={{ fontSize: '0.75rem', display: 'block', fontWeight: 'normal' }}>
                        ({performance.resolution_performance.resolved_on_time} / {performance.resolution_performance.total_with_expected} complaints)
                      </span>
                    </>
                  ) : 'N/A'}
                </h3>
              </div>
            </div>
          </div>

          {/* Breakdowns */}
          <div className="grid-3" style={{ marginBottom: 'var(--sp-lg)', gap: 'var(--sp-md)' }}>
            <div className="card">
              <p className="section-title">Priority Distribution</p>
              <table className="table mini-table">
                <thead>
                  <tr>
                    <th>Priority</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(performance.priority_breakdown).map(([p, count]) => (
                    <tr key={p}>
                      <td style={{ textTransform: 'capitalize' }}>{p}</td>
                      <td><strong>{count}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card">
              <p className="section-title">Category Distribution</p>
              <table className="table mini-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(performance.category_breakdown).map(([cat, count]) => (
                    <tr key={cat}>
                      <td>{cat}</td>
                      <td><strong>{count}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card">
              <p className="section-title">District Distribution</p>
              <table className="table mini-table">
                <thead>
                  <tr>
                    <th>District</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(performance.district_breakdown).map(([dist, count]) => (
                    <tr key={dist}>
                      <td>{dist}</td>
                      <td><strong>{count}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Employee Workload Table */}
          <div className="card">
            <p className="section-title">Employee Workload & Performance</p>
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Employee Name</th>
                    <th>Role</th>
                    <th>Assigned</th>
                    <th>In Progress</th>
                    <th>Resolved</th>
                    <th>Closed</th>
                    <th>Invalid</th>
                    <th>Avg Resolution Speed</th>
                  </tr>
                </thead>
                <tbody>
                  {performance.employee_workload.length > 0 ? (
                    performance.employee_workload.map((emp, i) => (
                      <tr key={i}>
                        <td><strong>{emp.name}</strong></td>
                        <td style={{ textTransform: 'capitalize' }}>{emp.role.replace(/_/g, ' ')}</td>
                        <td>{emp.assigned}</td>
                        <td>{emp.in_progress}</td>
                        <td>{emp.resolved}</td>
                        <td>{emp.closed}</td>
                        <td>{emp.invalid}</td>
                        <td>{formatDuration(emp.avg_resolution_time)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="8" className="text-center" style={{ color: 'var(--text-muted)' }}>
                        No employees found in this department.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
