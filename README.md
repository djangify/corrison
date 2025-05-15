# Corrison Headless E-commerce & CMS Backend

[![Astro](https://img.shields.io/badge/Astro-FF5D01?style=for-the-badge&logo=astro&logoColor=white)](https://astro.build/)
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![MariaDB](https://img.shields.io/badge/MariaDB-003545?style=for-the-badge&logo=mariadb&logoColor=white)](https://mariadb.org/)

A modular, API-first e-commerce and CMS backend built with Django and Django REST Framework, powering multiple websites with a shared API infrastructure. Choose any combination of:

* **Products & Store**: Full e-commerce functionality (products, carts, orders).
* **Blog**: Manage and expose blog posts and categories.
* **Pages**: CMS-powered landing pages.
* **LinkHub**: Structured "link-in-bio" pages. Add media including audio, video and PDF.
* **COMING SOON**: Events API and Calender API.

## 🌐 Live Sites

### [todiane.com](https://www.todiane.com)
The main website featuring:
- Blog content management
- LinkHub functionality (similar to Linktree)
- Content pages
- Personal portfolio features

### [ecommerce.todiane.com](https://djangifyecommerce.up.railway.app/)
A fully-featured e-commerce store with:
- Product catalog with categories
- Product variants (size, color, etc.)
- Shopping cart functionality
- Checkout process with Stripe integration
- Order management

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Getting Started](#getting-started)
5. [API Endpoints](#api-endpoints)
6. [Project Structure](#project-structure)
7. [Development](#development)
8. [Features in Detail](#features-in-detail)
9. [Deployment](#deployment)
10. [Contributing](#contributing)
11. [License](#license)

---

## Overview

Corrison is designed to be fully headless and modular. You can:

* Use only the **store** endpoints to power a headless shop.
* Use the **blog** endpoints for a standalone CMS blog.
* Use the **pages** endpoints for dynamic landing pages.
* Use **LinkHub** to create link-in-bio style pages.
* Mix and match; your existing Django site can fetch from Corrison's API without rewriting all your templates.

## 🏗️ Architecture

### Backend (Django)
- Django REST Framework API
- MariaDB database
- Comprehensive models for:
  - Products, categories, and variants
  - User profiles and authentication
  - Blog articles and media content
  - E-commerce orders and payments
  - LinkHub links and categories

### Frontend (Astro.js)
- Static site generation for optimal performance
- Tailwind CSS for styling
- TypeScript for type safety
- Responsive design for all devices
- API integration with the Django backend

## 📚 Key Features

### Core API Features
- RESTful API endpoints for content delivery
- JWT authentication
- Session management for e-commerce
- Media handling and optimisation
- Structured content delivery

### Main Site (todiane.com)
- Blog system with categories and tags
- LinkHub system for consolidated links
- Content pages with rich media support
- Contact form functionality
- SEO optimization

### E-commerce Site (ecommerce.todiane.com)
- Full product catalog with filtering and search
- Category navigation
- Product detail pages with variant selection
- Shopping cart with session persistence
- Secure checkout with Stripe integration
- Order confirmation and history
- Mobile-responsive shopping experience

---

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/your-org/corrison-backend.git
   cd corrison-backend
   ```
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Configure environment variables in `.env`:

   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://user:pass@localhost:5432/corrison
   ```
4. Run migrations and create a superuser:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
5. Start the development server:

   ```bash
   python manage.py runserver
   ```

---

## Installed Apps

* **corrison.products**: Product models, variants, categories.
* **corrison.cart**: Shopping cart logic.
* **corrison.orders**: Checkout and order management.
* **blog**: `BlogPost` models, serializers, viewsets.
* **pages**: `Page` models for CMS-driven landing pages.
* **linkhub**: `LinkHubPage` & `Link` models for link-in-bio pages.
* **api**: Central DRF router mounting all viewsets.

---

## API Endpoints

### Store

* `GET /api/v1/products/` — list products
* `GET /api/v1/products/{id}/` — product detail
* `POST /api/v1/cart/` — add to cart
* `GET /api/v1/cart/` — view cart
* `POST /api/v1/orders/checkout/` — place order

### Blog

* `GET /api/v1/blog/posts/` — list published posts
* `GET /api/v1/blog/posts/{slug}/` — post detail
* `GET /api/v1/blog/categories/` — list categories

### Pages

* `GET /api/v1/pages/` — list published pages
* `GET /api/v1/pages/{slug}/` — page detail

### LinkHub

* `GET /api/v1/linkhub/` — list link pages
* `GET /api/v1/linkhub/{slug}/` — link page detail

---

## Configuration

* **API Versioning**: All endpoints are prefixed with `/api/v1/`.
* **Authentication**: Token-based (JWT or OAuth2).
* **CORS**: Configure in `settings.py` under `CORS_ALLOWED_ORIGINS`.
* **Media & Static**: Served via Django or external storage; URLs exposed in API.

## 🔧 Project Structure

```
├── backend/              # Django backend
│   ├── core/             # Core functionality
│   ├── users/            # User authentication and profiles
│   ├── blog/             # Blog API
│   ├── linkhub/          # LinkHub API
│   ├── products/         # E-commerce products
│   ├── cart/             # Shopping cart functionality
│   └── orders/           # Order processing
│
├── todiane-site/         # Main website frontend
│   ├── src/              # Source code
│   │   ├── components/   # Shared components
│   │   ├── layouts/      # Page layouts
│   │   ├── pages/        # Main pages
│   │   └── lib/          # Utilities and API clients
│   └── public/           # Static assets
│
└── ecommerce-site/       # E-commerce website frontend
    ├── src/              # Source code
    │   ├── components/   # E-commerce components
    │   ├── layouts/      # Page layouts
    │   ├── pages/        # Store pages
    │   ├── api/          # API route handlers 
    │   └── lib/          # Utilities and API clients
    └── public/           # Static assets
```

## 💻 Development

### Prerequisites
- Node.js (v18+)
- Python (v3.9+)
- Database MariaDB or PostgreSQL

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/todiane-platform.git
cd todiane-platform/backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your database credentials

# Apply migrations
python manage.py migrate

# Load initial data
python manage.py loaddata initial_data

# Run development server
python manage.py runserver
```

### Frontend Setup
```bash
# For main site
cd ../todiane-site
npm install
npm run dev
.env PUBLIC_API_BASE_URL=http://localhost:8000 (amend with domain in production)

# For e-commerce site
cd ../ecommerce-site
npm install
npm run dev
```

## 🌟 Features in Detail

### E-commerce Functionality
The e-commerce site includes:
- **Product Catalog**: Browsable products with filtering
- **Shopping Cart**: Add, update, remove items
- **Checkout Process**: Multi-step checkout with shipping and payment
- **Stripe Integration**: Secure payment processing
- **Order Management**: Order history and status tracking
- **User Accounts**: Optional accounts for returning customers

### Cart System Implementation
- Session-based cart for guest users
- User-linked cart for logged-in users
- Automatic cart merging when a user logs in
- Local storage fallback for offline functionality
- Real-time stock validation

### Usage Examples

#### Fetching Blog Posts

In a front-end (e.g., Astro or Vite):

```js
const res = await fetch(`${API_URL}/blog/posts/`);
const posts = await res.json();
```

#### Rendering a LinkHub Page

```js
const res = await fetch(`${API_URL}/linkhub/my-links/`);
const page = await res.json();
// page.links -> array of { title, url, icon_url }
```

## 🚀 Deployment

You can use GitHub Actions for CI:

```yaml
name: Django CI/CD
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install
        run: pip install -r requirements.txt
      - name: Run migrations
        run: python manage.py migrate
      - name: Run tests
        run: pytest
      - name: Deploy to cPanel
        # your deployment steps here
```

The platform uses a serverless architecture:
- Django backend deployed as serverless functions
- Astro.js frontends deployed as static sites
- MariaDB, MySQL database on cpanel hosting 


## 🔐 Security Considerations
- CSRF protection for forms
- XSS protection
- Secure cookie handling
- HTTPS enforcement
- Stripe Elements for PCI-compliant payment handling
- Input validation and sanitization

## 👥 Contributing

1. Fork the repo.
2. Create a feature branch.
3. Open a pull request.
4. Ensure tests pass.

## 📝 License

MIT © Diane Corriette
@Djangify
https://www.djangify.com