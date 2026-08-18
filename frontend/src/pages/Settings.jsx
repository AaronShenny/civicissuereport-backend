import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthProvider';
import { api } from '../lib/api';

const TABS = ['Profile', 'Notifications', 'System', 'Security'];

export default function Settings() {
  const { profile: authProfile, role } = useAuth();
  const [activeTab, setActiveTab] = useState('Profile');
  
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [timezone, setTimezone] = useState('UTC+05:30');
  
  const [notifs, setNotifs] = useState({
    maintenanceDue: true, assetAssigned: true, newAsset: false, reportReady: true, lowStock: false,
  });
  
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (authProfile) {
      setName(authProfile.full_name || '');
      setEmail(authProfile.email || '');
      setPhone(authProfile.phone || '');
    }
  }, [authProfile]);

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSaved(false);
      
      // Update full_name and phone via PATCH /users/me/
      await api.patch('/users/me/', {
        full_name: name,
        phone: phone
      });
      
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      
      // Optionally trigger reload of session profile if needed, but the inputs are already updated.
    } catch (err) {
      setError(err.data?.detail || err.message || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const displayRole = role ? role.replace(/_/g, ' ') : 'User';

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Settings</h2>
          <p className="page-subtitle">Manage your account and system preferences.</p>
        </div>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button key={t} className={`tab${activeTab === t ? ' active' : ''}`} onClick={() => setActiveTab(t)}>{t}</button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'Profile' && (
        <div style={{ maxWidth: 600 }}>
          {error && (
            <div className="alert alert-error" style={{ marginBottom: 'var(--sp-md)' }}>
              {error}
            </div>
          )}

          <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
            <p className="section-title">Profile Information</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-lg)', marginBottom: 'var(--sp-xl)', paddingBottom: 'var(--sp-xl)', borderBottom: '1px solid var(--border)' }}>
              <div className="avatar avatar-lg" style={{ width: 72, height: 72, fontSize: 28 }}>
                {name ? name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div>
                <p style={{ fontWeight: 600, fontSize: 16 }}>{name || 'User'}</p>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{displayRole}</p>
              </div>
            </div>
            <div className="grid-2" style={{ gap: 'var(--sp-md)' }}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input className="input" value={name} onChange={(e) => setName(e.target.value)} disabled={saving} />
              </div>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input className="input" type="email" value={email} disabled style={{ background: 'var(--surface-muted)', color: 'var(--text-muted)' }} />
              </div>
              <div className="form-group">
                <label className="form-label">Phone</label>
                <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} disabled={saving} />
              </div>
              <div className="form-group">
                <label className="form-label">Timezone</label>
                <select className="select" value={timezone} onChange={(e) => setTimezone(e.target.value)} disabled={saving}>
                  {['UTC-08:00', 'UTC-05:00', 'UTC+00:00', 'UTC+01:00', 'UTC+05:30', 'UTC+08:00'].map((t) => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Role</label>
                <input className="input" value={displayRole} disabled style={{ background: 'var(--surface-muted)', color: 'var(--text-muted)', textTransform: 'capitalize' }} />
                <span className="form-hint">Contact a super admin to change your role.</span>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--sp-sm)' }}>
            {saved && <span style={{ fontSize: 13, color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>✓ Saved</span>}
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'Notifications' && (
        <div style={{ maxWidth: 600 }}>
          <div className="card">
            <p className="section-title">Email Notifications</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {[
                { key: 'maintenanceDue',  label: 'Maintenance Due',      desc: 'Get notified when a maintenance task is due.' },
                { key: 'assetAssigned',   label: 'Asset Assigned',       desc: 'Get notified when an asset is assigned to you.' },
                { key: 'newAsset',        label: 'New Asset Added',      desc: 'Get notified when a new asset is registered.' },
                { key: 'reportReady',     label: 'Report Ready',         desc: 'Get notified when a report is generated.' },
                { key: 'lowStock',        label: 'Low Stock Alert',      desc: 'Alert when available asset count drops below threshold.' },
              ].map((n, i, arr) => (
                <div
                  key={n.key}
                  style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: 'var(--sp-md) 0',
                    borderBottom: i < arr.length - 1 ? '1px solid var(--border)' : 'none',
                  }}
                >
                  <div>
                    <p style={{ fontSize: 14, fontWeight: 500 }}>{n.label}</p>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{n.desc}</p>
                  </div>
                  {/* Toggle */}
                  <button
                    role="switch"
                    aria-checked={notifs[n.key]}
                    onClick={() => setNotifs((prev) => ({ ...prev, [n.key]: !prev[n.key] }))}
                    style={{
                      width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer', flexShrink: 0,
                      background: notifs[n.key] ? 'var(--primary)' : 'var(--border)',
                      position: 'relative', transition: 'background 0.2s',
                    }}
                  >
                    <span style={{
                      position: 'absolute', top: 3, left: notifs[n.key] ? 23 : 3,
                      width: 18, height: 18, borderRadius: '50%', background: '#fff',
                      transition: 'left 0.2s', display: 'block',
                    }} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* System Tab */}
      {activeTab === 'System' && (
        <div style={{ maxWidth: 600 }}>
          <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
            <p className="section-title">System Preferences</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
              <div className="form-group">
                <label className="form-label">Organization Name</label>
                <input className="input" defaultValue="Acme Corporation" />
              </div>
              <div className="form-group">
                <label className="form-label">Currency</label>
                <select className="select">
                  <option>USD ($)</option><option>EUR (€)</option><option>GBP (£)</option><option>INR (₹)</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Date Format</label>
                <select className="select">
                  <option>MM/DD/YYYY</option><option>DD/MM/YYYY</option><option>YYYY-MM-DD</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Asset ID Prefix</label>
                <input className="input" defaultValue="AST-" />
                <span className="form-hint">Used when auto-generating asset IDs (e.g. AST-001)</span>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary" onClick={handleSave}>Save System Settings</button>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'Security' && (
        <div style={{ maxWidth: 600 }}>
          <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
            <p className="section-title">Change Password</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-md)' }}>
              <div className="form-group">
                <label className="form-label">Current Password</label>
                <input type="password" className="input" placeholder="Enter current password" />
              </div>
              <div className="form-group">
                <label className="form-label">New Password</label>
                <input type="password" className="input" placeholder="Enter new password" />
              </div>
              <div className="form-group">
                <label className="form-label">Confirm New Password</label>
                <input type="password" className="input" placeholder="Re-enter new password" />
              </div>
            </div>
            <div style={{ marginTop: 'var(--sp-lg)', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-primary">Update Password</button>
            </div>
          </div>
          <div className="card">
            <p className="section-title">Danger Zone</p>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 'var(--sp-md)' }}>
              Permanently delete your account and all associated data. This action cannot be undone.
            </p>
            <button className="btn btn-danger btn-sm">Delete Account</button>
          </div>
        </div>
      )}
    </div>
  );
}
