# Phase 2: Database Setup (Supabase)

**Status**: ⏳ **Pending**  
**Estimated Time**: 1-2 hours  
**Prerequisites**: [Phase 1: Preparation](phase-1-preparation.md) ✅  
**Next Phase**: [Phase 3: Backend Deployment](phase-3-backend.md)

## Overview

Phase 2 sets up production-ready PostgreSQL databases using Supabase for both staging and production environments. This includes creating projects, enabling required extensions, and migrating the existing schema from local development.

## Why Supabase?

- **Managed PostgreSQL**: No database administration overhead
- **pgvector Support**: Required for article similarity and content analysis
- **Connection Pooling**: Built-in connection management for production
- **Free Tier**: Generous limits for MVP development
- **Easy Scaling**: Automatic backups and monitoring
- **Integration Ready**: Works seamlessly with Railway and Vercel

## Phase 2 Tasks

### 📋 Task 2.1: Create Supabase Projects
*Estimated Time: 20 minutes*

#### Steps:
1. **Sign in to Supabase**: Visit [supabase.com](https://supabase.com)
2. **Create Staging Project**:
   - Project name: `dailybrief-staging`
   - Database password: Generate secure password
   - Region: Choose closest to your users
   - Pricing: Free tier for staging

3. **Create Production Project**:
   - Project name: `dailybrief-production`  
   - Database password: Generate different secure password
   - Region: Same as staging
   - Pricing: Free tier initially, can upgrade later

#### Expected Outputs:
- Two Supabase projects with unique URLs
- Database connection strings for both environments
- Admin dashboard access for both projects

### 📋 Task 2.2: Enable Required Extensions
*Estimated Time: 10 minutes*

DailyBrief requires specific PostgreSQL extensions for its content processing pipeline.

#### Required Extensions:
```sql
-- Enable pgvector for article similarity and embeddings
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Enable pg_trgm for full-text search optimization
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enable uuid-ossp for UUID generation (usually enabled by default)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

#### Steps:
1. **Access SQL Editor**: In each Supabase project dashboard
2. **Run Extension Commands**: Execute the SQL above in both staging and production
3. **Verify Installation**: Check that extensions are listed in the extensions tab

### 📋 Task 2.3: Export Local Schema
*Estimated Time: 15 minutes*

#### Steps:
1. **Ensure Local Database is Running**:
   ```bash
   docker-compose up db
   ```

2. **Export Schema**:
   ```bash
   # Export complete schema
   docker-compose exec db pg_dump -U postgres -s dailybrief > schema_export.sql
   
   # Export data (optional, for development data)
   docker-compose exec db pg_dump -U postgres --data-only dailybrief > data_export.sql
   ```

3. **Clean Export for Supabase**:
   - Remove Docker-specific user creation statements
   - Remove `CREATE DATABASE` statements
   - Remove `\connect` statements
   - Keep all table creation, indexes, and constraints

#### Expected Output:
- `schema_export.sql` - Clean schema ready for Supabase import

### 📋 Task 2.4: Import Schema to Supabase
*Estimated Time: 20 minutes*

#### Steps:
1. **Import to Staging Database**:
   - Use Supabase SQL Editor
   - Copy and paste cleaned schema
   - Execute and verify no errors

2. **Import to Production Database**:
   - Repeat process for production project
   - Ensure identical schema in both environments

3. **Verify Import**:
   - Check table count matches local development
   - Verify indexes and constraints are created
   - Test basic queries in SQL editor

### 📋 Task 2.5: Update Environment Variables
*Estimated Time: 15 minutes*

#### Update Staging Environment:
```bash
# Edit .env.staging
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT-ID].supabase.co
SUPABASE_KEY=[ANON-KEY]
SUPABASE_DB_HOST=db.[PROJECT-ID].supabase.co
SUPABASE_DB_PASSWORD=[YOUR-PASSWORD]
```

#### Update Production Environment:
```bash
# Edit .env.production  
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROD-PROJECT-ID].supabase.co:5432/postgres
SUPABASE_URL=https://[PROD-PROJECT-ID].supabase.co
SUPABASE_KEY=[PROD-ANON-KEY]
SUPABASE_DB_HOST=db.[PROD-PROJECT-ID].supabase.co
SUPABASE_DB_PASSWORD=[YOUR-PROD-PASSWORD]
```

### 📋 Task 2.6: Test Database Connectivity
*Estimated Time: 10 minutes*

#### Local Connection Test:
```bash
# Test staging database from local environment
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres" python backend/manage.py dbshell

