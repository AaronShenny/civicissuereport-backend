import React from 'react';
import { useNavigate } from 'react-router-dom';
import StatCard from '../../components/StatCard';
import { PENDING_STATUSES, IN_PROGRESS_STATUSES, InboxSvg, AlertSvg, WrenchSvg } from './Shared';

export default function EmployeeDashboard({ data }) {
  const navigate = useNavigate();

  return (
    <>
      <div className="grid-4" style={{ marginBottom: 'var(--sp-xl)' }}>
        {data?.assigned && (
          <>
            <StatCard 
              label="Total Assigned" 
              value={data.assigned.length} 
              icon={<InboxSvg size={24} />} 
              iconBg="rgba(8,27,50,0.06)" 
            />
            <StatCard 
              label="Pending My Action" 
              value={data.assigned.filter(c => PENDING_STATUSES.includes(c.status)).length} 
              icon={<AlertSvg size={24} />} 
              iconBg="rgba(248,220,93,0.18)" 
            />
            <StatCard 
              label="In Progress" 
              value={data.assigned.filter(c => IN_PROGRESS_STATUSES.includes(c.status)).length} 
              icon={<WrenchSvg size={24} />} 
              iconBg="rgba(120,172,233,0.12)" 
            />
          </>
        )}
      </div>
      <div className="card">
        <p className="section-title">Quick Actions</p>
        <div style={{ display: 'flex', gap: 'var(--sp-md)', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={() => navigate('/employee/complaints')}>
            View My Work Queue
          </button>
        </div>
      </div>
    </>
  );
}
