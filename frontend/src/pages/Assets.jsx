import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge';

const MOCK_ASSETS = [
  { id: 'AST-001', name: 'MacBook Pro 16"',     category: 'IT Equipment',  status: 'Active',      assignedTo: 'Sarah Chen',    location: 'HQ – Floor 3', value: '$2,499', purchase: '2024-01-15' },
  { id: 'AST-002', name: 'Dell Monitor 27"',     category: 'IT Equipment',  status: 'Active',      assignedTo: 'Mark Davis',    location: 'HQ – Floor 2', value: '$599',   purchase: '2023-08-20' },
  { id: 'AST-003', name: 'Standing Desk Pro',    category: 'Furniture',     status: 'Assigned',    assignedTo: 'Priya Sharma',  location: 'HQ – Floor 1', value: '$1,200', purchase: '2023-05-10' },
  { id: 'AST-004', name: 'HP LaserJet Pro',      category: 'IT Equipment',  status: 'Maintenance', assignedTo: 'Shared',        location: 'Copy Room',     value: '$450',   purchase: '2022-11-01' },
  { id: 'AST-005', name: 'iPhone 15 Pro',        category: 'IT Equipment',  status: 'Active',      assignedTo: 'Julia Roberts', location: 'Remote',        value: '$1,099', purchase: '2024-02-28' },
  { id: 'AST-006', name: 'Toyota Camry 2023',   category: 'Vehicles',      status: 'Active',      assignedTo: 'Fleet',         location: 'Parking B',    value: '$28,000', purchase: '2023-03-15' },
  { id: 'AST-007', name: 'Ergonomic Chair',      category: 'Furniture',     status: 'Available',   assignedTo: '—',             location: 'Storage',       value: '$380',   purchase: '2023-07-22' },
  { id: 'AST-008', name: 'Cisco IP Phone',       category: 'IT Equipment',  status: 'Active',      assignedTo: 'Reception',     location: 'Lobby',         value: '$220',   purchase: '2022-04-05' },
  { id: 'AST-009', name: 'Industrial Printer',   category: 'Machinery',     status: 'Maintenance', assignedTo: 'Production',    location: 'Warehouse',     value: '$5,400', purchase: '2021-09-18' },
  { id: 'AST-010', name: 'Dell Laptop 14"',      category: 'IT Equipment',  status: 'Retired',     assignedTo: '—',             location: 'Storage',       value: '$899',   purchase: '2020-06-12' },
  { id: 'AST-011', name: 'Conference Table',     category: 'Furniture',     status: 'Active',      assignedTo: 'Shared',        location: 'Meeting Rm 2',  value: '$2,100', purchase: '2022-01-30' },
  { id: 'AST-012', name: 'Projector Epson 4K',  category: 'IT Equipment',  status: 'Available',   assignedTo: '—',             location: 'AV Storage',    value: '$1,350', purchase: '2023-11-05' },
];

const CATEGORIES = ['All', 'IT Equipment', 'Furniture', 'Vehicles', 'Machinery', 'Office Supplies'];
const STATUSES   = ['All', 'Active', 'Assigned', 'Available', 'Maintenance', 'Retired'];

export default function Assets() {
  const navigate = useNavigate();
  const [search, setSearch]       = useState('');
  const [catFilter, setCat]       = useState('All');
  const [statusFilter, setStatus] = useState('All');
  const [sortField, setSortField] = useState('id');
  const [sortDir, setSortDir]     = useState('asc');

  const handleSort = (field) => {
    if (sortField === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortField(field); setSortDir('asc'); }
  };

  const filtered = MOCK_ASSETS
    .filter((a) => {
      const q = search.toLowerCase();
      if (q && !a.name.toLowerCase().includes(q) && !a.id.toLowerCase().includes(q) && !a.assignedTo.toLowerCase().includes(q)) return false;
      if (catFilter !== 'All' && a.category !== catFilter) return false;
      if (statusFilter !== 'All' && a.status !== statusFilter) return false;
      return true;
    })
    .sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      return a[sortField] > b[sortField] ? dir : -dir;
    });

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <span style={{ opacity: 0.3 }}>↕</span>;
    return <span>{sortDir === 'asc' ? '↑' : '↓'}</span>;
  };

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">All Assets</h2>
          <p className="page-subtitle">{filtered.length} assets found</p>
        </div>
        <div className="page-header-right">
          <button className="btn btn-secondary">
            <ExportSvg size={16} /> Export
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/assets/new')}>
            <PlusSvg size={16} /> Add Asset
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        <div className="toolbar-left">
          {/* Search */}
          <div className="search-bar" style={{ width: 280 }}>
            <SearchSvg size={16} />
            <input
              placeholder="Search by name, ID, assignee…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button onClick={() => setSearch('')} style={{ color: 'var(--text-muted)', cursor: 'pointer', background: 'none', border: 'none' }}>✕</button>
            )}
          </div>

          {/* Status filters */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {STATUSES.map((s) => (
              <button
                key={s}
                className={`filter-chip${statusFilter === s ? ' active' : ''}`}
                onClick={() => setStatus(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Category dropdown */}
        <div className="toolbar-right">
          <select
            className="select"
            style={{ width: 160 }}
            value={catFilter}
            onChange={(e) => setCat(e.target.value)}
          >
            {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('id')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                ID <SortIcon field="id" />
              </th>
              <th onClick={() => handleSort('name')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                Asset Name <SortIcon field="name" />
              </th>
              <th>Category</th>
              <th>Status</th>
              <th>Assigned To</th>
              <th>Location</th>
              <th>Value</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={8}>
                  <div className="empty-state" style={{ padding: 'var(--sp-3xl)' }}>
                    <p className="empty-state-title">No assets found</p>
                    <p className="empty-state-desc">Try adjusting your search or filter criteria.</p>
                  </div>
                </td>
              </tr>
            ) : (
              filtered.map((asset) => (
                <tr key={asset.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/assets/${asset.id}`)}>
                  <td>
                    <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)', background: 'var(--surface-muted)', padding: '2px 6px', borderRadius: 4 }}>
                      {asset.id}
                    </span>
                  </td>
                  <td style={{ fontWeight: 500 }}>{asset.name}</td>
                  <td>
                    <span className="tag tag-neutral">{asset.category}</span>
                  </td>
                  <td><StatusBadge status={asset.status} /></td>
                  <td style={{ color: 'var(--text-secondary)' }}>{asset.assignedTo}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{asset.location}</td>
                  <td style={{ fontWeight: 500 }}>{asset.value}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button className="btn btn-ghost btn-sm btn-icon" title="View" onClick={() => navigate(`/assets/${asset.id}`)}>
                        <EyeSvg size={15} />
                      </button>
                      <button className="btn btn-ghost btn-sm btn-icon" title="Edit" onClick={() => navigate(`/assets/${asset.id}/edit`)}>
                        <EditSvg size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination placeholder */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--sp-md)', padding: '0 var(--sp-xs)' }}>
        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Showing {filtered.length} of {MOCK_ASSETS.length} assets
        </p>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn btn-secondary btn-sm">← Prev</button>
          <button className="btn btn-primary btn-sm">1</button>
          <button className="btn btn-secondary btn-sm">Next →</button>
        </div>
      </div>
    </div>
  );
}

/* SVGs */
function SearchSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>;
}
function PlusSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
}
function ExportSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>;
}
function EyeSvg({ size = 15 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>;
}
function EditSvg({ size = 15 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>;
}
