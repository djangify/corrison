# Corrison - Headless E-commerce & CMS Platform

[![Astro](https://img.shields.io/badge/Astro-FF5D01?style=for-the-badge&logo=astro&logoColor=white)](https://astro.build/)
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

A modular, API-first headless platform built with Django REST Framework backend and Astro frontend, designed for e-commerce, content management, and advanced landing pages. Choose any combination of services:

* **Products & Store**: Full e-commerce functionality (products, carts, orders, Stripe integration)
* **Blog**: Content management for blog posts and categories  
* **Pages**: CMS-powered landing pages with advanced features
* **LinkHub**: Structured "link-in-bio" pages with multi-media support
* **Testimonials**: Global testimonial management with star ratings
* **Courses**: Complete Learning Management System with video lessons and progress tracking
* **Calendar**: Appointment booking system with availability management and notifications

## 🌐 Live Examples

### [corrisonapi.com](https://www.corrisonapi.com)
Main platform showcase featuring:
- Advanced landing pages with video backgrounds
- Blog content management
- LinkHub functionality 
- Enhanced hero sections with countdown timers
- Social proof with testimonials

### [todiane.com](https://www.todiane.com)
Personal website consuming the API:
- Pages and LinkHub APIs
- Custom branding and styling
- Portfolio features

### [API Backend](https://corrison.corrisonapi.com)
Django REST Framework API serving:
- All platform endpoints
- Authentication and user management
- Media and file handling

## 📚 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Live Examples](#live-examples)
5. [Getting Started](#getting-started)
6. [API Endpoints](#api-endpoints)
7. [Project Structure](#project-structure)
8. [Component Usage](#component-usage)
9. [Development](#development)
10. [Backend Features](#backend-features)
11. [Deployment](#deployment)
12. [Contributing](#contributing)
13. [License](#license)

---

## Overview

Corrison is designed to be fully headless and modular. You can:

* Use only the **store** endpoints to power a headless shop with Stripe integration
* Use the **blog** endpoints for a standalone CMS blog
* Use the **pages** endpoints for dynamic landing pages with advanced features
* Use **LinkHub** to create link-in-bio style pages with multi-media support
* Use **testimonials** for social proof across multiple pages
* Mix and match; your existing site can fetch from Corrison's API without rewriting templates

## 🏗️ Architecture Overview
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ E-commerce  │ │ CMS Frontend│ │ LinkHub     │           │
│  │ (Astro.js)  │ │ (Astro.js)  │ │ (Astro.js)  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                API Gateway Layer                            │
│         Passenger WSGI • CORS • JWT Auth                   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              API Layer (Django REST Framework)             │
│  Products • Cart • Blog • Pages • LinkHub • Testimonials  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                         │
│        Database (PostgreSQL) • Media Storage • Static Files│
└─────────────────────────────────────────────────────────────┘
// Get cart contents
const cart = await fetchCorrisonData('cart/');
```

---

### Backend Structure

frontend/
├── src/
│   ├── components/              # Reusable components
│   │   ├── EnhancedHero.astro      # Advanced hero for landing pages
│   │   ├── TestimonialGrid.astro   # Testimonial display component
│   │   ├── CountdownTimer.astro    # Countdown timer component
│   │   ├── Header.astro            # Site navigation
│   │   └── Footer.astro            # Site footer
│   ├── layouts/
│   │   └── BaseLayout.astro        # Main page layout
│   ├── pages/                   # Route pages
│   │   ├── index.astro             # Homepage (supports landing pages)
│   │   ├── blog/                   # Blog routes
│   │   │   ├── index.astro         # Blog listing
│   │   │   └── [slug].astro        # Individual blog posts
│   │   ├── linkhubs.astro          # LinkHub display
│   │   └── architecture.astro      # Platform documentation
│   ├── lib/
│   │   ├── api.ts                  # API integration functions
│   │   └── heroicons.ts            # Icon helper functions
│   ├── utils/                   # Utility functions
│   │   ├── blog.ts                 # Blog-related utilities
│   │   ├── images.ts               # Image optimization
│   │   ├── permalinks.ts           # URL generation
│   │   └── frontmatter.ts          # Content processing
│   ├── styles/
│   │   └── global.css              # Global styles and Tailwind
│   └── types.ts                 # TypeScript definitions
├── public/                      # Static assets
├── astro.config.mjs            # Astro configuration
└── package.json                # Dependencies and scripts
```

---
```
backend/
├── corrison/             # Main Django project
│   ├── settings/         # Environment-specific settings
│   ├── urls.py          # Main URL configuration
│   └── wsgi.py          # WSGI application
├── core/                # Core functionality
│   ├── models.py        # Base models and utilities
│   └── permissions.py   # Custom permissions
├── api/                 # API configuration
│   ├── urls.py          # API URL routing
│   └── views.py         # API viewsets and routers
├── products/            # E-commerce products
│   ├── models.py        # Product, Category, Variant models
│   ├── serializers.py   # DRF serializers
│   └── views.py         # Product viewsets
├── cart/                # Shopping cart
│   ├── models.py        # Cart and CartItem models
│   ├── serializers.py   # Cart serializers
│   └── views.py         # Cart management views
├── orders/              # Order processing
│   ├── models.py        # Order and OrderItem models
│   ├── serializers.py   # Order serializers
│   └── views.py         # Checkout and order views
├── blog/                # Blog functionality
│   ├── models.py        # BlogPost, Category models
│   ├── serializers.py   # Blog serializers
│   └── views.py         # Blog viewsets
├── pages/               # CMS pages
│   ├── models.py        # Page, PageFeature, Testimonial models
│   ├── serializers.py   # Page serializers
│   └── views.py         # Page viewsets
├── linkhub/             # LinkHub functionality
│   ├── models.py        # LinkHub and Link models
│   ├── serializers.py   # LinkHub serializers
│   └── views.py         # LinkHub viewsets
├── courses/             # Learning Management System
│   ├── models.py        # Course, Lesson, Enrollment models
│   ├── serializers.py   # Course serializers
│   └── views.py         # Course and enrollment viewsets
├── appointments/        # Calendar & Booking System
│   ├── models.py        # CalendarUser, Appointment, Availability models
│   ├── serializers.py   # Appointment serializers
│   └── views.py         # Calendar and booking viewsets
└── users/               # User management
    ├── models.py        # User profile models
    ├── serializers.py   # User serializers
    └── views.py         # Authentication views
```

### Frontend Structure

### Core Architecture Components

**Frontend (Astro.js)**
- Static site generation for optimal performance
- Tailwind CSS for styling
- TypeScript for type safety
- Responsive design for all devices
- API integration with the Django backend

**Backend (Django)**
- Django REST Framework API
- PostgreSQL database
- Comprehensive models for all features
- JWT authentication and session management
- Media handling and optimization
- RESTful API endpoints for content delivery

### Installed Apps

* **corrison.products**: Product models, variants, categories
* **corrison.cart**: Shopping cart logic with session persistence
* **corrison.orders**: Checkout and order management with Stripe
* **blog**: `BlogPost` models, serializers, viewsets
* **pages**: `Page` models for CMS-driven landing pages and testimonials
* **linkhub**: `LinkHubPage` & `Link` models for link-in-bio pages
* **courses**: Complete LMS with `Course`, `Lesson`, `Enrollment` models
* **appointments**: Calendar system with `CalendarUser`, `Appointment`, `Availability` models
* **api**: Central DRF router mounting all viewsets

---

## Key Features

### 🛒 **E-commerce Module**
- Product catalog with categories and variants
- Shopping cart with session persistence  
- Automatic cart merging for user login
- Secure checkout with Stripe integration
- Order management and processing
- User accounts for returning customers
- Real-time stock validation

### 📝 **Content Management System**
- Blog posts with featured images and YouTube embeds
- Dynamic pages with rich content
- File attachments and media management
- SEO-optimized meta fields
- Publishing controls and scheduling

### 🎯 **Advanced Landing Pages**
- **Video Backgrounds**: YouTube and custom video support
- **Countdown Timers**: Real-time countdown to launch dates
- **Prelaunch Badges**: "Coming Soon" and custom badges
- **Dual CTAs**: Primary and secondary call-to-action buttons
- **Social Proof**: Integrated testimonial sections
- **Scroll Indicators**: Animated scroll-down indicators

### 🌟 **Testimonial System**
- Global testimonial management
- Star ratings (1-5 scale)
- Category-based filtering
- Featured testimonial highlighting
- Multi-page testimonial relationships
- Customer photos and company details

### 🔗 **LinkHub (Link-in-Bio)**
- Multi-media link collections (videos, PDFs, audio, donations)
- Custom icons and descriptions
- Author attribution
- Background image support
- Category organization

### 🎓 **Learning Management System**
- Course creation and management with categories
- Video lessons with YouTube integration
- Student enrollment and progress tracking
- Instructor dashboards and analytics
- Course completion certificates
- Free and paid course support

### 📅 **Calendar & Booking System**
- Appointment scheduling and management
- Availability slot configuration
- Email notifications and reminders
- Payment integration for paid appointments
- Public booking pages for clients
- Recurring appointment patterns

### 🎨 **Enhanced Hero Sections**
- **Regular Pages**: Standard hero with image/content options
- **Landing Pages**: Advanced hero with video, countdown, dual CTAs
- **Content Flexibility**: Rich text content or custom right-side content
- **Image Options**: Upload or external URL support

### Main Platform (corrisonapi.com)
- **Landing Pages**: Advanced hero sections with video backgrounds
- **Blog System**: Full content management with categories
- **LinkHub**: Consolidated links with media support
- **Testimonials**: Social proof sections with star ratings
- **SEO Optimization**: Meta fields and structured data

### E-commerce Implementation
The platform includes full e-commerce capabilities:
- **Product Catalog**: Browsable products with filtering and search
- **Shopping Cart**: Add, update, remove items with session persistence
- **Checkout Process**: Multi-step checkout with shipping and payment
- **Stripe Integration**: Secure payment processing with webhooks
- **Order Management**: Order history and status tracking
- **User Accounts**: Optional accounts for returning customers

### Technical Features
- **Performance**: Static site generation with dynamic API calls
- **Security**: CSRF protection, XSS protection, secure cookies
- **Scalability**: Modular architecture allows selective feature usage
- **Developer Experience**: Comprehensive TypeScript definitions and API documentation

---

## 🔌 API Endpoints

### Store / E-commerce
```
GET    /api/v1/products/                 # List products with filtering
GET    /api/v1/products/{id}/            # Product detail with variants
POST   /api/v1/cart/                     # Add to cart
GET    /api/v1/cart/                     # View cart contents
PUT    /api/v1/cart/{item_id}/           # Update cart item
DELETE /api/v1/cart/{item_id}/           # Remove from cart
POST   /api/v1/orders/checkout/          # Place order with Stripe
GET    /api/v1/orders/                   # Order history (authenticated)
```

### Blog
```
GET    /api/v1/blog/posts/              # List published posts
GET    /api/v1/blog/posts/{slug}/       # Post detail with content
GET    /api/v1/blog/categories/         # List categories
GET    /api/v1/blog/posts/?category=X   # Filter posts by category
```

### Pages / CMS
```
GET    /api/v1/pages/                    # List all pages
GET    /api/v1/pages/{slug}/             # Get specific page with features
GET    /api/v1/pages/?type=landing       # Filter by page type
GET    /api/v1/pages/landing_pages/      # Get landing pages only
GET    /api/v1/pages/{slug}/testimonials/ # Get testimonials for page
```

### Testimonials
```
GET    /api/v1/testimonials/                    # List all testimonials
GET    /api/v1/testimonials/featured/           # Get featured testimonials
GET    /api/v1/testimonials/?category={cat}     # Filter by category
GET    /api/v1/testimonials/categories/         # Get available categories
```

### Courses API
```
GET    /api/v1/courses/                     # List all courses
GET    /api/v1/courses/{slug}/              # Course detail with lessons
POST   /api/v1/courses/{slug}/enroll/       # Enroll in course
GET    /api/v1/courses/my_courses/          # User's enrolled courses
GET    /api/v1/courses/{slug}/lessons/      # Course lessons
POST   /api/v1/courses/{slug}/lessons/{slug}/complete/ # Mark lesson complete
GET    /api/v1/enrollments/                 # User enrollment history
```

### Calendar API
```
GET    /api/v1/appointments/profiles/       # Calendar user profiles
GET    /api/v1/appointments/appointment-types/ # Available appointment types
GET    /api/v1/appointments/availability/   # Availability slots
POST   /api/v1/appointments/appointments/   # Create appointment
GET    /api/v1/appointments/public/{username}/ # Public calendar info
POST   /api/v1/appointments/public/book/    # Public booking endpoint
```

### LinkHub
```
GET    /api/v1/linkhubs/                # List all link hubs
GET    /api/v1/linkhubs/{slug}/         # Get specific link hub with links
```
- **API Versioning**: All endpoints prefixed with `/api/v1/`
- **Authentication**: JWT tokens for user sessions
- **CORS**: Configured for cross-origin requests
- **Rate Limiting**: API throttling for protection
- **Pagination**: Large datasets automatically paginated

---

## Technology Stack

**Frontend:**
- **Framework**: Astro.js (Static Site Generation)
- **Styling**: Tailwind CSS
- **Components**: Astro components with TypeScript
- **Performance**: Image optimization, lazy loading

**Backend:**
- **Framework**: Django + Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: JWT-based
- **Media**: Django file handling with WhiteNoise
- **Hosting**: Hetzner VPS with HestiaCP

**Infrastructure:**
- **Frontend Hosting**: Static deployment (Netlify, Vercel, etc.)
- **Backend Hosting**: Hetzner CPX21 VPS (Helsinki) with HestiaCP
- **Database**: PostgreSQL on VPS
- **CDN**: Frontend assets served via CDN
- **SSL**: Let's Encrypt certificates

## 💻 Getting Started

### Prerequisites
- Node.js (version 18.0.0 or higher)
- Python (version 3.9 or higher)
- PostgreSQL database
- npm or yarn package manager

### Backend Setup (Django)

1. **Clone and setup virtual environment:**
```bash
git clone https://github.com/djangify/corrison-backend.git
cd corrison-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
# Create .env file
cp .env.example .env
```

3. **Configure environment variables:**
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/corrison
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
CORS_ALLOWED_ORIGINS=http://localhost:4321,https://yourdomain.com
```

4. **Database setup:**
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (optional)
python manage.py loaddata initial_data
```

5. **Start development server:**
```bash
python manage.py runserver
# API available at http://localhost:8000/api/v1/
```

### Frontend Setup (Astro)

1. **Clone and install:**
```bash
git clone https://github.com/djangify/astro.git
cd astro
npm install
```

2. **Environment configuration:**
```bash
# Create .env file
cp .env.example .env
```

3. **Configure environment variables:**
```env
PUBLIC_API_BASE_URL=http://localhost:8000  # Development
# PUBLIC_API_BASE_URL=https://corrison.corrisonapi.com  # Production
PUBLIC_SITE_URL=http://localhost:4321
```

4. **Development server:**
```bash
npm run dev
# Available at http://localhost:4321
```

5. **Production build:**
```bash
npm run build
npm run preview
```

### Quick Start Integration

#### Fetching Data from API

```javascript
// Basic API integration
const API_BASE = "http://localhost:8000/api/v1/";

async function fetchCorrisonData(endpoint) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch ${endpoint}`);
  }
  
  return response.json();
}

// Example usage
const posts = await fetchCorrisonData('blog/posts/');
const products = await fetchCorrisonData('products/');
const page = await fetchCorrisonData('pages/homepage/');
```

#### Using the Shopping Cart

```javascript
// Add item to cart
async function addToCart(productId, quantity = 1) {
  const response = await fetch(`${API_BASE}cart/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      product_id: productId,
      quantity: quantity
    })
  });
  
  return response.json();
}

#### Working with Courses

```javascript
// Enroll in a course
async function enrollInCourse(courseSlug) {
  const response = await fetch(`${API_BASE}courses/${courseSlug}/enroll/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
}

// Get user's enrolled courses
const myCourses = await fetchCorrisonData('courses/my_courses/');

// Mark lesson as complete
async function completeLesson(courseSlug, lessonSlug) {
  const response = await fetch(`${API_BASE}courses/${courseSlug}/lessons/${lessonSlug}/complete/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
}
```

#### Working with Calendar/Appointments

```javascript
// Get available appointment slots
async function getAvailableSlots(username, appointmentTypeId, startDate) {
  const params = new URLSearchParams({
    appointment_type_id: appointmentTypeId,
    start_date: startDate
  });
  
  const response = await fetch(`${API_BASE}appointments/public/${username}/slots/?${params}`);
  return response.json();
}

// Book an appointment
async function bookAppointment(appointmentData) {
  const response = await fetch(`${API_BASE}appointments/public/book/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(appointmentData)
  });
  return response.json();
}
```

```
src/
├── components/              # Reusable components
│   ├── EnhancedHero.astro      # Advanced hero for landing pages
│   ├── TestimonialGrid.astro   # Testimonial display component
│   ├── CountdownTimer.astro    # Countdown timer component
│   ├── Header.astro            # Site navigation
│   └── Footer.astro            # Site footer
├── layouts/
│   └── BaseLayout.astro        # Main page layout
├── pages/                   # Route pages
│   ├── index.astro             # Homepage (supports landing pages)
│   ├── blog/                   # Blog routes
│   │   ├── index.astro         # Blog listing
│   │   └── [slug].astro        # Individual blog posts
│   ├── linkhubs.astro          # LinkHub display
│   └── architecture.astro      # Platform documentation
├── lib/
│   ├── api.ts                  # API integration functions
│   └── heroicons.ts            # Icon helper functions
├── utils/                   # Utility functions
│   ├── blog.ts                 # Blog-related utilities
│   ├── images.ts               # Image optimization
│   ├── permalinks.ts           # URL generation
│   └── frontmatter.ts          # Content processing
├── styles/
│   └── global.css              # Global styles and Tailwind
└── types.ts                 # TypeScript definitions
```

## Component Usage

### Enhanced Hero Section
```astro
---
import EnhancedHero from "../components/EnhancedHero.astro";
---

<EnhancedHero page={page} />
```

**Features:**
- Automatic video background detection
- Countdown timer integration
- Dual CTA button support
- Prelaunch badge display
- Scroll indicator animation

### Testimonial Grid
```astro
---
import TestimonialGrid from "../components/TestimonialGrid.astro";
---

<TestimonialGrid 
  testimonials={page.testimonials}
  title="What Our Customers Say"
  columns={3}
/>
```

### Countdown Timer
```astro
---
import CountdownTimer from "../components/CountdownTimer.astro";
---

<CountdownTimer 
  targetDate="2024-12-31T23:59:59"
  title="Launch Countdown"
  className="text-center"
/>
```

## API Integration Examples

### Fetching Landing Pages
```typescript
import { fetchLandingPages, fetchPagesByType } from "../lib/api";

// Get all landing pages
const landingPages = await fetchLandingPages();

// Get pages by type
const regularPages = await fetchPagesByType('page');
const landingPages = await fetchPagesByType('landing');
```

### Working with Testimonials
```typescript
import { 
  fetchTestimonials, 
  fetchFeaturedTestimonials,
  fetchPageTestimonials 
} from "../lib/api";

// Get all testimonials
const testimonials = await fetchTestimonials();

// Get featured testimonials only
const featured = await fetchFeaturedTestimonials();

// Get testimonials for specific page
const pageTestimonials = await fetchPageTestimonials('homepage');
```

### Blog Integration
```typescript
import { fetchPosts, fetchPost } from "../lib/api";

// Get all blog posts
const posts = await fetchPosts();

// Get specific blog post
const post = await fetchPost('my-blog-post-slug');
```

## Page Types

### Regular Pages
Standard content pages with:
- Basic hero section
- Rich text content
- Feature sections
- Image/content flexibility

### Landing Pages
Advanced marketing pages with:
- Video background support
- Countdown timers
- Prelaunch badges
- Dual CTA buttons
- Social proof sections
- Enhanced hero components

## Configuration

### Astro Configuration
```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  output: 'static',
  vite: {
    plugins: [tailwindcss()],
  },
});
```

### API Configuration
```typescript
// src/lib/api.ts
const API = "https://corrison.corrisonapi.com";

async function check<T>(res: Response, what: string): Promise<T> {
  if (!res.ok) throw new Error(`Failed to fetch ${what}`);
  return res.json();
}
```

## Deployment

### Static Deployment (Recommended)
1. **Build the project:**
```bash
npm run build
```

2. **Deploy `dist/` folder to:**
   - Netlify
   - Vercel  
   - AWS S3 + CloudFront
   - GitHub Pages
   - Any static hosting service

### Environment Variables for Production
```env
PUBLIC_API_BASE_URL=https://corrison.corrisonapi.com
PUBLIC_SITE_URL=https://your-production-domain.com
```

## Backend Features

The Django backend provides:

### 🛒 E-commerce Capabilities
- **Product Management**: Categories, variants, inventory tracking
- **Shopping Cart**: Session-based cart with user account merging
- **Order Processing**: Complete checkout flow with order management
- **Payment Integration**: Stripe payment processing with webhooks
- **User Accounts**: Customer registration and order history

### 📝 Content Management
- **Rich Text Editing**: WYSIWYG editors for all content fields
- **Media Management**: Image upload, optimization, and CDN integration
- **SEO Optimization**: Meta fields, structured data, sitemap generation
- **Publishing Controls**: Draft/published states with scheduling
- **Content Versioning**: Track changes and revisions

### 🎯 Landing Page Features
- **Page Types**: Clear distinction between regular pages and landing pages
- **Video Backgrounds**: YouTube and custom video URL support
- **Interactive Elements**: Countdown timers, scroll indicators
- **Social Proof**: Testimonial relationship management with star ratings
- **Advanced CTAs**: Dual call-to-action buttons with tracking

### 🎓 Learning Management Features
- **Course Creation**: Rich course content with categories and difficulty levels
- **Video Integration**: YouTube video embedding for lessons
- **Progress Tracking**: Student enrollment and lesson completion tracking
- **Instructor Tools**: Course management and student analytics
- **Flexible Pricing**: Support for both free and paid courses
- **Certificate Generation**: Course completion certificates (configurable)

### 📅 Calendar & Booking Features
- **Appointment Scheduling**: Public booking pages with time slot selection
- **Availability Management**: Flexible availability patterns and blocked times
- **Email Notifications**: Automatic confirmations, reminders, and updates
- **Payment Integration**: Optional payment for appointment types
- **Multi-timezone Support**: Proper timezone handling for global users
- **Recurring Appointments**: Support for recurring appointment patterns

### 🔌 API Features
- **RESTful Design**: Consistent endpoint structure and responses
- **JWT Authentication**: Secure token-based authentication
- **CORS Configuration**: Cross-origin request handling
- **Pagination**: Automatic pagination for large datasets
- **Filtering & Search**: Query parameters for content filtering
- **Rate Limiting**: API throttling for security and performance

### 🔐 Security & Performance
- **Data Protection**: CSRF protection, XSS prevention, input validation
- **Secure Payments**: PCI-compliant Stripe integration
- **Optimized Queries**: Efficient database queries with select_related/prefetch_related
- **Caching**: Redis caching for frequently accessed data
- **Static Files**: WhiteNoise for efficient static file serving

---

## Development

### Adding New Components
1. Create component in `src/components/`
2. Import and use in pages
3. Add TypeScript definitions in `src/types.ts`
4. Update API functions in `src/lib/api.ts` if needed

### Styling Guidelines
- Use Tailwind CSS utility classes
- Global styles in `src/styles/global.css`
- Component-specific styles in Astro components
- Responsive design with mobile-first approach

### Performance Optimization
- Images automatically optimized via Astro
- Lazy loading implemented
- Static generation for fast loading
- CDN-friendly asset structure

## Troubleshooting

### Common Issues

**Build Failures:**
```bash
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**API Connection Issues:**
- Verify `PUBLIC_API_BASE_URL` in environment
- Check CORS settings on backend
- Confirm API endpoint URLs

**Component Not Rendering:**
- Check TypeScript types match API response
- Verify component props are correctly passed
- Check browser console for errors

### Windows Development
If switching from WSL to Windows:
1. Reinstall Node.js for Windows
2. Clear npm cache: `npm cache clean --force`
3. Delete and reinstall node_modules
4. Update file paths in any scripts

## API Response Examples

### Page Response (Landing Page)
```json
{
  "id": 1,
  "slug": "homepage",
  "title": "Welcome to Corrison",
  "page_type": "landing",
  "hero_title": "Transform Your Business",
  "hero_subtitle": "The complete headless platform",
  "hero_video_url": "https://youtube.com/watch?v=example",
  "show_countdown": true,
  "countdown_target_date": "2024-12-31T23:59:59Z",
  "show_social_proof": true,
  "testimonials": [...],
  "features": [...],
  "hero_button_text": "Get Started",
  "hero_button_url": "/signup",
  "hero_button_2_text": "Learn More",
  "hero_button_2_url": "/about"
}
```

### Product Response
```json
{
  "id": 1,
  "name": "Premium T-Shirt",
  "slug": "premium-t-shirt",
  "description": "High-quality cotton t-shirt",
  "price": "29.99",
  "category": {
    "id": 1,
    "name": "Clothing",
    "slug": "clothing"
  },
  "variants": [
    {
      "id": 1,
      "size": "M",
      "color": "Blue", 
      "stock": 10,
      "price": "29.99"
    }
  ],
  "images": [...]
}
```

### Cart Response
```json
{
  "id": "cart_123",
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Premium T-Shirt",
        "price": "29.99"
      },
      "variant": {
        "size": "M",
        "color": "Blue"
      },
      "quantity": 2,
      "subtotal": "59.98"
    }
  ],
  "total": "59.98",
  "item_count": 2
}
```

### Testimonial Response
```json
{
  "id": 1,
  "name": "John Doe",
  "title": "CEO",
  "company": "Example Corp",
  "content": "Corrison transformed our business...",
  "rating": 5,
  "category": "business",
  "image": "/media/testimonials/john.jpg"
}
```

### Testimonial Response
```json
{
  "id": 1,
  "name": "John Doe",
  "title": "CEO",
  "company": "Example Corp",
  "content": "Corrison transformed our business...",
  "rating": 5,
  "category": "business",
  "image": "/media/testimonials/john.jpg"
}
```

### Course Response
```json
{
  "id": 1,
  "name": "Introduction to Django",
  "slug": "intro-to-django",
  "instructor": {
    "username": "teacher",
    "full_name": "John Teacher"
  },
  "category": {
    "name": "Web Development",
    "slug": "web-development"
  },
  "difficulty": "beginner",
  "price": null,
  "is_free": true,
  "lesson_count": 10,
  "estimated_duration": "4 weeks",
  "is_enrolled": false,
  "progress_percentage": 0
}
```

### Appointment Response
```json
{
  "id": 1,
  "appointment_type": {
    "name": "Consultation",
    "duration_minutes": 60,
    "price": "50.00"
  },
  "customer_name": "Jane Doe",
  "customer_email": "jane@example.com",
  "date": "2024-01-15",
  "start_time": "14:00:00",
  "end_time": "15:00:00",
  "status": "confirmed",
  "payment_status": "paid"
}
```

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature-name`
3. **Follow existing patterns**: Use established code patterns and TypeScript definitions
4. **Test thoroughly**: Test with both regular and landing page types, verify API integrations
5. **Document changes**: Update README and API documentation as needed
6. **Submit pull request**: Provide clear description of changes and testing performed

### Development Guidelines

**Backend (Django):**
- Follow Django best practices and PEP 8
- Write comprehensive tests for all API endpoints
- Use proper serializers and viewsets
- Implement proper error handling and validation

**Frontend (Astro):**
- Use TypeScript for all new components
- Follow Tailwind CSS utility-first approach
- Ensure responsive design for all screen sizes
- Test API integrations thoroughly

**Database:**
- Use PostgreSQL best practices for queries
- Implement proper indexing for performance
- Use migrations for all schema changes
- Backup database before major changes

### Code Quality Standards
- **Testing**: Minimum 80% code coverage
- **Documentation**: All public APIs must be documented
- **Performance**: Page load times under 2 seconds
- **Security**: Regular security audits and updates
- **Accessibility**: WCAG 2.1 AA compliance

---

## Scripts Reference

```bash
npm run dev      # Start development server
npm run build    # Build for production  
npm run preview  # Preview production build
npm run astro    # Run Astro CLI commands
```

## Support & Documentation

- **Frontend Issues**: Open issue in this repository
- **Backend API**: Contact Corrison API team
- **Architecture**: See `/architecture` page
- **Live Examples**: Visit corrisonapi.com and todiane.com

## 📄 License

MIT License © Diane Corriette

**Developer**: Diane Corriette  
**Company**: Djangify  
**Website**: [djangify.com](https://www.djangify.com)  
**GitHub**: [github.com/djangify](https://github.com/djangify)

---

**Developer**: Diane Corriette  
**Website**: [djangify.com](https://www.djangify.com)  
**GitHub**: [github.com/djangify](https://github.com/djangify)

## Quick Start Checklist

- [ ] **Node.js 18+** and **Python 3.9+** installed
- [ ] **PostgreSQL** database setup and running
- [ ] **Repository cloned** and dependencies installed (both backend and frontend)
- [ ] **Environment variables** configured for both Django and Astro
- [ ] **Database migrated** and superuser created
- [ ] **Development servers running** (Django on :8000, Astro on :4321)
- [ ] **API connection tested** between frontend and backend
- [ ] **Stripe keys configured** for e-commerce functionality (if using)
- [ ] **Production deployment** planned and tested
- [ ] **Domain and SSL** configured for production

## 🆕 Recent Platform Updates

### Enhanced E-commerce Features
- **Advanced Shopping Cart**: Session-based cart with user account merging
- **Stripe Integration**: Complete payment processing with webhooks
- **Order Management**: Full order lifecycle from cart to fulfillment
- **Product Variants**: Size, color, and custom variant support
- **Inventory Tracking**: Real-time stock validation and management

### Complete Learning Management System
- **Course Creation**: Full course authoring with categories and difficulty levels
- **Video Lessons**: YouTube integration with progress tracking
- **Student Enrollment**: Free and paid course enrollment with Stripe
- **Progress Analytics**: Detailed progress tracking and completion certificates
- **Instructor Dashboard**: Course management and student analytics

### Professional Calendar System
- **Appointment Booking**: Public booking pages with real-time availability
- **Payment Integration**: Optional payment collection for appointment types
- **Email Automation**: Automatic confirmations, reminders, and notifications
- **Multi-timezone Support**: Global availability management
- **Recurring Patterns**: Support for recurring appointments and availability

### Landing Page Enhancements
- **Video Backgrounds**: Full YouTube and custom video support with overlay controls
- **Countdown Timers**: Real-time countdown with customizable styling and target dates
- **Advanced Hero Sections**: Multiple CTA buttons, prelaunch badges, scroll indicators
- **Social Proof Integration**: Testimonial system with star ratings and category filtering
- **Page Type System**: Clear distinction between regular pages and conversion-focused landing pages

### Developer Experience Improvements
- **Comprehensive TypeScript**: Full type definitions for all API responses and components
- **Modular Architecture**: Clean separation of concerns for maintainability
- **Performance Optimization**: Image optimization, lazy loading, and static generation
- **Documentation**: Complete API documentation with response examples
- **Testing**: Comprehensive test coverage for critical functionality

### Infrastructure & Security
- **VPS Deployment**: Complete Hetzner VPS setup with HestiaCP
- **PostgreSQL**: Production-ready database configuration
- **Security Hardening**: CSRF protection, XSS prevention, secure authentication
- **Performance Monitoring**: Database query optimization and caching strategies
- **CI/CD Pipeline**: Automated deployment with GitHub Actions