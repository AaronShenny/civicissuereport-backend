import React, { useState } from 'react';

const MOCK_CATEGORIES = [
  { id: 1, name: 'IT Equipment',    icon: '💻', count: 487, color: '#081B32' },
  { id: 2, name: 'Furniture',       icon: '🪑', count: 312, color: '#2DB780' },
  { id: 3, name: 'Vehicles',        icon: '🚗', count: 98,  color: '#78ACE9' },
  { id: 4, name: 'Machinery',       icon: '⚙️', count: 153, color: '#F8DC5D' },
  { id: 5, name: 'Office Supplies', icon: '🖊️', count: 234, color: '#EB2C50' },
];

export default function Categories() {
  const [categories, setCategories]   = useState(MOCK_CATEGORIES);
  const [showModal, setShowModal]     = useState(false);
  const [editTarget, setEditTarget]   = useState(null);
  const [formName, setFormName]       = useState('');
  const [formIcon, setFormIcon]       = useState('📦');
  const [deleteTarget, setDeleteTarget] = useState(null);

  const openAdd = () => { setEditTarget(null); setFormName(''); setFormIcon('📦'); setShowModal(true); };
  const openEdit = (cat) => { setEditTarget(cat); setFormName(cat.name); setFormIcon(cat.icon); setShowModal(true); };

  const handleSave = () => {
    if (!formName.trim()) return;
    if (editTarget) {
      setCategories((cs) => cs.map((c) => c.id === editTarget.id ? { ...c, name: formName, icon: formIcon } : c));
    } else {
      setCategories((cs) => [...cs, { id: Date.now(), name: formName, icon: formIcon, count: 0, color: '#081B32' }]);
    }
    setShowModal(false);
  };

  const handleDelete = () => {
    setCategories((cs) => cs.filter((c) => c.id !== deleteTarget.id));
    setDeleteTarget(null);
  };

  const total = categories.reduce((s, c) => s + c.count, 0);

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Categories</h2>
          <p className="page-subtitle">Organise assets into groups for easier management.</p>
        </div>
        <div className="page-header-right">
          <button className="btn btn-primary" onClick={openAdd}>
            <PlusSvg size={16} /> Add Category
          </button>
        </div>
      </div>

      {/* Summary strip */}
      <div className="card" style={{ marginBottom: 'var(--sp-xl)', padding: 'var(--sp-md) var(--sp-lg)' }}>
        <div style={{ display: 'flex', gap: 'var(--sp-xl)', flexWrap: 'wrap' }}>
          <div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Total Categories</p>
            <p style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>{categories.length}</p>
          </div>
          <div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 500 }}>Total Assets</p>
            <p style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>{total.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Category grid */}
      <div className="grid-3">
        {categories.map((cat) => (
          <div key={cat.id} className="card" style={{ position: 'relative', transition: 'box-shadow 0.15s' }}>
            {/* Color bar */}
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, height: 4,
              background: cat.color, borderRadius: 'var(--r-lg) var(--r-lg) 0 0',
            }} />
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginTop: 8 }}>
              <div style={{ fontSize: 32 }}>{cat.icon}</div>
              <div style={{ display: 'flex', gap: 4 }}>
                <button className="btn btn-ghost btn-icon btn-sm" title="Edit" onClick={() => openEdit(cat)}>
                  <EditSvg size={14} />
                </button>
                <button className="btn btn-ghost btn-icon btn-sm" title="Delete" onClick={() => setDeleteTarget(cat)}>
                  <TrashSvg size={14} />
                </button>
              </div>
            </div>
            <div style={{ marginTop: 'var(--sp-md)' }}>
              <p style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-primary)' }}>{cat.name}</p>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
                <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{cat.count}</strong> assets
              </p>
            </div>
          </div>
        ))}

        {/* Add new card */}
        <button
          className="card"
          onClick={openAdd}
          style={{
            border: '2px dashed var(--border)',
            background: 'transparent',
            cursor: 'pointer',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 'var(--sp-sm)',
            minHeight: 140,
            transition: 'border-color 0.15s, background 0.15s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.background = 'var(--surface-muted)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.background = 'transparent'; }}
        >
          <div style={{ width: 40, height: 40, borderRadius: 'var(--r-full)', background: 'var(--surface-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <PlusSvg size={20} />
          </div>
          <p style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)' }}>Add Category</p>
        </button>
      </div>

      {/* Table view */}
      <div style={{ marginTop: 'var(--sp-xl)' }}>
        <p className="section-title">All Categories</p>
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr><th>Category</th><th>Assets</th><th>% of Total</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {categories.map((cat) => (
                <tr key={cat.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: 20 }}>{cat.icon}</span>
                      <span style={{ fontWeight: 500 }}>{cat.name}</span>
                    </div>
                  </td>
                  <td>{cat.count}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ flex: 1, height: 6, background: 'var(--border)', borderRadius: 'var(--r-full)', overflow: 'hidden', maxWidth: 120 }}>
                        <div style={{ height: '100%', width: `${total ? (cat.count / total * 100) : 0}%`, background: cat.color, borderRadius: 'var(--r-full)' }} />
                      </div>
                      <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                        {total ? Math.round(cat.count / total * 100) : 0}%
                      </span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button className="btn btn-ghost btn-sm btn-icon" onClick={() => openEdit(cat)}><EditSvg size={14} /></button>
                      <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setDeleteTarget(cat)}><TrashSvg size={14} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{editTarget ? 'Edit Category' : 'Add Category'}</h3>
              <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
                <div className="form-group">
                  <label className="form-label">Icon (emoji)</label>
                  <input className="input" value={formIcon} onChange={(e) => setFormIcon(e.target.value)} placeholder="e.g. 📦" style={{ fontSize: 20, width: 80 }} />
                </div>
                <div className="form-group">
                  <label className="form-label">Category Name <span className="required">*</span></label>
                  <input className="input" value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="e.g. Electronics" autoFocus />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={!formName.trim()}>
                {editTarget ? 'Save Changes' : 'Add Category'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirm */}
      {deleteTarget && (
        <div className="modal-overlay" onClick={() => setDeleteTarget(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Delete Category</h3>
              <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setDeleteTarget(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                Are you sure you want to delete <strong>{deleteTarget.name}</strong>?{' '}
                {deleteTarget.count > 0 && <span style={{ color: 'var(--error)' }}>This category has {deleteTarget.count} assets — they will become uncategorised.</span>}
              </p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setDeleteTarget(null)}>Cancel</button>
              <button className="btn btn-danger" onClick={handleDelete}>Delete</button>
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
function EditSvg({ size = 14 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>;
}
function TrashSvg({ size = 14 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>;
}
