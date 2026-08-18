import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const CATEGORIES = ['IT Equipment', 'Furniture', 'Vehicles', 'Machinery', 'Office Supplies', 'Other'];
const STATUSES   = ['Active', 'Available', 'Maintenance', 'Retired'];
const LOCATIONS  = ['HQ – Floor 1', 'HQ – Floor 2', 'HQ – Floor 3', 'Warehouse', 'Remote', 'Copy Room', 'Storage', 'Parking B'];
const PEOPLE     = ['Sarah Chen', 'Mark Davis', 'Priya Sharma', 'Julia Roberts', 'Tom Wilson', 'Shared', 'Fleet', 'Production', 'Reception'];

const EMPTY = {
  name: '', category: 'IT Equipment', status: 'Active',
  serialNumber: '', model: '', manufacturer: '',
  value: '', purchaseDate: '', warrantyExpiry: '',
  assignedTo: '', location: '', condition: 'Good', description: '',
};

export default function AssetForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);

  const [form, setForm] = useState(isEdit
    ? { ...EMPTY, name: 'MacBook Pro 16"', category: 'IT Equipment', status: 'Active', serialNumber: 'C02XL0ADJGH5', model: 'MacBook Pro 16" M3 Pro', manufacturer: 'Apple', value: '2499', purchaseDate: '2024-01-15', warrantyExpiry: '2027-01-15', assignedTo: 'Sarah Chen', location: 'HQ – Floor 3', condition: 'Excellent', description: 'Company-issued laptop for senior engineers. 16GB RAM, 512GB SSD.' }
    : EMPTY
  );
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    if (errors[name]) setErrors((err) => ({ ...err, [name]: '' }));
  };

  const validate = () => {
    const e = {};
    if (!form.name.trim())         e.name = 'Asset name is required.';
    if (!form.serialNumber.trim()) e.serialNumber = 'Serial number is required.';
    if (!form.value.trim())        e.value = 'Value is required.';
    if (!form.purchaseDate)        e.purchaseDate = 'Purchase date is required.';
    return e;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      navigate('/assets');
    }, 800);
  };

  return (
    <div>
      {/* Breadcrumb */}
      <div className="breadcrumb">
        <button className="btn btn-ghost btn-sm" style={{ height: 'auto', padding: '2px 0', fontSize: 14, color: 'var(--text-secondary)' }}
          onClick={() => navigate('/assets')}>Assets</button>
        <span className="breadcrumb-sep">/</span>
        {isEdit && (
          <>
            <button className="btn btn-ghost btn-sm" style={{ height: 'auto', padding: '2px 0', fontSize: 14, color: 'var(--text-secondary)' }}
              onClick={() => navigate(`/assets/${id}`)}>
              {form.name}
            </button>
            <span className="breadcrumb-sep">/</span>
          </>
        )}
        <span className="breadcrumb-current">{isEdit ? 'Edit' : 'New Asset'}</span>
      </div>

      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">{isEdit ? 'Edit Asset' : 'Add New Asset'}</h2>
          <p className="page-subtitle">{isEdit ? 'Update the asset information below.' : 'Fill in the details to register a new asset.'}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ maxWidth: 760 }}>
        {/* Basic Info */}
        <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
          <p className="section-title">Basic Information</p>
          <div className="grid-2" style={{ gap: 'var(--sp-md)' }}>
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label className="form-label" htmlFor="name">Asset Name <span className="required">*</span></label>
              <input id="name" name="name" className={`input${errors.name ? ' error' : ''}`} placeholder="e.g. MacBook Pro 16&quot;" value={form.name} onChange={handleChange} />
              {errors.name && <span className="form-error">{errors.name}</span>}
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="manufacturer">Manufacturer</label>
              <input id="manufacturer" name="manufacturer" className="input" placeholder="e.g. Apple" value={form.manufacturer} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="model">Model</label>
              <input id="model" name="model" className="input" placeholder="e.g. MacBook Pro 16&quot; M3 Pro" value={form.model} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="serialNumber">Serial Number <span className="required">*</span></label>
              <input id="serialNumber" name="serialNumber" className={`input${errors.serialNumber ? ' error' : ''}`} placeholder="e.g. C02XL0ADJGH5" value={form.serialNumber} onChange={handleChange} />
              {errors.serialNumber && <span className="form-error">{errors.serialNumber}</span>}
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="condition">Condition</label>
              <select id="condition" name="condition" className="select" value={form.condition} onChange={handleChange}>
                {['Excellent', 'Good', 'Fair', 'Poor'].map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label className="form-label" htmlFor="description">Description</label>
              <textarea id="description" name="description" className="textarea" placeholder="Add a brief description…" value={form.description} onChange={handleChange} />
            </div>
          </div>
        </div>

        {/* Classification */}
        <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
          <p className="section-title">Classification</p>
          <div className="grid-2" style={{ gap: 'var(--sp-md)' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="category">Category</label>
              <select id="category" name="category" className="select" value={form.category} onChange={handleChange}>
                {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="status">Status</label>
              <select id="status" name="status" className="select" value={form.status} onChange={handleChange}>
                {STATUSES.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Financial */}
        <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
          <p className="section-title">Financial</p>
          <div className="grid-2" style={{ gap: 'var(--sp-md)' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="value">Purchase Value ($) <span className="required">*</span></label>
              <input id="value" name="value" type="number" className={`input${errors.value ? ' error' : ''}`} placeholder="0.00" value={form.value} onChange={handleChange} />
              {errors.value && <span className="form-error">{errors.value}</span>}
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="purchaseDate">Purchase Date <span className="required">*</span></label>
              <input id="purchaseDate" name="purchaseDate" type="date" className={`input${errors.purchaseDate ? ' error' : ''}`} value={form.purchaseDate} onChange={handleChange} />
              {errors.purchaseDate && <span className="form-error">{errors.purchaseDate}</span>}
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="warrantyExpiry">Warranty Expiry</label>
              <input id="warrantyExpiry" name="warrantyExpiry" type="date" className="input" value={form.warrantyExpiry} onChange={handleChange} />
            </div>
          </div>
        </div>

        {/* Assignment */}
        <div className="card" style={{ marginBottom: 'var(--sp-xl)' }}>
          <p className="section-title">Assignment</p>
          <div className="grid-2" style={{ gap: 'var(--sp-md)' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="assignedTo">Assigned To</label>
              <select id="assignedTo" name="assignedTo" className="select" value={form.assignedTo} onChange={handleChange}>
                <option value="">— Unassigned —</option>
                {PEOPLE.map((p) => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="location">Location</label>
              <select id="location" name="location" className="select" value={form.location} onChange={handleChange}>
                <option value="">— Select location —</option>
                {LOCATIONS.map((l) => <option key={l}>{l}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 'var(--sp-sm)', justifyContent: 'flex-end' }}>
          <button type="button" className="btn btn-secondary" onClick={() => navigate(isEdit ? `/assets/${id}` : '/assets')}>
            Cancel
          </button>
          <button id="asset-form-submit" type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Asset'}
          </button>
        </div>
      </form>
    </div>
  );
}
