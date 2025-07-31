# Feature Implementation Plan

### Phase 1: Foundation
*Estimated Time: 1-2 days*

#### Backend
- [x] Set up Django project structure
- [x] Configure Django settings and environment variables
- [x] Set up Docker development environment
- [x] Create base models:
  - [x] User profile extension
  - [x] Topics, Regions, Languages, Publications
  - [x] Article and ArticleSummary
  - [x] Digest and DigestStory
  - [x] NewsAPI integration models
  - [x] AI provider tracking models
  - [x] Notification system models

#### Current Status (Database Schema)
We've implemented a comprehensive database schema following the modular monolith pattern:

1. **User Management (accounts)**: Extended user profiles with timezone preferences
2. **Content Structure (feeds)**: Core entities (topics, regions, languages, publications)
3. **User Preferences (feeds)**: User-to-content relationships with personalization weights
4. **Articles (articles)**: Article storage with metadata and classification fields
5. **Summarization (summariser)**: Models for AI-generated summaries and request tracking
6. **Digests (digest)**: Daily digest generation with clustered stories
7. **News API (newsapi)**: Request tracking and sync logging
8. **AI Integration (aiproviders)**: Provider usage tracking and configuration
9. **Notifications (notifications)**: User preferences and delivery tracking


#### Frontend
- [x] Set up Next.js project
- [x] Configure shadcn/ui with brand colors
- [x] Configure shadcn/ui with brand colors and theme support
  - [x] Implemented light/dark theme toggle in Profile > Reading Preferences
  - [x] Set up system preference detection with next-themes
  - [x] Created theme documentation in docs/theme-implementation.md
  - [x] Decided to use HSL color format in globals.css instead of OKLCH
  - [x] Removed tailwind.brand.ts as it was redundant with the HSL implementation

#### Authentication
- [x] Setup NextAuth.js with:
  - [x] Email (magic link)
  - [ ] Google OAuth
  - [ ] Apple OAuth
- [x] Create login/signup page
- [x] Implement user session handling
- [x] Implement authentication redirection flow (see [docs/auth/post-auth-redirect.md](auth/post-auth-redirect.md))

### Phase 2: Core Functionality
*Estimated Time: 2-3 days*

#### User Preferences
- [ ] Build user onboarding wizard UI
- [ ] Create API endpoints for:
  - [ ] Fetching available topics/regions/publications
  - [ ] Saving user preferences
- [ ] Implement preference management in user profile

#### News Fetching
- [ ] Integrate NewsAPI service
- [ ] Set up Celery tasks for hourly news fetching
- [ ] Implement article storage and management

#### Article Viewing
- [ ] Create article filtering based on user preferences
- [ ] Build article list view with:
  - [ ] Sorting options
  - [ ] Filtering controls
  - [ ] Infinite loading
- [ ] Create article detail page
- [ ] Implement "mark as read" functionality
- [ ] Add sharing options

### Phase 3: Enhanced Features
*Estimated Time: 2-3 days*

#### Article Summarization
- [ ] Integrate OpenAI/Anthropic APIs
- [ ] Implement article summarization:
  - [ ] Extraction of key points
  - [ ] Generation of concise abstracts
- [ ] Create a summarization queue for background processing
- [ ] Display summaries in article cards and detail view

#### Daily Digest
- [ ] Implement daily digest generation logic:
  - [ ] Group articles by topic
  - [ ] Select most important stories
  - [ ] Generate digestible summaries
- [ ] Schedule digest creation via Celery Beat
- [ ] Create daily digest view
- [ ] Implement digest history access

#### Offline Support
- [ ] Add service worker for PWA functionality
- [ ] Implement offline article caching
- [ ] Add "Add to Home Screen" prompt

### Phase 4: Optimization & Launch
*Estimated Time: 1-2 days*

#### Performance
- [ ] Optimize database queries
- [ ] Add caching layer for frequent requests
- [ ] Implement image optimization

#### Multi-language Support
- [ ] Add language selection in user preferences
- [ ] Implement content translation for summaries
- [ ] Support UI translation

#### Testing & Deployment
- [ ] Write tests for critical functionality
- [ ] Set up CI/CD pipeline
- [ ] Configure production environment on Vercel
- [ ] Set up Supabase for production database
- [ ] Configure Upstash for Redis in production
- [ ] Set up email service for production