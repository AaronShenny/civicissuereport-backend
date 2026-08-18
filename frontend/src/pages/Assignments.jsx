import React, { useState } from 'react';
import StatusBadge from '../components/StatusBadge';

const MOCK = [
  { id: 'ASN-001', asset: 'MacBook Pro 16"',    assetId: 'AST-001', assignedTo: 'Sarah Chen',   dept: 'Engineering', location: 'HQ – Floor 3', date: 'Jan 20, 2024', status: 'Active' },
  { id: 'ASN-002', asset: 'Dell Monitor 27"',    assetId: 'AST-002', assignedTo: 'Mark Davis',   dept: 'Marketing',   location: 'HQ – Floor 2', date: 'Aug 22, 2023', status: 'Active' },
  { id: 'ASN-003', asset: 'Standing Desk Pro',   assetId: 'AST-003', assignedTo: 'Priya Sharma', dept: 'Design',      location: 'HQ – Floor 1', date: 'May 12, 2023', status: 'Active' },
  { id: 'ASN-004', asset: 'iPhone 15 Pro',       assetId: 'AST-005', assignedTo: 'Julia Roberts',dept: 'Sales',       location: 'Remote',        date: 'Mar 01, 2024', status: 'Active' },
  { id: 'ASN-005', asset: 'Toyota Camry 2023',   assetId: 'AST-006', assignedTo: 'Fleet Mgr',    dept: 'Operations',  location: 'Parking B',    date: 'Mar 15, 2023', status: 'Active' },
  { id: 'ASN-006', asset: 'HP LaserJet Pro',     assetId: 'AST-004', assignedTo: 'Shared',       dept: 'General',     location: 'Copy Room',    date: 'Nov 05, 2022', status: 'Maintenance' },
  { id: 'ASN-007', asset: 'Ergonomic Chair',     assetId: 'AST-007', assignedTo: '—',            dept: '—',           location: 'Storage',      date: '—',           status: 'Unassigned' },
  { id: 'ASN-008', asset: 'Cisco IP Phone',      assetId: 'AST-008', assignedTo: 'Reception',    dept: 'Facilities',  location: 'Lobby',        date: 'Apr 06, 2022', status: 'Active' },
];

const DEPTS = ['All', 'Engineering', 'Marketing', 'Design', 'Sales', 'Operations', 'General', 'Facilities'];

export default function Assignments() {
  const [search, setSearch]   = useState('');
  const [dept, setDept]       = useState('All');
  const [showPanel, setPanel] = useState(false);

  const filtered = MOCK.filter((a) => {
    const q = search.toLowerCase();
    if (q && !a.asset.toLowerCase().includes(q) && !a.assignedTo.toLowerCase().includes(q)) return false;
    if (dept !== 'All' && a.dept !== dept) return false;
    return true;
  });

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Assignments</h2>
          <p className="page-subtitle">Track which assets are assigned to which people and locations.</p>
        </div>
        <div className="page-header-right">
          <button className="btn btn-primary" onClick={() => setPanel(true)}>
            <PlusSvg size={16} /> Assign Asset
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        <div className="toolbar-left">
          <div className="search-bar" style={{ width: 280 }}>
            <SearchSvg size={16} />
            <input placeholder="Search assets or assignees…" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
        </div>
        <div className="toolbar-right">
          <select className="select" style={{ width: 180 }} value={dept} onChange={(e) => setDept(e.target.value)}>
            {DEPTS.map((d) => <option key={d}>{d}</option>)}
          </select>
        </div>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Assignment ID</th>
              <th>Asset</th>
              <th>Assigned To</th>
              <th>Department</th>
              <th>Location</th>
              <th>Since</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((a) => (
              <tr key={a.id}>
                <td>
                  <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)', background: 'var(--surface-muted)', padding: '2px 6px', borderRadius: 4 }}>
                    {a.id}
                  </span>
                </td>
                <td>
                  <div>
                    <p style={{ fontWeight: 500 }}>{a.asset}</p>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.assetId}</p>
                  </div>
                </td>
                <td>
                  {a.assignedTo !== '—' ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div className="avatar avatar-sm">{a.assignedTo.charAt(0)}</div>
                      {a.assignedTo}
                    </div>
                  ) : '—'}
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{a.dept}</td>
                <td style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{a.location}</td>
                <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>{a.date}</td>
                <td><StatusBadge status={a.status} /></td>
                <td>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button className="btn btn-ghost btn-sm btn-icon" title="Re-assign"><EditSvg size={14} /></button>
                    <button className="btn btn-ghost btn-sm btn-icon" title="Unassign"><TrashSvg size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 'var(--sp-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{filtered.length} of {MOCK.length} assignments</p>
      </div>

      {/* Side Panel */}
      {showPanel && (
        <>
          <div className="modal-overlay" onClick={() => setPanel(false)} style={{ justifyContent: 'flex-end', padding: 0 }}>
            <div
              className="modal"
              style={{ height: '100vh', borderRadius: '0', maxWidth: 480, width: '100%', display: 'flex', flexDirection: 'column', margin: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header" style={{ padding: 'var(--sp-xl)', borderBottom: '1px solid var(--border)' }}>
                <h3 className="modal-title">Assign Asset</h3>
                <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setPanel(false)}>✕</button>
              </div>
              <div style={{ flex: 1, padding: 'var(--sp-xl)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)', overflowY: 'auto' }}>
                <div className="form-group">
                  <label className="form-label">Select Asset <span className="required">*</span></label>
                  <select className="select">
                    <option value="">— Choose asset —</option>
                    <option>Ergonomic Chair (AST-007)</option>
                    <option>Projector Epson 4K (AST-012)</option>
                    <option>Dell Laptop 14" (AST-010)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Assign To <span className="required">*</span></label>
                  <select className="select">
                    <option value="">— Choose person —</option>
                    <option>Sarah Chen</option>
                    <option>Mark Davis</option>
                    <option>Priya Sharma</option>
                    <option>Tom Wilson</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Department</label>
                  <select className="select">
                    <option>Engineering</option>
                    <option>Marketing</option>
                    <option>Design</option>
                    <option>Sales</option>
                    <option>Operations</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Location</label>
                  <select className="select">
                    <option>HQ – Floor 1</option>
                    <option>HQ – Floor 2</option>
                    <option>HQ – Floor 3</option>
                    <option>Remote</option>
                    <option>Warehouse</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Notes</label>
                  <textarea className="textarea" placeholder="Any additional notes…" style={{ minHeight: 80 }} />
                </div>
              </div>
              <div className="modal-footer" style={{ padding: 'var(--sp-lg) var(--sp-xl)', borderTop: '1px solid var(--border)' }}>
                <button className="btn btn-secondary" onClick={() => setPanel(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={() => setPanel(false)}>Save Assignment</button>
              </div>
            </div>
          </div>
        </>
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
