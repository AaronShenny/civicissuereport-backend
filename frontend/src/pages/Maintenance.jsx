import React, { useState } from 'react';
import StatusBadge from '../components/StatusBadge';

const MOCK = [
  { id: 'MNT-001', asset: 'HVAC Unit A',      assetId: 'AST-020', type: 'Preventive',   status: 'Scheduled',   due: 'Aug 18, 2024', assignedTo: 'Tech Team',   priority: 'Critical',  notes: 'Annual servicing.' },
  { id: 'MNT-002', asset: 'Generator 2',      assetId: 'AST-021', type: 'Preventive',   status: 'Scheduled',   due: 'Aug 21, 2024', assignedTo: 'Facilities',  priority: 'Scheduled', notes: 'Monthly check.' },
  { id: 'MNT-003', asset: 'HP LaserJet Pro', assetId: 'AST-004', type: 'Corrective',   status: 'In Progress', due: 'Aug 17, 2024', assignedTo: 'IT Dept',     priority: 'Scheduled', notes: 'Paper jam issue.' },
  { id: 'MNT-004', asset: 'Industrial Printer', assetId: 'AST-009', type: 'Corrective', status: 'In Progress', due: 'Aug 17, 2024', assignedTo: 'Vendor XYZ', priority: 'Critical',  notes: 'Belt replacement needed.' },
  { id: 'MNT-005', asset: 'Fire System',      assetId: 'AST-022', type: 'Inspection',  status: 'Scheduled',   due: 'Aug 24, 2024', assignedTo: 'Safety Team', priority: 'Scheduled', notes: 'Quarterly inspection.' },
  { id: 'MNT-006', asset: 'Dell Monitor 24"', assetId: 'AST-010', type: 'Corrective',  status: 'Completed',   due: 'Aug 10, 2024', assignedTo: 'IT Dept',     priority: 'Scheduled', notes: 'Pixel issue resolved.' },
  { id: 'MNT-007', asset: 'Toyota Camry',    assetId: 'AST-006', type: 'Preventive',   status: 'Completed',   due: 'Jul 30, 2024', assignedTo: 'AutoShop',    priority: 'Scheduled', notes: 'Oil change complete.' },
];

const STATUSES = ['All', 'Scheduled', 'In Progress', 'Completed'];
const TYPES    = ['All', 'Preventive', 'Corrective', 'Inspection'];

export default function Maintenance() {
  const [search, setSearch]       = useState('');
  const [statusF, setStatusF]     = useState('All');
  const [typeF, setTypeF]         = useState('All');
  const [showModal, setShowModal] = useState(false);

  const filtered = MOCK.filter((m) => {
    const q = search.toLowerCase();
    if (q && !m.asset.toLowerCase().includes(q)) return false;
    if (statusF !== 'All' && m.status !== statusF) return false;
    if (typeF   !== 'All' && m.type   !== typeF)   return false;
    return true;
  });

  const counts = {
    Scheduled:   MOCK.filter((m) => m.status === 'Scheduled').length,
    'In Progress': MOCK.filter((m) => m.status === 'In Progress').length,
    Completed:   MOCK.filter((m) => m.status === 'Completed').length,
  };

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Maintenance</h2>
          <p className="page-subtitle">Track maintenance schedules, tickets, and service history.</p>
        </div>
        <div className="page-header-right">
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <PlusSvg size={16} /> Log Maintenance
          </button>
        </div>
      </div>

      {/* Status summary */}
      <div className="grid-3" style={{ marginBottom: 'var(--sp-xl)' }}>
        {[
          { label: 'Scheduled',    count: counts['Scheduled'],    icon: '📅', color: 'rgba(120,172,233,0.12)', text: 'var(--info)' },
          { label: 'In Progress',  count: counts['In Progress'],  icon: '⚙️', color: 'rgba(248,220,93,0.18)', text: '#b8940a' },
          { label: 'Completed',    count: counts['Completed'],    icon: '✅', color: 'rgba(144,203,130,0.18)', text: 'var(--secondary)' },
        ].map((s) => (
          <div key={s.label} className="card" style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-md)' }}>
            <div style={{ width: 48, height: 48, borderRadius: 'var(--r-md)', background: s.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, flexShrink: 0 }}>
              {s.icon}
            </div>
            <div>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 500 }}>{s.label}</p>
              <p style={{ fontSize: 28, fontWeight: 700, color: s.text, lineHeight: 1 }}>{s.count}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        <div className="toolbar-left">
          <div className="search-bar" style={{ width: 260 }}>
            <SearchSvg size={16} />
            <input placeholder="Search assets…" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          {STATUSES.map((s) => (
            <button key={s} className={`filter-chip${statusF === s ? ' active' : ''}`} onClick={() => setStatusF(s)}>{s}</button>
          ))}
        </div>
        <div className="toolbar-right">
          <select className="select" style={{ width: 150 }} value={typeF} onChange={(e) => setTypeF(e.target.value)}>
            {TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr><th>ID</th><th>Asset</th><th>Type</th><th>Priority</th><th>Status</th><th>Due Date</th><th>Assigned To</th><th>Notes</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {filtered.map((m) => (
              <tr key={m.id}>
                <td>
                  <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)', background: 'var(--surface-muted)', padding: '2px 6px', borderRadius: 4 }}>
                    {m.id}
                  </span>
                </td>
                <td>
                  <div>
                    <p style={{ fontWeight: 500 }}>{m.asset}</p>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>{m.assetId}</p>
                  </div>
                </td>
                <td><span className="tag tag-neutral">{m.type}</span></td>
                <td><StatusBadge status={m.priority} /></td>
                <td><StatusBadge status={m.status} /></td>
                <td style={{ fontSize: 13, color: m.status === 'Completed' ? 'var(--text-muted)' : 'var(--text-primary)', fontWeight: m.priority === 'Critical' && m.status !== 'Completed' ? 600 : 400 }}>
                  {m.due}
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{m.assignedTo}</td>
                <td style={{ fontSize: 12, color: 'var(--text-muted)', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.notes}</td>
                <td>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button className="btn btn-ghost btn-sm btn-icon"><EditSvg size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Log Maintenance Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 560 }}>
            <div className="modal-header">
              <h3 className="modal-title">Log Maintenance</h3>
              <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
                <div className="form-group">
                  <label className="form-label">Asset <span className="required">*</span></label>
                  <select className="select"><option>— Select asset —</option><option>HVAC Unit A</option><option>Generator 2</option><option>HP LaserJet Pro</option></select>
                </div>
                <div className="grid-2" style={{ gap: 'var(--sp-md)' }}>
                  <div className="form-group">
                    <label className="form-label">Type</label>
                    <select className="select">{TYPES.filter(t => t !== 'All').map(t => <option key={t}>{t}</option>)}</select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Priority</label>
                    <select className="select"><option>Scheduled</option><option>Critical</option></select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Due Date <span className="required">*</span></label>
                    <input type="date" className="input" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Assigned To</label>
                    <input className="input" placeholder="e.g. IT Dept" />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Notes</label>
                  <textarea className="textarea" placeholder="Describe the maintenance work…" />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={() => setShowModal(false)}>Log Maintenance</button>
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
