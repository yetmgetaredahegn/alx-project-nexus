# Railway Celery Worker Setup Guide

This guide explains how to set up a Celery worker on Railway to handle background tasks for your Render-deployed Django application.

## Architecture Overview

- **Render**: Hosts your main Django application (API server)
- **Railway**: Hosts your Celery worker (background task processor)
- **Shared Resources**: Both use the same Redis (Upstash) and PostgreSQL database

## Prerequisites

1. Your Django app is deployed on Render
2. You have a Railway account
3. Your Redis URL and Database URL are accessible from Railway

## Step 1: Create a New Service on Railway

1. Go to [Railway Dashboard](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository: `alx-project-nexus`

## Step 2: Configure Railway Service

### 2.1 Service Settings

1. In your Railway service, go to **Settings**
2. Set the following:

   - **Name**: `alx-nexus-celery-worker` (or any name you prefer)
   - **Source**: Your GitHub repository
   - **Branch**: `main` (or your deployment branch)

### 2.2 Dockerfile Configuration

1. Go to **Settings** → **Docker**
2. Set **Dockerfile Path**: `Dockerfile.celery`

### 2.3 Environment Variables

Go to **Variables** and add all the same environment variables from Render:

#### Required Variables:

```bash
# Django Settings
DJANGO_ENV=production
SECRET_KEY=your-secret-key-here  # Same as Render
DEBUG=False

# Database (same as Render)
DATABASE_URL=your-postgresql-url

# Redis (same as Render - this is critical!)
REDIS_URL=redis://default:password@your-redis-host:6379

# Email Configuration (same as Render)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@example.com
SERVER_EMAIL=your-email@example.com

# Payment Configuration (if needed)
CHAPA_SECRET_KEY=your-chapa-secret-key
CHAPA_PUBLIC_KEY=your-chapa-public-key
CHAPA_BASE_URL=https://api.chapa.co/v1
PAYMENT_CALLBACK_URL=https://your-render-domain.onrender.com/api/payments/webhook/
PAYMENT_RETURN_URL=https://your-render-domain.onrender.com/payment-success/

# Security
ALLOWED_HOSTS=.onrender.com,your-domain.com
```

**Important Notes:**
- Use the **exact same** `SECRET_KEY`, `DATABASE_URL`, and `REDIS_URL` as your Render deployment
- The `REDIS_URL` is critical - both services must use the same Redis instance
- `ALLOWED_HOSTS` should include your Render domain

### 2.4 Start Command

In **Settings** → **Deploy**, the start command is already set in `Dockerfile.celery`:
```
celery -A alx_project_nexus worker --loglevel=info --pool=solo
```

**Why `--pool=solo`?**
- Railway's free tier doesn't support process forking
- `solo` pool runs tasks in the same process (single-threaded)
- For production with higher load, consider Railway's paid plans with `prefork` pool

## Step 3: Deploy

1. Click **Deploy** in Railway
2. Wait for the build to complete
3. Check the logs to ensure Celery worker starts successfully

## Step 4: Verify Connection

### 4.1 Check Railway Logs

In Railway dashboard, go to **Deployments** → **View Logs**. You should see:
```
[tasks] celery@hostname ready.
```

### 4.2 Test from Render

1. Trigger a background task from your Render-deployed API
2. Check Railway logs to see if the task is picked up
3. Verify task completion

## Step 5: Monitoring (Optional)

### Railway Metrics

Railway provides basic metrics:
- CPU usage
- Memory usage
- Network traffic

### Celery Monitoring

For advanced monitoring, consider:
- **Flower**: Celery monitoring tool (add as separate Railway service)
- **Sentry**: Error tracking
- **Log aggregation**: Use Railway's log streaming

## Troubleshooting

### Issue: "No module named 'celery'"

**Solution**: Ensure `celery` is in your `requirements.txt`

### Issue: "Connection refused" to Redis

**Solution**: 
- Verify `REDIS_URL` is correct
- Ensure Redis (Upstash) allows connections from Railway's IPs
- Check if Redis requires SSL (Upstash does)

### Issue: Tasks not being picked up

**Solution**:
1. Verify both services use the same `REDIS_URL`
2. Check Celery task routing configuration
3. Ensure task names match between producer and consumer

### Issue: "DATABASE_URL environment variable is required"

**Solution**: 
- Ensure `DATABASE_URL` is set in Railway environment variables
- Verify the variable name is exactly `DATABASE_URL` (case-sensitive)

### Issue: Worker crashes or restarts

**Solution**:
- Check Railway logs for error messages
- Verify all required environment variables are set
- Check memory limits (Railway free tier has limits)
- Consider using `--max-tasks-per-child=1000` to prevent memory leaks

## Production Recommendations

1. **Use Railway Pro** for better performance and `prefork` pool
2. **Set up health checks** to monitor worker status
3. **Configure auto-scaling** if needed (Railway Pro feature)
4. **Use separate Redis instances** for different environments
5. **Monitor task queue length** to prevent backlog
6. **Set up alerts** for failed tasks

## Cost Considerations

- **Railway Free Tier**: Limited resources, suitable for development
- **Railway Pro**: $5/month per service, better for production
- **Render Free Tier**: Suitable for API server
- **Upstash Redis**: Free tier available, pay-as-you-go for production

## Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Celery Documentation](https://docs.celeryproject.org)
- [Django Celery Best Practices](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)

