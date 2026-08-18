import React from 'react';

export default function AdminAuditLogs() {
  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Audit Logs</h2>
          <p className="page-subtitle">System-wide administrative and security actions</p>
        </div>
      </div>

      <div className="empty-state" style={{ marginBottom: '2rem' }}>
        <p className="empty-state-title">Audit Logging API Pending</p>
        <p>Application-level audit logging is currently pending backend implementation. The table below represents the structural design for this feature.</p>
      </div>

      <div className="card">
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>User</th>
                <th>Action</th>
                <th>Target</th>
              </tr>
            </thead>
            <tbody style={{ opacity: 0.7 }}>
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '2rem' }}>
                  <em>Audit data unavailable</em>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
