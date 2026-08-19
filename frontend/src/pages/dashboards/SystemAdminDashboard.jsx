import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import StatCard from '../../components/StatCard';
import { ListSvg, CheckSvg, AlertSvg } from './Shared';

export default function SystemAdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get('/admin/analytics/dashboard/');
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load system analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="empty-state">
        <p>Loading system analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <p className="empty-state-title" style={{ color: 'var(--danger-color)' }}>Error</p>
        <p>{error}</p>
        <button className="btn btn-secondary" onClick={fetchDashboardData} style={{ marginTop: 'var(--sp-md)' }}>Retry</button>
      </div>
    );
  }

  return (
    <>
      <h2 style={{ marginBottom: 'var(--sp-lg)' }}>System Overview</h2>
      
      <div className="grid-4" style={{ marginBottom: 'var(--sp-xl)' }}>
        <StatCard 
          label="Total Users" 
          value={data?.users?.total_users || 0} 
          icon={<svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 00-3-3.87"></path><path d="M16 3.13a4 4 0 010 7.75"></path></svg>} 
          iconBg="rgba(8,27,50,0.06)" 
        />
        <StatCard 
          label="Citizens" 
          value={data?.users?.citizens || 0} 
          icon={<svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>} 
          iconBg="rgba(120,172,233,0.12)" 
        />
        <StatCard 
          label="Employees" 
          value={data?.users?.employees || 0} 
          icon={<WrenchSvg size={24} />} 
          iconBg="rgba(248,220,93,0.18)" 
        />
        <StatCard 
          label="Total Complaints" 
          value={data?.summary?.total || 0} 
          icon={<ListSvg size={24} />} 
          iconBg="rgba(45,183,128,0.12)" 
        />
      </div>

      <div className="grid-3" style={{ marginBottom: 'var(--sp-xl)' }}>
        <StatCard 
          label="Pending Complaints" 
          value={data?.summary?.pending || 0} 
          icon={<AlertSvg size={24} />} 
          iconBg="rgba(248,220,93,0.18)" 
        />
        <StatCard 
          label="Resolved Complaints" 
          value={data?.summary?.resolved || 0} 
          icon={<CheckSvg size={24} />} 
          iconBg="rgba(45,183,128,0.12)" 
        />
        <StatCard 
          label="Avg Resolution Time" 
          value={data?.summary?.avg_resolution_time ? data.summary.avg_resolution_time.split('.')[0] : "N/A"} 
          icon={<svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>} 
          iconBg="rgba(8,27,50,0.06)" 
        />
      </div>

      <div className="grid-2" style={{ marginBottom: 'var(--sp-xl)', gap: 'var(--sp-lg)' }}>
        <div className="card">
          <p className="section-title">Complaints by Department</p>
          {data?.breakdowns?.department?.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {data.breakdowns.department.slice(0, 5).map((dept, i) => (
                <li key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                  <span>{dept.name}</span>
                  <strong>{dept.count}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state" style={{ minHeight: '150px' }}>
               <p className="empty-state-title" style={{ fontSize: '0.875rem' }}>No data</p>
            </div>
          )}
        </div>

        <div className="card">
          <p className="section-title">Complaints by Category</p>
          {data?.breakdowns?.category?.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {data.breakdowns.category.slice(0, 5).map((cat, i) => (
                <li key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                  <span>{cat.name}</span>
                  <strong>{cat.count}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state" style={{ minHeight: '150px' }}>
               <p className="empty-state-title" style={{ fontSize: '0.875rem' }}>No data</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

// Inline component for WrenchSvg missing from Shared in this scope
function WrenchSvg({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
    </svg>
  );
}
