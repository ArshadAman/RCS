import React, { useState, useEffect } from 'react';
import Card from '../components/Card';
import Button from '../components/Button';
import { createReview } from '../api/api';
import SaaSLayout from '../components/SaaSLayout';
import { useCompany } from '../context/CompanyContext';

export default function ReviewForm({ businessId }) {
  const { currentCompany } = useCompany();
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    rating: 0,
    reviewer_name: '',
    reviewer_email: '',
    is_anonymous: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [surveyQuestions, setSurveyQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [recommendUs, setRecommendUs] = useState(null);

  // Fetch survey questions for the selected company
  useEffect(() => {
    if (!currentCompany) return;
    // Replace with real API call: `/api/survey-questions/?company_id=${currentCompany.id}`
    setSurveyQuestions([
      { id: 1, text: 'Reliability', is_required: true },
      { id: 2, text: 'Delivery Speed', is_required: true },
      { id: 3, text: 'Product Availability', is_required: false },
      { id: 4, text: 'Communication Quality', is_required: true },
      { id: 5, text: 'Website Usability', is_required: false },
    ]);
  }, [currentCompany]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleRatingClick = (rating) => {
    setFormData({ ...formData, rating });
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers({ ...answers, [questionId]: value });
  };

  const handleRecommendChange = (value) => {
    setRecommendUs(value);
    if (value === 'yes') {
      // Auto-fill with 5 stars if user recommends
      setFormData({ ...formData, rating: formData.rating || 5 });
      // Auto-fill survey answers with high ratings
      const autoAnswers = {};
      surveyQuestions.forEach(q => {
        if (!answers[q.id]) autoAnswers[q.id] = '5';
      });
      setAnswers({ ...answers, ...autoAnswers });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Validation
    if (formData.rating < 1) {
      setError('Please select a rating');
      setLoading(false);
      return;
    }

    if (recommendUs === 'no' && !formData.content.trim()) {
      setError('Comment is required when you would not recommend us');
      setLoading(false);
      return;
    }

    // Check required survey questions
    for (const question of surveyQuestions) {
      if (question.is_required && !answers[question.id]) {
        setError(`Please answer: ${question.text}`);
        setLoading(false);
        return;
      }
    }

    try {
      const reviewData = {
        ...formData,
        business_id: businessId,
        answers: Object.entries(answers).map(([questionId, value]) => ({
          question: parseInt(questionId),
          value
        }))
      };

      await createReview(businessId, reviewData);
      setSuccess(true);
    } catch (err) {
      setError('Failed to submit review. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <SaaSLayout>
        <main className="flex-1 flex items-center justify-center px-4 bg-gradient-to-br from-indigo-50 via-white to-pink-50 min-h-screen">
          <Card gradient className="max-w-lg mx-auto text-center">
            <div className="text-pink-500 text-6xl mb-4">✓</div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Thank You!</h3>
            <p className="text-slate-500">Your review has been submitted and is pending approval.</p>
          </Card>
        </main>
      </SaaSLayout>
    );
  }

  if (!currentCompany) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        Loading...
      </div>
    );
  }

  return (
    <SaaSLayout>
      <main className="flex-1 flex flex-col items-center justify-center px-4 bg-gradient-to-br from-indigo-50 via-white to-pink-50 min-h-screen">
        <Card gradient className="w-full max-w-2xl mx-auto">
          <form onSubmit={handleSubmit}>
            {/* Primary Question */}
            <div className="mb-6">
              <label className="block text-lg font-bold text-slate-800 mb-2">
                Would you recommend us?
              </label>
              <div className="flex gap-4 justify-center mb-4">
                <Button
                  type="button"
                  className={`px-6 py-2 ${recommendUs === 'yes' ? 'ring-2 ring-pink-400' : ''}`}
                  onClick={() => handleRecommendChange('yes')}
                >
                  Yes
                </Button>
                <Button
                  type="button"
                  className={`px-6 py-2 ${recommendUs === 'no' ? 'ring-2 ring-indigo-400' : ''}`}
                  onClick={() => handleRecommendChange('no')}
                >
                  No
                </Button>
              </div>
            </div>

            {/* Rating Questions */}
            {(recommendUs === 'no' || (recommendUs === 'yes' && surveyQuestions.length > 0)) && (
              <div className="mb-6">
                <h4 className="text-lg font-medium text-slate-800 mb-4">Rate the following:</h4>
                <div className="space-y-4">
                  {surveyQuestions.map(question => (
                    <div key={question.id}>
                      <label className="block text-sm font-medium text-slate-800 mb-2">
                        {question.text} {question.is_required && <span className="text-red-500">*</span>}
                      </label>
                      <div className="flex space-x-2">
                        {[1, 2, 3, 4, 5].map(rating => (
                          <button
                            key={rating}
                            type="button"
                            onClick={() => handleAnswerChange(question.id, rating.toString())}
                            className={`text-2xl transition-colors ${
                              parseInt(answers[question.id]) >= rating ? 'text-pink-500' : 'text-gray-300'
                            }`}
                          >
                            ★
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Overall Rating */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-800 mb-2">
                Overall Rating <span className="text-red-500">*</span>
              </label>
              <div className="flex space-x-2">
                {[1, 2, 3, 4, 5].map(rating => (
                  <button
                    key={rating}
                    type="button"
                    onClick={() => handleRatingClick(rating)}
                    className={`text-3xl transition-colors ${
                      formData.rating >= rating ? 'text-pink-500' : 'text-gray-300'
                    }`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>

            {/* Review Details */}
            <div className="mb-6">
              <input
                type="text"
                name="title"
                placeholder="Review Title"
                value={formData.title}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-pink-200 mb-4"
                required
              />
              <textarea
                name="content"
                placeholder="Tell us about your experience..."
                value={formData.content}
                onChange={handleChange}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-pink-200"
                required={recommendUs === 'no'}
              />
            </div>

            {/* Reviewer Info */}
            <div className="grid md:grid-cols-2 gap-4 mb-6">
              <input
                type="text"
                name="reviewer_name"
                placeholder="Your Name"
                value={formData.reviewer_name}
                onChange={handleChange}
                className="px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-200"
                required
              />
              <input
                type="email"
                name="reviewer_email"
                placeholder="Your Email"
                value={formData.reviewer_email}
                onChange={handleChange}
                className="px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-200"
                required
              />
            </div>

            <div className="flex items-center mb-6">
              <input
                type="checkbox"
                name="is_anonymous"
                checked={formData.is_anonymous}
                onChange={handleChange}
                className="mr-2 accent-pink-500"
              />
              <label className="text-sm text-slate-500">Post anonymously</label>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full mt-4"
            >
              {loading ? 'Submitting...' : 'Submit Review'}
            </Button>
          </form>
        </Card>
      </main>
    </SaaSLayout>
  );
}
