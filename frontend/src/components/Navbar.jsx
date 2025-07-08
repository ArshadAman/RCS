import React from 'react';

export default function Navbar() {
  return (
    <nav className="bg-primary text-white px-6 py-4 flex justify-between items-center shadow-md sticky top-0 z-50">
      <a href="/" className="flex items-center gap-2">
        <span className="font-extrabold text-2xl tracking-tight">ReviewHub</span>
      </a>
      <div className="hidden md:flex gap-6 items-center">
        <a href="/businesses" className="hover:underline hover:text-accent transition">Businesses</a>
        <a href="/profile" className="hover:underline hover:text-accent transition">Profile</a>
        <a href="/admin" className="hover:underline hover:text-accent transition">Admin</a>
        <a href="/login" className="bg-accent text-white px-5 py-2 rounded-lg ml-2 hover:bg-accent-dark transition font-semibold shadow">Login</a>
      </div>
      <div className="md:hidden">
        {/* Mobile menu icon placeholder */}
        <span className="material-icons text-3xl">menu</span>
      </div>
    </nav>
  );
}
