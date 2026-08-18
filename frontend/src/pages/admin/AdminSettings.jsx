import React from 'react';

export default function AdminSettings() {
  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Settings</h2>
          <p className="page-subtitle">Global system configuration</p>
        </div>
      </div>

      <div className="empty-state">
        <p className="empty-state-title">Backend API Required</p>
        <p>Global system configuration management is currently pending backend implementation.</p>
      </div>
    </div>
  );
}
