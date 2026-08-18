import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

export default function AdminCategories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchCategories() {
      try {
        setLoading(true);
        const res = await api.get('/categories/');
        const catList = Array.isArray(res) ? res : (res.results || []);
        setCategories(catList);
      } catch (err) {
        setError(err.message || 'Failed to load categories');
      } finally {
        setLoading(false);
      }
    }
    fetchCategories();
  }, []);

  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-left">
          <h2 className="page-title">Categories</h2>
          <p className="page-subtitle">Manage complaint categories</p>
        </div>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="spinner"></div>
          <p>Loading categories...</p>
        </div>
      ) : error ? (
        <div className="empty-state">
          <p className="empty-state-title" style={{ color: 'var(--error)' }}>Error</p>
          <p>{error}</p>
        </div>
      ) : categories.length === 0 ? (
        <div className="empty-state">
          <p className="empty-state-title">No Categories</p>
          <p>No complaint categories exist.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Category Name</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {categories.map((c) => (
                  <tr key={c.id}>
                    <td><strong>{c.name}</strong></td>
                    <td>{c.description || 'No description provided.'}</td>
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
