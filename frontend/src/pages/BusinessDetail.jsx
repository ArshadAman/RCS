import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import SaaSLayout from '../components/SaaSLayout';
import Card from '../components/Card';
import Button from '../components/Button';
import { useCompany } from '../context/CompanyContext';
import { businesses, reviews, qr } from '../api/api';

export default function BusinessDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentCompany } = useCompany();
  const [business, setBusiness] = useState(null);
  const [businessReviews, setBusinessReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [newReview, setNewReview] = useState({
    rating: 5,
    comment: '',
    customer_name: '',
    customer_email: ''
  });

  useEffect(() => {
    if (id && currentCompany) {
      loadBusinessDetail();
    }
  }, [id, currentCompany]);

  const loadBusinessDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load business details and reviews
      const [businessData, reviewsData] = await Promise.all([
        businesses.get(id),
        businesses.getReviews(id)
      ]);

      setBusiness(businessData);
      setBusinessReviews(reviewsData.results || reviewsData || []);
    } catch (err) {
      console.error('Failed to load business details:', err);
      setError(err.message || 'Failed to load business details');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    
    try {
      const reviewData = {
        ...newReview,
        business: id,
        company: currentCompany.id
      };

      await reviews.create(reviewData);
      
      // Reset form and reload reviews
      setNewReview({
        rating: 5,
        comment: '',
        customer_name: '',
        customer_email: ''
      });
      setShowReviewForm(false);
      loadBusinessDetail();
    } catch (err) {
      console.error('Failed to submit review:', err);
      alert(err.message || 'Failed to submit review');
    }
  };

  const downloadQRCode = async () => {
    try {
      if (!currentCompany?.id || !business?.id) return;
      
      const qrData = await qr.generate(currentCompany.id, business.id);
      
      // Create download link
      const link = document.createElement('a');
      link.href = qrData.qr_code_url || qrData.url;
      link.download = `qr-code-${business.name.replace(/[^a-zA-Z0-9]/g, '-')}.png`;
      link.click();
    } catch (err) {
      console.error('Failed to download QR code:', err);
      alert('Failed to generate QR code. Please try again.');
    }
  };

  const respondToReview = async (reviewId, response) => {
    try {
      await reviews.respond(reviewId, { response });
      loadBusinessDetail(); // Reload to show response
    } catch (err) {
      console.error('Failed to respond to review:', err);
      alert('Failed to respond to review');
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

  if (loading) {
    return (
      <SaaSLayout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="animate-spin text-4xl mb-4">⚡</div>
            <p className="text-slate-600">Loading business details...</p>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  if (error || !business) {
    return (
      <SaaSLayout>
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-red-600 mb-2">Business Not Found</h2>
            <p className="text-slate-600 mb-4">{error || 'This business does not exist.'}</p>
            <Button onClick={() => navigate('/businesses')}>Back to Businesses</Button>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  return (
    <SaaSLayout>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-4 mb-4">
          <Button 
            onClick={() => navigate('/businesses')}
            className="bg-slate-500 hover:bg-slate-600"
          >
            ← Back
          </Button>
          <h1 className="text-4xl font-extrabold text-slate-900 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
            {business.name}
          </h1>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Business Info */}
        <div className="lg:col-span-2 space-y-6">
          <Card gradient>
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-slate-900 mb-2">{business.name}</h2>
                {business.category && (
                  <p className="text-slate-600 mb-2">📂 {business.category}</p>
                )}
                {business.description && (
                  <p className="text-slate-700 mb-4">{business.description}</p>
                )}
                {business.address && (
                  <p className="text-slate-600 mb-2">📍 {business.address}</p>
                )}
                {business.phone && (
                  <p className="text-slate-600 mb-2">📞 {business.phone}</p>
                )}
                {business.website && (
                  <p className="text-slate-600 mb-2">
                    🌐 <a href={business.website} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                      {business.website}
                    </a>
                  </p>
                )}
              </div>
              <div className="flex flex-col space-y-2">
                <Button onClick={downloadQRCode} size="sm">
                  📱 QR Code
                </Button>
                <Button 
                  onClick={() => setShowReviewForm(true)}
                  className="bg-gradient-to-r from-indigo-500 to-purple-500"
                  size="sm"
                >
                  ✍️ Write Review
                </Button>
              </div>
            </div>

            {/* Business Stats */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-200">
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-800">
                  {business.average_rating ? business.average_rating.toFixed(1) : '0.0'}
                </div>
                <div className="text-sm text-slate-600">Average Rating</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-800">{businessReviews.length}</div>
                <div className="text-sm text-slate-600">Total Reviews</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-800">
                  {businessReviews.filter(r => r.is_approved).length}
                </div>
                <div className="text-sm text-slate-600">Approved Reviews</div>
              </div>
            </div>
          </Card>

          {/* Reviews Section */}
          <Card gradient>
            <h3 className="text-xl font-bold text-slate-900 mb-6">Customer Reviews</h3>
            <div className="space-y-4">
              {businessReviews.length > 0 ? businessReviews.map((review) => (
                <div key={review.id} className="p-4 bg-white/50 rounded-lg border border-slate-200">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
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
                      <p className="text-slate-700 mb-3">{review.comment || 'No comment provided'}</p>
                      
                      {/* Business Response */}
                      {review.response && (
                        <div className="mt-3 p-3 bg-indigo-50 rounded-lg border-l-4 border-indigo-400">
                          <p className="text-sm font-medium text-indigo-800 mb-1">Business Response:</p>
                          <p className="text-indigo-700">{review.response}</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Response Form (for business owners) */}
                  {!review.response && (
                    <div className="mt-3">
                      <Button
                        size="sm"
                        onClick={() => {
                          const response = prompt('Enter your response:');
                          if (response) respondToReview(review.id, response);
                        }}
                        className="bg-indigo-500 hover:bg-indigo-600"
                      >
                        💬 Respond
                      </Button>
                    </div>
                  )}
                </div>
              )) : (
                <div className="text-center py-12 text-slate-500">
                  <div className="text-4xl mb-4">📝</div>
                  <h4 className="text-lg font-semibold mb-2">No Reviews Yet</h4>
                  <p className="mb-4">Be the first to leave a review for this business!</p>
                  <Button 
                    onClick={() => setShowReviewForm(true)}
                    className="bg-gradient-to-r from-indigo-500 to-purple-500"
                  >
                    ✍️ Write First Review
                  </Button>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card gradient>
            <h4 className="text-lg font-bold text-slate-900 mb-4">Quick Actions</h4>
            <div className="space-y-3">
              <Button 
                onClick={() => setShowReviewForm(true)}
                className="w-full bg-gradient-to-r from-indigo-500 to-purple-500"
              >
                ✍️ Write Review
              </Button>
              <Button onClick={downloadQRCode} className="w-full">
                📱 Download QR Code
              </Button>
              <Button 
                onClick={() => navigate(`/businesses/${business.id}/widget`)}
                className="w-full bg-gradient-to-r from-green-500 to-teal-500"
              >
                🔗 Get Widget
              </Button>
            </div>
          </Card>

          {/* Rating Distribution */}
          <Card gradient>
            <h4 className="text-lg font-bold text-slate-900 mb-4">Rating Distribution</h4>
            <div className="space-y-2">
              {[5, 4, 3, 2, 1].map((star) => {
                const count = businessReviews.filter(r => r.rating === star).length;
                const percentage = businessReviews.length > 0 ? (count / businessReviews.length) * 100 : 0;
                
                return (
                  <div key={star} className="flex items-center space-x-3">
                    <span className="text-sm font-medium w-8">{star}★</span>
                    <div className="flex-1 bg-slate-200 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-yellow-400 to-orange-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <span className="text-sm text-slate-600 w-8">{count}</span>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>

      {/* Review Form Modal */}
      {showReviewForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-96 overflow-y-auto">
            <h3 className="text-xl font-bold text-slate-900 mb-4">Write a Review</h3>
            <form onSubmit={handleSubmitReview} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Your Name</label>
                <input
                  type="text"
                  value={newReview.customer_name}
                  onChange={(e) => setNewReview(prev => ({ ...prev, customer_name: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email (optional)</label>
                <input
                  type="email"
                  value={newReview.customer_email}
                  onChange={(e) => setNewReview(prev => ({ ...prev, customer_email: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Rating</label>
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setNewReview(prev => ({ ...prev, rating: star }))}
                      className={`text-2xl ${
                        star <= newReview.rating ? 'text-yellow-400' : 'text-slate-300'
                      } hover:text-yellow-400 transition-colors`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Comment</label>
                <textarea
                  value={newReview.comment}
                  onChange={(e) => setNewReview(prev => ({ ...prev, comment: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  rows="3"
                  required
                />
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="button"
                  onClick={() => setShowReviewForm(false)}
                  className="flex-1 bg-slate-500 hover:bg-slate-600"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1 bg-gradient-to-r from-indigo-500 to-purple-500"
                >
                  Submit Review
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </SaaSLayout>
  );
}
