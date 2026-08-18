import React from 'react';

export default function DepartmentComplaints() {
  return (
    <div className="empty-state" style={{ minHeight: '60vh' }}>
      <p className="empty-state-title">Department Dashboard</p>
      <p className="empty-state-desc">
        <strong>Backend Gap Identified:</strong> The backend currently lacks specific 
        endpoints for Department Admins to view aggregate statistics or all department 
        complaints. Once these endpoints are implemented, this page will display them.
      </p>
    </div>
  );
}
