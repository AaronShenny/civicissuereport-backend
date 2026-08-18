import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

/* ─────────────────────────────────────────
   Inline SVG icon helpers
───────────────────────────────────────── */
const Icon = ({ d, size = 20, strokeWidth = 1.75, fill = 'none', stroke = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke={stroke}
    strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round">
    {Array.isArray(d) ? d.map((path, i) => <path key={i} d={path} />) : <path d={d} />}
  </svg>
);

const CheckCircle = ({ size = 12 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

/* ─────────────────────────────────────────
   Role data
───────────────────────────────────────── */
const ROLES = [
  {
    id: 'citizen',
    emoji: '👤',
    bg: '#EBF5F1',
    name: 'Citizen',
    desc: 'Anyone who wants to report a public issue in their community.',
    caps: [
      'Submit complaints with evidence',
      'Track complaint progress',
      'View nearby public issues',
      'Receive status notifications',
    ],
  },
  {
    id: 'employee',
    emoji: '🛠️',
    bg: '#E8F4FF',
    name: 'Ground-Level Employee',
    desc: 'Field staff who verify and update issues on the ground.',
    caps: [
      'View assigned complaints',
      'Verify reported issues on-site',
      'Update complaint progress',
      'Upload resolution proof',
    ],
  },
  {
    id: 'supervisor',
    emoji: '📋',
    bg: '#FEF9EB',
    name: 'Supervisor',
    desc: 'Team leads who oversee operations and handle escalations.',
    caps: [
      'Monitor all department complaints',
      'Assign and reassign employees',
      'Track high-priority & overdue issues',
      'Monitor team workload',
    ],
  },
  {
    id: 'dept_admin',
    emoji: '🏢',
    bg: '#FFF0F3',
    name: 'Department Admin',
    desc: 'Department-level administrators who manage performance and staff.',
    caps: [
      'Monitor department performance',
      'Manage department employees',
      'Review complaint workload',
      'Access department-level reports',
    ],
  },
  {
    id: 'sys_admin',
    emoji: '⚙️',
    bg: '#F0F0FF',
    name: 'System Admin',
    desc: 'Platform administrators with full system-wide access.',
    caps: [
      'Manage all users and accounts',
      'Manage departments',
      'Configure roles & permissions',
      'Monitor system-wide statistics',
    ],
  },
];

/* ─────────────────────────────────────────
   Main component
───────────────────────────────────────── */
export default function Landing() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeRole, setActiveRole] = useState('citizen');
  const [trackId, setTrackId] = useState('');
  const [trackError, setTrackError] = useState('');

  const role = ROLES.find(r => r.id === activeRole);

  const scrollTo = (id) => {
    setMenuOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleTrack = (e) => {
    e.preventDefault();
    if (!trackId.trim()) {
      setTrackError('Please enter a Complaint ID.');
      return;
    }
    setTrackError('');
    navigate(`/track?id=${encodeURIComponent(trackId.trim())}`);
  };

  return (
    <div className="civic-landing">

      {/* ═══════════════════════════════
          NAVIGATION BAR
      ═══════════════════════════════ */}
      <nav className="civic-nav" id="home">
        <div className="civic-nav-inner">
          {/* Logo */}
          <a className="civic-logo" onClick={() => scrollTo('home')} style={{ cursor: 'pointer' }}>
            <div className="civic-logo-icon">
              <Icon size={20} stroke="#fff" d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10" />
            </div>
            <div className="civic-logo-text">
              <span className="civic-logo-name">CivicConnect</span>
              <span className="civic-logo-tag">Report · Track · Resolve</span>
            </div>
          </a>

          {/* Desktop Nav Links */}
          <div className="civic-nav-links">
            <button className="civic-nav-link" onClick={() => scrollTo('home')}>Home</button>
            <button className="civic-nav-link" onClick={() => scrollTo('how-it-works')}>How It Works</button>
            <button className="civic-nav-link" onClick={() => scrollTo('track')}>Track Complaint</button>
            <button className="civic-nav-link" onClick={() => scrollTo('features')}>About</button>
          </div>

          {/* Desktop Actions */}
          <div className="civic-nav-actions">
            <button className="civic-btn-outline" onClick={() => navigate('/login')}>Login</button>
            <button className="civic-btn-primary" onClick={() => navigate('/login')}>
              Report an Issue
            </button>
          </div>

          {/* Hamburger */}
          <button className="civic-hamburger" onClick={() => setMenuOpen(o => !o)} aria-label="Toggle menu">
            <span /><span /><span />
          </button>
        </div>

        {/* Mobile Menu */}
        <div className={`civic-mobile-menu${menuOpen ? ' open' : ''}`}>
          <button className="civic-nav-link" style={{ width: '100%', textAlign: 'left' }} onClick={() => scrollTo('home')}>Home</button>
          <button className="civic-nav-link" style={{ width: '100%', textAlign: 'left' }} onClick={() => scrollTo('how-it-works')}>How It Works</button>
          <button className="civic-nav-link" style={{ width: '100%', textAlign: 'left' }} onClick={() => scrollTo('track')}>Track Complaint</button>
          <button className="civic-nav-link" style={{ width: '100%', textAlign: 'left' }} onClick={() => scrollTo('features')}>About</button>
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <button className="civic-btn-outline" style={{ flex: 1 }} onClick={() => navigate('/login')}>Login</button>
            <button className="civic-btn-primary" style={{ flex: 1 }} onClick={() => navigate('/login')}>Report Issue</button>
          </div>
        </div>
      </nav>

      {/* ═══════════════════════════════
          HERO SECTION
      ═══════════════════════════════ */}
      <section className="civic-hero">
        <div className="civic-hero-inner">
          {/* Left */}
          <div className="civic-hero-left">
            <div className="civic-hero-eyebrow">
              <div className="civic-hero-eyebrow-dot" />
              Civic Issue Reporting Platform
            </div>
            <h1 className="civic-hero-title">
              A better way to report and resolve public issues.
            </h1>
            <p className="civic-hero-sub">
              Report civic problems in your area, track their progress, and stay informed as the responsible authorities take action.
            </p>
            <div className="civic-hero-actions">
              <button className="civic-btn-primary-lg" onClick={() => navigate('/login')}>
                <Icon size={18} d="M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                Report an Issue
              </button>
              <button
                className="civic-btn-outline-lg"
                style={{ borderColor: 'var(--border)', color: 'var(--primary)' }}
                onClick={() => scrollTo('track')}
              >
                <Icon size={18} d="M21 10H3 M21 6H3 M21 14H3 M21 18H3" />
                Track a Complaint
              </button>
            </div>

            <div className="civic-trust-row">
              {[
                'Easy to report',
                'Track progress in real time',
                'Connected to the right department',
              ].map(t => (
                <div className="civic-trust-item" key={t}>
                  <div className="civic-trust-icon"><CheckCircle /></div>
                  {t}
                </div>
              ))}
            </div>
          </div>

          {/* Right — Visual Composition */}
          <div className="civic-hero-visual">
            {/* Map area */}
            <div className="civic-map-area">
              <div className="civic-map-grid" />
              {/* Roads */}
              <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.25 }} viewBox="0 0 400 220" preserveAspectRatio="xMidYMid slice">
                <line x1="0" y1="110" x2="400" y2="110" stroke="#081B32" strokeWidth="12" />
                <line x1="200" y1="0" x2="200" y2="220" stroke="#081B32" strokeWidth="8" />
                <line x1="0" y1="55" x2="400" y2="55" stroke="#081B32" strokeWidth="4" />
                <line x1="0" y1="165" x2="400" y2="165" stroke="#081B32" strokeWidth="4" />
              </svg>
              <div className="civic-map-pin" />
              <div className="civic-map-label">📍 MG Road, Sector 14</div>
            </div>

            {/* Card A — complaint detail */}
            <div className="civic-issue-card civic-card-a">
              <div className="civic-card-header">
                <span className="civic-card-id">CMP-2026-04821</span>
                <span className="civic-status-pill civic-status-active">● Active</span>
              </div>
              <div className="civic-card-title">Pothole — Road Damage</div>
              <div className="civic-card-sub">Submitted 2 hours ago · NH-48, Sector 14</div>
              <div className="civic-progress-bar">
                <div className="civic-progress-fill" style={{ width: '60%' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 11, color: 'var(--text-muted)' }}>
                <span>Submitted</span><span>Verified</span><span style={{ fontWeight: 700, color: 'var(--secondary)' }}>In Progress</span><span>Resolved</span>
              </div>
              <div className="civic-dept-tag">
                <Icon size={12} d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75" />
                Roads & Infrastructure Dept.
              </div>
            </div>

            {/* Card B — priority */}
            <div className="civic-issue-card civic-card-b">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <div style={{ width: 32, height: 32, background: '#FFF0F3', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={16} stroke="#EB2C50" d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z M12 9v4 M12 17h.01" />
                </div>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--error)' }}>HIGH PRIORITY</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>AI Assessment</div>
                </div>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Severity: <strong>High</strong> · Duplicates: <strong>3 similar</strong>
              </div>
            </div>

            {/* Card C — resolution */}
            <div className="civic-issue-card civic-card-c">
              <div className="civic-card-header">
                <span className="civic-card-id">CMP-2026-03915</span>
                <span className="civic-status-pill civic-status-resolved">✓ Resolved</span>
              </div>
              <div className="civic-card-title">Streetlight Failure</div>
              <div className="civic-card-sub">Resolved in 3.5 days</div>
              <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                <div style={{ flex: 1, height: 5, background: 'var(--secondary)', borderRadius: 3 }} />
              </div>
              <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                ✅ Verified by Electrical Dept.
              </div>
            </div>

            {/* Card D — notification */}
            <div className="civic-issue-card civic-card-d">
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <div style={{ width: 28, height: 28, background: '#EBF5F1', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Icon size={14} stroke="var(--secondary)" d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9 M13.73 21a2 2 0 0 1-3.46 0" />
                </div>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--primary)', marginBottom: 2 }}>Update Received</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.4 }}>Your complaint has been assigned to a field officer.</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom fade */}
        <div style={{ height: 64, background: 'linear-gradient(to bottom, transparent, #F5F7FA)' }} />
      </section>

      {/* ═══════════════════════════════
          TRACK COMPLAINT SECTION
      ═══════════════════════════════ */}
      <section className="civic-track-section" id="track">
        <div className="civic-track-inner">
          <div>
            <h2 className="civic-track-title">Already reported an issue?</h2>
            <p className="civic-track-sub">
              Enter your Complaint ID to check its latest status and progress.
            </p>
          </div>
          <div>
            <form onSubmit={handleTrack} noValidate>
              <div className="civic-track-form">
                <input
                  className="civic-track-input"
                  type="text"
                  placeholder="CMP-2026-XXXXX"
                  value={trackId}
                  onChange={e => { setTrackId(e.target.value); setTrackError(''); }}
                  aria-label="Complaint ID"
                />
                <button type="submit" className="civic-btn-green" style={{ height: 48, padding: '0 24px', fontSize: 14 }}>
                  Track Complaint
                </button>
              </div>
              {trackError && (
                <p style={{ color: 'var(--error)', fontSize: 12, marginTop: 6 }}>{trackError}</p>
              )}
            </form>
            <p className="civic-track-link">
              Don't have a Complaint ID?{' '}
              <a onClick={() => navigate('/login')}>Sign in to view My Complaints.</a>
            </p>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════
          HOW IT WORKS
      ═══════════════════════════════ */}
      <section className="civic-section" id="how-it-works">
        <div className="civic-section-inner">
          <div className="civic-section-label">
            <Icon size={14} d="M12 2L2 7l10 5 10-5-10-5z M2 17l10 5 10-5 M2 12l10 5 10-5" />
            Process
          </div>
          <h2 className="civic-section-title">From report to resolution</h2>
          <p className="civic-section-subtitle">
            A transparent four-step process that takes your complaint from submission to verified resolution.
          </p>

          <div className="civic-steps">
            {[
              {
                step: '01',
                label: 'Step 1',
                title: 'Report',
                text: 'Tell us what happened, add a description, upload photo evidence, and pin the exact location on the map.',
                icon: 'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z M12 7v5l3 3',
              },
              {
                step: '02',
                label: 'Step 2',
                title: 'Smart Assessment',
                text: 'The system classifies the complaint, assesses severity and priority, and identifies possible duplicate reports.',
                icon: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M12 8v4l3 3',
              },
              {
                step: '03',
                label: 'Step 3',
                title: 'Assigned & Verified',
                text: 'The complaint is routed to the responsible department and reviewed by authorized staff before action begins.',
                icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
              },
              {
                step: '04',
                label: 'Step 4',
                title: 'Resolved & Updated',
                text: 'Track progress in real time, receive updates at every stage, and view the final verified resolution.',
                icon: 'M22 11.08V12a10 10 0 1 1-5.93-9.14 M22 4L12 14.01l-3-3',
              },
            ].map(s => (
              <div className="civic-step" key={s.step}>
                <div className="civic-step-num">
                  <Icon size={22} d={s.icon} />
                </div>
                <div className="civic-step-label">{s.label}</div>
                <div className="civic-step-title">{s.title}</div>
                <p className="civic-step-text">{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════
          FEATURES
      ═══════════════════════════════ */}
      <section className="civic-section civic-features-bg" id="features">
        <div className="civic-section-inner">
          <div className="civic-section-label">
            <Icon size={14} d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            Features
          </div>
          <h2 className="civic-section-title">Built to make public issue reporting simpler</h2>
          <p className="civic-section-subtitle">
            Every feature is designed with citizens and government staff in mind — clear, simple, and effective.
          </p>

          <div className="civic-features-grid">
            {[
              {
                icon: 'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z M15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0z',
                title: 'Smart Complaint Reporting',
                text: 'Report an issue with description, category, location, and optional photo or video evidence.',
              },
              {
                icon: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M12 8v4 M12 16h.01',
                title: 'AI-Assisted Classification',
                text: 'Complaints are categorized and assessed using AI, with manual review available when needed.',
              },
              {
                icon: 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z M12 9v4 M12 17h.01',
                title: 'Priority Assessment',
                text: 'High-impact issues are prioritized based on severity, volume, and location-related factors.',
              },
              {
                icon: 'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71 M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71',
                title: 'Duplicate Detection',
                text: 'Similar complaints are identified and linked to avoid multiple independent cases for the same issue.',
              },
              {
                icon: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
                title: 'Real-Time Tracking',
                text: 'Citizens can follow their complaint from submission through verification, progress, and resolution.',
              },
              {
                icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
                title: 'Department Coordination',
                text: 'Issues are routed to the appropriate department and staff based on category and location.',
              },
            ].map(f => (
              <div className="civic-feature-card" key={f.title}>
                <div className="civic-feature-icon">
                  <Icon size={20} d={f.icon} />
                </div>
                <div className="civic-feature-title">{f.title}</div>
                <p className="civic-feature-text">{f.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════
          ROLES SECTION
      ═══════════════════════════════ */}
      <section className="civic-section" id="roles">
        <div className="civic-section-inner">
          <div className="civic-section-label">
            <Icon size={14} d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75" />
            Platform Roles
          </div>
          <h2 className="civic-section-title">One platform. The right tools for every role.</h2>
          <p className="civic-section-subtitle">
            CivicConnect gives each stakeholder exactly what they need — no more, no less.
          </p>

          <div className="civic-roles-grid">
            {/* Tabs */}
            <div className="civic-roles-tabs">
              {ROLES.map(r => (
                <button
                  key={r.id}
                  className={`civic-role-tab${activeRole === r.id ? ' active' : ''}`}
                  onClick={() => setActiveRole(r.id)}
                >
                  <div className="civic-role-tab-icon" style={{ background: r.bg }}>{r.emoji}</div>
                  <div>
                    <div className="civic-role-tab-name">{r.name}</div>
                    <div className="civic-role-tab-desc">{r.id === 'citizen' ? 'Public user' : r.id === 'employee' ? 'Field staff' : r.id === 'supervisor' ? 'Team lead' : r.id === 'dept_admin' ? 'Dept. administrator' : 'System administrator'}</div>
                  </div>
                </button>
              ))}
            </div>

            {/* Panel */}
            <div className="civic-role-panel">
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
                <div style={{ width: 48, height: 48, background: role.bg, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22 }}>
                  {role.emoji}
                </div>
                <div>
                  <div className="civic-role-panel-title">{role.name}</div>
                </div>
              </div>
              <p className="civic-role-panel-sub">{role.desc}</p>
              <div className="civic-role-capabilities">
                {role.caps.map(cap => (
                  <div className="civic-cap-item" key={cap}>
                    <div className="civic-cap-check"><CheckCircle /></div>
                    <span className="civic-cap-text">{cap}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 24, paddingTop: 20, borderTop: '1px solid var(--border)' }}>
                <button className="civic-btn-primary" style={{ height: 42 }} onClick={() => navigate('/login')}>
                  Get Started as {role.name}
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════
          STATISTICS
      ═══════════════════════════════ */}
      <section className="civic-stats-section" id="stats">
        <div className="civic-stats-inner">
          <div className="civic-stats-header">
            <div className="civic-stats-eyebrow">
              <Icon size={14} stroke="var(--secondary)" d="M18 20V10 M12 20V4 M6 20v-6" />
              Platform Impact
            </div>
            <h2 className="civic-stats-title">Civic issues reported, tracked, and resolved.</h2>
            <p className="civic-stats-sub">Live statistics updated from the platform database.</p>
          </div>

          <div className="civic-stats-grid">
            {[
              { num: '1,248', unit: '+', label: 'Issues Reported', accent: 'Total complaints submitted' },
              { num: '936', unit: '', label: 'Issues Resolved', accent: '75% resolution rate' },
              { num: '4.2', unit: ' Days', label: 'Avg. Resolution Time', accent: 'Down from 8.6 days' },
              { num: '12', unit: '', label: 'Departments Connected', accent: 'Across the city' },
            ].map(s => (
              <div className="civic-stat-item" key={s.label} data-stat-id={s.label.replace(/\s+/g, '_').toLowerCase()}>
                <div className="civic-stat-num">{s.num}<span>{s.unit}</span></div>
                <div className="civic-stat-label">{s.label}</div>
                <div className="civic-stat-accent">{s.accent}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════
          FINAL CTA
      ═══════════════════════════════ */}
      <section className="civic-cta-section">
        <div className="civic-cta-inner">
          <h2 className="civic-cta-title">See a problem?<br />Help get it resolved.</h2>
          <p className="civic-cta-sub">
            Your report can help the responsible authorities identify and address issues in your community. It only takes a minute.
          </p>
          <div className="civic-cta-actions">
            <button className="civic-btn-green" style={{ height: 52, fontSize: 15 }} onClick={() => navigate('/login')}>
              <Icon size={18} d="M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
              Report an Issue
            </button>
            <button className="civic-btn-outline-lg" onClick={() => scrollTo('track')}>
              Track My Complaint
            </button>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════
          FOOTER
      ═══════════════════════════════ */}
      <footer className="civic-footer">
        <div className="civic-footer-inner">
          <div className="civic-footer-top">
            <div className="civic-footer-brand">
              <div className="civic-footer-logo">
                <div className="civic-footer-logo-icon">
                  <Icon size={18} stroke="rgba(255,255,255,0.7)" d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10" />
                </div>
                <span className="civic-footer-logo-name">CivicConnect</span>
              </div>
              <p className="civic-footer-desc">
                Helping citizens and public authorities work together to identify, track, and resolve civic issues effectively.
              </p>
            </div>

            <div className="civic-footer-nav">
              <div className="civic-footer-nav-title">Navigation</div>
              <div className="civic-footer-nav-links">
                {[
                  { label: 'Home', action: () => scrollTo('home') },
                  { label: 'How It Works', action: () => scrollTo('how-it-works') },
                  { label: 'Track Complaint', action: () => scrollTo('track') },
                  { label: 'Login', action: () => navigate('/login') },
                  { label: 'About', action: () => scrollTo('features') },
                ].map(l => (
                  <button key={l.label} className="civic-footer-nav-link" style={{ background: 'none', border: 'none', textAlign: 'left', padding: 0, cursor: 'pointer', fontFamily: 'inherit' }} onClick={l.action}>
                    {l.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="civic-footer-bottom">
            <span>© 2026 CivicConnect. All rights reserved.</span>
            <div className="civic-footer-legal">
              <a onClick={() => {}}>Privacy Policy</a>
              <a onClick={() => {}}>Terms of Use</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
