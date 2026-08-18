import React from 'react';

export default function AdminRoles() {
  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Roles & Permissions</h2>
          <p className="page-subtitle">View and configure system roles</p>
        </div>
      </div>

      <div className="empty-state" style={{ marginBottom: '2rem' }}>
        <p className="empty-state-title">Backend API Required</p>
        <p>Dynamic permission management is currently pending backend implementation. The table below represents the structural design for this feature.</p>
      </div>

      <div className="card">
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>Role</th>
                <th>Permissions Summary</th>
              </tr>
            </thead>
            <tbody style={{ opacity: 0.7 }}>
              <tr>
                <td><strong>Citizen</strong></td>
                <td>Submit complaints, track own complaints</td>
              </tr>
              <tr>
                <td><strong>Employee</strong></td>
                <td>Verify complaints, submit progress, resolve assigned complaints</td>
              </tr>
              <tr>
                <td><strong>Supervisor</strong></td>
                <td>Manage department queue, assign/reassign employees</td>
              </tr>
              <tr>
                <td><strong>Department Admin</strong></td>
                <td>Oversee department, view analytics and members</td>
              </tr>
              <tr>
                <td><strong>System Admin</strong></td>
                <td>Global administration, manage departments, users, rules</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
