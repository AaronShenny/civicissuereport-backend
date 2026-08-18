import React, { useMemo } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';

export default function Sidebar() {
  const navigate = useNavigate();
  const { profile, role, loading, profileError } = useAuth();

  const navItems = useMemo(() => {
    const items = [];

    // Everyone gets a dashboard
    items.push({
      section: 'Overview',
      items: [{ to: '/dashboard', label: 'Dashboard', icon: GridIcon }],
    });

    if (role === 'citizen') {
      items.push({
        section: 'Complaints',
        items: [
          { to: '/complaints/new', label: 'Report Issue', icon: PlusIcon },
          { to: '/complaints', label: 'My Complaints', icon: ListIcon },
        ],
      });
    }

    if (role === 'ground_level_employee') {
      items.push({
        section: 'Work Queue',
        items: [
          { to: '/employee/complaints', label: 'Assigned to Me', icon: InboxIcon },
        ],
      });
    }

    if (role === 'supervisor') {
      items.push({
        section: 'Department',
        items: [
          { to: '/supervisor/unassigned', label: 'Unassigned', icon: AlertIcon },
          { to: '/supervisor/complaints', label: 'All Complaints', icon: FolderIcon },
        ],
      });
    }

    if (role === 'department_admin') {
      items.push({
        section: 'Department',
        items: [
          { to: '/department/complaints', label: 'All Complaints', icon: FolderIcon },
        ],
      });
    }

    if (role === 'system_admin') {
      items.push({
        section: 'Administration',
        items: [
          { to: '/admin/overview', label: 'System Overview', icon: ChartIcon },
        ],
      });
    }

    // Removed Legacy AssetFlow links completely per user instruction

    return items;
  }, [role]);

  let displayRole = 'Loading...';
  if (profileError) {
    displayRole = 'Error loading role';
  } else if (!loading && role) {
    displayRole = role.replace(/_/g, ' ');
  } else if (!loading && !role) {
    displayRole = 'Unknown Role';
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark" style={{ background: 'var(--primary)', color: 'var(--surface)' }}>C</div>
        <span className="sidebar-logo-text">CivicConnect</span>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {navItems.map((group) => (
          <div key={group.section}>
            <p className="sidebar-section-label">{group.section}</p>
            {group.items.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end
                className={({ isActive }) =>
                  `sidebar-nav-item${isActive ? ' active' : ''}`
                }
              >
                <Icon size={18} />
                {label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* User */}
      <div className="sidebar-footer">
        <div className="sidebar-user" onClick={() => navigate('/settings')}>
          <div className="sidebar-avatar" style={{ background: profileError ? 'var(--error)' : undefined }}>
            {profile?.full_name ? profile.full_name.charAt(0).toUpperCase() : (profileError ? '!' : 'U')}
          </div>
          <div className="sidebar-user-info">
            <p className="sidebar-user-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: profileError ? 'var(--error)' : undefined }}>
              {profileError ? 'Session Error' : (profile?.full_name || (loading ? 'Loading...' : 'Unknown User'))}
            </p>
            <p className="sidebar-user-role" style={{ textTransform: 'capitalize', color: profileError ? 'var(--error)' : undefined }}>
              {displayRole}
            </p>
          </div>
          <ChevronIcon size={14} color="rgba(255,255,255,0.4)" />
        </div>
      </div>
    </aside>
  );
}

// Icons
function GridIcon({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>;
}
function PlusIcon({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
}
function ListIcon({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>;
}
function InboxIcon({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>;
}
function AlertIcon({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>;
}
function FolderIcon({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>;
}
function ChartIcon({ size = 20 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>;
}
function ChevronIcon({ size = 16, color = 'currentColor' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>;
}
