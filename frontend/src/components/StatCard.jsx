import React from 'react';

export default function StatCard({ label, value, change, changeType = 'neutral', icon, iconBg }) {
  return (
    <div className="stat-card">
      {icon && (
        <div
          className="stat-card-icon"
          style={{ background: iconBg ?? 'var(--surface-subtle)' }}
        >
          {icon}
        </div>
      )}
      <p className="stat-card-label">{label}</p>
      <p className="stat-card-value">{value}</p>
      {change && (
        <p className={`stat-card-change ${changeType}`}>
          {changeType === 'up' && <ArrowUp />}
          {changeType === 'down' && <ArrowDown />}
          {change}
        </p>
      )}
    </div>
  );
}

function ArrowUp() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <polyline points="18 15 12 9 6 15"/>
    </svg>
  );
}
function ArrowDown() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <polyline points="6 9 12 15 18 9"/>
    </svg>
  );
}
