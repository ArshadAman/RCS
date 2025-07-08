import React, { useState } from 'react';
import SaaSLayout from '../components/SaaSLayout';
import Button from '../components/Button';
import { login, register } from '../api/api';

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    username: '',
    password_confirm: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        const data = await login({
          email: formData.email,
          password: formData.password
        });
        localStorage.setItem('token', data.tokens.access);
        window.location.href = '/dashboard';
      } else {
        if (formData.password !== formData.password_confirm) {
          setError('Passwords do not match');
          return;
        }
        await register(formData);
        setError('Registration successful! Please check your email to verify your account.');
      }
    } catch (err) {
      // Show exact error message from backend if available
      if (err && err.message) {
        setError(err.message);
      } else {
        setError(isLogin ? 'Invalid credentials' : 'Registration failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <SaaSLayout>
      <main className="flex-1 flex flex-col items-center justify-center px-4 min-h-screen bg-slate-50">
        <div className="w-full max-w-3xl mx-auto flex flex-col md:flex-row shadow-2xl rounded-3xl overflow-hidden bg-white border border-slate-200 min-h-[700px] min-w-[380px] md:min-w-[850px]" style={{height: '90vh', maxHeight: 900}}>
          {/* Left Stripe-style panel */}
          <div className="hidden md:flex flex-col justify-center items-center bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white px-12 py-20 w-1/2 h-full">
            <h2 className="text-4xl font-extrabold mb-4 tracking-tight">{isLogin ? 'Create your account' : 'Create your account'}</h2>
            <p className="text-lg mb-8 opacity-90">Start collecting reviews with a beautiful SaaS experience.</p>
            <div className="flex flex-col items-center mb-4">
              <div className="w-24 h-24 rounded-full bg-white flex items-center justify-center shadow-xl mb-2">
                <span className="text-6xl font-extrabold text-indigo-500">S</span>
              </div>
              <div className="text-xs opacity-70">Powered by RCS</div>
            </div>
          </div>
          {/* Right form panel */}
          <div className="flex-1 flex flex-col justify-center px-12 py-16 h-full">
            <div className="mb-8 text-center">
              <h2 className="text-3xl font-extrabold text-slate-900 mb-2 tracking-tight">
                {isLogin ? 'Sign in to your account' : 'Sign up for an account'}
              </h2>
              <p className="text-slate-500 text-sm">
                Fill in your details to get started.
              </p>
            </div>
            {error && (
              <div className={`mb-4 p-3 rounded text-center font-semibold ${
                error.includes('successful') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                {error}
              </div>
            )}
            <form onSubmit={handleSubmit} className="space-y-6">
              {!isLogin && (
                <div className="flex gap-4">
                  <input
                    type="text"
                    name="first_name"
                    placeholder="First Name"
                    value={formData.first_name}
                    onChange={handleChange}
                    className="flex-1 px-4 py-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition text-base placeholder-slate-400 shadow-sm text-slate-900"
                    required={!isLogin}
                  />
                  <input
                    type="text"
                    name="last_name"
                    placeholder="Last Name"
                    value={formData.last_name}
                    onChange={handleChange}
                    className="flex-1 px-4 py-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition text-base placeholder-slate-400 shadow-sm text-slate-900"
                    required={!isLogin}
                  />
                </div>
              )}
              {!isLogin && (
                <input
                  type="text"
                  name="username"
                  placeholder="Username"
                  value={formData.username}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition text-base placeholder-slate-400 shadow-sm text-slate-900"
                  required={!isLogin}
                />
              )}
              <input
                type="email"
                name="email"
                placeholder="Email address"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition text-base placeholder-slate-400 shadow-sm text-slate-900"
                required
              />
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition text-base placeholder-slate-400 shadow-sm text-slate-900"
                required
              />
              {!isLogin && (
                <input
                  type="password"
                  name="password_confirm"
                  placeholder="Confirm Password"
                  value={formData.password_confirm}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition text-base placeholder-slate-400 shadow-sm text-slate-900"
                  required
                />
              )}
              <Button
                type="submit"
                disabled={loading}
                className="w-full py-3 text-lg rounded-lg font-bold shadow-md bg-gradient-to-r from-indigo-500 to-pink-500 hover:from-indigo-600 hover:to-pink-600 transition"
              >
                {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Sign Up')}
              </Button>
            </form>
            <div className="mt-10 text-center">
              <span className="text-slate-500 text-sm">
                {isLogin ? "Don't have an account?" : "Already have an account?"}
              </span>
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="ml-2 text-indigo-600 hover:underline font-bold text-sm"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </div>
          </div>
        </div>
      </main>
    </SaaSLayout>
  );
}
