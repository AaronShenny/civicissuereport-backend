import React, { useState } from 'react';
import StatusBadge from '../components/StatusBadge';

const MOCK_USERS = [
  { id: 'USR-001', name: 'Admin User',    email: 'admin@company.com',   role: 'Administrator', status: 'Active', assets: 2,  lastActive: 'Just now' },
  { id: 'USR-002', name: 'Sarah Chen',    email: 'schen@company.com',   role: 'Manager',       status: 'Active', assets: 4,  lastActive: '1 hr ago' },
  { id: 'USR-003', name: 'Mark Davis',    email: 'mdavis@company.com',  role: 'User',          status: 'Active', assets: 2,  lastActive: 'Yesterday' },
  { id: 'USR-004', name: 'Priya Sharma',  email: 'psharma@company.com', role: 'User',          status: 'Active', assets: 1,  lastActive: '3 days ago' },
  { id: 'USR-005', name: 'Julia Roberts', email: 'jroberts@company.com',role: 'Manager',       status: 'Active', assets: 3,  lastActive: '2 hrs ago' },
  { id: 'USR-006', name: 'Tom Wilson',    email: 'twilson@company.com', role: 'User',          status: 'Inactive',assets: 0,  lastActive: '2 mos ago' },
  { id: 'USR-007', name: 'IT Support',    email: 'it@company.com',      role: 'Administrator', status: 'Active', assets: 15, lastActive: '5 mins ago' },
];

export default function Users() {
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);

  const filtered = MOCK_USERS.filter((u) => {
    const q = search.toLowerCase();
    return q ? u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q) : true;
  });

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Users & Team</h2>
          <p className="page-subtitle">Manage who has access to the asset management system.</p>
        </div>
        <div className="page-header-right">
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <PlusSvg size={16} /> Invite User
          </button>
        </div>
      </div>

      <div className="toolbar">
        <div className="toolbar-left">
          <div className="search-bar" style={{ width: 280 }}>
            <SearchSvg size={16} />
            <input placeholder="Search users by name or email…" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
        </div>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr><th>Name</th><th>Role</th><th>Status</th><th>Assigned Assets</th><th>Last Active</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {filtered.map((u) => (
              <tr key={u.id}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div className="avatar avatar-md">{u.name.charAt(0)}</div>
                    <div>
                      <p style={{ fontWeight: 500 }}>{u.name}</p>
                      <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{u.email}</p>
                    </div>
                  </div>
                </td>
                <td><span className="tag tag-neutral">{u.role}</span></td>
                <td><StatusBadge status={u.status} /></td>
                <td><span className="counter">{u.assets}</span></td>
                <td style={{ color: 'var(--text-secondary)' }}>{u.lastActive}</td>
                <td>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button className="btn btn-ghost btn-sm btn-icon"><EditSvg size={14} /></button>
                    <button className="btn btn-ghost btn-sm btn-icon"><TrashSvg size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Invite User</h3>
              <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input className="input" placeholder="e.g. Jane Doe" />
                </div>
                <div className="form-group">
                  <label className="form-label">Email Address <span className="required">*</span></label>
                  <input type="email" className="input" placeholder="jane@company.com" />
                </div>
                <div className="form-group">
                  <label className="form-label">Role</label>
                  <select className="select">
                    <option>User</option><option>Manager</option><option>Administrator</option>
                  </select>
                  <span className="form-hint">Administrators have full access to system settings.</span>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={() => setShowModal(false)}>Send Invite</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PlusSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
}
function SearchSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>;
}
function EditSvg({ size = 14 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>;
}
function TrashSvg({ size = 14 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>;
}
