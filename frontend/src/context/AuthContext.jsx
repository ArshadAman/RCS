import React, { createContext, useContext } from "react";

const AuthContext = createContext();

const demoUser = {
  username: "admin",
  email: "admin@example.com",
  isAdmin: true,
};

export const AuthProvider = ({ children }) => {
  // Always authenticated as demo admin
  return (
    <AuthContext.Provider value={{ isAuthenticated: true, user: demoUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
