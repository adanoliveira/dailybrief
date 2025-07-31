# DailyBrief Deployment Guide

This directory contains complete documentation for deploying DailyBrief using the **hybrid Vercel + Railway approach**.

## Deployment Architecture

DailyBrief uses a hybrid cloud deployment strategy that leverages the strengths of both platforms:

- **Frontend (Vercel)**: Next.js application with optimal static site generation and edge functions
- **Backend (Railway)**: Django API + Celery workers for background processing
- **Database (Supabase)**: Managed PostgreSQL with pgvector extension
- **Email (Resend)**: Transactional email service for authentication

## Why This Architecture?

- **Performance**: Vercel's edge network for fast frontend delivery
- **Simplicity**: Railway's Docker-native deployment for complex backend services
- **Cost-Effective**: ~$35-70/month for production-ready infrastructure
- **Scalability**: Both platforms auto-scale based on demand
- **Developer Experience**: Familiar tools with excellent monitoring

## Documentation Structure

### Phase-by-Phase Guides
- [`phase-1-preparation.md`](phase-1-preparation.md) - Repository and environment setup ✅
- [`phase-2-database.md`](phase-2-database.md) - Supabase database configuration
- [`phase-3-backend.md`](phase-3-backend.md) - Railway backend deployment
- [`phase-4-frontend.md`](phase-4-frontend.md) - Vercel frontend deployment
- [`phase-5-integration.md`](phase-5-integration.md) - End-to-end testing
- [`phase-6-production.md`](phase-6-production.md) - Production deployment
- [`phase-7-post-deployment.md`](phase-7-post-deployment.md) - Monitoring and maintenance

### Reference Documentation
- [`environment-variables.md`](environment-variables.md) - Complete environment configuration
- [`troubleshooting.md`](troubleshooting.md) - Common issues and solutions
- [`rollback-procedures.md`](rollback-procedures.md) - Emergency rollback steps
- [`monitoring-setup.md`](monitoring-setup.md) - Health checks and alerts
- [`cost-optimization.md`](cost-optimization.md) - Managing deployment costs

### Platform-Specific Guides
- [`railway-configuration.md`](railway-configuration.md) - Railway setup and optimization
- [`vercel-configuration.md`](vercel-configuration.md) - Vercel deployment settings
- [`supabase-setup.md`](supabase-setup.md) - Database configuration and migration

## Quick Start

If you're ready to deploy immediately:

1. **Prerequisites**: Ensure you have accounts for Railway, Vercel, and Supabase
2. **Start with Phase 1**: Follow [`phase-1-preparation.md`](phase-1-preparation.md) ✅ (Completed)
3. **Continue sequentially**: Each phase builds on the previous one
4. **Total time**: Approximately 12-17 hours over 3-5 days

## Current Status

- ✅ **Phase 1 Complete**: Repository prepared with production-ready configurations
- 🔄 **Phase 2 Next**: Database setup and migration to Supabase
- ⏳ **Phases 3-7**: Pending deployment execution

## Emergency Contacts

- **Rollback**: See [`rollback-procedures.md`](rollback-procedures.md)
- **Support**: Platform-specific support documentation in each guide
- **Monitoring**: Health checks available at `/api/health/` endpoint

---

*Last updated: Phase 1 completion - Repository preparation with Docker, Railway, and Vercel configurations.* 