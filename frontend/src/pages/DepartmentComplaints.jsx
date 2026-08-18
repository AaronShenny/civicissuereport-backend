import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function DepartmentComplaints() {
  const navigate = useNavigate();

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Department Complaints</h2>
          <p className="page-subtitle">View and manage all issues routed to your department.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
        <div style={{ display: 'flex', gap: 'var(--sp-md)', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: 1, minWidth: '200px' }}>
            <label className="form-label">Search</label>
            <input type="text" className="form-input" placeholder="Search ID, location..." disabled />
          </div>
          <div className="form-group" style={{ flex: 1, minWidth: '150px' }}>
            <label className="form-label">Status</label>
            <select className="form-input" disabled>
              <option>All Statuses</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1, minWidth: '150px' }}>
            <label className="form-label">Priority</label>
            <select className="form-input" disabled>
              <option>All Priorities</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1, minWidth: '150px' }}>
            <label className="form-label">Category</label>
            <select className="form-input" disabled>
              <option>All Categories</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Complaint ID</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Assigned To</th>
                <th>Location</th>
                <th>Submitted</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan="8" className="text-center" style={{ padding: 'var(--sp-xl)' }}>
                  <div className="empty-state">
                    <p className="empty-state-title" style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
                      Data Unavailable (API Pending)
                    </p>
                    <p>
                      The endpoint to list all department complaints for Department Admins is not yet available.
                    </p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
