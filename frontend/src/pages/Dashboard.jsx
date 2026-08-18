import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { api } from '../lib/api';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';

const PENDING_STATUSES = ['submitted', 'under_verification', 'assigned', 'verified'];
const IN_PROGRESS_STATUSES = ['in_progress'];
const RESOLVED_STATUSES = ['resolved', 'closed'];

export default function Dashboard() {
  const { profile, role, profileError } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadDashboardData() {
      if (!role) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        if (role === 'citizen') {
          const res = await api.get('/complaints/');
          const complaints = Array.isArray(res) ? res : (res.results || []);
          setData({ complaints });
        } else if (role === 'ground_level_employee') {
          const res = await api.get('/employee/complaints/');
          const assigned = Array.isArray(res) ? res : (res.results || []);
          setData({ assigned });
        } else if (role === 'supervisor') {
          const res = await api.get('/supervisor/complaints/unassigned/');
          const unassigned = Array.isArray(res) ? res : (res.results || []);
          setData({ unassigned });
        } else {
          // system_admin or department_admin
          setData({});
        }
      } catch (err) {
        setError(err.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, [role]);

  if (profileError) {
    return (
      <div className="empty-state">
        <p className="empty-state-title" style={{ color: 'var(--error)' }}>Session Error</p>
        <p>{profileError}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Reload Page</button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner"></div>
        <p>Loading your dashboard...</p>
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

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Welcome back, {profile?.full_name?.split(' ')[0] || 'User'} 👋</h2>
          <p className="page-subtitle">Here is your CivicConnect overview.</p>
        </div>
        {role === 'citizen' && (
          <div className="page-header-right">
            <button className="btn btn-primary" onClick={() => navigate('/complaints/new')}>
              Report an Issue
            </button>
          </div>
        )}
      </div>

      <div className="grid-4" style={{ marginBottom: 'var(--sp-xl)' }}>
        {role === 'citizen' && data?.complaints && (
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

        {role === 'ground_level_employee' && data?.assigned && (
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

        {role === 'supervisor' && data?.unassigned && (
          <>
            <StatCard 
              label="Requires Assignment" 
              value={data.unassigned.length} 
              icon={<AlertSvg size={24} />} 
              iconBg="rgba(235,44,80,0.10)" 
            />
          </>
        )}
      </div>

      {role === 'citizen' && data?.complaints?.length === 0 && (
        <div className="card empty-state" style={{ marginBottom: 'var(--sp-xl)' }}>
          <p className="empty-state-title">No complaints yet.</p>
          <p>You haven't reported any civic issues.</p>
          <button className="btn btn-primary" style={{ marginTop: 'var(--sp-sm)' }} onClick={() => navigate('/complaints/new')}>
            Report an Issue
          </button>
        </div>
      )}

      {role === 'citizen' && data?.complaints?.length > 0 && (
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

      {/* Quick Access Area */}
      <div className="card">
        <p className="section-title">Quick Actions</p>
        <div style={{ display: 'flex', gap: 'var(--sp-md)', flexWrap: 'wrap' }}>
          {role === 'citizen' && (
            <button className="btn btn-secondary" onClick={() => navigate('/complaints')}>
              View My Complaints
            </button>
          )}
          {role === 'ground_level_employee' && (
            <button className="btn btn-secondary" onClick={() => navigate('/employee/complaints')}>
              View My Work Queue
            </button>
          )}
          {role === 'supervisor' && (
            <>
              <button className="btn btn-primary" onClick={() => navigate('/supervisor/unassigned')}>
                Assign Complaints
              </button>
              <button className="btn btn-secondary" onClick={() => navigate('/supervisor/complaints')}>
                View Department Queue
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Icons
function ListSvg({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>;
}
function InboxSvg({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>;
}
function AlertSvg({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>;
}

function WrenchSvg({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>;
}
function CheckSvg({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>;
}
