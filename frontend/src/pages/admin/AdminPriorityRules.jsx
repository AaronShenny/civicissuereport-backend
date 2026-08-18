import React from 'react';

export default function AdminPriorityRules() {
  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Priority Rules</h2>
          <p className="page-subtitle">Configure automated priority scoring</p>
        </div>
      </div>

      <div className="empty-state" style={{ marginBottom: '2rem' }}>
        <p className="empty-state-title">Backend API Required</p>
        <p>Configurable priority rules are currently pending backend implementation. The table below represents the structural design for this feature.</p>
      </div>

      <div className="card">
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>Factor</th>
                <th>Description</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody style={{ opacity: 0.7 }}>
              <tr>
                <td><strong>Severity</strong></td>
                <td>AI-detected severity score multiplier</td>
                <td><span className="status-badge status-verified">Active</span></td>
              </tr>
              <tr>
                <td><strong>Traffic Proximity</strong></td>
                <td>Distance to major roads or intersections</td>
                <td><span className="status-badge status-verified">Active</span></td>
              </tr>
              <tr>
                <td><strong>School Proximity</strong></td>
                <td>Distance to educational institutions</td>
                <td><span className="status-badge status-verified">Active</span></td>
              </tr>
              <tr>
                <td><strong>Hospital Proximity</strong></td>
                <td>Distance to healthcare facilities</td>
                <td><span className="status-badge status-verified">Active</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
