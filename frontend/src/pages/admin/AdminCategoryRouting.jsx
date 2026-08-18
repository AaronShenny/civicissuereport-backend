import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function AdminCategoryRouting() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchRules() {
      try {
        setLoading(true);
        const res = await api.get('/departments/category-rules/');
        const rulesList = Array.isArray(res) ? res : (res.results || []);
        setRules(rulesList);
      } catch (err) {
        setError(err.message || 'Failed to load category routing rules');
      } finally {
        setLoading(false);
      }
    }
    fetchRules();
  }, []);

  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Category Routing</h2>
          <p className="page-subtitle">View system-wide complaint routing mapping</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-body">
          <h3 style={{ marginTop: 0, marginBottom: '1rem', fontSize: '1.25rem' }}>How routing works</h3>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', color: 'var(--text-secondary)' }}>
            <li style={{ marginBottom: '0.5rem' }}><strong>Category</strong> determines the responsible department.</li>
            <li style={{ marginBottom: '0.5rem' }}><strong>District</strong> determines the jurisdiction.</li>
            <li><strong>Department + District</strong> determines which supervisors receive the complaint.</li>
          </ul>
          <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '4px' }}>
            <strong>Example:</strong> Streetlight + Ernakulam &rarr; KSEB &rarr; KSEB supervisors in Ernakulam
          </div>
        </div>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="spinner"></div>
          <p>Loading routing configuration...</p>
        </div>
      ) : error ? (
        <div className="empty-state">
          <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
          <p>{error}</p>
        </div>
      ) : rules.length === 0 ? (
        <div className="empty-state">
          <p className="empty-state-title">No Routing Rules Found</p>
          <p>There are no category rules available in the system.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Responsible Department</th>
                  <th>Jurisdiction (District)</th>
                  <th>Priority</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r) => (
                  <tr key={r.id}>
                    <td style={{ textTransform: 'capitalize' }}>
                      <strong>{r.category_name?.replace(/_/g, ' ')}</strong>
                    </td>
                    <td>{r.department_name}</td>
                    <td>{r.jurisdiction_name ? r.jurisdiction_name : <span style={{ color: 'var(--text-muted)' }}>Global (All Districts)</span>}</td>
                    <td>{r.priority_rank}</td>
                    <td>
                      <span className={`status-badge status-${r.is_active ? 'verified' : 'invalid'}`}>
                        {r.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
