import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import StatCard from '../../components/StatCard';
import { ListSvg, AlertSvg, WrenchSvg, CheckSvg } from './Shared';

export default function DepartmentAdminDashboard() {
  const navigate = useNavigate();
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
      setError(err.message || 'Failed to load department analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="empty-state">
        <p>Loading department analytics...</p>
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
      <div className="grid-4" style={{ marginBottom: 'var(--sp-xl)' }}>
        <StatCard 
          label="Total Complaints" 
          value={data?.summary?.total || 0} 
          icon={<ListSvg size={24} />} 
          iconBg="rgba(8,27,50,0.06)" 
        />
        <StatCard 
          label="Pending" 
          value={data?.summary?.pending || 0} 
          icon={<AlertSvg size={24} />} 
          iconBg="rgba(248,220,93,0.18)" 
        />
        <StatCard 
          label="In Progress" 
          value={data?.summary?.in_progress || 0} 
          icon={<WrenchSvg size={24} />} 
          iconBg="rgba(120,172,233,0.12)" 
        />
        <StatCard 
          label="Resolved" 
          value={data?.summary?.resolved || 0} 
          icon={<CheckSvg size={24} />} 
          iconBg="rgba(45,183,128,0.12)" 
        />
      </div>

      <div className="grid-2" style={{ marginBottom: 'var(--sp-xl)', gap: 'var(--sp-lg)' }}>
        <div className="card">
          <p className="section-title">Priority Breakdown</p>
          {data?.breakdowns?.priority?.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {data.breakdowns.priority.map((p, i) => (
                <li key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                  <span>{p.name}</span>
                  <strong>{p.count}</strong>
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
          <p className="section-title">Category Breakdown</p>
          {data?.breakdowns?.category?.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {data.breakdowns.category.map((cat, i) => (
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

      <div className="card" style={{ marginBottom: 'var(--sp-xl)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-md)' }}>
          <p className="section-title" style={{ margin: 0 }}>Employee Workload / Performance</p>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/department/employees')}>View Team</button>
        </div>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Assigned (Pending)</th>
                <th>In Progress</th>
                <th>Resolved/Closed</th>
              </tr>
            </thead>
            <tbody>
              {data?.workload?.length > 0 ? (
                data.workload.map((emp, i) => (
                  <tr key={i}>
                    <td>{emp.full_name}</td>
                    <td>{emp.assigned}</td>
                    <td>{emp.in_progress}</td>
                    <td>{emp.resolved}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="text-center" style={{ padding: 'var(--sp-lg)', color: 'var(--text-muted)' }}>
                    No employee workload data found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <p className="section-title">Quick Actions</p>
        <div style={{ display: 'flex', gap: 'var(--sp-md)', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => navigate('/department/complaints')}>
            View Department Complaints
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/department/employees')}>
            Manage Team
          </button>
        </div>
      </div>
    </>
  );
}
