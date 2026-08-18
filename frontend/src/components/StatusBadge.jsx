import React from 'react';

export default function StatusBadge({ status }) {
  const map = {
    'Active':          'tag-success',
    'active':          'tag-success',
    'In Use':          'tag-success',
    'Available':       'tag-neutral',
    'available':       'tag-neutral',
    'In Stock':        'tag-neutral',
    'Maintenance':     'tag-warning',
    'maintenance':     'tag-warning',
    'In Progress':     'tag-warning',
    'Scheduled':       'tag-info',
    'scheduled':       'tag-info',
    'Retired':         'tag-error',
    'retired':         'tag-error',
    'Disposed':        'tag-error',
    'Completed':       'tag-success',
    'completed':       'tag-success',
    'Assigned':        'tag-primary',
    'assigned':        'tag-primary',
    'Unassigned':      'tag-neutral',
    'Pending':         'tag-warning',
    'pending':         'tag-warning',
    'Overdue':         'tag-error',
    'Critical':        'tag-error',
  };
  const cls = map[status] ?? 'tag-neutral';
  return <span className={`tag ${cls}`}>{status}</span>;
}
