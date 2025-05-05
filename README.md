# Corrison Headless E‑Commerce API

A standalone, API‑only e‑commerce backend built with Django and Django REST Framework, designed to power multiple front‑ends (e.g., Astro, Next.js, Vue).

---

## Features

* **API‑First**: All commerce functionality (products, carts, orders, users) exposed via JSON under `/api/v1/`
* **Token Authentication**: JWT‑based auth for secure access, with public catalog browsing
* **Media & Static**: Serve product images and uploaded media via Django’s `static/` and `media/`
* **Versioned Routes**: Ready for future `/api/v2/` without breaking existing clients
* **Auto‑Docs**: Swagger/OpenAPI docs generated for fast front‑end onboarding
* **CORS Support**: Whitelist storefront domains (e.g., `juicecleanseme.com`, `inspirationalguidance.com`)
* **CI/CD Ready**: Linted, tested, and deployable via GitHub Actions and cPanel

---

## Quickstart

### 1. Clone & Install

```bash
git clone https://github.com/djangify/corrison.git
cd corrison
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment

Copy `.env.example` to `.env` and update:

```ini
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,corrison.djangify.com,
DATABASE_URL=postgres://user:pass@localhost:5432/corrison
```

### 3. Database Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Run Server (Local)

```bash
python manage.py runserver
```

Access Swagger docs at `http://localhost:8000/api/v1/docs/`.

---

## Project Structure

```
corrison/             # Django project root
├── api/               # API app (serializers, viewsets, routers)
├── accounts/          # Authentication and user registration
├── core/              # Core models and utilities
├── corrison/          # Project settings and URL config
├── static/            # Static files (CSS, JS, images)
├── media/             # Uploaded user content
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## API Overview

All endpoints are under `/api/v1/` and follow REST conventions.

| Resource | URL                 | Methods   | Auth           |
| -------- | ------------------- | --------- | -------------- |
| Products | `/api/v1/products/` | GET, POST | Public/Private |
| Carts    | `/api/v1/carts/`    | GET, POST | Authenticated  |
| Orders   | `/api/v1/orders/`   | GET, POST | Authenticated  |
| Users    | `/api/v1/users/`    | GET, POST | Authenticated  |

---

## CORS & Security

* Configure allowed origins in `settings.py` with `django-cors-headers`.
* JWT token expiration and refresh strategy handled by Simple JWT.

---

## Deployment

* Hosted on cPanel via `corrison.djangify.com`
* SSL & env vars via cPanel dashboard.
* CI via GitHub Actions: lint, test, build migrations.

---

## Next Steps

* Flesh out serializers and viewsets in `api/`
* Generate detailed OpenAPI spec and review
* Integrate front‑end storefronts against this API

---

For detailed setup, see [API Backend Setup](./docs/api_setup.md).
