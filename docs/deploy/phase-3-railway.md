# Phase 3: Railway Backend Deployment

## Status: 🔄 **In Progress**

*Estimated Time: 1-2 hours*  
*Prerequisites: [Phase 2: Database Setup](phase-2-database.md) ✅*  
*Next Phase: [Phase 4: Frontend Deployment](phase-4-frontend.md)*

Deploy Django backend, Celery worker, and Celery beat to Railway as separate services.

---

## Overview

Phase 3 deploys the complete DailyBrief backend infrastructure to Railway using a multi-service architecture:

- **Backend Service**: Django API server with Gunicorn
- **Worker Service**: Celery worker for background tasks  
- **Beat Service**: Celery beat for scheduled tasks
- **Redis**: Managed Redis for task queue and caching

## Why Railway?

- **Multi-Service Support**: Deploy backend, worker, and beat from same codebase
- **Managed Redis**: Built-in Redis with automatic scaling
- **Docker Support**: Uses our existing Docker configuration
- **Auto-Deploy**: Git-based deployments with branch integration
- **Production Ready**: Load balancing, health checks, monitoring
- **Cost Effective**: Pay-per-use pricing with generous free tier

---

## Phase 3 Tasks

### 📋 Task 3.1: Setup Railway Project
*Estimated Time: 15 minutes*

#### Steps:
1. **Create Railway Account**: Visit [railway.app](https://railway.app)
2. **Connect GitHub**: Link your GitHub account
3. **Create New Project**: Select "Deploy from GitHub repo"
4. **Connect Repository**: Link your DailyBrief repository
5. **Initial Setup**: Configure basic project settings

#### Expected Outputs:
- Railway project created and linked to GitHub
- Automatic deployments configured
- Project dashboard accessible

### 📋 Task 3.2: Configure Redis Service
*Estimated Time: 10 minutes*

#### Steps:
1. **Add Redis Service**: In Railway dashboard
2. **Configure Redis**: Use Railway's managed Redis
3. **Get Connection Details**: Note Redis URL for environment variables

### 📋 Task 3.3: Deploy Backend Service
*Estimated Time: 30 minutes*

#### Steps:
1. **Configure Backend Service**: Using `railway.json`
2. **Set Environment Variables**: Copy from `.env.staging`
3. **Deploy and Verify**: Check health endpoint
4. **Test Database Connection**: Verify Supabase connectivity

### 📋 Task 3.4: Deploy Worker and Beat Services
*Estimated Time: 20 minutes*

#### Steps:
1. **Configure Worker Service**: Celery worker with concurrency settings
2. **Configure Beat Service**: Celery beat for scheduled tasks
3. **Verify Services**: Check logs and health status

### 📋 Task 3.5: Configure Environment Variables
*Estimated Time: 15 minutes*

#### Required Variables:
- Database connection (Supabase Session Pooler)
- Redis connection (Railway managed)
- Django settings (DEBUG, SECRET_KEY, etc.)
- External service keys (if any)

### 📋 Task 3.6: Test Complete Backend
*Estimated Time: 10 minutes*

#### Tests:
- Health check endpoints respond
- Database queries work
- Celery tasks execute
- API endpoints accessible

---

## Railway Configuration

### Multi-Service Architecture

Our `backend/railway.json` defines three services:

```json
{
  "services": {
    "backend": {
      "source": "./",
      "build": {
        "builder": "dockerfile",
        "dockerfilePath": "Dockerfile"
      },
      "deploy": {
        "startCommand": "python manage.py migrate && gunicorn dailybrief.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --worker-class gevent --worker-connections 1000"
      },
      "healthcheckPath": "/api/health/",
      "restartPolicyType": "on_failure"
    },
    "worker": {
      "source": "./",
      "build": {
        "builder": "dockerfile",
        "dockerfilePath": "Dockerfile"
      },
      "deploy": {
        "startCommand": "celery -A dailybrief worker --loglevel=info --concurrency=2 --max-tasks-per-child=1000"
      },
      "restartPolicyType": "always"
    },
    "beat": {
      "source": "./",
      "build": {
        "builder": "dockerfile", 
        "dockerfilePath": "Dockerfile"
      },
      "deploy": {
        "startCommand": "celery -A dailybrief beat --loglevel=info"
      },
      "restartPolicyType": "always"
    }
  }
}
```

### Production Optimizations

- **Gunicorn WSGI**: Production-ready server with gevent workers
- **Database Migrations**: Automatic on backend startup
- **Health Checks**: Monitor service status
- **Restart Policies**: Automatic recovery from failures
- **Concurrency**: Optimized worker and connection counts

---

## Environment Variables Setup

### Required Variables for All Services

```bash
# Django Configuration
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=*.railway.app
CORS_ALLOWED_ORIGINS=https://*.vercel.app

# Database (Supabase Session Pooler)
DATABASE_URL=postgresql://postgres.[project-id]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
PGGSSENCMODE=disable

# Redis (Railway Managed)
REDIS_URL=redis://redis.railway.internal:6379/0

# Supabase Details
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_KEY=[anon-key]
```

---

## Expected Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (Vercel)      │───▶│   (Railway)     │───▶│   (Supabase)    │
│                 │    │                 │    │                 │
│ • Next.js App   │    │ • Django API    │    │ • PostgreSQL    │
│ • NextAuth      │    │ • Health Checks │    │ • Extensions    │
│ • PWA           │    │ • CORS          │    │ • Session Pool  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Celery Worker  │    │  Celery Beat    │
                       │   (Railway)     │    │   (Railway)     │
                       │                 │    │                 │
                       │ • Process Tasks │    │ • Schedule Jobs │
                       │ • Content AI    │    │ • Periodic Sync │
                       │ • Email Queue   │    │ • Maintenance   │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                       ┌─────────────────────────────────────────┐
                       │              Redis Queue                │
                       │             (Railway)                   │
                       │                                         │
                       │ • Task Queue • Results Cache • Sessions │
                       └─────────────────────────────────────────┘
```

---

## Next Steps

Once Phase 3 is complete, you'll have:
- Django backend running on Railway
- Celery worker processing background tasks
- Celery beat handling scheduled jobs
- Redis managing task queue and caching
- Health monitoring and auto-restart
- Production-ready configuration

**Continue to**: [Phase 4: Frontend Deployment](phase-4-frontend.md)

---

*Last updated: July 31, 2025* 