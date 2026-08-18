import React from 'react';
import { useNavigate } from 'react-router-dom';
import StatCard from '../../components/StatCard';
import StatusBadge from '../../components/StatusBadge';
import { PENDING_STATUSES, IN_PROGRESS_STATUSES, RESOLVED_STATUSES, ListSvg, AlertSvg, WrenchSvg, CheckSvg } from './Shared';

export default function CitizenDashboard({ data }) {
  const navigate = useNavigate();

  return (
    <>
      <div className="grid-4" style={{ marginBottom: 'var(--sp-xl)' }}>
        {data?.complaints && (
          <>
            <StatCard 
              label="Total Reported" 
              value={data.complaints.length} 
              icon={<ListSvg size={24} />} 
              iconBg="rgba(8,27,50,0.06)" 
            />
            <StatCard 
              label="Pending" 
              value={data.complaints.filter(c => PENDING_STATUSES.includes(c.status)).length} 
              icon={<AlertSvg size={24} />} 
              iconBg="rgba(248,220,93,0.18)" 
            />
            <StatCard 
              label="In Progress" 
              value={data.complaints.filter(c => IN_PROGRESS_STATUSES.includes(c.status)).length} 
              icon={<WrenchSvg size={24} />} 
              iconBg="rgba(120,172,233,0.12)" 
            />
            <StatCard 
              label="Resolved/Closed" 
              value={data.complaints.filter(c => RESOLVED_STATUSES.includes(c.status)).length} 
              icon={<CheckSvg size={24} />} 
              iconBg="rgba(45,183,128,0.12)" 
            />
          </>
        )}
      </div>

      {data?.complaints?.length === 0 && (
        <div className="card empty-state" style={{ marginBottom: 'var(--sp-xl)' }}>
          <p className="empty-state-title">No complaints yet.</p>
          <p>You haven't reported any civic issues.</p>
          <button className="btn btn-primary" style={{ marginTop: 'var(--sp-sm)' }} onClick={() => navigate('/complaints/new')}>
            Report an Issue
          </button>
        </div>
      )}

      {data?.complaints?.length > 0 && (
        <div className="card" style={{ marginBottom: 'var(--sp-xl)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-md)' }}>
            <p className="section-title" style={{ margin: 0 }}>Recent Complaints</p>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/complaints')}>View All</button>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Complaint ID</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>District/Location</th>
                  <th>Submitted</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {data.complaints.slice(0, 5).map((c) => (
                  <tr key={c.id}>
                    <td>{c.complaint_number || 'N/A'}</td>
                    <td>{c.category_name || 'Issue'}</td>
                    <td><StatusBadge status={c.status} /></td>
                    <td>{c.district || c.location_address || 'N/A'}</td>
                    <td>{new Date(c.submitted_at).toLocaleDateString()}</td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/complaints/${c.id}`)}>
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card">
        <p className="section-title">Quick Actions</p>
        <div style={{ display: 'flex', gap: 'var(--sp-md)', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={() => navigate('/complaints')}>
            View My Complaints
          </button>
        </div>
      </div>
    </>
  );
}
