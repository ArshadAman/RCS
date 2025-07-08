# 🚀 API Integration Guide - UI Elements & Endpoints

This document provides a comprehensive overview of where each API endpoint is implemented and used in the frontend UI.

## 📱 **Navigation & Access**

### **Main Navigation (SaaSLayout.jsx)**
- **Dashboard** (`/dashboard`) - Overview with analytics
- **Businesses** (`/businesses`) - Business management
- **Reviews** (`/reviews`) - Review moderation
- **Surveys** (`/surveys`) - Survey question management
- **Widgets & QR** (`/widgets`) - Widget and QR code tools
- **Admin** (`/admin`) - Administrative controls
- **Profile** (`/profile`) - User profile settings

---

## 🔐 **Authentication APIs** (`/api/auth/`)

### **Used in: Auth.jsx, Profile.jsx**

| Endpoint | Method | UI Element | Description |
|----------|--------|------------|-------------|
| `/auth/login/` | POST | Login form in Auth.jsx | User login with email/password |
| `/auth/register/` | POST | Registration form in Auth.jsx | New user registration |
| `/auth/logout/` | POST | Logout button in navigation | User logout |
| `/auth/profile/` | GET/PUT/PATCH | Profile page forms | View/edit user profile |
| `/auth/profile/simple/` | GET | User avatar in topbar | Quick profile info |
| `/auth/password/change/` | POST | Password change form | Change password |
| `/auth/password/reset/` | POST | Forgot password form | Initiate password reset |
| `/auth/password/reset/confirm/` | POST | Reset confirmation form | Confirm password reset |
| `/auth/email/verify/` | POST | Email verification | Verify email address |
| `/auth/token/refresh/` | POST | Automatic token refresh | Maintain authentication |

### **UI Elements:**
- **Login Form**: Email/password inputs, submit button
- **Registration Form**: User details form with validation
- **Profile Settings**: Edit name, email, preferences
- **Password Management**: Change/reset password forms

---

## 🏢 **Business Management APIs** (`/api/businesses/`)

### **Used in: Dashboard.jsx, BusinessList.jsx, BusinessDetail.jsx, Admin.jsx**

| Endpoint | Method | UI Element | Description |
|----------|--------|------------|-------------|
| `/businesses/` | GET | Business grid, dashboard cards | List all businesses |
| `/businesses/` | POST | "Add Business" modal form | Create new business |
| `/businesses/{id}/` | GET | Business detail page | Individual business info |
| `/businesses/{id}/` | PUT/PATCH | Edit business modal | Update business details |
| `/businesses/{id}/` | DELETE | Delete button | Remove business |
| `/businesses/{id}/reviews/` | GET | Reviews section | Business-specific reviews |
| `/businesses/{id}/stats/` | GET | Stats cards, dashboard metrics | Business analytics |

### **UI Elements:**
- **Business Cards**: Name, category, rating, review count
- **Create Business Modal**: Form with name, description, category, address
- **Business Detail Page**: Full business info, reviews, stats
- **Search & Filter**: Search by name, filter by category
- **QR Code Buttons**: Generate/download QR codes for each business

---

## 📝 **Review Management APIs** (`/api/reviews/`)

### **Used in: Dashboard.jsx, Reviews.jsx, BusinessDetail.jsx, Admin.jsx**

| Endpoint | Method | UI Element | Description |
|----------|--------|------------|-------------|
| `/reviews/` | GET | Review lists, recent reviews | All reviews with filtering |
| `/reviews/` | POST | Review submission form | Create new review |
| `/reviews/{id}/` | GET/PUT/PATCH | Review details | Individual review management |
| `/reviews/{id}/` | DELETE | Delete review button | Remove review |
| `/reviews/{id}/response/` | PUT/PATCH | Business response form | Respond to reviews |
| `/reviews/{id}/approve/` | POST | Approve button | Approve pending reviews |
| `/reviews/{id}/like/` | POST | Like button | Like/unlike reviews |

### **UI Elements:**
- **Review Cards**: Customer name, rating stars, comment, status badges
- **Review Form**: Rating selector, comment textarea, customer details
- **Moderation Controls**: Approve/reject buttons, delete options
- **Response System**: Business response forms and display
- **Filter Controls**: Status, business, search filters

---

## 🏭 **Company Management APIs** (`/api/companies/`)

### **Used in: CompanyContext.jsx, SaaSLayout.jsx**

| Endpoint | Method | UI Element | Description |
|----------|--------|------------|-------------|
| `/companies/` | GET | Company dropdown, context | List user's companies |

### **UI Elements:**
- **Company Switcher**: Dropdown in topbar to switch between companies
- **Company Context**: Global state management for multi-tenancy

---

## 📋 **Survey APIs** (`/api/survey-questions/`, `/api/review-answers/`)

### **Used in: Surveys.jsx, Admin.jsx**

