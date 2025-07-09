import React, { useState } from "react";
import SaaSLayout from "../components/SaaSLayout";

const initialProfile = {
  username: "admin",
  email: "admin@example.com",
  first_name: "Admin",
  last_name: "User",
  phone_number: "",
  date_of_birth: "",
};

const ProfilePage = () => {
  const [profile, setProfile] = useState(initialProfile);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(profile);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });
  const handleSave = () => {
    setProfile(form);
    setEditing(false);
  };

  return (
    <SaaSLayout>
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-pink-50">
        <div className="w-full max-w-lg bg-white rounded-2xl shadow-xl p-8 flex flex-col items-center">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-pink-400 to-indigo-500 flex items-center justify-center text-4xl text-white font-bold mb-4 shadow-lg">
            {profile.first_name[0]}
          </div>
          <h1 className="text-3xl font-extrabold text-indigo-700 mb-1 tracking-tight">{profile.first_name} {profile.last_name}</h1>
          <p className="text-slate-500 mb-4">{profile.email}</p>
          <div className="w-full max-w-md">
            {editing ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">First Name</label>
                  <input name="first_name" value={form.first_name} onChange={handleChange} className="w-full border border-indigo-200 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-400" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Last Name</label>
                  <input name="last_name" value={form.last_name} onChange={handleChange} className="w-full border border-indigo-200 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-400" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number</label>
                  <input name="phone_number" value={form.phone_number} onChange={handleChange} className="w-full border border-indigo-200 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-400" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Date of Birth</label>
                  <input name="date_of_birth" value={form.date_of_birth} onChange={handleChange} className="w-full border border-indigo-200 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-400" />
                </div>
                <div className="flex justify-end space-x-2 pt-2">
                  <button className="px-4 py-2 bg-gray-200 text-slate-700 rounded hover:bg-gray-300" onClick={() => setEditing(false)}>Cancel</button>
                  <button className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-pink-500 text-white rounded shadow hover:from-indigo-600 hover:to-pink-600 font-semibold" onClick={handleSave}>Save</button>
                </div>
              </div>
            ) : (
              <div className="w-full space-y-2 text-slate-700 text-base mt-2">
                <div className="flex items-center justify-between border-b py-2">
                  <span className="font-medium">Username:</span> <span>{profile.username}</span>
                </div>
                <div className="flex items-center justify-between border-b py-2">
                  <span className="font-medium">Email:</span> <span>{profile.email}</span>
                </div>
                <div className="flex items-center justify-between border-b py-2">
                  <span className="font-medium">First Name:</span> <span>{profile.first_name}</span>
                </div>
                <div className="flex items-center justify-between border-b py-2">
                  <span className="font-medium">Last Name:</span> <span>{profile.last_name}</span>
                </div>
                <div className="flex items-center justify-between border-b py-2">
                  <span className="font-medium">Phone Number:</span> <span>{profile.phone_number || <span className="text-slate-400">—</span>}</span>
                </div>
                <div className="flex items-center justify-between border-b py-2">
                  <span className="font-medium">Date of Birth:</span> <span>{profile.date_of_birth || <span className="text-slate-400">—</span>}</span>
                </div>
                <div className="flex justify-end pt-4">
                  <button className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-pink-500 text-white rounded shadow hover:from-indigo-600 hover:to-pink-600 font-semibold" onClick={() => setEditing(true)}>Edit</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </SaaSLayout>
  );
};

export default ProfilePage;
