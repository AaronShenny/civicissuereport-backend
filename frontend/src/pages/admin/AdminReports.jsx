import React, { useState, useEffect } from 'react';
import { useAuth } from '../../auth/AuthProvider';
import { api } from '../../lib/api';

export default function AdminReports() {
  const { role, departmentId } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    category: '',
    department: '',
    district: ''
  });

  const [categories, setCategories] = useState([]);
  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    fetchMetadata();
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [filters]);

  const fetchMetadata = async () => {
    try {
      const [catsRes, deptsRes] = await Promise.all([
        api.get('/api/v1/categories/'),
        api.get('/api/v1/departments/')
      ]);
      setCategories(catsRes.data);
      setDepartments(deptsRes.data);
    } catch (err) {
      console.error('Failed to fetch metadata', err);
    }
  };

  const fetchAnalytics = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, val]) => {
        if (val) params.append(key, val);
      });
      const res = await api.get(`/api/v1/admin/reports/analytics/?${params.toString()}`);
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError('Failed to load reports data.');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const handleExport = async (format) => {
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, val]) => {
        if (val) params.append(key, val);
      });
      params.append('format', format);

      const res = await api.get(`/api/v1/admin/reports/export/?${params.toString()}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `civic_report.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export failed', err);
      alert('Failed to export report.');
    }
  };

  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Reports & Analytics</h2>
          <p className="page-subtitle">Export and view system-wide statistics</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-secondary" onClick={() => handleExport('pdf')}>Export PDF</button>
          <button className="btn btn-secondary" onClick={() => handleExport('xlsx')}>Export Excel</button>
        </div>
      </div>

      <div className="card filters-card" style={{ padding: '1rem', marginBottom: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <label className="form-label" style={{ fontSize: '0.8rem' }}>Start Date</label>
          <input type="date" className="form-input" name="start_date" value={filters.start_date} onChange={handleFilterChange} />
        </div>
        <div>
          <label className="form-label" style={{ fontSize: '0.8rem' }}>End Date</label>
          <input type="date" className="form-input" name="end_date" value={filters.end_date} onChange={handleFilterChange} />
        </div>
        <div>
          <label className="form-label" style={{ fontSize: '0.8rem' }}>Category</label>
          <select className="form-select" name="category" value={filters.category} onChange={handleFilterChange}>
            <option value="">All Categories</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        
        {role === 'system_admin' && (
          <div>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Department</label>
            <select className="form-select" name="department" value={filters.department} onChange={handleFilterChange}>
              <option value="">All Departments</option>
              {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
        )}
        
        <div>
          <label className="form-label" style={{ fontSize: '0.8rem' }}>District</label>
          <input type="text" className="form-input" name="district" placeholder="District name" value={filters.district} onChange={handleFilterChange} />
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading && !data ? (
        <p>Loading analytics...</p>
      ) : data ? (
        <>
          <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            <div className="stat-card">
              <div className="stat-value">{data.summary.total}</div>
              <div className="stat-label">Total Complaints</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.summary.pending}</div>
              <div className="stat-label">Pending</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.summary.resolved}</div>
              <div className="stat-label">Resolved / Closed</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.summary.invalid}</div>
              <div className="stat-label">Invalid / Rejected</div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: '1.5rem', padding: '1.5rem' }}>
            <h3>Average Resolution Time</h3>
            <p style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
              {data.summary.avg_resolution_time ? data.summary.avg_resolution_time : 'N/A'}
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div className="card" style={{ padding: '1.5rem' }}>
              <h3>By Category</h3>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {data.breakdowns.category.map((c, i) => (
                  <li key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                    <span>{c.name}</span>
                    <span style={{ fontWeight: 'bold' }}>{c.count}</span>
                  </li>
                ))}
                {data.breakdowns.category.length === 0 && <li>No data</li>}
              </ul>
            </div>
            
            <div className="card" style={{ padding: '1.5rem' }}>
              <h3>By Priority</h3>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {data.breakdowns.priority.map((p, i) => (
                  <li key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                    <span>{p.name.toUpperCase()}</span>
                    <span style={{ fontWeight: 'bold' }}>{p.count}</span>
                  </li>
                ))}
                {data.breakdowns.priority.length === 0 && <li>No data</li>}
              </ul>
            </div>

            {role === 'system_admin' && (
              <div className="card" style={{ padding: '1.5rem', gridColumn: '1 / -1' }}>
                <h3>By Department</h3>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {data.breakdowns.department.map((d, i) => (
                    <li key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                      <span>{d.name}</span>
                      <span style={{ fontWeight: 'bold' }}>{d.count}</span>
                    </li>
                  ))}
                  {data.breakdowns.department.length === 0 && <li>No data</li>}
                </ul>
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}
