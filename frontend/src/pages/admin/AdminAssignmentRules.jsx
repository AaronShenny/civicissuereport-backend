import React from 'react';

export default function AdminAssignmentRules() {
  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Assignment Rules</h2>
          <p className="page-subtitle">Configure department and category routing</p>
        </div>
      </div>

      <div className="empty-state">
        <p className="empty-state-title">Backend API Required</p>
        <p>Dynamic routing rule management is currently pending backend implementation. The routing logic is currently handled directly by the backend rule engine.</p>
      </div>
    </div>
  );
}
