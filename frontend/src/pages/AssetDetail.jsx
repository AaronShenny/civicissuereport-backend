import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge';

const ASSETS_DB = {
  'AST-001': {
    id: 'AST-001', name: 'MacBook Pro 16"', category: 'IT Equipment', status: 'Active',
    assignedTo: 'Sarah Chen', department: 'Engineering', location: 'HQ – Floor 3',
    value: '$2,499', purchaseDate: 'Jan 15, 2024', warrantyExpiry: 'Jan 15, 2027',
    serialNumber: 'C02XL0ADJGH5', model: 'MacBook Pro 16" M3 Pro', manufacturer: 'Apple',
    condition: 'Excellent', description: 'Company-issued laptop for senior engineers. 16GB RAM, 512GB SSD.',
    history: [
      { date: 'Aug 17, 2024', action: 'Status Updated', by: 'Admin', note: 'Renewed warranty.' },
      { date: 'Jan 20, 2024', action: 'Assigned',        by: 'Admin', note: 'Assigned to Sarah Chen.' },
      { date: 'Jan 15, 2024', action: 'Asset Added',     by: 'Admin', note: 'Purchased from Apple Store.' },
    ],
    maintenance: [
      { date: 'Mar 10, 2024', type: 'Software Update', status: 'Completed', by: 'IT Dept' },
      { date: 'Jun 05, 2024', type: 'Battery Check',   status: 'Completed', by: 'IT Dept' },
    ],
  },
  'AST-002': {
    id: 'AST-002', name: 'Dell Monitor 27"', category: 'IT Equipment', status: 'Active',
    assignedTo: 'Mark Davis', department: 'Marketing', location: 'HQ – Floor 2',
    value: '$599', purchaseDate: 'Aug 20, 2023', warrantyExpiry: 'Aug 20, 2026',
    serialNumber: 'CN-0HJ9JX-28832', model: 'Dell S2722QC 4K', manufacturer: 'Dell',
    condition: 'Good', description: '27-inch 4K USB-C monitor.',
    history: [
      { date: 'Aug 22, 2023', action: 'Assigned',    by: 'Admin', note: 'Assigned to Mark Davis.' },
      { date: 'Aug 20, 2023', action: 'Asset Added', by: 'Admin', note: 'Purchased from Dell Business.' },
    ],
    maintenance: [],
  },
};

const TABS = ['Overview', 'History', 'Maintenance'];

