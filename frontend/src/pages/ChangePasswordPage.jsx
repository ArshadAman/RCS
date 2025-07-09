import React, { useState } from "react";

const ChangePasswordPage = () => {
  const [form, setForm] = useState({ old_password: "", new_password: "", new_password_confirm: "" });
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });
  const handleSubmit = e => {
    e.preventDefault();
    if (form.old_password !== "admin") {
      setError("Old password is incorrect (hint: admin)");
      setSuccess(false);
    } else if (form.new_password !== form.new_password_confirm) {
      setError("New passwords do not match");
      setSuccess(false);
    } else {
      setError("");
      setSuccess(true);
    }
  };

  return (
    <div className="max-w-md mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Change Password (Demo)</h1>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block mb-1">Old Password</label>
          <input name="old_password" type="password" value={form.old_password} onChange={handleChange} className="w-full border rounded px-3 py-2" />
        </div>
        <div className="mb-4">
          <label className="block mb-1">New Password</label>
          <input name="new_password" type="password" value={form.new_password} onChange={handleChange} className="w-full border rounded px-3 py-2" />
        </div>
        <div className="mb-4">
          <label className="block mb-1">Confirm New Password</label>
          <input name="new_password_confirm" type="password" value={form.new_password_confirm} onChange={handleChange} className="w-full border rounded px-3 py-2" />
        </div>
        {error && <div className="text-red-600 mb-2">{error}</div>}
        {success && <div className="text-green-600 mb-2">Password changed (not really, demo only)</div>}
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded">Change Password</button>
      </form>
    </div>
  );
};

export default ChangePasswordPage;
