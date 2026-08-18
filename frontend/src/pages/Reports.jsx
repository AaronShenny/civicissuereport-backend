import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, AreaChart, Area,
} from 'recharts';

const assetValueByMonth = [
  { month: 'Jan', value: 320000 },
  { month: 'Feb', value: 338000 },
  { month: 'Mar', value: 375000 },
  { month: 'Apr', value: 402000 },
  { month: 'May', value: 443000 },
  { month: 'Jun', value: 478000 },
  { month: 'Jul', value: 501000 },
  { month: 'Aug', value: 512000 },
];

const depreciationData = [
  { year: 'Y0', IT: 100, Furniture: 100, Vehicles: 100 },
  { year: 'Y1', IT: 75,  Furniture: 92,  Vehicles: 80 },
  { year: 'Y2', IT: 55,  Furniture: 84,  Vehicles: 65 },
  { year: 'Y3', IT: 38,  Furniture: 78,  Vehicles: 52 },
  { year: 'Y4', IT: 24,  Furniture: 72,  Vehicles: 42 },
  { year: 'Y5', IT: 14,  Furniture: 68,  Vehicles: 34 },
];

const categoryValue = [
  { name: 'IT Equipment',   value: 487000, color: '#081B32' },
  { name: 'Vehicles',       value: 196000, color: '#2DB780' },
  { name: 'Machinery',      value: 153000, color: '#78ACE9' },
  { name: 'Furniture',      value: 62400,  color: '#F8DC5D' },
  { name: 'Office Supplies', value: 11700, color: '#EB2C50' },
];

const maintenanceCost = [
  { month: 'Jan', cost: 2800 },
  { month: 'Feb', cost: 1600 },
  { month: 'Mar', cost: 4200 },
  { month: 'Apr', cost: 3100 },
  { month: 'May', cost: 5400 },
  { month: 'Jun', cost: 2900 },
  { month: 'Jul', cost: 3700 },
  { month: 'Aug', cost: 1200 },
];

const RANGES = ['Last 30 Days', 'Last Quarter', 'This Year', 'All Time'];

export default function Reports() {
  const [range, setRange] = useState('This Year');

  const fmt = (v) => v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`;
  const totalValue = categoryValue.reduce((s, c) => s + c.value, 0);

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Reports</h2>
          <p className="page-subtitle">Asset analytics, depreciation, and cost overview.</p>
        </div>
        <div className="page-header-right">
          <div style={{ display: 'flex', gap: 6 }}>
            {RANGES.map((r) => (
              <button key={r} className={`filter-chip${range === r ? ' active' : ''}`} onClick={() => setRange(r)}>
                {r}
              </button>
            ))}
          </div>
          <button className="btn btn-secondary" style={{ marginLeft: 'var(--sp-sm)' }}>
            <ExportSvg size={16} /> Export PDF
          </button>
        </div>
      </div>

      {/* Summary KPI row */}
      <div className="grid-4" style={{ marginBottom: 'var(--sp-xl)' }}>
        {[
          { label: 'Total Asset Value', value: '$910,100', sub: 'Current book value' },
          { label: 'Avg Asset Age',     value: '2.4 yrs',  sub: 'Across all assets' },
          { label: 'Maintenance Cost',  value: '$24,900',  sub: 'Year to date' },
          { label: 'Assets Retired',    value: '166',       sub: 'Lifetime total' },
        ].map((k) => (
          <div key={k.label} className="card">
            <p style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{k.label}</p>
            <p style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', margin: '6px 0 2px', lineHeight: 1 }}>{k.value}</p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{k.sub}</p>
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid-2" style={{ marginBottom: 'var(--sp-xl)' }}>
        {/* Asset Value Over Time */}
        <div className="card">
          <p className="section-title">Total Asset Value Over Time</p>
          <ResponsiveContainer width="100%" height={230}>
            <AreaChart data={assetValueByMonth}>
              <defs>
                <linearGradient id="valueGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#081B32" stopOpacity={0.12}/>
                  <stop offset="95%" stopColor="#081B32" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false}/>
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false}/>
              <YAxis tickFormatter={fmt} tick={{ fontSize: 12, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false}/>
              <Tooltip
                formatter={(v) => [`$${v.toLocaleString()}`, 'Total Value']}
                contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13 }}
              />
              <Area type="monotone" dataKey="value" stroke="#081B32" strokeWidth={2} fill="url(#valueGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Value by Category */}
        <div className="card">
          <p className="section-title">Value by Category</p>
          <div style={{ display: 'flex', gap: 'var(--sp-lg)', alignItems: 'center' }}>
            <ResponsiveContainer width="45%" height={200}>
              <PieChart>
                <Pie data={categoryValue} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" paddingAngle={3}>
                  {categoryValue.map((e, i) => <Cell key={i} fill={e.color} />)}
                </Pie>
                <Tooltip formatter={(v) => [`$${v.toLocaleString()}`, '']} contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13 }}/>
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {categoryValue.map((c) => (
                <div key={c.name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 3 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: c.color }} />
                      <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{c.name}</span>
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 600 }}>{Math.round(c.value / totalValue * 100)}%</span>
                  </div>
                  <div style={{ height: 4, background: 'var(--border)', borderRadius: 'var(--r-full)', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${c.value / totalValue * 100}%`, background: c.color, borderRadius: 'var(--r-full)' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid-2">
        {/* Depreciation */}
        <div className="card">
          <p className="section-title">Depreciation by Category (%)</p>
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={depreciationData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false}/>
              <XAxis dataKey="year" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false}/>
              <YAxis tick={{ fontSize: 12, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} domain={[0,100]} tickFormatter={(v) => `${v}%`}/>
              <Tooltip
                formatter={(v, name) => [`${v}%`, name]}
                contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13 }}
              />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }}/>
              <Line type="monotone" dataKey="IT"        stroke="#081B32" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Furniture" stroke="#2DB780" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Vehicles"  stroke="#78ACE9" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Maintenance Cost */}
        <div className="card">
          <p className="section-title">Monthly Maintenance Cost</p>
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={maintenanceCost}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false}/>
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false}/>
              <YAxis tickFormatter={(v) => `$${v/1000}k`} tick={{ fontSize: 12, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false}/>
              <Tooltip
                formatter={(v) => [`$${v.toLocaleString()}`, 'Cost']}
                contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13 }}
                cursor={{ fill: 'var(--surface-subtle)' }}
              />
              <Bar dataKey="cost" name="Maintenance Cost" fill="#2DB780" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function ExportSvg({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>;
}
