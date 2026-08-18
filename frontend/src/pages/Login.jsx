import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.email || !form.password) {
      setError('Please fill in all fields.');
      return;
    }
    setError('');
    setLoading(true);
    // Mock auth — any credentials work
    setTimeout(() => {
      setLoading(false);
      navigate('/dashboard');
    }, 900);
  };

  return (
    <div className="login-page" style={{ position: 'relative' }}>
      <button
        className="btn btn-ghost btn-icon"
        title="Go Back"
        onClick={() => navigate(-1)}
        style={{ position: 'absolute', top: 'var(--sp-xl)', left: 'var(--sp-xl)' }}
      >
        <ArrowLeftIcon size={24} />
      </button>

      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-mark">A</div>
          <span className="login-logo-text">AssetFlow</span>
        </div>

        {/* Heading */}
        <h1 className="login-heading">Welcome back</h1>
        <p className="login-sub">Sign in to your account to continue.</p>

        {error && (
          <div
            style={{
              background: '#fff0f3',
              border: '1px solid var(--error)',
              borderRadius: 'var(--r-sm)',
              padding: '10px 12px',
              fontSize: 13,
              color: 'var(--error)',
              marginBottom: 'var(--sp-md)',
            }}
          >
            {error}
          </div>
        )}

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              className="input"
              placeholder="admin@company.com"
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              className="input"
              placeholder="Enter your password"
              value={form.password}
              onChange={handleChange}
              autoComplete="current-password"
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-ghost btn-sm" style={{ padding: 0, height: 'auto', fontSize: 13 }}>
              Forgot password?
            </button>
          </div>

          <button
            id="login-submit"
            type="submit"
            className="btn btn-primary btn-lg"
            style={{ width: '100%', marginTop: 'var(--sp-sm)' }}
            disabled={loading}
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p
          style={{
            textAlign: 'center',
            fontSize: 13,
            color: 'var(--text-muted)',
            marginTop: 'var(--sp-lg)',
          }}
        >
          Don&apos;t have an account?{' '}
          <button className="btn btn-ghost btn-sm" style={{ padding: 0, height: 'auto', fontSize: 13, color: 'var(--primary)', fontWeight: 600 }}>
            Contact your admin
          </button>
        </p>
      </div>
    </div>
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
