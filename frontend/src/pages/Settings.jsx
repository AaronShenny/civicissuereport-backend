import React, { useState } from 'react';

const TABS = ['Profile', 'Notifications', 'System', 'Security'];

export default function Settings() {
  const [activeTab, setActiveTab] = useState('Profile');
  const [profile, setProfile] = useState({
    name: 'Admin User', email: 'admin@company.com', role: 'Administrator', phone: '+1 (555) 012-3456', timezone: 'UTC+05:30',
  });
  const [notifs, setNotifs] = useState({
    maintenanceDue: true, assetAssigned: true, newAsset: false, reportReady: true, lowStock: false,
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

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
          <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
            <p className="section-title">Profile Information</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-lg)', marginBottom: 'var(--sp-xl)', paddingBottom: 'var(--sp-xl)', borderBottom: '1px solid var(--border)' }}>
              <div className="avatar avatar-lg" style={{ width: 72, height: 72, fontSize: 28 }}>
                {profile.name.charAt(0)}
              </div>
              <div>
                <p style={{ fontWeight: 600, fontSize: 16 }}>{profile.name}</p>
                <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{profile.role}</p>
                <button className="btn btn-secondary btn-sm" style={{ marginTop: 8 }}>Change Avatar</button>
              </div>
            </div>
            <div className="grid-2" style={{ gap: 'var(--sp-md)' }}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input className="input" value={profile.name} onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input className="input" type="email" value={profile.email} onChange={(e) => setProfile((p) => ({ ...p, email: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Phone</label>
                <input className="input" value={profile.phone} onChange={(e) => setProfile((p) => ({ ...p, phone: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Timezone</label>
                <select className="select" value={profile.timezone} onChange={(e) => setProfile((p) => ({ ...p, timezone: e.target.value }))}>
                  {['UTC-08:00', 'UTC-05:00', 'UTC+00:00', 'UTC+01:00', 'UTC+05:30', 'UTC+08:00'].map((t) => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Role</label>
                <input className="input" value={profile.role} disabled style={{ background: 'var(--surface-muted)', color: 'var(--text-muted)' }} />
                <span className="form-hint">Contact a super admin to change your role.</span>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--sp-sm)' }}>
            {saved && <span style={{ fontSize: 13, color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>✓ Saved</span>}
            <button className="btn btn-primary" onClick={handleSave}>Save Changes</button>
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
