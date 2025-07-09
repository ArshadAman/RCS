import React from 'react';
import SaaSLayout from '../components/SaaSLayout';
import { useCompany } from '../context/CompanyContext';

export default function Profile() {
  const { currentCompany } = useCompany();
  // Demo user
  const user = {
    name: 'Admin User',
    email: 'admin@example.com',
    joined: '2024-01-01',
    avatar: '',
  };

  if (!currentCompany) return <div className="flex items-center justify-center min-h-screen">Loading...</div>;

  return (
    <SaaSLayout>
      <main className="flex-1 flex flex-col items-center justify-center px-4">
        <div className="w-full max-w-md bg-white rounded shadow p-8">
          <div className="flex flex-col items-center">
            <div className="w-20 h-20 rounded-full bg-pink-200 flex items-center justify-center text-3xl text-white mb-4">
              {user.avatar ? <img src={user.avatar} alt="avatar" className="rounded-full w-full h-full" /> : (user.name ? user.name[0] : 'A')}
            </div>
            <h2 className="text-xl font-bold text-pink-500 mb-1">{user.name}</h2>
            <p className="text-slate-500 mb-2">{user.email}</p>
            <p className="text-sm text-slate-500">Joined: {user.joined}</p>
          </div>
        </div>
      </main>
    </SaaSLayout>
  );
}
