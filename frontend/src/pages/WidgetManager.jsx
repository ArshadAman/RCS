import React, { useState, useEffect } from 'react';
import SaaSLayout from '../components/SaaSLayout';
import Card from '../components/Card';
import Button from '../components/Button';
import { useCompany } from '../context/CompanyContext';
import { widget, businesses, qr } from '../api/api';

export default function WidgetManager() {
  const { currentCompany } = useCompany();
  const [widgetData, setWidgetData] = useState(null);
  const [businessesList, setBusinessesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBusiness, setSelectedBusiness] = useState('');
  const [activeTab, setActiveTab] = useState('preview');

  useEffect(() => {
    if (currentCompany?.id) {
      loadData();
    }
  }, [currentCompany]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [widgetInfo, businessData] = await Promise.all([
        widget.getData(currentCompany.id),
        businesses.list(currentCompany.id)
      ]);

      setWidgetData(widgetInfo);
      setBusinessesList(businessData.results || businessData || []);
    } catch (err) {
      console.error('Failed to load widget data:', err);
      setError(err.message || 'Failed to load widget data');
    } finally {
      setLoading(false);
    }
  };

  const generateQRCode = async (businessId) => {
    try {
      if (!businessId) {
        alert('Please select a business first');
        return;
      }

      const qrData = await qr.generate(currentCompany.id, businessId);
      
      // Create download link
      const link = document.createElement('a');
      link.href = qrData.qr_code_url || qrData.url;
      link.download = `qr-code-business-${businessId}.png`;
      link.click();
    } catch (err) {
      console.error('Failed to generate QR code:', err);
      alert('Failed to generate QR code. Please try again.');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy:', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      alert('Copied to clipboard!');
    });
  };

  const generateWidgetCode = (businessId = 'YOUR_BUSINESS_ID') => {
    const baseUrl = window.location.origin;
    return `<!-- Review Collection Widget -->
<div id="rcs-widget-${businessId}"></div>
<script>
  (function() {
    var script = document.createElement('script');
    script.src = '${baseUrl}/widget.js';
    script.onload = function() {
      RCSWidget.init({
        companyId: '${currentCompany.id}',
        businessId: '${businessId}',
        theme: 'modern',
        position: 'bottom-right'
      });
    };
    document.head.appendChild(script);
  })();
</script>`;
  };

  const generateEmbedCode = (businessId = 'YOUR_BUSINESS_ID') => {
    const baseUrl = window.location.origin;
    return `<iframe 
  src="${baseUrl}/widget/${currentCompany.id}?business=${businessId}" 
  width="100%" 
  height="400" 
  frameborder="0"
  style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
</iframe>`;
  };

  const generateQRFeedbackUrl = (businessId = 'YOUR_BUSINESS_ID') => {
    const baseUrl = window.location.origin;
    return `${baseUrl}/qr-feedback?company=${currentCompany.id}&business=${businessId}`;
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
            <p className="text-slate-600">Loading widget data...</p>
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
            <h2 className="text-xl font-semibold text-red-600 mb-2">Error Loading Widget</h2>
            <p className="text-slate-600 mb-4">{error}</p>
            <Button onClick={loadData}>Retry</Button>
          </div>
        </div>
      </SaaSLayout>
    );
  }

  const tabs = [
    { id: 'preview', name: 'Preview', icon: '👁️' },
    { id: 'embed', name: 'Embed Code', icon: '🔗' },
    { id: 'qr', name: 'QR Codes', icon: '📱' },
    { id: 'settings', name: 'Settings', icon: '⚙️' }
  ];

  return (
    <SaaSLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-extrabold text-slate-900 mb-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
          Widget & QR Manager
        </h1>
        <p className="text-slate-600">Embed review collection widgets and generate QR codes for {currentCompany.name}</p>
      </div>

      {/* Business Selector */}
      <Card gradient className="mb-8">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-slate-700">Select Business:</label>
          <select
            value={selectedBusiness}
            onChange={(e) => setSelectedBusiness(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="">Choose a business</option>
            {businessesList.map(business => (
              <option key={business.id} value={business.id}>
                {business.name}
              </option>
            ))}
          </select>
          {selectedBusiness && (
            <span className="text-sm text-slate-500">
              Selected: {businessesList.find(b => b.id.toString() === selectedBusiness)?.name}
            </span>
          )}
        </div>
      </Card>

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

      {/* Tab Content */}
      {activeTab === 'preview' && (
        <div className="space-y-8">
          <Card gradient>
            <h3 className="text-xl font-bold text-slate-900 mb-6">Widget Preview</h3>
            <div className="bg-slate-100 p-8 rounded-lg min-h-96 flex items-center justify-center">
              <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
                <h4 className="text-lg font-bold text-slate-900 mb-4">
                  📝 Leave a Review
                </h4>
                <p className="text-slate-600 mb-4">
                  {selectedBusiness 
                    ? `Share your experience with ${businessesList.find(b => b.id.toString() === selectedBusiness)?.name}`
                    : 'Share your experience with our business'
                  }
                </p>
                <div className="space-y-3">
                  <div className="flex justify-center space-x-1 mb-3">
                    {[1, 2, 3, 4, 5].map(star => (
                      <span key={star} className="text-2xl text-yellow-400 cursor-pointer hover:text-yellow-500">★</span>
                    ))}
                  </div>
                  <textarea 
                    placeholder="Tell us about your experience..."
                    className="w-full p-3 border border-slate-300 rounded-lg"
                    rows="3"
                    disabled
                  />
                  <input
                    type="text"
                    placeholder="Your name (optional)"
                    className="w-full p-3 border border-slate-300 rounded-lg"
                    disabled
                  />
                  <button className="w-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white py-3 rounded-lg font-medium">
                    Submit Review
                  </button>
                </div>
              </div>
            </div>
            <div className="mt-4 text-center text-slate-500 text-sm">
              This is a preview of how the widget will appear on your website
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'embed' && (
        <div className="space-y-8">
          {/* Widget Code */}
          <Card gradient>
            <h3 className="text-xl font-bold text-slate-900 mb-6">JavaScript Widget</h3>
            <p className="text-slate-600 mb-4">
              Add this code to your website to display a floating review widget:
            </p>
            <div className="bg-slate-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
              <pre>{generateWidgetCode(selectedBusiness)}</pre>
            </div>
            <div className="flex justify-between items-center mt-4">
              <p className="text-sm text-slate-500">
                The widget will appear as a floating button on your website
              </p>
              <Button
                onClick={() => copyToClipboard(generateWidgetCode(selectedBusiness))}
                className="bg-green-500 hover:bg-green-600"
              >
                📋 Copy Code
              </Button>
            </div>
          </Card>

          {/* Embed Code */}
          <Card gradient>
            <h3 className="text-xl font-bold text-slate-900 mb-6">iFrame Embed</h3>
            <p className="text-slate-600 mb-4">
              Embed the review form directly into your page using an iframe:
            </p>
            <div className="bg-slate-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
              <pre>{generateEmbedCode(selectedBusiness)}</pre>
            </div>
            <div className="flex justify-between items-center mt-4">
              <p className="text-sm text-slate-500">
                This will embed the full review form inline with your content
              </p>
              <Button
                onClick={() => copyToClipboard(generateEmbedCode(selectedBusiness))}
                className="bg-green-500 hover:bg-green-600"
              >
                📋 Copy Code
              </Button>
            </div>
          </Card>

          {/* Direct Link */}
          <Card gradient>
            <h3 className="text-xl font-bold text-slate-900 mb-6">Direct Link</h3>
            <p className="text-slate-600 mb-4">
              Share this direct link to your review form:
            </p>
            <div className="bg-slate-100 p-4 rounded-lg font-mono text-sm break-all">
              {generateQRFeedbackUrl(selectedBusiness)}
            </div>
            <div className="flex justify-between items-center mt-4">
              <p className="text-sm text-slate-500">
                Use this link in emails, social media, or anywhere you want to collect reviews
              </p>
              <Button
                onClick={() => copyToClipboard(generateQRFeedbackUrl(selectedBusiness))}
                className="bg-blue-500 hover:bg-blue-600"
              >
                📋 Copy Link
              </Button>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'qr' && (
        <div className="space-y-8">
          <Card gradient>
            <h3 className="text-xl font-bold text-slate-900 mb-6">QR Code Generator</h3>
            
            <div className="grid md:grid-cols-2 gap-8">
              {/* QR Code Generator */}
              <div>
                <h4 className="text-lg font-semibold text-slate-800 mb-4">Generate QR Codes</h4>
                <p className="text-slate-600 mb-4">
                  Generate QR codes that customers can scan to quickly leave reviews for your businesses.
                </p>
                
                <div className="space-y-4">
                  {businessesList.map(business => (
                    <div key={business.id} className="flex items-center justify-between p-3 bg-white/50 rounded-lg border border-slate-200">
                      <div>
                        <h5 className="font-medium text-slate-800">{business.name}</h5>
                        <p className="text-sm text-slate-500">{business.category || 'No category'}</p>
                      </div>
                      <Button
                        onClick={() => generateQRCode(business.id)}
                        size="sm"
                        className="bg-gradient-to-r from-indigo-500 to-purple-500"
                      >
                        📱 Generate QR
                      </Button>
                    </div>
                  ))}
                  
                  {businessesList.length === 0 && (
                    <div className="text-center py-8 text-slate-500">
                      <div className="text-4xl mb-4">🏢</div>
                      <p>No businesses found. Create a business first to generate QR codes.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* QR Code Preview */}
              <div>
                <h4 className="text-lg font-semibold text-slate-800 mb-4">QR Code Preview</h4>
                <div className="bg-white p-8 rounded-lg border border-slate-200 text-center">
                  <div className="w-48 h-48 bg-slate-100 rounded-lg mx-auto mb-4 flex items-center justify-center">
                    <div className="text-6xl">📱</div>
                  </div>
                  <p className="text-slate-600 mb-2">
                    {selectedBusiness 
                      ? `QR Code for ${businessesList.find(b => b.id.toString() === selectedBusiness)?.name}`
                      : 'Select a business to preview QR code'
                    }
                  </p>
                  {selectedBusiness && (
                    <Button
                      onClick={() => generateQRCode(selectedBusiness)}
                      className="mt-4 bg-gradient-to-r from-indigo-500 to-purple-500"
                    >
                      📱 Download QR Code
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </Card>

          {/* QR Code Usage Tips */}
          <Card gradient>
            <h4 className="text-lg font-semibold text-slate-800 mb-4">QR Code Usage Tips</h4>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h5 className="font-medium text-slate-700 mb-2">📍 Physical Locations</h5>
                <ul className="text-sm text-slate-600 space-y-1 ml-4">
                  <li>• Print on table tents at restaurants</li>
                  <li>• Display at checkout counters</li>
                  <li>• Include on receipts and invoices</li>
                  <li>• Post near service completion areas</li>
                </ul>
              </div>
              <div>
                <h5 className="font-medium text-slate-700 mb-2">📱 Digital Usage</h5>
                <ul className="text-sm text-slate-600 space-y-1 ml-4">
                  <li>• Include in email signatures</li>
                  <li>• Add to social media posts</li>
                  <li>• Include in delivery confirmations</li>
                  <li>• Display on digital screens</li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="space-y-8">
          <Card gradient>
            <h3 className="text-xl font-bold text-slate-900 mb-6">Widget Settings</h3>
            
            <div className="space-y-6">
              {/* Widget Configuration */}
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-lg font-semibold text-slate-800 mb-4">Appearance</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Widget Theme</label>
                      <select className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                        <option value="modern">Modern (Default)</option>
                        <option value="classic">Classic</option>
                        <option value="minimal">Minimal</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Position</label>
                      <select className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                        <option value="bottom-right">Bottom Right</option>
                        <option value="bottom-left">Bottom Left</option>
                        <option value="top-right">Top Right</option>
                        <option value="top-left">Top Left</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Primary Color</label>
                      <input 
                        type="color" 
                        defaultValue="#6366f1"
                        className="h-10 w-20 border border-slate-300 rounded-lg"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-semibold text-slate-800 mb-4">Behavior</h4>
                  <div className="space-y-4">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="auto_open"
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded"
                        defaultChecked
                      />
                      <label htmlFor="auto_open" className="ml-2 block text-sm text-slate-700">
                        Auto-open after 5 seconds
                      </label>
                    </div>
                    
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="show_powered_by"
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded"
                        defaultChecked
                      />
                      <label htmlFor="show_powered_by" className="ml-2 block text-sm text-slate-700">
                        Show "Powered by" link
                      </label>
                    </div>
                    
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="require_name"
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded"
                      />
                      <label htmlFor="require_name" className="ml-2 block text-sm text-slate-700">
                        Require customer name
                      </label>
                    </div>
                  </div>
                </div>
              </div>

              {/* API Information */}
              <div className="pt-6 border-t border-slate-200">
                <h4 className="text-lg font-semibold text-slate-800 mb-4">API Information</h4>
                <div className="bg-slate-50 p-4 rounded-lg">
                  <div className="grid md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-slate-700">Company ID:</span>
                      <span className="ml-2 font-mono text-slate-600">{currentCompany.id}</span>
                    </div>
                    <div>
                      <span className="font-medium text-slate-700">Widget Endpoint:</span>
                      <span className="ml-2 font-mono text-slate-600">/api/widget/{currentCompany.id}/</span>
                    </div>
                    <div>
                      <span className="font-medium text-slate-700">QR Endpoint:</span>
                      <span className="ml-2 font-mono text-slate-600">/api/qr-code/{currentCompany.id}/[business_id]/</span>
                    </div>
                    <div>
                      <span className="font-medium text-slate-700">Feedback Endpoint:</span>
                      <span className="ml-2 font-mono text-slate-600">/api/qr-feedback/[business_id]/</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Save Settings */}
              <div className="flex justify-end pt-6 border-t border-slate-200">
                <Button className="bg-gradient-to-r from-indigo-500 to-purple-500">
                  💾 Save Settings
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </SaaSLayout>
  );
}
