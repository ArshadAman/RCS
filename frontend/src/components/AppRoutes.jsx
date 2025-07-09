import React from "react";
import { Routes, Route } from "react-router-dom";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import ForgotPasswordPage from "../pages/ForgotPasswordPage";
import ResetPasswordPage from "../pages/ResetPasswordPage";
import ProfilePage from "../pages/ProfilePage";
import ChangePasswordPage from "../pages/ChangePasswordPage";
import Dashboard from "../pages/Dashboard";
import CompanyListPage from "../pages/CompanyListPage";
import BusinessListPage from "../pages/BusinessListPage";
import BusinessDetailPage from "../pages/BusinessDetailPage";
import ReviewsPage from "../pages/ReviewsPage";
import ReviewDetailPage from "../pages/ReviewDetailPage";
import SurveysPage from "../pages/SurveysPage";
import WidgetManagerPage from "../pages/WidgetManagerPage";
import AdminPage from "../pages/AdminPage";
import NotFoundPage from "../pages/NotFoundPage";

const AppRoutes = () => (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/forgot-password" element={<ForgotPasswordPage />} />
    <Route path="/reset-password" element={<ResetPasswordPage />} />
    <Route path="/profile" element={<ProfilePage />} />
    <Route path="/change-password" element={<ChangePasswordPage />} />
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/companies" element={<CompanyListPage />} />
    <Route path="/businesses" element={<BusinessListPage />} />
    <Route path="/businesses/:id" element={<BusinessDetailPage />} />
    <Route path="/reviews" element={<ReviewsPage />} />
    <Route path="/reviews/:id" element={<ReviewDetailPage />} />
    <Route path="/surveys" element={<SurveysPage />} />
    <Route path="/widgets" element={<WidgetManagerPage />} />
    <Route path="/admin" element={<AdminPage />} />
    <Route path="*" element={<NotFoundPage />} />
  </Routes>
);

export default AppRoutes;
