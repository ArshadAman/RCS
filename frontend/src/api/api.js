/**
 * Comprehensive API Integration for Review Collection System
 * 
 * This file provides a complete interface to all backend API endpoints
 * including authentication, business management, reviews, companies,
 * survey questions, QR codes, widgets, and more.
 */

// Base configuration
const BASE_URL = 'http://127.0.0.1:8000/api';

// Utility functions
function getToken() {
  return localStorage.getItem('token');
}

function getAuthHeaders() {
  const token = getToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Generic API request handler
export async function apiRequest(endpoint, method = 'GET', data = null, auth = false, isFormData = false) {
  const headers = {
    ...(!isFormData && { 'Content-Type': 'application/json' }),
    ...(auth && getAuthHeaders()),
  };

  const options = {
    method,
    headers,
  };

  if (data) {
    options.body = isFormData ? data : JSON.stringify(data);
  }

  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, options);
    
    if (res.status === 401) {
      // Token invalid or expired: clear and redirect
      if (window.location.pathname !== '/login') {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      throw new Error('Unauthorized. Please log in again.');
    }
    if (!res.ok) {
      const errorText = await res.text();
      let errorMessage;
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorData.message || Object.values(errorData).flat().join(', ');
      } catch {
        errorMessage = errorText || `HTTP ${res.status}`;
      }
      throw new Error(errorMessage);
    }

    // Handle empty responses (e.g., 204 No Content)
    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await res.json();
    }
    return null;
  } catch (error) {
    console.error(`API Error (${method} ${endpoint}):`, error);
    throw error;
  }
}

// ============================================================================
// AUTHENTICATION ENDPOINTS
// ============================================================================

export const auth = {
  // User registration and login
  register: (data) => apiRequest('/auth/register/', 'POST', data),
  login: (data) => apiRequest('/auth/login/', 'POST', data),
  logout: () => apiRequest('/auth/logout/', 'POST', null, true),
  profile: () => apiRequest('/auth/profile/', 'GET', null, true),
  
  // Profile management
  getProfile: () => apiRequest('/auth/profile/', 'GET', null, true),
  updateProfile: (data) => apiRequest('/auth/profile/', 'PUT', data, true),
  patchProfile: (data) => apiRequest('/auth/profile/', 'PATCH', data, true),
  getSimpleProfile: () => apiRequest('/auth/profile/simple/', 'GET', null, true),
  
  // Password management
  changePassword: (data) => apiRequest('/auth/password/change/', 'POST', data, true),
  resetPassword: (data) => apiRequest('/auth/password/reset/', 'POST', data),
  confirmPasswordReset: (data) => apiRequest('/auth/password/reset/confirm/', 'POST', data),
  
  // Email and token management
  verifyEmail: (data) => apiRequest('/auth/email/verify/', 'POST', data),
  refreshToken: (data) => apiRequest('/auth/token/refresh/', 'POST', data),
};

// ============================================================================
// BUSINESS ENDPOINTS
// ============================================================================

export const businesses = {
  // Business CRUD operations
  list: (companyId = null) => {
    const endpoint = companyId ? `/businesses/?company_id=${companyId}` : '/businesses/';
    return apiRequest(endpoint, 'GET', null, true);
  },
  get: (id) => apiRequest(`/businesses/${id}/`, 'GET', null, true),
  create: (data) => apiRequest('/businesses/', 'POST', data, true),
  update: (id, data) => apiRequest(`/businesses/${id}/`, 'PUT', data, true),
  patch: (id, data) => apiRequest(`/businesses/${id}/`, 'PATCH', data, true),
  delete: (id) => apiRequest(`/businesses/${id}/`, 'DELETE', null, true),
  
  // Business-specific data
  getReviews: (businessId, params = {}) => {
    const queryParams = new URLSearchParams(params).toString();
    const endpoint = `/businesses/${businessId}/reviews/${queryParams ? `?${queryParams}` : ''}`;
    return apiRequest(endpoint, 'GET', null, true);
  },
  getStats: (businessId) => apiRequest(`/businesses/${businessId}/stats/`, 'GET', null, true),
};

// ============================================================================
// REVIEW ENDPOINTS
// ============================================================================

export const reviews = {
  // Review CRUD operations
  list: (params = {}) => {
    const queryParams = new URLSearchParams(params).toString();
    const endpoint = `/reviews/${queryParams ? `?${queryParams}` : ''}`;
    return apiRequest(endpoint, 'GET', null, true);
  },
  get: (id) => apiRequest(`/reviews/${id}/`, 'GET', null, true),
  create: (data) => apiRequest('/reviews/', 'POST', data, true),
  update: (id, data) => apiRequest(`/reviews/${id}/`, 'PUT', data, true),
  patch: (id, data) => apiRequest(`/reviews/${id}/`, 'PATCH', data, true),
  delete: (id) => apiRequest(`/reviews/${id}/`, 'DELETE', null, true),
  
  // Review interactions
  respond: (id, data) => apiRequest(`/reviews/${id}/response/`, 'PUT', data, true),
  patchResponse: (id, data) => apiRequest(`/reviews/${id}/response/`, 'PATCH', data, true),
  approve: (reviewId) => apiRequest(`/reviews/${reviewId}/approve/`, 'POST', null, true),
  like: (reviewId) => apiRequest(`/reviews/${reviewId}/like/`, 'POST', null, true),
  unlike: (reviewId) => apiRequest(`/reviews/${reviewId}/like/`, 'DELETE', null, true),
};

