# Environment Variables Reference

Complete reference for all environment variables used in DailyBrief deployment across local development, staging, and production environments.

## Variable Categories

### Django Core Settings
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DEBUG` | Yes | Enable/disable debug mode | `False` (production) |
| `SECRET_KEY` | Yes | Django secret key for cryptographic signing | `your-secret-key-here` |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of allowed hosts | `*.railway.app,yourdomain.com` |
| `CORS_ALLOWED_ORIGINS` | Yes | Frontend URLs allowed for CORS | `https://yourapp.vercel.app` |

### Database Configuration
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | Complete PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SUPABASE_URL` | No | Supabase project URL (additional reference) | `https://project.supabase.co` |
| `SUPABASE_KEY` | No | Supabase anon key (if using Supabase client) | `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...` |
| `SUPABASE_DB_HOST` | No | Database host (extracted from DATABASE_URL) | `db.project.supabase.co` |
| `SUPABASE_DB_NAME` | No | Database name | `postgres` |
| `SUPABASE_DB_USER` | No | Database username | `postgres` |
| `SUPABASE_DB_PASSWORD` | No | Database password | `secure-password` |
| `SUPABASE_DB_PORT` | No | Database port | `5432` |

### Redis and Celery
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `REDIS_URL` | Yes | Redis connection for caching | `redis://redis.railway.internal:6379/0` |
| `CELERY_BROKER_URL` | Yes | Redis URL for Celery message broker | `redis://redis.railway.internal:6379/0` |
| `CELERY_RESULT_BACKEND` | Yes | Redis URL for Celery results | `redis://redis.railway.internal:6379/0` |

### External API Keys
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEWS_API_KEY` | Yes | NewsAPI.org API key for article fetching | `abc123def456...` |
| `OPENAI_API_KEY` | Yes | OpenAI API key for content processing | `sk-proj-abc123...` |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude models | `sk-ant-api03-abc123...` |

### Frontend and Authentication
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `FRONTEND_URL` | Yes | Complete frontend application URL | `https://yourapp.vercel.app` |
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL (exposed to frontend) | `https://backend.railway.app/api` |
| `NEXTAUTH_URL` | Yes | NextAuth callback URL | `https://yourapp.vercel.app` |
| `NEXTAUTH_SECRET` | Yes | NextAuth encryption secret | `random-secret-string` |

### OAuth Providers
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID | `123456789-abc123.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth client secret | `GOCSPX-abc123...` |
| `APPLE_ID` | No | Apple Sign-In service ID | `com.yourapp.signin` |
| `APPLE_SECRET` | No | Apple Sign-In private key | `-----BEGIN PRIVATE KEY-----...` |

### Email Service
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `EMAIL_FROM` | Yes | Default sender email address | `noreply@yourdomain.com` |
| `RESEND_API_KEY` | Yes | Resend API key for email delivery | `re_abc123...` |

### Platform-Specific
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `PORT` | No | Application port (Railway sets automatically) | `8000` |
| `RAILWAY_ENVIRONMENT` | No | Railway environment identifier | `staging` or `production` |
| `NODE_ENV` | No | Node.js environment (Vercel sets automatically) | `production` |

## Environment-Specific Configurations

### Local Development (.env)
```bash
# Local development with Docker Compose
DEBUG=True
SECRET_KEY=dev-secret-key-replace-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,backend
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000

# Local database (Docker)
DATABASE_URL=postgresql://postgres:postgres@db:5432/dailybrief
SUPABASE_DB_HOST=db
SUPABASE_DB_NAME=dailybrief
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=postgres
SUPABASE_DB_PORT=5432

# Local Redis (Docker)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Frontend (local)
FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXTAUTH_URL=http://localhost:3000
```

### Staging Environment (.env.staging)
```bash
# Staging configuration
DEBUG=False
SECRET_KEY=staging-secret-key-generate-new
ALLOWED_HOSTS=*.railway.app,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://dailybrief-staging.vercel.app,http://localhost:3000

