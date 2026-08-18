import React from 'react';

export default function AdminOverview() {
  return (
    <div className="empty-state" style={{ minHeight: '60vh' }}>
      <p className="empty-state-title">System Administration</p>
      <p className="empty-state-desc">
        <strong>Backend Gap Identified:</strong> The backend currently lacks specific 
        endpoints for System Admins to view system-wide analytics or manage all users. 
        Once these endpoints are implemented, this page will display them.
      </p>
    </div>
  );
}
