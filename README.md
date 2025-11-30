# 🛍️ **ALX Project Nexus – Modular E-Commerce Backend**

*A production-ready, scalable backend built using Django, DRF, Celery, Redis, PostgreSQL, and clean architecture.*

---

## 🚀 **Project Overview**

**ALX Project Nexus** is a modular monolithic **E-Commerce Backend Platform** designed for real-world scalability, clean domain separation, and production-ready deployment.

It implements:

* **REST APIs** using Django REST Framework
* **JWT Authentication** with Djoser + SimpleJWT
* **Celery background tasks** (emails, notifications)
* **Redis as broker/backing** (production-ready for Railway)
* **PostgreSQL database** using Neon
* **Modular architecture** (each domain isolated)
* **Render deployment** for API
* **Railway deployment** for Celery worker
* **Automated testing** with Pytest
* **Docker-based local dev environment**

This backend demonstrates real engineering concepts: async workflows, caching, modular boundaries, and cloud deployment.

---

## 🧱 **Architecture Summary**

### **Architecture Type:**

🔹 *Modular Monolith*: each business domain is its own Django app

🔹 *High Cohesion + Low Coupling*

🔹 *Shared Core Layer* for common utilities

```
alx_project_nexus/
│
├── core/               # Common utilities, base models, mixins
├── accounts/           # Authentication, profiles, JWT via Djoser
├── catalog/            # Categories, products, reviews
├── cart/               # Shopping cart management
├── orders/             # Orders, order items, order status updates
├── payments/           # Payment verification (e.g., Chapa integration)
├── notifications/      # Email + async notification tasks (Celery)
└── alx_project_nexus/  # Settings, URLs, Celery config
```

---

## ⚙️ **Tech Stack**

| Layer                 | Technology                             |
| --------------------- | -------------------------------------- |
| **Backend Framework** | Django 5                               |
| **API Layer**         | Django REST Framework                  |
| **Database**          | PostgreSQL (Neon)                      |
| **Cache / Broker**    | Redis                                  |
| **Task Queue**        | Celery 5                               |
| **Auth**              | JWT (SimpleJWT) + Djoser               |
| **Testing**           | Pytest                                 |
| **CI/CD**             | GitHub Actions                         |
| **Deployment**        | Render (API) + Railway (Celery Worker) |
| **Containerization**  | Docker + Docker Compose                |

---

## 🔌 **REST API Endpoints Overview**

### **Authentication (JWT – via Djoser)**

```
POST /api/auth/jwt/create/
POST /api/auth/jwt/refresh/
GET /api/auth/users/me/
```

### **Catalog**

```
GET /api/catalog/categories/
POST /api/catalog/categories/
GET /api/catalog/products/
POST /api/catalog/products/
GET /api/catalog/products/{id}/reviews/
POST /api/catalog/products/{id}/reviews/
```

### **Cart**

```
GET /api/cart/cart/
POST /api/cart/cart/items/
PATCH /api/cart/cart/items/<id>/
DELETE /api/cart/cart/items/<id>/
DELETE /api/cart/cart/clear/
```

### **Orders**

```
POST /api/orders/
GET /api/orders/
GET /api/orders/<id>/
```

### **Payments**

```
POST /api/payments/initiate/
POST /api/payments/webhook/
GET /api/payments/
GET /api/payments/<id>/
```

### **Notifications**

Triggered by events (asynchronous via Celery worker)

### **API Documentation**