export default function AssetDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('Overview');
  const [showDelete, setShowDelete] = useState(false);

  const asset = ASSETS_DB[id];

  if (!asset) {
    return (
      <div className="empty-state" style={{ minHeight: '60vh' }}>
        <div className="empty-state-icon">
          <BoxSvg size={56} />
        </div>
        <p className="empty-state-title">Asset not found</p>
        <p className="empty-state-desc">The asset ID <strong>{id}</strong> does not exist.</p>
        <button className="btn btn-primary" onClick={() => navigate('/assets')}>Back to Assets</button>
      </div>
    );
  }

  return (
    <div>
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <button className="btn btn-ghost btn-sm" style={{ height: 'auto', padding: '2px 0', fontSize: 14, color: 'var(--text-secondary)' }}
          onClick={() => navigate('/assets')}>
          Assets
        </button>
        <span className="breadcrumb-sep">/</span>
        <span className="breadcrumb-current">{asset.name}</span>
      </div>

      {/* Header */}
      <div className="page-header">
        <div className="page-header-left" style={{ flexDirection: 'row', alignItems: 'center', gap: 'var(--sp-md)' }}>
          <div style={{
            width: 56, height: 56, borderRadius: 'var(--r-lg)',
            background: 'var(--surface-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: '1px solid var(--border)',
          }}>
            <BoxSvg size={28} />
          </div>
          <div>
            <h2 className="page-title">{asset.name}</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
              <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)', background: 'var(--surface-muted)', padding: '2px 6px', borderRadius: 4 }}>
                {asset.id}
              </span>
              <StatusBadge status={asset.status} />
            </div>
          </div>
        </div>
        <div className="page-header-right">
          <button className="btn btn-secondary" onClick={() => setShowDelete(true)}>
            <TrashSvg size={15} /> Archive
          </button>
          <button className="btn btn-primary" onClick={() => navigate(`/assets/${id}/edit`)}>
            <EditSvg size={15} /> Edit Asset
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {TABS.map((t) => (
          <button key={t} className={`tab${activeTab === t ? ' active' : ''}`} onClick={() => setActiveTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {/* Overview */}
      {activeTab === 'Overview' && (
        <div className="grid-2" style={{ gap: 'var(--sp-lg)', alignItems: 'start' }}>
          {/* Details Card */}
          <div className="card">
            <p className="section-title">Asset Details</p>
            <div className="detail-grid">
              <DetailField label="Manufacturer" value={asset.manufacturer} />
              <DetailField label="Model" value={asset.model} />
              <DetailField label="Serial Number" value={<code style={{ fontSize: 13, background: 'var(--surface-muted)', padding: '2px 6px', borderRadius: 4 }}>{asset.serialNumber}</code>} />
              <DetailField label="Condition" value={asset.condition} />
              <DetailField label="Purchase Value" value={<strong>{asset.value}</strong>} />
              <DetailField label="Purchase Date" value={asset.purchaseDate} />
              <DetailField label="Warranty Expiry" value={asset.warrantyExpiry} />
              <DetailField label="Category" value={<span className="tag tag-neutral">{asset.category}</span>} />
            </div>
            {asset.description && (
              <div style={{ marginTop: 'var(--sp-md)', paddingTop: 'var(--sp-md)', borderTop: '1px solid var(--border)' }}>
                <p style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 6 }}>Description</p>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{asset.description}</p>
              </div>
            )}
          </div>

          {/* Assignment Card */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
            <div className="card">
              <p className="section-title">Assignment</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-sm)' }}>
                  <div className="avatar avatar-lg">{asset.assignedTo.charAt(0)}</div>
                  <div>
                    <p style={{ fontWeight: 600, fontSize: 15 }}>{asset.assignedTo}</p>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{asset.department}</p>
                  </div>
                </div>
                <div style={{ paddingTop: 'var(--sp-sm)', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <DetailField label="Location" value={asset.location} />
                </div>
              </div>
              <button className="btn btn-secondary" style={{ marginTop: 'var(--sp-md)', width: '100%' }}
                onClick={() => navigate('/assignments')}>
                Manage Assignment
              </button>
            </div>

            {/* Quick actions */}
            <div className="card">
              <p className="section-title">Quick Actions</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start', gap: 10 }}
                  onClick={() => navigate('/maintenance')}>
                  <WrenchSvg size={16} /> Schedule Maintenance
                </button>
                <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start', gap: 10 }}>
                  <PrintSvg size={16} /> Print Asset Label
                </button>
                <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start', gap: 10 }}>
                  <ShareSvg size={16} /> Share Details
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'History' && (
        <div className="card" style={{ maxWidth: 640 }}>
          <p className="section-title">Activity History</p>
          <div className="timeline">
            {asset.history.map((h, i) => (
              <div key={i} className="timeline-item">
                <div className="timeline-dot">
                  <HistorySvg size={14} />
                </div>
                <div className="timeline-content">
                  <p className="timeline-content-title">{h.action}</p>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>{h.note}</p>
                  <p className="timeline-content-meta">{h.by} · {h.date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Maintenance Tab */}
      {activeTab === 'Maintenance' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 'var(--sp-md)' }}>
            <button className="btn btn-primary" onClick={() => navigate('/maintenance')}>
              <PlusSvg size={16} /> Log Maintenance
            </button>
          </div>
          {asset.maintenance.length === 0 ? (
            <div className="empty-state card">
              <p className="empty-state-title">No maintenance records</p>
              <p className="empty-state-desc">Maintenance logs will appear here once recorded.</p>
            </div>
          ) : (
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr><th>Date</th><th>Type</th><th>Status</th><th>Performed By</th></tr>
                </thead>
                <tbody>
                  {asset.maintenance.map((m, i) => (
                    <tr key={i}>
                      <td>{m.date}</td>
                      <td>{m.type}</td>
                      <td><StatusBadge status={m.status} /></td>
                      <td>{m.by}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Delete Modal */}
      {showDelete && (
        <div className="modal-overlay" onClick={() => setShowDelete(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Archive Asset</h3>
              <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setShowDelete(false)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                Are you sure you want to archive <strong>{asset.name}</strong>? It will be moved to retired status.
              </p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowDelete(false)}>Cancel</button>
              <button className="btn btn-danger" onClick={() => navigate('/assets')}>Archive Asset</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DetailField({ label, value }) {
  return (
    <div className="detail-field">
      <p className="detail-field-label">{label}</p>
      <div className="detail-field-value">{value}</div>
    </div>
  );
}

function BoxSvg({ size = 24, color = 'var(--text-muted)' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>;
}
function EditSvg({ size = 15 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>;
}
function TrashSvg({ size = 15 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>;
}
function WrenchSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>;
}
function PrintSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>;
}
function ShareSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>;
}
function HistorySvg({ size = 14 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>;
}
function PlusSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
}