// ============================================================================
// CATEGORY ENDPOINTS
// ============================================================================

export const categories = {
  list: () => apiRequest('/categories/', 'GET'),
};

// ============================================================================
// COMPANY ENDPOINTS
// ============================================================================

export const companies = {
  list: () => apiRequest('/companies/', 'GET', null, true),
  getUserCompanies: () => apiRequest('/companies/', 'GET', null, true),
  create: (data) => apiRequest('/companies/', 'POST', data, true),
};

// ============================================================================
// ORDER ENDPOINTS
// ============================================================================

export const orders = {
  webhook: (data) => apiRequest('/orders/webhook/', 'POST', data),
};

// ============================================================================
// SURVEY QUESTION ENDPOINTS
// ============================================================================

export const surveyQuestions = {
  // Survey question CRUD operations
  list: (companyId = null) => {
    const endpoint = companyId ? `/survey-questions/?company_id=${companyId}` : '/survey-questions/';
    return apiRequest(endpoint, 'GET', null, true);
  },
  get: (id) => apiRequest(`/survey-questions/${id}/`, 'GET', null, true),
  create: (data) => apiRequest('/survey-questions/', 'POST', data, true),
  update: (id, data) => apiRequest(`/survey-questions/${id}/`, 'PUT', data, true),
  patch: (id, data) => apiRequest(`/survey-questions/${id}/`, 'PATCH', data, true),
  delete: (id) => apiRequest(`/survey-questions/${id}/`, 'DELETE', null, true),
};

// ============================================================================
// REVIEW ANSWER ENDPOINTS
// ============================================================================

export const reviewAnswers = {
  // Review answer CRUD operations
  list: (params = {}) => {
    const queryParams = new URLSearchParams(params).toString();
    const endpoint = `/review-answers/${queryParams ? `?${queryParams}` : ''}`;
    return apiRequest(endpoint, 'GET', null, true);
  },
  get: (id) => apiRequest(`/review-answers/${id}/`, 'GET', null, true),
  create: (data) => apiRequest('/review-answers/', 'POST', data, true),
  update: (id, data) => apiRequest(`/review-answers/${id}/`, 'PUT', data, true),
  patch: (id, data) => apiRequest(`/review-answers/${id}/`, 'PATCH', data, true),
  delete: (id) => apiRequest(`/review-answers/${id}/`, 'DELETE', null, true),
};

// ============================================================================
// WIDGET ENDPOINTS
// ============================================================================

export const widget = {
  getData: (companyId) => apiRequest(`/widget/${companyId}/`, 'GET'),
  getPublicData: (companyId) => apiRequest(`/widget/${companyId}/`, 'GET'),
};

// ============================================================================
// QR CODE ENDPOINTS
// ============================================================================

export const qr = {
  generate: (companyId, branchId) => apiRequest(`/qr-code/${companyId}/${branchId}/`, 'GET', null, true),
  submitFeedback: (branchId, data) => apiRequest(`/qr-feedback/${branchId}/`, 'POST', data),
};

// ============================================================================
// LEGACY EXPORTS (for backward compatibility)
// ============================================================================

// Auth legacy exports
export const login = auth.login;
export const register = auth.register;
export const logout = auth.logout;
export const getProfile = auth.getProfile;
export const updateProfile = auth.updateProfile;
export const patchProfile = auth.patchProfile;
export const getSimpleProfile = auth.getSimpleProfile;
export const verifyEmail = auth.verifyEmail;
export const changePassword = auth.changePassword;
export const resetPassword = auth.resetPassword;
export const confirmPasswordReset = auth.confirmPasswordReset;
export const refreshToken = auth.refreshToken;

// Business legacy exports
export const getBusinesses = businesses.list;
export const getBusiness = businesses.get;
export const createBusiness = businesses.create;
export const updateBusiness = businesses.update;
export const patchBusiness = businesses.patch;
export const deleteBusiness = businesses.delete;
export const getBusinessReviews = businesses.getReviews;
export const getBusinessStats = businesses.getStats;

// Review legacy exports
export const getReviews = reviews.list;
export const createReview = reviews.create;
export const getReview = reviews.get;
export const updateReview = reviews.update;
export const patchReview = reviews.patch;
export const deleteReview = reviews.delete;
export const respondToReview = reviews.respond;
export const patchReviewResponse = reviews.patchResponse;
export const approveReview = reviews.approve;
export const likeReview = reviews.like;

// Category legacy exports
export const getCategories = categories.list;

// Company legacy exports
export const getUserCompanies = companies.getUserCompanies;

// Order legacy exports
export const createOrderWebhook = orders.webhook;

// Survey question legacy exports
export const getSurveyQuestions = surveyQuestions.list;
export const createSurveyQuestion = surveyQuestions.create;
export const getSurveyQuestion = surveyQuestions.get;
export const updateSurveyQuestion = surveyQuestions.update;
export const patchSurveyQuestion = surveyQuestions.patch;
export const deleteSurveyQuestion = surveyQuestions.delete;

// Review answer legacy exports
export const getReviewAnswers = reviewAnswers.list;
export const createReviewAnswer = reviewAnswers.create;
export const getReviewAnswer = reviewAnswers.get;
export const updateReviewAnswer = reviewAnswers.update;
export const patchReviewAnswer = reviewAnswers.patch;
export const deleteReviewAnswer = reviewAnswers.delete;

// Widget legacy exports
export const getWidgetData = widget.getData;

// QR legacy exports
export const generateQRCode = qr.generate;
export const submitQRFeedback = qr.submitFeedback;
