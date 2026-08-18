import React from 'react';

export default function AdminReports() {
  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Reports</h2>
          <p className="page-subtitle">Export and view system-wide analytics</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-secondary" disabled>Export PDF</button>
          <button className="btn btn-secondary" disabled>Export Excel</button>
        </div>
      </div>

      <div className="empty-state">
        <p className="empty-state-title">Backend API Required</p>
        <p>Reporting and export endpoints are currently pending backend implementation. Buttons have been disabled.</p>
      </div>
    </div>
  );
}
