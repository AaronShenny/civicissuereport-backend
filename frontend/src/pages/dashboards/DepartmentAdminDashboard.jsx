import React from 'react';
import { useNavigate } from 'react-router-dom';
import StatCard from '../../components/StatCard';
import { ListSvg, AlertSvg, WrenchSvg, CheckSvg } from './Shared';

export default function DepartmentAdminDashboard() {
  const navigate = useNavigate();

  return (
    <>
      <div className="grid-4" style={{ marginBottom: 'var(--sp-xl)' }}>
        <StatCard 
          label="Total Complaints" 
          value="--" 
          icon={<ListSvg size={24} />} 
          iconBg="rgba(8,27,50,0.06)" 
        />
        <StatCard 
          label="Pending" 
          value="--" 
          icon={<AlertSvg size={24} />} 
          iconBg="rgba(248,220,93,0.18)" 
        />
        <StatCard 
          label="In Progress" 
          value="--" 
          icon={<WrenchSvg size={24} />} 
          iconBg="rgba(120,172,233,0.12)" 
        />
        <StatCard 
          label="Resolved" 
          value="--" 
          icon={<CheckSvg size={24} />} 
          iconBg="rgba(45,183,128,0.12)" 
        />
      </div>
      
      <div className="empty-state" style={{ marginBottom: 'var(--sp-xl)', padding: 'var(--sp-lg)' }}>
        <p className="empty-state-title" style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>
          Data Unavailable (API Pending)
        </p>
        <p style={{ fontSize: '0.875rem' }}>
          Aggregate statistics and department performance metrics will appear here once backend analytics endpoints are implemented.
        </p>
      </div>

      <div className="grid-2" style={{ marginBottom: 'var(--sp-xl)', gap: 'var(--sp-lg)' }}>
        <div className="card">
          <p className="section-title">Priority Breakdown</p>
          <div className="empty-state" style={{ minHeight: '150px' }}>
             <p className="empty-state-title" style={{ fontSize: '0.875rem' }}>Data Unavailable</p>
          </div>
        </div>
        <div className="card">
          <p className="section-title">Category Breakdown</p>
          <div className="empty-state" style={{ minHeight: '150px' }}>
             <p className="empty-state-title" style={{ fontSize: '0.875rem' }}>Data Unavailable</p>
          </div>
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
                <th>Assigned</th>
                <th>In Progress</th>
                <th>Resolved</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan="4" className="text-center" style={{ padding: 'var(--sp-lg)', color: 'var(--text-muted)' }}>
                  Workload data unavailable (API pending)
                </td>
              </tr>
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