# Run a simple query
SELECT version();
SELECT COUNT(*) FROM django_migrations;
```

#### Django Migration Test:
```bash
# Test Django can connect and run migrations
cd backend
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres" python manage.py showmigrations
```

## Configuration Details

### Supabase Connection Settings

**Connection Pooling**: Supabase automatically provides connection pooling. For high-traffic applications, use the pooled connection string:
```
postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:6543/postgres
```

**SSL Requirements**: Supabase requires SSL connections. Django automatically handles this with the connection string format.

**Connection Limits**: Free tier provides up to 60 concurrent connections, which is sufficient for MVP deployment.

### Database Schema Overview

DailyBrief's schema includes:

- **9 Django Apps**: Each with dedicated tables and relationships
- **Vector Extensions**: For content similarity and search
- **Indexes**: Optimized for content processing queries
- **Constraints**: Data integrity for article processing pipeline

## Verification Checklist

### ✅ Supabase Projects
- [ ] Staging project created and accessible
- [ ] Production project created and accessible  
- [ ] Both projects have secure, different passwords
- [ ] Admin access confirmed for both projects

### ✅ Extensions
- [ ] pgvector enabled in staging
- [ ] pgvector enabled in production
- [ ] pg_trgm enabled in both environments
- [ ] All extensions show as active in dashboard

### ✅ Schema Migration
- [ ] Local schema exported successfully
- [ ] Schema cleaned for Supabase compatibility
- [ ] Schema imported to staging without errors
- [ ] Schema imported to production without errors
- [ ] Table count matches between environments

### ✅ Connectivity
- [ ] Django can connect to staging database
- [ ] Django can connect to production database
- [ ] Migration status shows correctly
- [ ] Basic queries execute successfully

### ✅ Environment Configuration
- [ ] .env.staging updated with staging database URLs
- [ ] .env.production updated with production database URLs
- [ ] Connection strings tested and working
- [ ] SSL connectivity confirmed

## Troubleshooting

### Common Issues:

**Connection Refused**:
- Verify Supabase project is active
- Check connection string format
- Ensure SSL is not being disabled

**Schema Import Errors**:
- Remove Docker-specific statements
- Import tables in dependency order
- Check for naming conflicts with Supabase system tables

**Extension Errors**:
- Verify you have admin access
- Some extensions may need to be enabled by Supabase support

**Migration Failures**:
- Ensure schema was imported successfully
- Check Django can read the database
- Verify all required tables exist

## Security Considerations

- **Database Passwords**: Use different, secure passwords for staging and production
- **Connection Strings**: Never commit actual connection strings to Git
- **Row Level Security**: Consider enabling RLS for sensitive tables
- **Network Access**: Supabase allows connections from any IP by default

## Next Steps

With Phase 2 complete, you'll have:
- Staging and production PostgreSQL databases ready
- Required extensions enabled for content processing
- Schema migrated and verified in both environments
- Environment variables configured for cloud deployment

**Continue to**: [Phase 3: Backend Deployment](phase-3-backend.md)

## Rollback Information

If you need to rollback Phase 2:

1. **Delete Supabase Projects**: From Supabase dashboard settings
2. **Revert Environment Files**: 
   ```bash
   git checkout HEAD -- .env.staging .env.production
   ```
3. **Continue with Local Database**: Use Docker Compose as before

See [rollback-procedures.md](rollback-procedures.md) for complete rollback documentation. 