| Endpoint | Method | UI Element | Description |
|----------|--------|------------|-------------|
| `/survey-questions/` | GET | Survey questions list | Display all survey questions |
| `/survey-questions/` | POST | Create question modal | Add new survey question |
| `/survey-questions/{id}/` | GET/PUT/PATCH | Edit question form | Update survey question |
| `/survey-questions/{id}/` | DELETE | Delete question button | Remove survey question |
| `/review-answers/` | GET | Survey responses list | Display survey responses |
| `/review-answers/` | POST | Dynamic survey forms | Submit survey responses |
| `/review-answers/{id}/` | GET/PUT/PATCH/DELETE | Answer management | Manage individual responses |

### **UI Elements:**
- **Question Builder**: Form to create text, choice, rating questions
- **Question List**: Display of all survey questions with type badges
- **Response Viewer**: Show survey answers with question context
- **Question Types**: Text, textarea, radio, checkbox, rating, yes/no
- **Export Functionality**: Download survey data as CSV

---

## 🔗 **Widget & QR APIs** (`/api/widget/`, `/api/qr-code/`, `/api/qr-feedback/`)

### **Used in: WidgetManager.jsx, Dashboard.jsx, BusinessList.jsx**

| Endpoint | Method | UI Element | Description |
|----------|--------|------------|-------------|
| `/widget/{company_id}/` | GET | Widget preview, embed codes | Get widget configuration |
| `/qr-code/{company_id}/{branch_id}/` | GET | QR code generator | Generate QR codes |
| `/qr-feedback/{branch_id}/` | POST | QR feedback form | Submit feedback via QR |

### **UI Elements:**
- **Widget Preview**: Live preview of review widget
- **Embed Code Generator**: JavaScript and iframe embed codes
- **QR Code Generator**: Generate and download QR codes for businesses
- **Widget Configuration**: Theme, position, color settings
- **QR Code Display**: Visual QR codes with download links

---

## 📊 **Order Management APIs** (`/api/orders/`)

### **Used in: Admin.jsx, potentially for webhooks**

| Endpoint | Method | UI Element | Description |
|----------|--------|------------|-------------|
| `/orders/webhook/` | POST | Webhook management | Handle order webhooks |

---

## 📂 **Category APIs** (`/api/categories/`)

### **Used in: BusinessList.jsx, BusinessDetail.jsx, Surveys.jsx**

| Endpoint | Method | UI Element | Description |
|----------|--------|------------|-------------|
| `/categories/` | GET | Category dropdown filters | List all business categories |

### **UI Elements:**
- **Category Filter**: Dropdown to filter businesses by category
- **Business Form**: Category selection in business creation/editing

---

## 🎯 **Key UI Features by Page**

### **📊 Dashboard** (`/dashboard`)
- **Metrics Cards**: Business count, review count, average rating, badge status
- **Review Trends**: 6-month chart showing review volume and ratings
- **Top Businesses**: Best performing businesses with ratings
- **Recent Reviews**: Latest customer feedback
- **Quick Actions**: Export data, QR generation, refresh

### **🏢 Business List** (`/businesses`)
- **Business Grid**: Card layout with business info and actions
- **Search & Filter**: Text search and category filtering
- **Create Business**: Modal form for adding new businesses
- **Business Actions**: View details, QR codes, delete options

### **📝 Reviews Management** (`/reviews`)
- **Review List**: Comprehensive review display with filtering
- **Moderation Tools**: Approve, reject, respond, delete actions
- **Filter System**: Status, business, search functionality
- **Bulk Operations**: Export reviews, batch approval

### **📋 Survey Management** (`/surveys`)
- **Question Builder**: Create dynamic survey questions
- **Question Types**: Support for text, choice, rating questions
- **Response Viewer**: Display and analyze survey responses
- **Export Tools**: CSV export of survey data

### **🔗 Widget Manager** (`/widgets`)
- **Widget Preview**: Live preview of review collection widget
- **Code Generation**: JavaScript and iframe embed codes
- **QR Code Tools**: Generate and download QR codes
- **Configuration**: Widget theming and positioning

### **👑 Admin Panel** (`/admin`)
- **Multi-tab Interface**: Overview, Reviews, Businesses, Surveys, Export
- **Data Management**: Comprehensive admin controls
- **Export Functionality**: CSV export for all data types
- **Moderation Tools**: Review approval, business management

---

## 🛡️ **Security & Authentication**

- **JWT Token Management**: Automatic token handling in all API calls
- **Company Context**: Multi-tenant security with company isolation
- **Role-based Access**: Different UI elements based on user permissions
- **Error Handling**: Comprehensive error states and recovery

---

## 📱 **Mobile Responsiveness**

All UI elements are designed to be mobile-friendly:
- **Responsive Grids**: Adapt from desktop to mobile layouts
- **Touch-friendly Buttons**: Appropriately sized for mobile interaction
- **Collapsible Navigation**: Mobile hamburger menu
- **Optimized Forms**: Mobile-first form design

---

## 🎨 **Design System**

- **Modern SaaS Aesthetic**: Stripe-inspired gradients and spacing
- **Consistent Theming**: Unified color scheme (indigo, purple, pink)
- **Component Library**: Reusable Card, Button, and layout components
- **Accessibility**: Proper contrast ratios and keyboard navigation

This comprehensive integration ensures that all backend API endpoints are accessible through intuitive UI elements, providing a complete SaaS feedback collection platform! 🚀
