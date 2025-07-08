import React, { useState } from 'react';
import SaaSLayout from '../components/SaaSLayout';
import Card from '../components/Card';
import Button from '../components/Button';
import { useCompany } from '../context/CompanyContext';

export default function QRFeedback() {
  const { currentCompany } = useCompany();
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const branchId = new URLSearchParams(window.location.search).get('id');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (rating < 1) {
      alert('Please select a rating');
      return;
    }
    
    if (rating <= 2 && !comment.trim()) {
      alert('Please provide a comment for ratings below 3 stars');
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch(`/api/qr-feedback/${branchId}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, comment: comment.trim() })
      });
      
      if (response.ok) {
        setSubmitted(true);
      } else {
        alert('Failed to submit feedback. Please try again.');
      }
    } catch (error) {
      alert('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!currentCompany) return <div className="flex items-center justify-center min-h-screen">Loading...</div>;

  if (submitted) {
    return (
      <SaaSLayout>
        <main className="flex-1 flex items-center justify-center px-4 bg-gradient-to-br from-indigo-50 via-white to-pink-50 min-h-screen">
          <Card gradient className="max-w-md w-full text-center">
            <div className="text-pink-500 text-6xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">Thank You!</h2>
            <p className="text-slate-500">Your feedback has been submitted successfully.</p>
          </Card>
        </main>
      </SaaSLayout>
    );
  }

  return (
    <SaaSLayout>
      <main className="flex-1 flex items-center justify-center px-4 bg-gradient-to-br from-indigo-50 via-white to-pink-50 min-h-screen">
        <Card gradient className="max-w-md w-full">
          <h1 className="text-2xl font-bold text-slate-900 mb-6 text-center">
            Share Your Feedback
          </h1>
          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-800 mb-2">
                Rate your experience:
              </label>
              <div className="flex justify-center space-x-2">
                {[1, 2, 3, 4, 5].map(star => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className={`text-3xl transition-colors ${star <= rating ? 'text-pink-500' : 'text-gray-300'}`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-800 mb-2">
                Comment {rating <= 2 && <span className="text-red-500">*</span>}:
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={4}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-pink-200"
                placeholder="Tell us about your experience..."
                required={rating <= 2}
              />
            </div>
            <Button
              type="submit"
              disabled={loading || rating < 1}
              className="w-full"
            >
              {loading ? 'Submitting...' : 'Submit Feedback'}
            </Button>
          </form>
        </Card>
      </main>
    </SaaSLayout>
  );
}
