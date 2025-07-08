import React from 'react';

export default function Card({ children, className = '', gradient = false }) {
  // GenZ/Stripe-style gradient card if enabled
  const base = gradient
    ? 'bg-gradient-to-br from-indigo-50 via-white to-pink-50 shadow-xl'
    : 'bg-white shadow-lg';
  return (
    <div className={`${base} rounded-2xl p-8 ${className}`}>
      {children}
    </div>
  );
}
