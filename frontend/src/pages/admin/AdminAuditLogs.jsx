import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError('');
      // Basic implementation without pagination params for now
      const res = await api.get('/admin/audit-logs/');
      setLogs(res.results || res);
    } catch (err) {
      setError(err.message || 'Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Audit Logs</h2>
          <p className="page-subtitle">System-wide administrative and security actions</p>
        </div>
        <div className="page-header-right">
          <button className="btn btn-secondary" onClick={fetchLogs} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div className="card">
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity Type</th>
                <th>Entity ID</th>
                <th>Changes</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>
                    Loading audit logs...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>
                    <em>No audit logs found.</em>
                  </td>
                </tr>
              ) : (
                logs.map(log => (
                  <tr key={log.id}>
                    <td>{new Date(log.created_at).toLocaleString()}</td>
                    <td>{log.actor || 'System'}</td>
                    <td><span className="badge bg-gray-100 text-gray-800">{log.action}</span></td>
                    <td>{log.entity_type}</td>
                    <td>{log.entity_id}</td>
                    <td style={{ fontSize: '0.8rem', maxWidth: '300px', overflowX: 'auto' }}>
                      {log.old_value && (
                        <div style={{ color: '#d32f2f' }}>
                          <strong>Old:</strong> {JSON.stringify(log.old_value)}
                        </div>
                      )}
                      {log.new_value && (
                        <div style={{ color: '#2e7d32' }}>
                          <strong>New:</strong> {JSON.stringify(log.new_value)}
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
