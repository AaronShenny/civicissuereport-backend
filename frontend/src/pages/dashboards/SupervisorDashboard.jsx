import React from 'react';
import { useNavigate } from 'react-router-dom';
import StatCard from '../../components/StatCard';
import { AlertSvg } from './Shared';

export default function SupervisorDashboard({ data }) {
  const navigate = useNavigate();

  return (
    <>
      <div className="grid-4" style={{ marginBottom: 'var(--sp-xl)' }}>
        {data?.unassigned && (
          <StatCard 
            label="Requires Assignment" 
            value={data.unassigned.length} 
            icon={<AlertSvg size={24} />} 
            iconBg="rgba(235,44,80,0.10)" 
          />
        )}
      </div>
      <div className="card">
        <p className="section-title">Quick Actions</p>
        <div style={{ display: 'flex', gap: 'var(--sp-md)', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => navigate('/supervisor/unassigned')}>
            Assign Complaints
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/supervisor/complaints')}>
            View Department Queue
          </button>
        </div>
      </div>
    </>
  );
}
