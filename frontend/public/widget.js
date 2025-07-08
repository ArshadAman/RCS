// Widget embedding script
(function() {
  // Get script element and company ID
  const scripts = document.getElementsByTagName('script');
  const currentScript = scripts[scripts.length - 1];
  const companyId = currentScript.getAttribute('data-company-id');
  
  if (!companyId) {
    console.error('ReviewHub Widget: data-company-id attribute is required');
    return;
  }
  
  // Create widget container
  const container = document.createElement('div');
  container.id = `reviewhub-widget-${companyId}`;
  container.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    font-family: Inter, sans-serif;
  `;
  
  // Insert widget HTML
  container.innerHTML = `
    <div id="widget-${companyId}" style="
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
      max-width: 300px;
      cursor: pointer;
    ">
      <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <div id="logo-${companyId}" style="width: 32px; height: 32px; margin-right: 8px;"></div>
        <h3 id="name-${companyId}" style="margin: 0; font-size: 16px; font-weight: 600;"></h3>
        <span id="badge-${companyId}" style="margin-left: 8px; font-size: 12px;"></span>
      </div>
      <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <span id="rating-${companyId}" style="color: #10b981; font-weight: bold; font-size: 18px;"></span>
        <span id="count-${companyId}" style="color: #64748b; margin-left: 8px; font-size: 14px;"></span>
      </div>
      <div id="recommend-${companyId}" style="color: #64748b; font-size: 14px; margin-bottom: 12px;"></div>
      <button style="
        background: #6366f1;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
        font-size: 14px;
      ">Read Reviews</button>
    </div>
  `;
  
  // Add to page
  document.body.appendChild(container);
  
  // Fetch widget data
  fetch(`/api/widget/${companyId}/`)
    .then(response => response.json())
    .then(data => {
      const { company, badge, average_rating, total_reviews, recommend_percent } = data;
      
      // Update widget content
      document.getElementById(`name-${companyId}`).textContent = company.name;
      document.getElementById(`rating-${companyId}`).textContent = `${average_rating}★`;
      document.getElementById(`count-${companyId}`).textContent = `(${total_reviews} reviews)`;
      document.getElementById(`recommend-${companyId}`).textContent = `${recommend_percent}% recommend us`;
      
      if (company.logo) {
        document.getElementById(`logo-${companyId}`).innerHTML = `<img src="${company.logo}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 4px;">`;
      }
      
      if (badge) {
        const badgeEl = document.getElementById(`badge-${companyId}`);
        badgeEl.textContent = badge.badge_type.toUpperCase();
        badgeEl.style.cssText = `
          padding: 2px 8px;
          border-radius: 4px;
          font-weight: 600;
          ${badge.badge_type === 'gold' ? 'background: #fef3c7; color: #92400e;' :
            badge.badge_type === 'silver' ? 'background: #f3f4f6; color: #374151;' :
            'background: #fed7aa; color: #9a3412;'}
        `;
      }
      
      // Add click handler
      document.getElementById(`widget-${companyId}`).addEventListener('click', () => {
        window.open(`/company/${companyId}/reviews`, '_blank');
      });
    })
    .catch(error => {
      console.error('ReviewHub Widget: Failed to load data', error);
    });
})();
