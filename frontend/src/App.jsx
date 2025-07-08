import React from 'react';
import AppRoutes from './routes/AppRoutes';
import './index.css';
import { CompanyProvider } from './context/CompanyContext';

export default function App() {
  return (
    <CompanyProvider>
      <div className="min-h-screen bg-background">
        <AppRoutes />
      </div>
    </CompanyProvider>
  );
}
