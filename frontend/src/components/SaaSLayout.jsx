import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useCompany } from '../context/CompanyContext';
import CreateCompanyModal from './CreateCompanyModal';

const navLinks = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/businesses', label: 'Businesses', icon: '🏢' },
  { to: '/reviews', label: 'Reviews', icon: '📝' },
  { to: '/surveys', label: 'Surveys', icon: '📋' },
  { to: '/widgets', label: 'Widgets & QR', icon: '🔗' },
  { to: '/admin', label: 'Admin', icon: '👑' },
  { to: '/profile', label: 'Profile', icon: '👤' },
];

export default function SaaSLayout({ children }) {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { companies, currentCompany, setCurrentCompany, loading } = useCompany();
  const [showCreateCompany, setShowCreateCompany] = useState(false);

  // Show modal if no companies
  React.useEffect(() => {
    if (!loading && companies.length === 0) {
      setShowCreateCompany(true);
    }
  }, [companies, loading]);

  const handleCompanyCreated = (company) => {
    setShowCreateCompany(false);
    window.location.reload(); // reload to refetch companies and set current
  };

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-indigo-50 via-white to-pink-50 font-sans">
      {showCreateCompany && <CreateCompanyModal onCreated={handleCompanyCreated} />}
      {/* Sidebar */}
      <aside className={`bg-gradient-to-b from-indigo-900 via-indigo-800 to-pink-700 text-white w-64 flex-shrink-0 flex flex-col transition-transform duration-200 z-30 shadow-xl ${sidebarOpen ? 'translate-x-0' : '-translate-x-64'} md:translate-x-0`}>
        <div className="h-16 flex items-center px-6 border-b border-indigo-800">
          {currentCompany?.logo ? (
            <img src={currentCompany.logo} alt={currentCompany.name} className="h-10 w-10 rounded mr-2" />
          ) : (
            <span className="text-2xl font-bold text-pink-400">RCS</span>
          )}
          <span className="font-semibold text-white text-lg truncate">{currentCompany?.name || 'Your Company'}</span>
        </div>
        <nav className="flex-1 py-6 px-2 space-y-1">
          {navLinks.map(link => (
            <Link
              key={link.to}
              to={link.to}
              className={`flex items-center px-4 py-2 rounded-lg transition-colors font-medium gap-3 ${
                location.pathname.startsWith(link.to)
                  ? 'bg-pink-600/80 text-white shadow' : 'hover:bg-indigo-800/80 hover:text-pink-200 text-white'
              }`}
            >
              <span className="text-xl">{link.icon}</span>
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-indigo-800 text-xs text-pink-200">© {new Date().getFullYear()} ReviewHub</div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-16 bg-white/80 border-b border-pink-100 flex items-center px-8 justify-between sticky top-0 z-20 shadow-sm backdrop-blur">
          <button className="md:hidden text-2xl text-indigo-700" onClick={() => setSidebarOpen(!sidebarOpen)}>
            ☰
          </button>
          <div className="flex items-center gap-4">
            {/* Company Switcher */}
            <div className="relative">
              <button className="flex items-center gap-2 px-3 py-1 rounded bg-indigo-50 hover:bg-pink-50 text-indigo-700 font-medium" disabled={loading}>
                {currentCompany?.logo ? (
                  <img src={currentCompany.logo} alt={currentCompany.name} className="h-6 w-6 rounded" />
                ) : (
                  <span className="text-lg font-bold text-pink-400">RCS</span>
                )}
                <span className="truncate max-w-[120px]">{currentCompany?.name || 'Your Company'}</span>
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
              </button>
              {/* Dropdown for company switcher */}
              {companies.length > 1 && (
                <div className="absolute left-0 mt-2 w-56 bg-white rounded shadow-lg z-50">
                  {companies.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => setCurrentCompany(c)}
                      className={`w-full text-left px-4 py-2 hover:bg-pink-50 ${currentCompany?.id === c.id ? 'bg-pink-100 font-bold' : ''}`}
                    >
                      {c.logo && <img src={c.logo} alt={c.name} className="h-5 w-5 inline-block mr-2 rounded" />}
                      {c.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {/* User Menu */}
            <div className="relative">
              <button className="flex items-center gap-2 px-3 py-1 rounded bg-indigo-50 hover:bg-pink-50 text-indigo-700 font-medium">
                <span className="inline-block w-8 h-8 bg-pink-200 rounded-full text-center leading-8 font-bold">U</span>
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
              </button>
              {/* Dropdown for user menu can go here */}
            </div>
          </div>
        </header>
        <main className="flex-1 p-8 md:p-12 bg-transparent overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
