import React, { useState, useEffect } from 'react';
import SaaSLayout from '../components/SaaSLayout';
import Card from '../components/Card';
import Button from '../components/Button';
import { useCompany } from '../context/CompanyContext';
import { businesses, reviews, surveyQuestions, reviewAnswers, auth } from '../api/api';

export default function Admin() {
  const { currentCompany } = useCompany();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [adminData, setAdminData] = useState({
    businesses: [],
    reviews: [],
    surveyQuestions: [],
    reviewAnswers: [],
    stats: {
      totalBusinesses: 0,
      totalReviews: 0,
      pendingReviews: 0,
      avgRating: 0
    }
  });

  useEffect(() => {
    if (currentCompany?.id) {
      loadAdminData();
    }
  }, [currentCompany]);

  const loadAdminData = async () => {
    if (!currentCompany?.id) return;
    
    try {
      setLoading(true);
      
      // Load all admin data
      const [businessData, reviewData, questionData, answerData] = await Promise.all([
        businesses.list(currentCompany.id),
        reviews.list({ company_id: currentCompany.id }),
        surveyQuestions.list(currentCompany.id),
        reviewAnswers.list({ company_id: currentCompany.id })
      ]);

      const businessList = businessData.results || businessData || [];
      const reviewList = reviewData.results || reviewData || [];
      const questionList = questionData.results || questionData || [];
      const answerList = answerData.results || answerData || [];

      // Calculate stats
      const pendingReviews = reviewList.filter(r => !r.is_approved).length;
      const avgRating = reviewList.length > 0 
        ? (reviewList.reduce((sum, r) => sum + (r.rating || 0), 0) / reviewList.length).toFixed(1)
        : 0;

      setAdminData({
        businesses: businessList,
        reviews: reviewList,
        surveyQuestions: questionList,
        reviewAnswers: answerList,
        stats: {
          totalBusinesses: businessList.length,
          totalReviews: reviewList.length,
          pendingReviews,
          avgRating
        }
      });
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveReview = async (reviewId) => {
    try {
      await reviews.approve(reviewId);
      loadAdminData(); // Reload data
    } catch (err) {
      console.error('Failed to approve review:', err);
      alert('Failed to approve review');
    }
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm('Are you sure you want to delete this review?')) return;
    
    try {
      await reviews.delete(reviewId);
      loadAdminData(); // Reload data
    } catch (err) {
      console.error('Failed to delete review:', err);
      alert('Failed to delete review');
    }
  };

  const handleDeleteBusiness = async (businessId) => {
    if (!window.confirm('Are you sure you want to delete this business? This will also delete all its reviews.')) return;
    
    try {
      await businesses.delete(businessId);
      loadAdminData(); // Reload data
    } catch (err) {
      console.error('Failed to delete business:', err);
      alert('Failed to delete business');
    }
  };

  const exportData = async (type) => {
    try {
      let data, filename;
      
      switch (type) {
        case 'reviews':
          data = adminData.reviews;
          filename = `reviews-${currentCompany.name}-${new Date().toISOString().split('T')[0]}.csv`;
          break;
        case 'businesses':
          data = adminData.businesses;
          filename = `businesses-${currentCompany.name}-${new Date().toISOString().split('T')[0]}.csv`;
          break;
        case 'survey-answers':
          data = adminData.reviewAnswers;
          filename = `survey-answers-${currentCompany.name}-${new Date().toISOString().split('T')[0]}.csv`;
          break;
        default:
          return;
      }

      if (!data.length) {
        alert('No data to export');
        return;
      }

      // Convert to CSV
      const headers = Object.keys(data[0]).join(',');
      const csvContent = [
        headers,
        ...data.map(row => 
          Object.values(row).map(value => 
            typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value
          ).join(',')
        )
      ].join('\n');

      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export data:', err);
      alert('Failed to export data');
    }
  };

  if (!currentCompany) {
    return (
      <SaaSLayout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="text-4xl mb-4">🏢</div>
            <h2 className="text-xl font-semibold text-slate-700 mb-2">No Company Selected</h2>
            <p className="text-slate-500">Please select a company from the dropdown above.</p>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: '📊' },
    { id: 'reviews', name: 'Reviews', icon: '📝' },
    { id: 'businesses', name: 'Businesses', icon: '🏢' },
    { id: 'surveys', name: 'Surveys', icon: '📋' },
    { id: 'export', name: 'Export', icon: '📤' }
  ];

  return (
    <SaaSLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-extrabold text-slate-900 mb-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
          Admin Dashboard
        </h1>
        <p className="text-slate-600">Manage and monitor {currentCompany.name}</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 mb-8 border-b border-slate-200">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 font-medium text-sm rounded-t-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-indigo-500 text-white border-b-2 border-indigo-500'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            {tab.icon} {tab.name}
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin text-4xl mb-4">⚡</div>
            <p className="text-slate-600">Loading admin data...</p>
          </div>
        </div>
      )}

      {!loading && (
        <>
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-8">
              {/* Stats Grid */}
              <div className="grid md:grid-cols-4 gap-6">
                <Card gradient>
                  <div className="text-3xl mb-2">🏢</div>
                  <div className="text-2xl font-bold text-slate-800">{adminData.stats.totalBusinesses}</div>
                  <div className="text-slate-600 text-sm">Total Businesses</div>
                </Card>
                <Card gradient>
                  <div className="text-3xl mb-2">📝</div>
                  <div className="text-2xl font-bold text-slate-800">{adminData.stats.totalReviews}</div>
                  <div className="text-slate-600 text-sm">Total Reviews</div>
                </Card>
                <Card gradient>
                  <div className="text-3xl mb-2">⏳</div>
                  <div className="text-2xl font-bold text-slate-800">{adminData.stats.pendingReviews}</div>
                  <div className="text-slate-600 text-sm">Pending Reviews</div>
                </Card>
                <Card gradient>
                  <div className="text-3xl mb-2">⭐</div>
                  <div className="text-2xl font-bold text-slate-800">{adminData.stats.avgRating}</div>
                  <div className="text-slate-600 text-sm">Average Rating</div>
                </Card>
              </div>

              {/* Quick Actions */}
              <Card gradient>
                <h3 className="text-xl font-bold text-slate-900 mb-4">Quick Actions</h3>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Button onClick={() => setActiveTab('reviews')} className="bg-gradient-to-r from-blue-500 to-indigo-500">
                    📝 Manage Reviews
                  </Button>
                  <Button onClick={() => setActiveTab('businesses')} className="bg-gradient-to-r from-green-500 to-teal-500">
                    🏢 Manage Businesses
                  </Button>
                  <Button onClick={() => setActiveTab('surveys')} className="bg-gradient-to-r from-purple-500 to-pink-500">
                    📋 Manage Surveys
                  </Button>
                  <Button onClick={() => setActiveTab('export')} className="bg-gradient-to-r from-amber-500 to-orange-500">
                    📤 Export Data
                  </Button>
                </div>
              </Card>

              {/* Recent Activity */}
              <Card gradient>
                <h3 className="text-xl font-bold text-slate-900 mb-4">Recent Reviews</h3>
                <div className="space-y-3">
                  {adminData.reviews.slice(0, 5).map((review) => (
                    <div key={review.id} className="flex items-center justify-between p-3 bg-white/50 rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-medium text-slate-800">{review.customer_name || 'Anonymous'}</span>
                          <div className="text-yellow-400">{'★'.repeat(review.rating || 0)}</div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            review.is_approved ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {review.is_approved ? 'Approved' : 'Pending'}
                          </span>
                        </div>
                        <p className="text-sm text-slate-600 truncate">{review.comment || 'No comment'}</p>
                      </div>
                      <div className="flex space-x-2">
                        {!review.is_approved && (
                          <Button
                            size="sm"
                            onClick={() => handleApproveReview(review.id)}
                            className="bg-green-500 hover:bg-green-600"
                          >
                            ✓
                          </Button>
                        )}
                        <Button
                          size="sm"
                          onClick={() => handleDeleteReview(review.id)}
                          className="bg-red-500 hover:bg-red-600"
                        >
                          🗑️
                        </Button>
                      </div>
                    </div>
                  ))}
                  {adminData.reviews.length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      <div className="text-2xl mb-2">📝</div>
                      <p>No reviews yet.</p>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}

          {/* Reviews Tab */}
          {activeTab === 'reviews' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-slate-900">Review Management</h3>
                <Button onClick={() => exportData('reviews')} className="bg-gradient-to-r from-indigo-500 to-purple-500">
                  📤 Export Reviews
                </Button>
              </div>
              
              <Card gradient>
                <div className="space-y-4">
                  {adminData.reviews.map((review) => (
                    <div key={review.id} className="p-4 bg-white/50 rounded-lg border border-slate-200">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className="font-semibold text-slate-800">{review.customer_name || 'Anonymous'}</span>
                            <div className="text-yellow-400">{'★'.repeat(review.rating || 0)}</div>
                            <span className="text-sm text-slate-500">
                              {new Date(review.created_at).toLocaleDateString()}
                            </span>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              review.is_approved ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {review.is_approved ? 'Approved' : 'Pending'}
                            </span>
                          </div>
                          <p className="text-slate-600 mb-2">{review.comment || 'No comment provided'}</p>
                          <p className="text-sm text-slate-500">Business: {review.business_name || 'Unknown'}</p>
                        </div>
                        <div className="flex space-x-2">
                          {!review.is_approved && (
                            <Button
                              size="sm"
                              onClick={() => handleApproveReview(review.id)}
                              className="bg-green-500 hover:bg-green-600"
                            >
                              ✓ Approve
                            </Button>
                          )}
                          <Button
                            size="sm"
                            onClick={() => handleDeleteReview(review.id)}
                            className="bg-red-500 hover:bg-red-600"
                          >
                            🗑️ Delete
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                  {adminData.reviews.length === 0 && (
                    <div className="text-center py-12 text-slate-500">
                      <div className="text-4xl mb-4">📝</div>
                      <p>No reviews to manage.</p>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}

          {/* Businesses Tab */}
          {activeTab === 'businesses' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-slate-900">Business Management</h3>
                <Button onClick={() => exportData('businesses')} className="bg-gradient-to-r from-indigo-500 to-purple-500">
                  📤 Export Businesses
                </Button>
              </div>
              
              <Card gradient>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {adminData.businesses.map((business) => (
                    <div key={business.id} className="p-4 bg-white/50 rounded-lg border border-slate-200">
                      <div className="flex items-start justify-between mb-3">
                        <h4 className="font-semibold text-slate-800 flex-1">{business.name}</h4>
                        <Button
                          size="sm"
                          onClick={() => handleDeleteBusiness(business.id)}
                          className="bg-red-500 hover:bg-red-600 ml-2"
                        >
                          🗑️
                        </Button>
                      </div>
                      <p className="text-sm text-slate-600 mb-2">{business.description || 'No description'}</p>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">Category: {business.category || 'None'}</span>
                        <span className="font-medium">
                          {business.average_rating ? `${business.average_rating}★` : 'No ratings'}
                        </span>
                      </div>
                    </div>
                  ))}
                  {adminData.businesses.length === 0 && (
                    <div className="col-span-full text-center py-12 text-slate-500">
                      <div className="text-4xl mb-4">🏢</div>
                      <p>No businesses to manage.</p>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}

          {/* Surveys Tab */}
          {activeTab === 'surveys' && (
            <div className="space-y-6">
              <h3 className="text-2xl font-bold text-slate-900">Survey Management</h3>
              
              <div className="grid lg:grid-cols-2 gap-8">
                {/* Survey Questions */}
                <Card gradient>
                  <h4 className="text-xl font-bold text-slate-900 mb-4">Survey Questions</h4>
                  <div className="space-y-3">
                    {adminData.surveyQuestions.map((question) => (
                      <div key={question.id} className="p-3 bg-white/50 rounded-lg">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-medium text-slate-800">{question.question_text}</p>
                            <p className="text-sm text-slate-500 mt-1">
                              Type: {question.question_type} • Required: {question.is_required ? 'Yes' : 'No'}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                    {adminData.surveyQuestions.length === 0 && (
                      <div className="text-center py-8 text-slate-500">
                        <div className="text-2xl mb-2">📋</div>
                        <p>No survey questions configured.</p>
                      </div>
                    )}
                  </div>
                </Card>

                {/* Survey Answers */}
                <Card gradient>
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-xl font-bold text-slate-900">Survey Responses</h4>
                    <Button onClick={() => exportData('survey-answers')} size="sm">
                      📤 Export
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {adminData.reviewAnswers.slice(0, 10).map((answer) => (
                      <div key={answer.id} className="p-3 bg-white/50 rounded-lg">
                        <p className="text-sm text-slate-600 mb-1">{answer.answer_text}</p>
                        <p className="text-xs text-slate-500">
                          Question ID: {answer.question} • Review ID: {answer.review}
                        </p>
                      </div>
                    ))}
                    {adminData.reviewAnswers.length === 0 && (
                      <div className="text-center py-8 text-slate-500">
                        <div className="text-2xl mb-2">📊</div>
                        <p>No survey responses yet.</p>
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            </div>
          )}

          {/* Export Tab */}
          {activeTab === 'export' && (
            <div className="space-y-6">
              <h3 className="text-2xl font-bold text-slate-900">Data Export</h3>
              
              <div className="grid md:grid-cols-3 gap-6">
                <Card gradient>
                  <div className="text-center">
                    <div className="text-4xl mb-4">📝</div>
                    <h4 className="text-lg font-bold text-slate-900 mb-2">Reviews</h4>
                    <p className="text-slate-600 mb-4">Export all review data as CSV</p>
                    <Button 
                      onClick={() => exportData('reviews')}
                      className="bg-gradient-to-r from-blue-500 to-indigo-500 w-full"
                    >
                      Export Reviews ({adminData.reviews.length})
                    </Button>
                  </div>
                </Card>

                <Card gradient>
                  <div className="text-center">
                    <div className="text-4xl mb-4">🏢</div>
                    <h4 className="text-lg font-bold text-slate-900 mb-2">Businesses</h4>
                    <p className="text-slate-600 mb-4">Export business directory as CSV</p>
                    <Button 
                      onClick={() => exportData('businesses')}
                      className="bg-gradient-to-r from-green-500 to-teal-500 w-full"
                    >
                      Export Businesses ({adminData.businesses.length})
                    </Button>
                  </div>
                </Card>

                <Card gradient>
                  <div className="text-center">
                    <div className="text-4xl mb-4">📊</div>
                    <h4 className="text-lg font-bold text-slate-900 mb-2">Survey Data</h4>
                    <p className="text-slate-600 mb-4">Export survey responses as CSV</p>
                    <Button 
                      onClick={() => exportData('survey-answers')}
                      className="bg-gradient-to-r from-purple-500 to-pink-500 w-full"
                    >
                      Export Surveys ({adminData.reviewAnswers.length})
                    </Button>
                  </div>
                </Card>
              </div>
            </div>
          )}
        </>
      )}
    </SaaSLayout>
  );
}
