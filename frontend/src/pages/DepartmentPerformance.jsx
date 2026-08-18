import React from 'react';

export default function DepartmentPerformance() {
  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Department Performance</h2>
          <p className="page-subtitle">Analytics and workload metrics across your department.</p>
        </div>
      </div>

      <div className="empty-state" style={{ minHeight: '400px' }}>
        <p className="empty-state-title" style={{ color: 'var(--text-muted)' }}>
          Analytics Unavailable
        </p>
        <p style={{ maxWidth: '500px', margin: '0 auto' }}>
          The backend aggregation API for performance metrics (such as workload distribution, resolution times, and overdue workload) has not been implemented yet.
        </p>
      </div>
    </div>
  );
}
