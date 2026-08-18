import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const pageTitles = {
  '/dashboard':   'Dashboard',
  '/assets':      'Assets',
  '/categories':  'Categories',
  '/assignments': 'Assignments',
  '/maintenance': 'Maintenance',
  '/reports':     'Reports',
  '/users':       'Users & Team',
  '/settings':    'Settings',
};

export default function Header() {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  // Match longest prefix
  const title = Object.entries(pageTitles)
    .sort((a, b) => b[0].length - a[0].length)
    .find(([path]) => pathname.startsWith(path))?.[1] ?? 'AssetFlow';

  return (
    <header className="top-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-sm)' }}>
        <button
          className="btn btn-ghost btn-icon"
          title="Go Back"
          onClick={() => navigate(-1)}
          style={{ marginRight: 'var(--sp-sm)' }}
        >
          <ArrowLeftIcon size={18} />
        </button>
        <h1 className="top-header-title">{title}</h1>
      </div>
      <div className="top-header-actions">
        <button className="btn btn-ghost btn-icon" title="Notifications">
          <BellIcon size={18} />
        </button>
        <div className="avatar avatar-md" style={{ background: 'var(--secondary)', fontSize: 13 }}>
          AD
        </div>
      </div>
    </header>
  );
}

function ArrowLeftIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  );
}

function BellIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
  );
}
