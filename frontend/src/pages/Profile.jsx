import React, { useEffect, useState } from 'react';
import SaaSLayout from '../components/SaaSLayout';
import Card from '../components/Card';
import { useCompany } from '../context/CompanyContext';
import { auth } from '../api/api';

export default function Profile() {
  const { currentCompany } = useCompany();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchProfile() {
      try {
        setLoading(true);
        setError(null);
        const data = await auth.profile();
        setUser(data);
      } catch (err) {
        setError(err.message || 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    }
    fetchProfile();
  }, []);

  if (!currentCompany) return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  if (loading) return <div className="flex items-center justify-center min-h-screen">Loading profile...</div>;
  if (error) return <div className="flex items-center justify-center min-h-screen text-red-500">{error}</div>;
  if (!user) return null;

  return (
    <SaaSLayout>
      <main className="flex-1 flex flex-col items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <div className="flex flex-col items-center">
            <div className="w-20 h-20 rounded-full bg-pink-200 flex items-center justify-center text-3xl text-white mb-4">
              {user.avatar ? <img src={user.avatar} alt="avatar" className="rounded-full w-full h-full" /> : user.name?.[0]}
            </div>
            <h2 className="text-xl font-bold text-pink-500 mb-1">{user.name}</h2>
            <p className="text-slate-500 mb-2">{user.email}</p>
            <p className="text-sm text-slate-500">Joined: {user.joined || user.date_joined}</p>
          </div>
        </Card>
      </main>
    </SaaSLayout>
  );
}
