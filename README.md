# Corrison Headless E-commerce & CMS Backend

A modular, API-first e-commerce and CMS backend built with Django and Django REST Framework. Choose any combination of:

* **Products & Store**: Full e-commerce functionality (products, carts, orders).
* **Blog**: Manage and expose blog posts and categories.
* **Pages**: CMS-powered landing pages.
* **LinkHub**: Structured "link-in-bio" pages.

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Installed Apps](#installed-apps)
4. [API Endpoints](#api-endpoints)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Deployment](#deployment)
8. [Contributing](#contributing)
9. [License](#license)

---

## Overview

Corrison is designed to be fully headless and modular. You can:

* Use only the **store** endpoints to power a headless shop.
* Use the **blog** endpoints for a standalone CMS blog.
* Use the **pages** endpoints for dynamic landing pages.
* Use **LinkHub** to create link-in-bio style pages.
* Mix and match; your existing Django site can fetch from Corrison’s API without rewriting all your templates.

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

---

## Usage Examples

### Fetching Blog Posts

In a front-end (e.g., Astro or Vite):

```js
const res = await fetch(`${API_URL}/blog/posts/`);
const posts = await res.json();
```

### Rendering a LinkHub Page

```js
const res = await fetch(`${API_URL}/linkhub/my-links/`);
const page = await res.json();
// page.links -> array of { title, url, icon_url }
```

---

## Deployment

We recommend using GitHub Actions for CI:

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

---

## Contributing

1. Fork the repo.
2. Create a feature branch.
3. Open a pull request.
4. Ensure tests pass.

---

## License

MIT © Diane Corriette
@Djangify
https://www.djangify.com 
