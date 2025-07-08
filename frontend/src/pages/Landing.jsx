import React from 'react';
import SaaSLayout from '../components/SaaSLayout';
import Button from '../components/Button';
import { useCompany } from '../context/CompanyContext';

const customerLogos = [
  // Add logo URLs or use placeholder SVGs
  'https://upload.wikimedia.org/wikipedia/commons/4/44/Google-flutter-logo.svg',
  'https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg',
  'https://upload.wikimedia.org/wikipedia/commons/6/6a/JavaScript-logo.png',
  'https://upload.wikimedia.org/wikipedia/commons/9/96/SVG_Logo.svg',
];

export default function Landing() {
  const { currentCompany } = useCompany();
  return (
    <SaaSLayout>
      {/* Hero Section */}
      <section className="w-full max-w-4xl mx-auto text-center py-20 px-4 bg-gradient-to-br from-indigo-50 to-white rounded-3xl shadow-lg mb-12">
        <h1 className="text-5xl md:text-6xl font-extrabold text-slate-900 mb-6 leading-tight">
          Financial infrastructure<br className="hidden md:inline" /> to grow your revenue
        </h1>
        <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto">
          Collect, manage, and showcase customer reviews for your business. Build trust, improve your reputation, and engage with your customers—all in one place.
        </p>
        <Button className="text-lg px-10 py-4 rounded-full bg-indigo-600 hover:bg-indigo-700 shadow-lg transition" onClick={() => window.location.href='/businesses'}>
          Explore Businesses
        </Button>
      </section>

      {/* Customer Logos */}
      <section className="w-full max-w-3xl mx-auto flex flex-wrap items-center justify-center gap-8 py-6 mb-16">
        {customerLogos.map((logo, idx) => (
          <img key={idx} src={logo} alt="Customer logo" className="h-10 grayscale opacity-70 hover:opacity-100 transition" />
        ))}
      </section>

      {/* Features Section */}
      <section className="w-full max-w-5xl mx-auto grid md:grid-cols-3 gap-8 mb-20 px-2">
        <div className="bg-white rounded-2xl shadow p-8 flex flex-col items-center text-center border border-slate-100">
          <span className="text-4xl mb-4">⚡️</span>
          <h3 className="font-bold text-lg mb-2">Instant Feedback</h3>
          <p className="text-slate-500">Collect reviews in real time with QR codes, widgets, and mobile-friendly forms.</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-8 flex flex-col items-center text-center border border-slate-100">
          <span className="text-4xl mb-4">🔒</span>
          <h3 className="font-bold text-lg mb-2">Secure & Compliant</h3>
          <p className="text-slate-500">GDPR-ready, rate-limited, and built with enterprise-grade security and privacy.</p>
        </div>
        <div className="bg-white rounded-2xl shadow p-8 flex flex-col items-center text-center border border-slate-100">
          <span className="text-4xl mb-4">📊</span>
          <h3 className="font-bold text-lg mb-2">Analytics & Insights</h3>
          <p className="text-slate-500">Track review trends, customer sentiment, and badge achievements in a modern dashboard.</p>
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="w-full max-w-3xl mx-auto text-center py-12 mb-8 bg-indigo-600 rounded-3xl shadow-lg">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Ready to get started?</h2>
        <p className="text-lg text-indigo-100 mb-6">Create an account instantly or contact us to design a custom package for your business.</p>
        <div className="flex flex-col md:flex-row gap-4 justify-center">
          <Button className="bg-white text-indigo-700 hover:bg-indigo-50 font-bold px-8 py-3 rounded-full shadow" onClick={() => window.location.href='/register'}>
            Start now
          </Button>
          <Button className="bg-indigo-800 hover:bg-indigo-900 text-white font-bold px-8 py-3 rounded-full shadow" onClick={() => window.location.href='/contact'}>
            Contact sales
          </Button>
        </div>
      </section>
    </SaaSLayout>
  );
}
