---

```markdown
# 🛍️ ALX Project Nexus -  E-Commerce Backend

A **modular monolithic Django backend** built with clean architecture, high cohesion, and low coupling — providing a scalable foundation for real-world e-commerce systems.

This project follows **ALX Backend Engineering** best practices for production-grade API design, DevOps integration, and automated testing.

---

## 🚀 Overview

**ALX Project Nexus** is a backend platform for managing users, products, carts, orders, and payments, designed with maintainability and extensibility in mind.  
It demonstrates **modular monolithic architecture**, where each domain (accounts, catalog, orders, payments, notifications, etc.) lives in its own Django app with clearly defined boundaries.

Key Features:
- RESTful APIs built with **Django REST Framework**
- **GraphQL** endpoint for rich product browsing
- **JWT Authentication** with Djoser
- **Celery + RabbitMQ** for background tasks (emails, async notifications)
- **Redis** caching for performance optimization
- **PostgreSQL** database with clean schema
- **Pytest** for automated testing
- **Docker** containerization
- **GitHub Actions CI/CD**
- API documentation with **Swagger / OpenAPI**

---

## 🧱 Architecture

**Type:** Modular Monolith  
**Principles:** High Cohesion, Low Coupling  
**Structure:**

```

`alx_project_nexus`/
├── core/                          # Common utilities, base models, shared mixins
├── accounts/                      # Auth, profiles (Djoser + JWT)
├── catalog/                       # Categories, products, reviews, carts
├── orders/                        # Orders and order items
├── payments/                      # Payment handling, Chapa/Stripe gateway integration
├── notifications/                 # Email + in-app notifications (Celery workers)
├── graphql_api/                   # GraphQL schema for product browsing
└── `alx_project_nexus`/           # Project settings, URLs, ASGI/Wsgi, Celery config

````

- Each module manages its own models, serializers, services, and tests.
- Shared logic (e.g., BaseModel, timestamp mixins, signals) lives in `core/`.

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-------------|
| **Framework** | Django 5 + Django REST Framework |
| **GraphQL** | Graphene-Django / Ariadne |
| **Database** | PostgreSQL |
| **Cache** | Redis |
| **Message Broker** | RabbitMQ |
| **Task Queue** | Celery |
| **Auth** | JWT (SimpleJWT + Djoser) |
| **Tests** | Pytest + DRF Test Client |
| **Docs** | Swagger (drf-spectacular) |
| **CI/CD** | GitHub Actions |
| **Containerization** | Docker + Docker Compose |

---

## 🧩 Modular Apps and Responsibilities

| App | Responsibility |
|-----|----------------|
| **core** | Shared base models, utilities, health checks |
| **accounts** | User registration, authentication, profiles |
| **catalog** | Product, category, review, and cart management |
| **orders** | Order creation, tracking, and management |
| **payments** | Payment gateway integration (Chapa, Stripe) |
| **notifications** | Email + in-app notifications (Celery) |
| **graphql_api** | Product search and browsing via GraphQL |

---

## 🗺️ API Documentation

- **Swagger UI:** [`/api/docs/`](http://localhost:8000/api/docs/)
- **OpenAPI Schema:** `/api/schema/`
- **GraphQL Playground:** `/graphql/`

### Authentication
JWT Authentication (via Djoser)
```bash
POST /api/auth/jwt/create/
POST /api/auth/jwt/refresh/
GET /api/auth/users/me/
````

---

## 📦 Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/yetmgetaredahegn/alx-project-nexus.git
cd alx-project-nexus
```

### 2. Environment Variables

Create `.env` file in the root:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://postgres:password@db:5432/nexus
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Build and Run with Docker

```bash
docker-compose up --build
```

Services included:

* `web` → Django app
* `db` → PostgreSQL
* `redis` → caching
* `rabbitmq` → message broker
* `celery_worker` → background task processor

### 4. Apply Migrations

```bash
docker exec -it web python manage.py migrate
```

### 5. Create Superuser

```bash
docker exec -it web python manage.py createsuperuser
```

### 6. Run Tests

```bash
pytest
```

---

## 🧠 Key Features by Domain

### Accounts

* User registration with email verification (Celery + RabbitMQ)
* JWT-based login/logout
* Profile management

### Catalog

* Product CRUD with image upload
* Nested reviews (per product)
* Redis-cached product listing
* Category hierarchy

### Cart

* Session or user-based cart
* Item quantity updates and merging
* Live stock validation

### Orders

* Transactional order creation from cart
* Order tracking and cancellation
* Admin control for status updates

### Payments

* Chapa integration
* Secure webhook handling
* Idempotent payment updates

### Notifications

* Celery background emails
* Read/unread tracking
* Optional WebSocket real-time updates

---

## 🔄 Background Tasks

| Task                         | Trigger           | Worker Queue |
| ---------------------------- | ----------------- | ------------ |
| Send welcome email           | User registration | `emails`     |
| Order confirmation           | Order placed      | `emails`     |
| Payment success notification | Webhook verified  | `emails`     |
| Cache invalidation           | Product updated   | `default`    |

**Celery Config:**

```python
CELERY_BROKER_URL = "amqp://guest:guest@rabbitmq:5672//"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"
```

---

## 🧪 Testing Strategy

* **Unit Tests:** models, serializers, utils (pytest)
* **Integration Tests:** API endpoints via DRF `APIClient`
* **E2E:** simulate checkout flow (cart → order → payment)
* **CI:** automated in GitHub Actions (run tests + lint + build Docker image)

---

## 🧰 Developer Notes

### Modular Monolith Guidelines

* Each app should **own its models and serializers**.
* Cross-app imports allowed **only through `core` services or signals**.
* Maintain **high cohesion** within apps, **low coupling** between them.
* Shared base class: `core.models.BaseModel` → includes UUID PKs, timestamps.

### Commands

```bash
python manage.py runserver
python manage.py shell
celery -A config worker -l info
celery -A config beat -l info
```

---

## 🧭 Project Roadmap

1. ✅ Define ERD and modular boundaries
2. ✅ Define API endpoints (REST + GraphQL)
3. 🚧 Implement models & serializers per app
4. 🚧 Add Celery + Redis integration
5. 🚧 Implement tests (pytest)
6. 🚧 Deploy with Docker + GitHub Actions

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch

   ```bash
   git checkout -b feature/new-module
   ```
3. Commit your changes

   ```bash
   git commit -m "Add product caching feature"
   ```
4. Push and create a Pull Request

---

## 🧑‍💻 Author

**Yetmgeta Redahegn Kassaye**
Software Engineering Student @ Adama Science and Technology University
Focused on  Backend Engineering

> *"Building scalable systems, one module at a time."*

---

