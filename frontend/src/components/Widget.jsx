import React, { useEffect, useState } from 'react';
import { useCompany } from '../context/CompanyContext';

export default function Widget() {
  const { currentCompany } = useCompany();
  const [data, setData] = useState(null);
  const [showReviews, setShowReviews] = useState(false);

  useEffect(() => {
    if (!currentCompany) return;
    fetch(`/api/widget/${currentCompany.id}/`)
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, [currentCompany]);

  if (!currentCompany || !data) return <div>Loading...</div>;

  const { company, badge, average_rating, total_reviews, recommend_percent, recent_reviews } = data;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-md max-w-sm">
      <div className="flex items-center mb-3">
        {company.logo && (
          <img src={company.logo} alt={company.name} className="w-8 h-8 rounded mr-2" />
        )}
        <h3 className="font-semibold text-slate-800">{company.name}</h3>
        {badge && (
          <span className={`ml-2 px-2 py-1 text-xs rounded ${
            badge.badge_type === 'gold' ? 'bg-yellow-100 text-yellow-800' :
            badge.badge_type === 'silver' ? 'bg-gray-100 text-gray-800' :
            'bg-orange-100 text-orange-800'
          }`}>
            {badge.badge_type.toUpperCase()}
          </span>
        )}
      </div>
      
      <div className="flex items-center mb-2">
        <span className="text-pink-500 font-bold text-lg">{average_rating}★</span>
        <span className="text-slate-400 ml-2">({total_reviews} reviews)</span>
      </div>
      
      <div className="text-sm text-text-light mb-3">
        {recommend_percent}% of customers recommend us
      </div>
      
      <button
        onClick={() => setShowReviews(!showReviews)}
        className="bg-primary text-white px-4 py-2 rounded text-sm hover:bg-primary-dark transition-colors w-full"
      >
        {showReviews ? 'Hide Reviews' : 'Read Reviews'}
      </button>
      
      {showReviews && (
        <div className="mt-4 space-y-3 max-h-64 overflow-y-auto">
          {recent_reviews.map(review => (
            <div key={review.id} className="border-t pt-2">
              <div className="flex items-center mb-1">
                <span className="text-accent text-sm">{review.rating}★</span>
                <span className="text-text-light text-xs ml-2">{review.reviewer_name}</span>
              </div>
              <p className="text-xs text-text">{review.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
