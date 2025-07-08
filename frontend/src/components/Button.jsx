import React from 'react';

export default function Button({ children, className = '', gradient = true, ...props }) {
  // GenZ/Stripe-style gradient button
  const base = gradient
    ? 'bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-600 hover:to-pink-600 text-white shadow-lg'
    : 'bg-primary hover:bg-primary-dark text-white';
  return (
    <button
      className={`${base} font-semibold px-4 py-2 rounded-full transition ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
