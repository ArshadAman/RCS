import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SaaSLayout from '../components/SaaSLayout';
import Card from '../components/Card';
import Button from '../components/Button';
import { useCompany } from '../context/CompanyContext';
import { reviews, businesses } from '../api/api';

export default function Reviews() {
  const navigate = useNavigate();
  const { currentCompany } = useCompany();
  const [reviewsList, setReviewsList] = useState([]);
  const [businessesList, setBusinessesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, pending, approved
  const [selectedBusiness, setSelectedBusiness] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (!currentCompany?.id) return;
    // Only fetch if company is selected
    loadData();
    // eslint-disable-next-line
  }, [currentCompany]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [reviewsData, businessData] = await Promise.all([
        reviews.list({ company_id: currentCompany.id }),
        businesses.list(currentCompany.id)
      ]);

      setReviewsList(reviewsData.results || reviewsData || []);
      setBusinessesList(businessData.results || businessData || []);
    } catch (err) {
      console.error('Failed to load data:', err);
      setError(err.message || 'Failed to load reviews');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveReview = async (reviewId) => {
    try {
      await reviews.approve(reviewId);
      loadData(); // Reload data
    } catch (err) {
      console.error('Failed to approve review:', err);
      alert('Failed to approve review');
    }
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm('Are you sure you want to delete this review?')) return;
    
    try {
      await reviews.delete(reviewId);
      loadData(); // Reload data
    } catch (err) {
      console.error('Failed to delete review:', err);
      alert('Failed to delete review');
    }
  };

  const handleLikeReview = async (reviewId) => {
    try {
      await reviews.like(reviewId);
      loadData(); // Reload to update like count
    } catch (err) {
      console.error('Failed to like review:', err);
    }
  };

  const handleRespondToReview = async (reviewId) => {
    const response = prompt('Enter your response:');
    if (!response) return;

    try {
      await reviews.respond(reviewId, { response });
      loadData(); // Reload data
    } catch (err) {
      console.error('Failed to respond to review:', err);
      alert('Failed to respond to review');
    }
  };

  // Filter reviews based on criteria
  const filteredReviews = reviewsList.filter(review => {
    const matchesFilter = filter === 'all' || 
                         (filter === 'pending' && !review.is_approved) ||
                         (filter === 'approved' && review.is_approved);
    
    const matchesBusiness = !selectedBusiness || review.business_name === selectedBusiness;
    
    const matchesSearch = !searchTerm || 
                         (review.customer_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (review.comment || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesFilter && matchesBusiness && matchesSearch;
  });

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

  if (loading) {
    return (
      <SaaSLayout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="animate-spin text-4xl mb-4">⚡</div>
            <p className="text-slate-600">Loading reviews...</p>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  if (error) {
    return (
      <SaaSLayout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-red-600 mb-2">Error Loading Reviews</h2>
            <p className="text-slate-600 mb-4">{error}</p>
            <Button onClick={loadData}>Retry</Button>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  const pendingCount = reviewsList.filter(r => !r.is_approved).length;
  const approvedCount = reviewsList.filter(r => r.is_approved).length;

  return (
    <SaaSLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-extrabold text-slate-900 mb-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
          Reviews Management
        </h1>
        <p className="text-slate-600">Manage and moderate all reviews for {currentCompany.name}</p>
      </div>

      {/* Stats */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <Card gradient>
          <div className="text-3xl mb-2">📝</div>
          <div className="text-2xl font-bold text-slate-800">{reviewsList.length}</div>
          <div className="text-slate-600 text-sm">Total Reviews</div>
        </Card>
        <Card gradient>
          <div className="text-3xl mb-2">⏳</div>
          <div className="text-2xl font-bold text-slate-800">{pendingCount}</div>
          <div className="text-slate-600 text-sm">Pending Approval</div>
        </Card>
        <Card gradient>
          <div className="text-3xl mb-2">✅</div>
          <div className="text-2xl font-bold text-slate-800">{approvedCount}</div>
          <div className="text-slate-600 text-sm">Approved</div>
        </Card>
        <Card gradient>
          <div className="text-3xl mb-2">⭐</div>
          <div className="text-2xl font-bold text-slate-800">
            {reviewsList.length > 0 
              ? (reviewsList.reduce((sum, r) => sum + (r.rating || 0), 0) / reviewsList.length).toFixed(1)
              : '0.0'
            }
          </div>
          <div className="text-slate-600 text-sm">Average Rating</div>
        </Card>
      </div>

      {/* Filters */}
      <Card gradient className="mb-8">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search reviews..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* Status Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending ({pendingCount})</option>
            <option value="approved">Approved ({approvedCount})</option>
          </select>

          {/* Business Filter */}
          <select
            value={selectedBusiness}
            onChange={(e) => setSelectedBusiness(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="">All Businesses</option>
            {businessesList.map(business => (
              <option key={business.id} value={business.name}>{business.name}</option>
            ))}
          </select>

          {/* Quick Actions */}
          <Button
            onClick={() => {
              setFilter('all');
              setSelectedBusiness('');
              setSearchTerm('');
            }}
            className="bg-slate-500 hover:bg-slate-600"
          >
            Clear Filters
          </Button>
        </div>
      </Card>

      {/* Reviews List */}
      <div className="space-y-4">
        {filteredReviews.length > 0 ? filteredReviews.map((review) => (
          <Card key={review.id} gradient>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {/* Review Header */}
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                    {(review.customer_name || 'A')[0].toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-semibold text-slate-800">
                        {review.customer_name || 'Anonymous'}
                      </span>
                      <div className="text-yellow-400">
                        {'★'.repeat(review.rating || 0)}
                      </div>
                      <span className="text-sm text-slate-500">
                        {new Date(review.created_at).toLocaleDateString()}
                      </span>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        review.is_approved ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {review.is_approved ? 'Approved' : 'Pending'}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600">
                      Business: {review.business_name || 'Unknown'}
                    </p>
                  </div>
                </div>

                {/* Review Content */}
                <div className="mb-4">
                  <p className="text-slate-700 mb-3">{review.comment || 'No comment provided'}</p>
                  
                  {/* Business Response */}
                  {review.response && (
                    <div className="p-3 bg-indigo-50 rounded-lg border-l-4 border-indigo-400">
                      <p className="text-sm font-medium text-indigo-800 mb-1">Business Response:</p>
                      <p className="text-indigo-700">{review.response}</p>
                    </div>
                  )}
                </div>

                {/* Review Metadata */}
                <div className="flex items-center space-x-4 text-sm text-slate-500">
                  {review.customer_email && (
                    <span>📧 {review.customer_email}</span>
                  )}
                  <span>👁️ ID: {review.id}</span>
                  {review.like_count && (
                    <span>👍 {review.like_count} likes</span>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col space-y-2 ml-4">
                {!review.is_approved && (
                  <Button
                    size="sm"
                    onClick={() => handleApproveReview(review.id)}
                    className="bg-green-500 hover:bg-green-600"
                  >
                    ✓ Approve
                  </Button>
                )}
                
                {!review.response && (
                  <Button
                    size="sm"
                    onClick={() => handleRespondToReview(review.id)}
                    className="bg-blue-500 hover:bg-blue-600"
                  >
                    💬 Respond
                  </Button>
                )}
                
                <Button
                  size="sm"
                  onClick={() => handleLikeReview(review.id)}
                  className="bg-pink-500 hover:bg-pink-600"
                >
                  👍 Like
                </Button>
                
                <Button
                  size="sm"
                  onClick={() => navigate(`/businesses/${review.business}`)}
                  className="bg-indigo-500 hover:bg-indigo-600"
                >
                  🏢 View Business
                </Button>
                
                <Button
                  size="sm"
                  onClick={() => handleDeleteReview(review.id)}
                  className="bg-red-500 hover:bg-red-600"
                >
                  🗑️ Delete
                </Button>
              </div>
            </div>
          </Card>
        )) : (
          <Card gradient>
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-xl font-semibold text-slate-700 mb-2">No Reviews Found</h3>
              <p className="text-slate-500 mb-4">
                {searchTerm || filter !== 'all' || selectedBusiness
                  ? 'No reviews match your current filters.'
                  : 'No reviews have been submitted yet.'
                }
              </p>
              {(searchTerm || filter !== 'all' || selectedBusiness) && (
                <Button
                  onClick={() => {
                    setFilter('all');
                    setSelectedBusiness('');
                    setSearchTerm('');
                  }}
                  className="bg-gradient-to-r from-indigo-500 to-purple-500"
                >
                  Clear Filters
                </Button>
              )}
            </div>
          </Card>
        )}
      </div>

      {/* Footer Stats */}
      {filteredReviews.length > 0 && (
        <div className="mt-8 text-center text-slate-500 text-sm">
          Showing {filteredReviews.length} of {reviewsList.length} reviews
          {(searchTerm || filter !== 'all' || selectedBusiness) && (
            <span className="ml-2">
              • <button 
                onClick={() => { setSearchTerm(''); setFilter('all'); setSelectedBusiness(''); }}
                className="text-indigo-600 hover:text-indigo-800 underline"
              >
                Show all reviews
              </button>
            </span>
          )}
        </div>
      )}
    </SaaSLayout>
  );
}