- **Swagger UI:** [`/api/docs/`](http://localhost:8000/api/docs/)
- **OpenAPI Schema:** `/api/schema/`
- **ReDoc:** `/api/redoc/`

---

## 🔄 **Background Tasks (Celery)**

| Task                     | Trigger          | Worker        |
| ------------------------ | ---------------- | ------------- |
| Welcome email            | User registers   | Celery Worker |
| Order confirmation email | Order placed     | Celery Worker |
| Payment confirmation     | Payment verified | Celery Worker |
| Notification dispatch    | Various events   | Celery Worker |

### **Celery Config (Production – Railway Worker)**

```python
CELERY_BROKER_URL = os.getenv("REDIS_URL")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL")
```

### **Deployment Setup**

* Render runs **Django API**
* Railway runs **Celery Worker**
* Both share:
  * Same Neon PostgreSQL DB
  * Same Redis URL

This enables **true asynchronous background tasks** in production.

---

## 🧱 **Data Model (ERD Summary)**

### **Accounts**

* User
* Profile

### **Catalog**

* Category
* Product
* Review

### **Cart**

* Cart
* CartItem

### **Orders**

* Order
* OrderItem
* OrderCancellationRequest

### **Payments**

* Payment
* TransactionLog

### **Notifications**

* Notification
* EmailNotificationTask

---

## 🏗️ **Installation & Setup**

### 1. Clone

```bash
git clone https://github.com/yetmgetaredahegn/alx-project-nexus.git
cd alx-project-nexus
```

### 2. Create `.env`

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=<postgres url>
REDIS_URL=<redis url>
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
ALLOWED_HOSTS=*
```

### 3. Run with Docker

```bash
docker-compose up --build
```

Services included:

* `web` → Django app
* `db` → PostgreSQL
* `redis` → caching and Celery broker
* `celery_worker` → background task processor
* `celery_beat` → periodic task scheduler

### 4. Migrate

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

## 🧪 **Testing Strategy**

* **Unit Tests**
  * models
  * serializers
  * utils

* **Integration Tests**
  * auth flow
  * product listing
  * order creation

* **End-to-End Tests**
  * cart → order flow
  * payment → webhook → confirmation email

* **CI/CD**
  * automated tests
  * docker build
  * quality checks

---

## ☁️ **Deployment Summary (Production)**

### **Render**

* Django REST API
* Gunicorn server
* Auto-deploy on push

### **Railway (Worker)**

* Celery worker consuming Redis queues
* Handles notifications, payments, emails

### **Neon PostgreSQL**

* Shared database for both services

### **Redis**

* Shared broker for Celery + cache backend

---

## 🧩 **Modular Apps and Responsibilities**

| App | Responsibility |
|-----|----------------|
| **core** | Shared base models, utilities, health checks |
| **accounts** | User registration, authentication, profiles |
| **catalog** | Product, category, review management |
| **cart** | Shopping cart and cart items |
| **orders** | Order creation, tracking, and management |
| **payments** | Payment gateway integration (Chapa) |
| **notifications** | Email + in-app notifications (Celery) |

---

## 🧠 **Key Features by Domain**

### Accounts

* User registration with email verification (Celery)
* JWT-based login/logout
* Profile management

### Catalog

* Product CRUD with image upload
* Nested reviews (per product)
* Redis-cached product listing
* Category hierarchy

### Cart

* User-based cart
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

---

## 🧰 **Developer Notes**

### Modular Monolith Guidelines

* Each app should **own its models and serializers**.
* Cross-app imports allowed **only through `core` services or signals**.
* Maintain **high cohesion** within apps, **low coupling** between them.
* Shared base class: `core.models.BaseModel` → includes UUID PKs, timestamps.

### Commands

```bash
python manage.py runserver
python manage.py shell
celery -A alx_project_nexus worker -l info
celery -A alx_project_nexus beat -l info
```

---

## 🧭 **Roadmap**

* [x] Modular architecture
* [x] REST APIs
* [x] Notifications (Celery)
* [x] Basic payments
* [x] Render + Railway deployment
* [ ] WebSockets for live order status
* [ ] Admin dashboard
* [ ] Advanced analytics
* [ ] AI-powered recommendations

---

## 🤝 **Contributing**

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

## 👨‍💻 **Author**

**Yetmgeta Redahegn Kassaye**

Backend Engineering Student @ ASTU

ALX Backend Engineering Program

> *"Building scalable systems, one module at a time."*

---

