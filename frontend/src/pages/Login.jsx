import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn } = useAuth();
  
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const from = location.state?.from?.pathname || '/dashboard';

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.password) {
      setError('Please fill in all fields.');
      return;
    }
    setError('');
    setLoading(true);
    
    try {
      await signIn(form.email, form.password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Failed to sign in.');
      setLoading(false);
    }
  };

  return (
    <div className="login-page" style={{ position: 'relative' }}>
      <button
        className="btn btn-ghost btn-icon"
        title="Go Back"
        onClick={() => navigate('/')}
        style={{ position: 'absolute', top: 'var(--sp-xl)', left: 'var(--sp-xl)' }}
      >
        <ArrowLeftIcon size={24} />
      </button>

      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-mark" style={{ background: 'var(--primary)', color: 'var(--surface)' }}>J</div>
          <span className="login-logo-text">JanaSeva</span>
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
          <button type="button" className="btn btn-ghost btn-sm" style={{ padding: 0, height: 'auto', fontSize: 13, color: 'var(--primary)', fontWeight: 600 }}>
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
