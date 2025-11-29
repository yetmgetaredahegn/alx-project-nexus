# Use Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Collect static files (using dummy SECRET_KEY for build-time)
# This allows collectstatic to run during build without requiring runtime env vars
# Static files will be collected again at runtime with proper env vars
RUN SECRET_KEY=build-time-dummy-key DJANGO_ENV=production python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Start Gunicorn server
# PORT will be set by Railway/Render at runtime
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "alx_project_nexus.wsgi:application", "--bind", "0.0.0.0:8000"]
