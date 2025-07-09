import React, { createContext, useContext, useState } from 'react';

const CompanyContext = createContext();

// Demo mode: always provide a default company
const demoCompanies = [
  { id: 1, name: 'Demo Company', industry: 'Software', created_at: '2024-01-01' }
];

export function CompanyProvider({ children }) {
  const [companies, setCompanies] = useState(demoCompanies);
  // No API calls, always has at least one company
  return (
    <CompanyContext.Provider value={{ companies, setCompanies }}>
      {children}
    </CompanyContext.Provider>
  );
}

export function useCompany() {
  return useContext(CompanyContext);
}
