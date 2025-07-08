import React, { createContext, useContext, useState, useEffect } from 'react';
import { getUserCompanies } from '../api/api';

const CompanyContext = createContext();

export function CompanyProvider({ children }) {
  const [companies, setCompanies] = useState([]);
  const [currentCompany, setCurrentCompany] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchCompanies() {
      try {
        setLoading(true);
        const data = await getUserCompanies();
        if (Array.isArray(data) && data.length > 0) {
          setCompanies(data);
          setCurrentCompany(data[0]);
        } else {
          setCompanies([]);
          setCurrentCompany(null);
        }
      } catch (err) {
        setCompanies([]);
        setCurrentCompany(null);
        // If unauthorized, api.js will redirect to login
      } finally {
        setLoading(false);
      }
    }
    fetchCompanies();
  }, []);

  return (
    <CompanyContext.Provider value={{ companies, currentCompany, setCurrentCompany, loading }}>
      {children}
    </CompanyContext.Provider>
  );
}

export function useCompany() {
  return useContext(CompanyContext);
}
