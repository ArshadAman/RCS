import React, { useState, useEffect } from 'react';
import SaaSLayout from '../components/SaaSLayout';
import Card from '../components/Card';
import Button from '../components/Button';
import { useCompany } from '../context/CompanyContext';
import { businesses, reviews, qr, widget } from '../api/api';

export default function Dashboard() {
  const { currentCompany } = useCompany();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    businessCount: 0,
    reviewCount: 0,
    avgRating: 0,
    recentReviews: [],
    reviewTrends: [],
    topBusinesses: []
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    if (currentCompany?.id) {
      loadDashboardData();
    }
  }, [currentCompany]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load businesses for this company
      const businessData = await businesses.list(currentCompany.id);
      const businessCount = businessData.results?.length || businessData.length || 0;

      // Load reviews data
      const reviewData = await reviews.list({ company_id: currentCompany.id });
      const allReviews = reviewData.results || reviewData || [];
      const reviewCount = allReviews.length;

      // Calculate average rating
      const avgRating = allReviews.length > 0 
        ? (allReviews.reduce((sum, review) => sum + (review.rating || 0), 0) / allReviews.length).toFixed(1)
        : 0;

      // Get recent reviews (last 5)
      const recentReviews = allReviews
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5);

      // Calculate review trends (mock data for now - you can enhance this)
      const reviewTrends = generateReviewTrends(allReviews);

      // Get top businesses by rating
      const businessStats = [];
      for (const business of (businessData.results || businessData || [])) {
        try {
          const stats = await businesses.getStats(business.id);
          businessStats.push({
            ...business,
            ...stats
          });
        } catch (err) {
          console.warn(`Failed to load stats for business ${business.id}`, err);
        }
      }
      
      const topBusinesses = businessStats
        .sort((a, b) => (b.average_rating || 0) - (a.average_rating || 0))
        .slice(0, 3);

      setDashboardData({
        businessCount,
        reviewCount,
        avgRating,
        recentReviews,
        reviewTrends,
        topBusinesses
      });

    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateReviewTrends = (reviews) => {
    // Group reviews by month for the last 6 months
    const months = [];
    const now = new Date();
    
    for (let i = 5; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthName = date.toLocaleDateString('en', { month: 'short' });
      const monthReviews = reviews.filter(review => {
        const reviewDate = new Date(review.created_at);
        return reviewDate.getMonth() === date.getMonth() && 
               reviewDate.getFullYear() === date.getFullYear();
      });
      
      months.push({
        name: monthName,
        reviews: monthReviews.length,
        avgRating: monthReviews.length > 0 
          ? (monthReviews.reduce((sum, r) => sum + (r.rating || 0), 0) / monthReviews.length).toFixed(1)
          : 0
      });
    }
    
    return months;
  };

  const downloadQRCode = async (businessId) => {
    try {
      if (!currentCompany?.id || !businessId) return;
      
      const qrData = await qr.generate(currentCompany.id, businessId);
      
      // Create download link
      const link = document.createElement('a');
      link.href = qrData.qr_code_url || qrData.url;
      link.download = `qr-code-${businessId}.png`;
      link.click();
    } catch (err) {
      console.error('Failed to download QR code:', err);
      alert('Failed to generate QR code. Please try again.');
    }
  };

  const exportReviews = async () => {
    try {
      const allReviews = await reviews.list({ company_id: currentCompany.id });
      const reviewData = allReviews.results || allReviews || [];
      
      // Convert to CSV
      const headers = ['Date', 'Business', 'Customer', 'Rating', 'Comment', 'Status'];
      const csvContent = [
        headers.join(','),
        ...reviewData.map(review => [
          new Date(review.created_at).toLocaleDateString(),
          review.business_name || 'N/A',
          review.customer_name || 'Anonymous',
          review.rating || 0,
          `"${(review.comment || '').replace(/"/g, '""')}"`,
          review.is_approved ? 'Approved' : 'Pending'
        ].join(','))
      ].join('\n');

      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `reviews-${currentCompany.name}-${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export reviews:', err);
      alert('Failed to export reviews. Please try again.');
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
            <p className="text-slate-600">Loading dashboard...</p>
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
            <h2 className="text-xl font-semibold text-red-600 mb-2">Error Loading Dashboard</h2>
            <p className="text-slate-600 mb-4">{error}</p>
            <Button onClick={loadDashboardData}>Retry</Button>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  const { name, logo, plan, badge = 'Bronze' } = currentCompany;
  const { businessCount, reviewCount, avgRating, recentReviews, reviewTrends, topBusinesses } = dashboardData;

  return (
    <SaaSLayout>
      {/* Header */}
      <div className="mb-10 text-center">
        <h1 className="text-4xl font-extrabold text-slate-900 mb-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p className="text-slate-600">Welcome back! Here's what's happening with {name}.</p>
      </div>

      {/* Key Metrics */}
      <div className="grid md:grid-cols-4 gap-6 mb-10">
        <Card gradient>
          <div className="text-3xl mb-2">🏢</div>
          <div className="text-2xl font-bold text-slate-800 mb-1">{businessCount}</div>
          <div className="text-slate-600 text-sm">Businesses</div>
        </Card>
        <Card gradient>
          <div className="text-3xl mb-2">📝</div>
          <div className="text-2xl font-bold text-slate-800 mb-1">{reviewCount}</div>
          <div className="text-slate-600 text-sm">Total Reviews</div>
        </Card>
        <Card gradient>
          <div className="text-3xl mb-2">⭐</div>
          <div className="text-2xl font-bold text-slate-800 mb-1">{avgRating}</div>
          <div className="text-slate-600 text-sm">Avg Rating</div>
        </Card>
        <Card gradient>
          <div className="text-3xl mb-2">{badge === 'Gold' ? '🥇' : badge === 'Silver' ? '🥈' : '🥉'}</div>
          <div className="text-lg font-semibold text-slate-800 mb-1">{badge}</div>
          <div className="text-slate-600 text-sm">Current Badge</div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-8 mb-10">
        {/* Review Trends */}
        <Card gradient>
          <h2 className="text-xl font-bold text-slate-900 mb-6">Review Trends (Last 6 Months)</h2>
          <div className="space-y-4">
            {reviewTrends.map((month, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-600">{month.name}</span>
                <div className="flex items-center space-x-3">
                  <div className="flex-1 bg-slate-200 rounded-full h-2 w-20">
                    <div 
                      className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, (month.reviews / Math.max(...reviewTrends.map(m => m.reviews), 1)) * 100)}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-slate-800 min-w-[3rem]">{month.reviews}</span>
                  <span className="text-xs text-slate-500 min-w-[2rem]">({month.avgRating}★)</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Top Businesses */}
        <Card gradient>
          <h2 className="text-xl font-bold text-slate-900 mb-6">Top Performing Businesses</h2>
          <div className="space-y-4">
            {topBusinesses.length > 0 ? topBusinesses.map((business, index) => (
              <div key={business.id} className="flex items-center justify-between p-3 bg-white/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-semibold text-slate-800">{business.name}</div>
                    <div className="text-xs text-slate-500">{business.review_count || 0} reviews</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-slate-800">{business.average_rating || 0}★</div>
                  <Button 
                    size="sm" 
                    onClick={() => downloadQRCode(business.id)}
                    className="mt-1 text-xs"
                  >
                    QR Code
                  </Button>
                </div>
              </div>
            )) : (
              <div className="text-center py-8 text-slate-500">
                <div className="text-2xl mb-2">🏢</div>
                <p>No businesses yet. Create your first business to get started!</p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Recent Reviews */}
      <Card gradient className="mb-8">
        <h2 className="text-xl font-bold text-slate-900 mb-6">Recent Reviews</h2>
        <div className="space-y-4">
          {recentReviews.length > 0 ? recentReviews.map((review) => (
            <div key={review.id} className="flex items-start space-x-4 p-4 bg-white/50 rounded-lg">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                  {review.customer_name?.[0] || '?'}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-semibold text-slate-800">
                    {review.customer_name || 'Anonymous'}
                  </p>
                  <div className="flex items-center space-x-2">
                    <div className="text-yellow-400">{'★'.repeat(review.rating || 0)}</div>
                    <span className="text-xs text-slate-500">
                      {new Date(review.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-slate-600 truncate">{review.comment || 'No comment'}</p>
                <p className="text-xs text-slate-500 mt-1">Business: {review.business_name || 'Unknown'}</p>
              </div>
            </div>
          )) : (
            <div className="text-center py-8 text-slate-500">
              <div className="text-2xl mb-2">📝</div>
              <p>No reviews yet. Start collecting feedback to see them here!</p>
            </div>
          )}
        </div>
      </Card>

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-4 justify-center">
        <Button className="bg-gradient-to-r from-indigo-500 to-purple-500">
          📤 Send Review Invites
        </Button>
        <Button 
          onClick={exportReviews}
          className="bg-gradient-to-r from-pink-500 to-indigo-500"
        >
          📊 Export Reviews
        </Button>
        <Button className="bg-gradient-to-r from-green-500 to-teal-500">
          🎯 Manage Campaigns
        </Button>
        <Button 
          onClick={loadDashboardData}
          className="bg-gradient-to-r from-amber-500 to-orange-500"
        >
          🔄 Refresh Data
        </Button>
      </div>
    </SaaSLayout>
  );
}
