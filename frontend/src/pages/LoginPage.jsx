import React, { useState } from "react";

const LoginPage = () => {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const handleSubmit = (e) => {
    e.preventDefault();
    if (form.username === "admin" && form.password === "admin") {
      setLoggedIn(true);
      setError("");
    } else {
      setError("Invalid credentials. Use admin/admin");
    }
  };

  if (loggedIn) {
    return <div className="p-8 text-green-700">Logged in as <b>admin</b>. You can now use the app.</div>;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded shadow">
        <h1 className="text-2xl font-bold mb-6">Sign In (Demo)</h1>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block mb-1">Username</label>
            <input name="username" value={form.username} onChange={handleChange} className="w-full border rounded px-3 py-2" />
          </div>
          <div className="mb-4">
            <label className="block mb-1">Password</label>
            <input name="password" type="password" value={form.password} onChange={handleChange} className="w-full border rounded px-3 py-2" />
          </div>
          {error && <div className="text-red-600 mb-2">{error}</div>}
          <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded">Login</button>
        </form>
        <div className="mt-4 text-sm text-gray-500">Demo: <b>admin</b> / <b>admin</b></div>
      </div>
    </div>
  );
};

export default LoginPage;
