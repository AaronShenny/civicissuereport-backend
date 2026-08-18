import React from 'react';

export default function PriorityBadge({ priority }) {
  if (!priority) return null;
  const p = priority.toUpperCase();
  let bg = 'bg-gray-100 text-gray-800';
  if (p === 'HIGH') bg = 'bg-red-100 text-red-800';
  if (p === 'MEDIUM') bg = 'bg-yellow-100 text-yellow-800';
  if (p === 'LOW') bg = 'bg-green-100 text-green-800';
  
  return (
    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${bg}`}>
      {p}
    </span>
  );
}
