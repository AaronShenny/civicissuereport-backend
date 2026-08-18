import React, { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthProvider';
import { api } from '../lib/api';

import CitizenDashboard from './dashboards/CitizenDashboard';
import EmployeeDashboard from './dashboards/EmployeeDashboard';
import SupervisorDashboard from './dashboards/SupervisorDashboard';
import DepartmentAdminDashboard from './dashboards/DepartmentAdminDashboard';
import SystemAdminDashboard from './dashboards/SystemAdminDashboard';

export default function Dashboard() {
  const { profile, role, profileError } = useAuth();
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
      </div>

      {role === 'citizen' && <CitizenDashboard data={data} />}
      {role === 'ground_level_employee' && <EmployeeDashboard data={data} />}
      {role === 'supervisor' && <SupervisorDashboard data={data} />}
      {role === 'department_admin' && <DepartmentAdminDashboard />}
      {role === 'system_admin' && <SystemAdminDashboard />}
    </div>
  );
}
