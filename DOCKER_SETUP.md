# Docker Compose Setup Guide

This guide will help you set up the ALX Project Nexus locally using Docker Compose.

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose) installed
- Git (to clone the repository)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd alx-project-nexus
```

### 2. Create Environment File

Create a `.env` file in the root directory:

```bash
cp .env.example .env  # If .env.example exists
# Or create .env manually
```

Minimum required variables in `.env`:

```env
SECRET_KEY=your-secret-key-here
DJANGO_ENV=development
DEBUG=True

DB_NAME=alx_nexus_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

### 3. Build and Start Services

```bash
docker-compose up --build
```

This will start:
- **PostgreSQL** database on port 5432
- **Redis** cache/broker on port 6379
- **Django web server** on port 8000
- **Celery worker** for background tasks
- **Celery beat** for scheduled tasks

### 4. Run Migrations

In a new terminal:

```bash
docker-compose exec web python manage.py migrate
```

### 5. Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Access the Application

- **API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes (Clean Slate)

```bash
docker-compose down -v
```

### Run Django Management Commands

```bash
docker-compose exec web python manage.py <command>
```

Examples:
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic
```

### Access Django Shell

```bash
docker-compose exec web python manage.py shell
```

### Run Tests

```bash
docker-compose exec web pytest
```

### Rebuild After Code Changes

```bash
docker-compose up --build
```

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| `web` | 8000 | Django application server (Gunicorn) |
| `db` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache and Celery broker |
| `celery_worker` | - | Background task processor |
| `celery_beat` | - | Scheduled task scheduler |

## Troubleshooting

### Port Already in Use

If port 8000, 5432, or 6379 is already in use, modify the ports in `docker-compose.yml` or stop the conflicting service.

### Database Connection Issues

1. Ensure the database service is healthy:
   ```bash
   docker-compose ps
   ```

2. Check database logs:
   ```bash
   docker-compose logs db
   ```

3. Verify environment variables in `.env` match `docker-compose.yml`

### Redis Connection Issues

1. Check Redis is running:
   ```bash
   docker-compose exec redis redis-cli ping
   ```
   Should return `PONG`

### Celery Worker Not Processing Tasks

1. Check worker logs:
   ```bash
   docker-compose logs celery_worker
   ```

2. Verify Redis connection:
   ```bash
   docker-compose exec celery_worker python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"
   ```

### Static Files Not Loading

Run collectstatic:
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Reset Everything

To start fresh (⚠️ **This will delete all data**):

```bash
docker-compose down -v
docker-compose up --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Development Tips

1. **Code Changes**: Most code changes are reflected immediately due to volume mounting. Restart services only if needed:
   ```bash
   docker-compose restart web
   ```

2. **Database Changes**: After model changes:
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```

3. **Viewing Logs**: Keep a terminal open with logs:
   ```bash
   docker-compose logs -f web celery_worker
   ```

## Production Notes

⚠️ **This docker-compose.yml is configured for local development only.**

For production:
- Use environment-specific settings
- Set `DEBUG=False`
- Use strong `SECRET_KEY`
- Configure proper `ALLOWED_HOSTS`
- Use production database and Redis instances
- Set up proper SSL/TLS
- Configure email backend properly
- Review security settings

