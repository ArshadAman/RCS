import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SaaSLayout from '../components/SaaSLayout';
import Card from '../components/Card';
import Button from '../components/Button';
import { businesses, categories, qr } from '../api/api';
import { useCompany } from '../context/CompanyContext';

export default function BusinessList() {
  const navigate = useNavigate();
  const { currentCompany } = useCompany();
  const [businessList, setBusinessList] = useState([]);
  const [categoriesList, setCategoriesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [newBusiness, setNewBusiness] = useState({
    name: '',
    description: '',
    address: '',
    phone: '',
    email: '',
    website: '',
    category: ''
  });

  useEffect(() => {
    loadData();
  }, [currentCompany]);

  const loadData = async () => {
    if (!currentCompany) return;
    
    try {
      setLoading(true);
      setError('');

      // Load businesses and categories in parallel
      const [businessData, categoryData] = await Promise.all([
        businesses.list(currentCompany.id),
        categories.list()
      ]);

      setBusinessList(businessData.results || businessData || []);
      setCategoriesList(categoryData.results || categoryData || []);
    } catch (err) {
      console.error('Failed to load data:', err);
      setError(err.message || 'Failed to load businesses');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBusiness = async (e) => {
    e.preventDefault();
    if (!newBusiness.name.trim()) {
      alert('Business name is required');
      return;
    }

    try {
      setCreateLoading(true);
      const businessData = {
        ...newBusiness,
        company: currentCompany.id
      };
      
      await businesses.create(businessData);
      
      // Reset form and reload data
      setNewBusiness({
        name: '',
        description: '',
        address: '',
        phone: '',
        email: '',
        website: '',
        category: ''
      });
      setShowCreateForm(false);
      loadData();
    } catch (err) {
      console.error('Failed to create business:', err);
      alert(err.message || 'Failed to create business');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteBusiness = async (businessId, businessName) => {
    if (!window.confirm(`Are you sure you want to delete "${businessName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await businesses.delete(businessId);
      loadData();
    } catch (err) {
      console.error('Failed to delete business:', err);
      alert(err.message || 'Failed to delete business');
    }
  };

  const downloadQRCode = async (businessId, businessName) => {
    try {
      if (!currentCompany?.id) return;
      
      const qrData = await qr.generate(currentCompany.id, businessId);
      
      // Create download link
      const link = document.createElement('a');
      link.href = qrData.qr_code_url || qrData.url;
      link.download = `qr-code-${businessName.replace(/[^a-zA-Z0-9]/g, '-')}.png`;
      link.click();
    } catch (err) {
      console.error('Failed to download QR code:', err);
      alert('Failed to generate QR code. Please try again.');
    }
  };

  // Filter businesses based on search and category
  const filteredBusinesses = businessList.filter(business => {
    const matchesSearch = business.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (business.description || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !selectedCategory || business.category === selectedCategory;
    return matchesSearch && matchesCategory;
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
            <p className="text-slate-600">Loading businesses...</p>
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
            <h2 className="text-xl font-semibold text-red-600 mb-2">Error Loading Businesses</h2>
            <p className="text-slate-600 mb-4">{error}</p>
            <Button onClick={loadData}>Retry</Button>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  return (
    <SaaSLayout>
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row items-center justify-between mb-6">
          <h2 className="text-4xl font-extrabold text-slate-900 mb-4 sm:mb-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
            Businesses
          </h2>
          <Button 
            onClick={() => setShowCreateForm(true)}
            className="bg-gradient-to-r from-indigo-500 to-purple-500"
          >
            ➕ Add Business
          </Button>
        </div>

        {/* Search and Filter */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search businesses..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            {categoriesList.map(cat => (
              <option key={cat.id} value={cat.name}>{cat.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Create Business Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-96 overflow-y-auto">
            <h3 className="text-xl font-bold text-slate-900 mb-4">Add New Business</h3>
            <form onSubmit={handleCreateBusiness} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Business Name *</label>
                <input
                  type="text"
                  value={newBusiness.name}
                  onChange={(e) => setNewBusiness(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea
                  value={newBusiness.description}
                  onChange={(e) => setNewBusiness(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  rows="2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
                <select
                  value={newBusiness.category}
                  onChange={(e) => setNewBusiness(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  <option value="">Select Category</option>
                  {categoriesList.map(cat => (
                    <option key={cat.id} value={cat.name}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Address</label>
                <input
                  type="text"
                  value={newBusiness.address}
                  onChange={(e) => setNewBusiness(prev => ({ ...prev, address: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <div className="flex gap-4 pt-4">
                <Button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1 bg-slate-500 hover:bg-slate-600"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createLoading}
                  className="flex-1 bg-gradient-to-r from-indigo-500 to-purple-500"
                >
                  {createLoading ? 'Creating...' : 'Create'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Business Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredBusinesses.length > 0 ? filteredBusinesses.map(business => (
          <Card key={business.id} gradient className="hover:scale-105 transition-transform">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-bold text-slate-800 flex-1 mr-2">{business.name}</h3>
              <div className="flex space-x-1">
                <button
                  onClick={() => downloadQRCode(business.id, business.name)}
                  className="text-indigo-600 hover:text-indigo-800 text-sm"
                  title="Download QR Code"
                >
                  📱
                </button>
                <button
                  onClick={() => handleDeleteBusiness(business.id, business.name)}
                  className="text-red-600 hover:text-red-800 text-sm"
                  title="Delete Business"
                >
                  🗑️
                </button>
              </div>
            </div>

            {business.category && (
              <p className="text-slate-500 text-sm mb-2">📂 {business.category}</p>
            )}
            
            {business.description && (
              <p className="text-slate-600 text-sm mb-3 line-clamp-2">{business.description}</p>
            )}

            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <span className="text-yellow-500 font-bold text-lg">
                  {business.average_rating ? `${business.average_rating}★` : 'No rating'}
                </span>
                <span className="text-slate-400 ml-2 text-sm">
                  ({business.total_reviews || 0} reviews)
                </span>
              </div>
            </div>

            {business.address && (
              <p className="text-slate-500 text-xs mb-3">📍 {business.address}</p>
            )}

            <div className="flex gap-2">
              <Button 
                className="flex-1 text-sm" 
                onClick={() => navigate(`/businesses/${business.id}`)}
              >
                View Details
              </Button>
              <Button 
                className="flex-1 text-sm bg-gradient-to-r from-pink-500 to-indigo-500" 
                onClick={() => navigate(`/businesses/${business.id}/reviews`)}
              >
                Reviews
              </Button>
            </div>
          </Card>
        )) : (
          <div className="col-span-full text-center py-12">
            <div className="text-4xl mb-4">🏢</div>
            <h3 className="text-xl font-semibold text-slate-700 mb-2">
              {searchTerm || selectedCategory ? 'No businesses match your search' : 'No businesses yet'}
            </h3>
            <p className="text-slate-500 mb-6">
              {searchTerm || selectedCategory 
                ? 'Try adjusting your search criteria or filters.'
                : 'Create your first business to start collecting reviews!'
              }
            </p>
            {!searchTerm && !selectedCategory && (
              <Button 
                onClick={() => setShowCreateForm(true)}
                className="bg-gradient-to-r from-indigo-500 to-purple-500"
              >
                ➕ Add Your First Business
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Statistics */}
      {businessList.length > 0 && (
        <div className="mt-8 text-center text-slate-500 text-sm">
          Showing {filteredBusinesses.length} of {businessList.length} businesses
          {(searchTerm || selectedCategory) && (
            <span className="ml-2">
              • <button 
                onClick={() => { setSearchTerm(''); setSelectedCategory(''); }}
                className="text-indigo-600 hover:text-indigo-800 underline"
              >
                Clear filters
              </button>
            </span>
          )}
        </div>
      )}
    </SaaSLayout>
  );
}