# Supabase staging database
DATABASE_URL=postgresql://postgres:PASSWORD@db.STAGING-PROJECT-ID.supabase.co:5432/postgres
SUPABASE_URL=https://STAGING-PROJECT-ID.supabase.co
SUPABASE_KEY=staging-anon-key

# Railway managed Redis
REDIS_URL=redis://redis.railway.internal:6379/0
CELERY_BROKER_URL=redis://redis.railway.internal:6379/0
CELERY_RESULT_BACKEND=redis://redis.railway.internal:6379/0

# Staging frontend
FRONTEND_URL=https://dailybrief-staging.vercel.app
NEXT_PUBLIC_API_URL=https://backend-staging.railway.app/api
NEXTAUTH_URL=https://dailybrief-staging.vercel.app
NEXTAUTH_SECRET=staging-nextauth-secret-generate-new

# Email (staging can use same Resend account)
EMAIL_FROM=staging@yourdomain.com
RESEND_API_KEY=your-resend-api-key

# Platform
RAILWAY_ENVIRONMENT=staging
```

### Production Environment (.env.production)
```bash
# Production configuration
DEBUG=False
SECRET_KEY=production-secret-key-generate-unique
ALLOWED_HOSTS=*.railway.app,yourdomain.com,dailybrief.vercel.app
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://dailybrief.vercel.app

# Supabase production database
DATABASE_URL=postgresql://postgres:PROD-PASSWORD@db.PROD-PROJECT-ID.supabase.co:5432/postgres
SUPABASE_URL=https://PROD-PROJECT-ID.supabase.co
SUPABASE_KEY=production-anon-key

# Railway managed Redis
REDIS_URL=redis://redis.railway.internal:6379/0
CELERY_BROKER_URL=redis://redis.railway.internal:6379/0
CELERY_RESULT_BACKEND=redis://redis.railway.internal:6379/0

# Production frontend
FRONTEND_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://backend-production.railway.app/api
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=production-nextauth-secret-generate-unique

# Production email
EMAIL_FROM=noreply@yourdomain.com
RESEND_API_KEY=production-resend-api-key

# Platform
RAILWAY_ENVIRONMENT=production
```

## Security Best Practices

### Secret Generation
```bash
# Generate secure secrets
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Or using OpenSSL
openssl rand -base64 50
```

### Environment Variable Security

1. **Never Commit Secrets**: Use `.env.*` patterns in `.gitignore`
2. **Different Keys**: Use unique secrets for each environment
3. **Rotation Policy**: Rotate API keys and secrets quarterly
4. **Access Control**: Limit who can view production environment variables
5. **Platform Security**: Use Railway/Vercel environment variable management

### Validation Checklist

Before deployment, verify:
- [ ] All required variables are set
- [ ] Database connections work
- [ ] API keys are valid and active
- [ ] Frontend can reach backend endpoints
- [ ] CORS origins match frontend domains
- [ ] Email service credentials work
- [ ] OAuth providers configured correctly

## Platform Configuration

### Railway Environment Variables
Set via Railway dashboard or CLI:
```bash
railway variables set SECRET_KEY="your-secret"
railway variables set DATABASE_URL="postgresql://..."
```

### Vercel Environment Variables
Set via Vercel dashboard or CLI:
```bash
vercel env add NEXT_PUBLIC_API_URL
vercel env add NEXTAUTH_SECRET
```

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` format
- Check Supabase project status
- Ensure SSL is enabled (default for Supabase)

### CORS Errors
- Verify `CORS_ALLOWED_ORIGINS` includes your frontend domain
- Check protocol (http/https) matches
- Ensure no trailing slashes in URLs

### API Key Failures
- Verify API keys are active and have correct permissions
- Check rate limits and usage quotas
- Ensure keys match the correct environment

### Email Delivery Issues
- Verify Resend API key is valid
- Check sender domain is verified
- Ensure `EMAIL_FROM` uses verified domain

## Reference Links

- [Django Settings Documentation](https://docs.djangoproject.com/en/5.0/ref/settings/)
- [Railway Environment Variables](https://docs.railway.app/reference/variables)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Supabase Database Settings](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [NextAuth Environment Variables](https://next-auth.js.org/configuration/options#environment-variables) 