import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from '../pages/Landing';
import Auth from '../pages/Auth';
import BusinessList from '../pages/BusinessList';
import BusinessDetail from '../pages/BusinessDetail';
import Profile from '../pages/Profile';
import Admin from '../pages/Admin';
import QRFeedback from '../pages/QRFeedback';
import Dashboard from '../pages/Dashboard';
import Reviews from '../pages/Reviews';
import Surveys from '../pages/Surveys';
import WidgetManager from '../pages/WidgetManager';

export default function AppRoutes() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Auth />} />
        <Route path="/register" element={<Auth />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/businesses" element={<BusinessList />} />
        <Route path="/businesses/:id" element={<BusinessDetail />} />
        <Route path="/reviews" element={<Reviews />} />
        <Route path="/surveys" element={<Surveys />} />
        <Route path="/widgets" element={<WidgetManager />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/qr-feedback" element={<QRFeedback />} />
      </Routes>
    </Router>
  );
}
