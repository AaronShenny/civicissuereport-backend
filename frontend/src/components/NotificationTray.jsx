import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

export default function NotificationTray({ onClose, onStatusChange }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const data = await api.get('/notifications/');
      // Depending on pagination, data could be an array or { results: [...] }
      setNotifications(data.results || data);
      setError(null);
    } catch (err) {
      setError('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkAsRead = async (e, id) => {
    e.stopPropagation();
    try {
      await api.post(`/notifications/${id}/read/`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      if (onStatusChange) onStatusChange();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await api.post('/notifications/read-all/');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      if (onStatusChange) onStatusChange();
    } catch (err) {
      console.error(err);
    }
  };

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      handleMarkAsRead({ stopPropagation: () => {} }, notification.id);
    }
    if (notification.complaint_id) {
      // Basic navigation logic; might need adjustment based on role
      // For now, redirect to the general view or let the user use the main view.
      navigate(`/complaints/${notification.complaint_id}`);
      onClose();
    }
  };

  return (
    <div className="notification-tray" onClick={(e) => e.stopPropagation()}>
      <div className="notification-tray-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '1rem' }}>Notifications</h3>
        <div style={{ display: 'flex', gap: '8px' }}>
          {notifications.some(n => !n.is_read) && (
            <button className="btn btn-sm" onClick={handleMarkAllAsRead} style={{ fontSize: '0.8rem', padding: '0.2rem 0.5rem' }}>
              Mark all read
            </button>
          )}
          <button className="btn btn-ghost btn-icon" onClick={onClose} title="Close">
            <CloseIcon size={16} />
          </button>
        </div>
      </div>
      
      <div className="notification-tray-body" style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {loading ? (
          <div style={{ padding: '2rem 1rem', textAlign: 'center' }}>Loading...</div>
        ) : error ? (
          <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'red' }}>{error}</div>
        ) : notifications.length === 0 ? (
          <div className="empty-state" style={{ padding: '2rem 1rem' }}>
            <p className="empty-state-title" style={{ fontSize: '0.95rem' }}>No notifications</p>
            <p style={{ fontSize: '0.85rem' }}>You're all caught up!</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0px' }}>
            {notifications.map(n => (
              <div 
                key={n.id} 
                onClick={() => handleNotificationClick(n)}
                style={{
                  padding: '1rem',
                  borderBottom: '1px solid var(--border-color)',
                  backgroundColor: n.is_read ? 'transparent' : 'var(--bg-secondary)',
                  cursor: n.complaint_id ? 'pointer' : 'default',
                  display: 'flex',
                  gap: '1rem',
                  alignItems: 'flex-start'
                }}
              >
                {!n.is_read && <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'red', marginTop: 6, flexShrink: 0 }} />}
                <div style={{ flex: 1, paddingLeft: n.is_read ? '16px' : '0px' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: n.is_read ? 'normal' : '600' }}>
                    {n.trigger_event.replace('_', ' ').toUpperCase()}
                  </div>
                  <div style={{ fontSize: '0.9rem', marginTop: 4 }}>{n.message_content}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 8 }}>
                    {new Date(n.created_at).toLocaleString()}
                  </div>
                </div>
                {!n.is_read && (
                  <button className="btn btn-ghost btn-icon" onClick={(e) => handleMarkAsRead(e, n.id)} title="Mark as read">
                    <CheckIcon size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CheckIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
  );
}

function CloseIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"></line>
      <line x1="6" y1="6" x2="18" y2="18"></line>
    </svg>
  );
}
