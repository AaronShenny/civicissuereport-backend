import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';

/* ---- Mock Data ---- */
const stats = [
  { label: 'Total Assets',       value: '1,284', change: '+12 this month', changeType: 'up',   iconBg: 'rgba(8,27,50,0.06)',    icon: <BoxSvg /> },
  { label: 'Active Assets',      value: '1,031', change: '80% of total',   changeType: 'neutral', iconBg: 'rgba(45,183,128,0.12)', icon: <CheckSvg /> },
  { label: 'Under Maintenance',  value: '87',    change: '+5 since last week', changeType: 'down', iconBg: 'rgba(248,220,93,0.18)', icon: <WrenchSvg /> },
  { label: 'Retired / Disposed', value: '166',   change: 'Lifetime total', changeType: 'neutral', iconBg: 'rgba(235,44,80,0.10)',  icon: <ArchiveSvg /> },
];

const monthlyData = [
  { month: 'Jan', added: 24, retired: 4 },
  { month: 'Feb', added: 18, retired: 2 },
  { month: 'Mar', added: 35, retired: 6 },
  { month: 'Apr', added: 28, retired: 3 },
  { month: 'May', added: 41, retired: 8 },
  { month: 'Jun', added: 30, retired: 5 },
  { month: 'Jul', added: 22, retired: 2 },
  { month: 'Aug', added: 12, retired: 1 },
];

const categoryData = [
  { name: 'IT Equipment',   value: 487, color: '#081B32' },
  { name: 'Furniture',      value: 312, color: '#2DB780' },
  { name: 'Vehicles',       value: 98,  color: '#78ACE9' },
  { name: 'Office Supplies', value: 234, color: '#F8DC5D' },
  { name: 'Machinery',      value: 153, color: '#EB2C50' },
];

const recentActivity = [
  { id: 1, action: 'Asset Added',       asset: 'MacBook Pro 16" — MBP-2024-047', user: 'Sarah Chen',     time: '2 min ago',  status: 'Active' },
  { id: 2, action: 'Maintenance Logged', asset: 'Printer HP LaserJet — PRN-019',  user: 'Mark Davis',     time: '1 hr ago',   status: 'Maintenance' },
  { id: 3, action: 'Assignment Changed', asset: 'Standing Desk — DESK-112',        user: 'Priya Sharma',   time: '3 hrs ago',  status: 'Assigned' },
  { id: 4, action: 'Asset Retired',      asset: 'Dell Monitor 24" — MON-003',      user: 'Tom Wilson',     time: 'Yesterday',  status: 'Retired' },
  { id: 5, action: 'Asset Added',        asset: 'iPhone 15 Pro — PHN-2024-031',    user: 'Julia Roberts',  time: 'Yesterday',  status: 'Active' },
];

const upcomingMaint = [
  { id: 1, asset: 'HVAC Unit A', due: 'Tomorrow',  priority: 'Critical' },
  { id: 2, asset: 'Generator 2', due: 'In 3 days', priority: 'Scheduled' },
  { id: 3, asset: 'Fire System', due: 'In 7 days', priority: 'Scheduled' },
];

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Good morning, Admin 👋</h2>
          <p className="page-subtitle">Here's what's happening with your assets today.</p>
        </div>
        <div className="page-header-right">
          <button className="btn btn-secondary" onClick={() => navigate('/reports')}>
            <ReportSvg size={16} /> View Reports
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/assets/new')}>
            <PlusSvg size={16} /> Add Asset
          </button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid-4" style={{ marginBottom: 'var(--sp-xl)' }}>
        {stats.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginBottom: 'var(--sp-xl)' }}>
        {/* Bar Chart */}
        <div className="card">
          <p className="section-title">Asset Activity — 2024</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={monthlyData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13 }}
                cursor={{ fill: 'var(--surface-subtle)' }}
              />
              <Bar dataKey="added"   name="Added"   fill="#081B32" radius={[4,4,0,0]} />
              <Bar dataKey="retired" name="Retired" fill="#EB2C50" radius={[4,4,0,0]} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="card">
          <p className="section-title">Assets by Category</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-lg)' }}>
            <ResponsiveContainer width="50%" height={220}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={90}
                  dataKey="value"
                  paddingAngle={3}
                >
                  {categoryData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13 }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {categoryData.map((c) => (
                <div key={c.name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: c.color, flexShrink: 0 }} />
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)', flex: 1 }}>{c.name}</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{c.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid-2">
        {/* Recent Activity */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: 'var(--sp-lg)', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p className="section-title" style={{ margin: 0 }}>Recent Activity</p>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/assets')}>View all</button>
          </div>
          <div>
            {recentActivity.map((item, i) => (
              <div
                key={item.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 'var(--sp-md)',
                  padding: 'var(--sp-md) var(--sp-lg)',
                  borderBottom: i < recentActivity.length - 1 ? '1px solid var(--border)' : 'none',
                }}
              >
                <div className="avatar avatar-sm" style={{ marginTop: 2, background: 'var(--surface-subtle)', color: 'var(--text-muted)' }}>
                  {item.user.charAt(0)}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{item.action}</p>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.asset}
                  </p>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>{item.user} · {item.time}</p>
                </div>
                <StatusBadge status={item.status} />
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Maintenance */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: 'var(--sp-lg)', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p className="section-title" style={{ margin: 0 }}>Upcoming Maintenance</p>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/maintenance')}>View all</button>
          </div>
          <div>
            {upcomingMaint.map((m, i) => (
              <div
                key={m.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--sp-md)',
                  padding: 'var(--sp-md) var(--sp-lg)',
                  borderBottom: i < upcomingMaint.length - 1 ? '1px solid var(--border)' : 'none',
                }}
              >
                <div style={{
                  width: 40, height: 40, borderRadius: 'var(--r-md)',
                  background: m.priority === 'Critical' ? 'rgba(235,44,80,0.08)' : 'rgba(120,172,233,0.12)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                }}>
                  <WrenchSvg size={18} color={m.priority === 'Critical' ? 'var(--error)' : 'var(--info)'} />
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>{m.asset}</p>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Due: {m.due}</p>
                </div>
                <StatusBadge status={m.priority} />
              </div>
            ))}
            <div style={{ padding: 'var(--sp-md) var(--sp-lg)' }}>
              <button className="btn btn-secondary" style={{ width: '100%' }} onClick={() => navigate('/maintenance')}>
                Schedule Maintenance
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* Inline SVG helpers */
function BoxSvg({ size = 20, color = 'var(--primary)' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>;
}
function CheckSvg({ size = 20, color = 'var(--secondary)' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>;
}
function WrenchSvg({ size = 20, color = 'var(--warning)' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>;
}
function ArchiveSvg({ size = 20, color = 'var(--error)' }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>;
}
function PlusSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
}
function ReportSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>;
}
