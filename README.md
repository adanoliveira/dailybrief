# DailyBrief - AI-Powered News Reader

[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green?logo=django)](https://djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?logo=postgresql)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)](https://docker.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)](https://www.typescriptlang.org/)

<p align="center">
  <!-- Replace with actual logo when available -->
  <img src="docs/assets/dailybrief-logo.png" alt="DailyBrief Logo" width="200"/>
</p>

> Transform your news consumption with AI-powered summaries and personalized daily digests

## 🚀 Overview

DailyBrief is an intelligent content aggregation platform that transforms how users consume information from across the web. By providing AI-generated summaries, personalized daily digests, and a clean mobile-first interface, DailyBrief enables users to efficiently stay informed on topics that matter to them.

### 🌐 Vision

DailyBrief aims to be a comprehensive web content aggregator that goes beyond traditional news sources and addresses the limitations of existing content discovery platforms:

- **Diverse Content Sources**: Aggregating from both established news outlets and independent creators across multiple platforms:
  - Traditional publishers and news sites
  - Independent blogs and Substack newsletters
  - YouTube channels and video content
  - Reddit communities and discussions
  - Podcasts and audio content
  - Social media thought leadership

- **Target Audiences**:
  - **Professionals seeking domain expertise**: Stay updated on industry trends and developments from trusted sources in just minutes per day
  - **Financial professionals and investors**: Track real-time updates on macro/microeconomic news affecting investment strategies, specific assets, companies, or regions
  - **Reputation and sentiment monitoring**: Track citations and public sentiment around specific entities, brands, or topics of interest

### 🔄 Market Positioning

DailyBrief serves as both an alternative and complement to existing major web platforms for content consumption:

- **Unlike Google**: DailyBrief offers passive discovery rather than requiring proactive searching. Content comes to you based on your interests, not your search queries.

- **Unlike Meta platforms** (Facebook, Instagram): DailyBrief focuses exclusively on informational content without personal updates from friends that add noise. Content isn't subject to social feed algorithm bias, and users don't need to post content to receive value.

- **Unlike X/Twitter**: DailyBrief doesn't require users to post content or follow specific accounts. It focuses on comprehensive content aggregation rather than user announcements and discussions.

- **Modern reinvention**: Similar to the classic Yahoo homepage concept but reimagined with AI-powered recommendations, intelligent summarization, and personalized content curation for efficient consumption.

The platform processes content through a sophisticated 5-stage AI pipeline to deliver concise, relevant information tailored to each user's specific interests and needs.

### ✨ Key Features

- **Personalized Daily Digests**: AI-curated summaries of content from across the web, tailored to user interests
- **Cross-Platform Aggregation**: Unified content from traditional news, blogs, videos, podcasts, and social platforms
- **Intelligent Summaries**: Every piece of content includes structured summaries (headline, abstract, key facts, opinions, impact)
- **Smart Event Clustering**: Related content from different sources automatically grouped into meaningful events
- **Domain-Specific Monitoring**: Track industry trends, financial news, or specific topics with custom filters
- **Entity & Sentiment Tracking**: Monitor mentions and sentiment around specific companies, people, or topics
- **Mobile-First Design**: Clean, distraction-free reading experience optimized for mobile devices
- **Cost-Optimized AI**: Smart combination of open-source NLP and targeted LLM usage for scalable processing

<details>
<summary><strong>📸 Screenshots</strong></summary>
<br>

<!-- Replace with actual screenshots when available -->
| Daily Digest | Article View | Headlines Feed |
|:-------------------------:|:-------------------------:|:-------------------------:|
| <img src="docs/assets/screenshot-digest.png" alt="Daily Digest" width="250"/> | <img src="docs/assets/screenshot-article.png" alt="Article View" width="250"/> | <img src="docs/assets/screenshot-feed.png" alt="Headlines Feed" width="250"/> |

</details>

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Development](#-development)
- [Project Structure](#-project-structure)
- [Data Models](#-data-models)
- [Pipeline Architecture](#-pipeline-architecture)
- [Team Workflow](#-team-workflow)
- [Project Status](#-project-status)

## 🏛 Architecture

DailyBrief implements a modular monolith architecture that combines the simplicity of a single deployable unit with the organizational benefits of microservices. This approach provides better code maintainability and organization while keeping operational overhead low.

<p align="center">
  <!-- Replace with actual architecture diagram when available -->
  <img src="docs/assets/architecture-diagram.png" alt="DailyBrief Architecture" width="700"/>
</p>

### Modular Monolith Structure

```
DailyBrief Architecture
├── accounts/          → User management & authentication
├── feeds/             → RSS feed management & publication tracking  
├── articles/          → Central article repository
├── content/           → AI processing pipeline (5 sub-apps)
│   ├── fetcher/          → News content extraction
│   ├── processor/        → AI content processing (content structuring & cleaning)
│   ├── summariser/       → 4-stage AI summarization pipeline
│   ├── analyzer/         → 8-stage analysis (entities, events, topics)
│   └── digest/           → Daily digest generation with multiple strategies
├── newsapi/           → News API client & request tracking
├── aiproviders/       → AI provider abstraction & usage tracking
├── notifications/     → User notification system
└── core/              → Shared API utilities & authentication
```

## 🛠 Tech Stack

### Backend
- **Django 5**: REST API with modular monolith architecture
- **Celery + Redis**: Background task processing and scheduling  
- **PostgreSQL + pgvector**: Database with vector embeddings for semantic search
- **OpenAI & Anthropic APIs**: AI content processing and summarization
- **News API**: External news source integration
- **spaCy + langdetect**: Cost-optimized natural language processing

### Frontend
- **Next.js 15**: React framework with App Router and Server Components
- **TypeScript**: Type-safe JavaScript development throughout
- **NextAuth.js**: Authentication with Google and Email magic links
- **Tailwind CSS + shadcn/ui**: Modern UI components and responsive design
- **Prisma**: Database ORM for frontend authentication layer

### Infrastructure
- **Docker**: Containerized development and deployment
- **GitHub Actions**: CI/CD pipeline
- **Vercel**: Frontend hosting
- **PostgreSQL**: Database with pgvector extension

## 🚦 Getting Started

### Prerequisites

- **Docker & Docker Compose** (recommended for development)
- **Python 3.11+** and **Node.js 18+** (if running without Docker)  
- **PostgreSQL 15+** with pgvector extension (if running without Docker)
- **Redis** (for Celery task processing)

### Required API Keys

To work on DailyBrief, you'll need access to these API keys (contact the team lead):

```bash
OPENAI_API_KEY          # For AI content processing
ANTHROPIC_API_KEY       # Alternative AI provider  
NEWS_API_KEY            # For news article fetching
```

### Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/company-internal/dailybrief.git
   cd dailybrief
   ```

2. **Set up environment files**:
   ```bash
   # Copy environment templates
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   
   # Add your API keys to the .env files (get these from the team lead)
   ```

3. **Start the development environment**:
   ```bash
   # Build and start all containers
   ./docker.sh up
   
   # Run database migrations
   ./docker.sh django migrate
   
   # Load initial feed data
   ./docker.sh django loaddata feeds/fixtures/initial_data.json
   
   # Create superuser (optional)
   ./docker.sh django createsuperuser
   ```

4. **Access the application**:
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **Admin Panel**: http://localhost:8000/admin

### Local Setup (Alternative)

<details>
<summary>View local development setup instructions</summary>

1. **Backend setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Database setup
   python manage.py migrate
   python manage.py loaddata feeds/fixtures/initial_data.json
   python manage.py runserver
   ```

2. **Frontend setup** (new terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Background workers** (new terminal):
   ```bash
   cd backend
   celery -A dailybrief worker --loglevel=info
   celery -A dailybrief beat --loglevel=info
   ```
</details>

## 🧑‍💻 Development

### Development Commands

```bash
# Development workflow
./docker.sh up              # Start all services
./docker.sh down            # Stop all services
./docker.sh django <cmd>    # Run Django management commands
./docker.sh logs <service>  # View service logs

# Database operations
./docker.sh django migrate                  # Apply migrations
./docker.sh django makemigrations           # Create migrations
./docker.sh django shell                    # Django shell

# Content pipeline operations
./docker.sh django fetch_articles           # Fetch new articles from News API
./docker.sh django process_articles         # Stage 2: AI content processing
./docker.sh django generate_summaries       # Stage 3: AI summarization
./docker.sh django analyze_events           # Stage 4: Event clustering and analysis
./docker.sh django generate_digest          # Create personalized daily digest

# Pipeline monitoring and maintenance
./docker.sh django test_pipeline --status   # Check pipeline health and status
./docker.sh django cleanup_stuck_articles   # Reset failed processing attempts
./docker.sh django reset_failed_to_fetch_pending  # Retry failed articles
```

### Initial Data Population

```bash
# Fetch latest articles from News API
./docker.sh django fetch_articles

# Process articles through complete AI pipeline
./docker.sh django process_articles

# Generate AI summaries for processed articles
./docker.sh django generate_summaries

# Analyze articles and cluster into events
./docker.sh django analyze_events

# Create personalized daily digest
./docker.sh django generate_digest
```

## 📁 Project Structure

<details>
<summary><strong>Backend Structure</strong></summary>

```bash
backend/
├── apps/
│   ├── accounts/           # User authentication & profiles
│   │   ├── models.py      # User profile extensions
│   │   ├── views.py       # Auth API endpoints
│   │   └── management/    # User management commands
│   ├── feeds/              # RSS feed management
│   │   ├── models.py      # Feed, Publication, Category models
│   │   ├── views.py       # Feed CRUD API
│   │   └── fixtures/      # Initial feed data
│   ├── articles/           # Core article storage
│   │   ├── models.py      # Article, StoryGroup models
│   │   └── views.py       # Article retrieval API
│   ├── content/            # AI processing pipeline
│   │   ├── fetcher/       # Content aggregation
│   │   │   ├── models.py  # FetchLog, RSSEntry models
│   │   │   ├── services.py # RSS parsing & News API integration
│   │   │   └── tasks.py   # Celery fetch tasks
│   │   ├── processor/     # AI content processing
│   │   │   ├── ai_processor.py      # OpenAI/Anthropic integration
│   │   │   ├── algorithmic_processor.py # Fallback processing
│   │   │   └── services.py # Processing orchestration
│   │   ├── summariser/    # AI summarization
│   │   │   ├── models.py  # Summary storage & embeddings
│   │   │   ├── services.py # AI summary generation
│   │   │   └── tasks.py   # Background summarization
│   │   ├── analyzer/      # Event clustering & analysis
│   │   │   ├── models.py  # Event, Entity models
│   │   │   ├── services.py # Semantic clustering algorithms
│   │   │   └── tasks.py   # Analysis pipeline
│   │   └── digest/        # Daily digest creation
│   │       ├── models.py  # Digest, DigestEvent models
│   │       ├── services/  # Digest generation strategies
│   │       └── tasks.py   # Scheduled digest creation
│   ├── newsapi/           # News API integration
│   │   ├── models.py      # External article tracking
│   │   └── services/      # API client & processing
│   ├── aiproviders/       # AI model configuration
│   │   ├── models.py      # Provider & model definitions
│   │   └── services.py    # Dynamic AI client factory
│   └── notifications/     # User notifications
│       ├── models.py      # Notification preferences
│       └── services.py    # Notification delivery
├── dailybrief/            # Django project configuration
│   ├── settings.py        # Environment-based configuration
│   ├── celery.py         # Celery task processing setup
│   └── urls.py           # API route definitions
├── requirements.txt       # Python dependencies
├── manage.py             # Django management interface
└── Dockerfile            # Backend containerization
```
</details>

<details>
<summary><strong>Frontend Structure</strong></summary>

```bash
frontend/
├── app/                  # Next.js 15 App Router
│   ├── (authenticated)/  # Protected route groups
│   │   ├── (main)/       # Main app navigation
│   │   │   ├── home/     # Dashboard & recent articles
│   │   │   ├── headlines/ # Top news headlines
│   │   │   └── world/    # World news category
│   │   ├── (digest)/     # Daily digest interface
│   │   │   └── digest/   # Digest viewing & archive
│   │   └── (article)/    # Individual article view
│   │       └── article/  # Article reading interface
│   ├── auth/             # Authentication pages
│   │   ├── page.tsx      # Sign-in interface
│   │   ├── error/        # Auth error handling
│   │   └── verify-request/ # Email verification
│   ├── onboarding/       # New user setup
│   │   └── page.tsx      # Multi-step onboarding flow
│   ├── api/              # API route handlers
│   │   └── auth/         # NextAuth.js configuration
│   ├── globals.css       # Global styles & Tailwind imports
│   └── layout.tsx        # Root layout with providers
├── components/           # Reusable React components
│   ├── ui/              # shadcn/ui component library (50+ components)
│   ├── auth-provider.tsx # NextAuth session management
│   ├── authenticated-shell.tsx # App layout & navigation
│   ├── article/         # Article-specific components
│   ├── digest/          # Digest interface components
│   ├── onboarding/      # User setup workflow
│   └── preferences/     # Settings management
├── lib/                 # Utility functions & configurations
│   ├── api-client.ts    # Django API integration
│   ├── auth.ts          # NextAuth.js configuration
│   └── utils.ts         # Helper functions
├── types/               # TypeScript type definitions
├── hooks/               # Custom React hooks
├── public/              # Static assets & PWA files
├── package.json         # Node.js dependencies
├── next.config.js       # Next.js configuration
├── tailwind.config.js   # Tailwind CSS setup
└── Dockerfile           # Frontend containerization
```
</details>

## 📊 Data Models

<details>
<summary><strong>Core Data Models</strong></summary>

### User Management
- **User**: Django's built-in user model extended with profile
- **UserProfile**: User preferences, timezone, onboarding status, digest settings

### Content Classification
- **Publication**: News sources with metadata and authority scoring
- **Topic**: Content categories (business, technology, sports, etc.)
- **Region**: Geographic classification (US, BR, UK, etc.)  
- **Language**: Supported languages with ISO codes

### Article Pipeline
- **Article**: Central content model with 4-stage processing status
- **ArticleRBC**: Rich Bullet Compression (first summarization stage)
- **ArticleSummary**: Structured summary output
- **ArticleEmbedding**: Vector embeddings for semantic similarity

### Analysis and Events
- **Entity**: Master entity catalog with deduplication
- **Event**: Clustered article groupings representing real-world events
- **ArticleAnalysis**: Comprehensive analysis metadata

### Digest System
- **Digest**: Daily personalized news summary
- **DigestTopic**: Topic sections within digests
- **DigestStory**: Individual stories with AI-enhanced summaries

### Infrastructure Models
- **AIProviderUsage**: Tracks AI costs and performance across providers
- **FetchLog**: Content fetching attempts and success rates  
- **ProcessingLog**: AI processing performance and error tracking
- **QualityScoring**: Content quality assessment results

</details>

## 🔄 Pipeline Architecture

DailyBrief processes content through a sophisticated 5-stage AI pipeline:

<p align="center">
  <!-- Replace with actual pipeline diagram when available -->
  <img src="docs/assets/pipeline-diagram.png" alt="Content Pipeline" width="700"/>
</p>

1. **Fetching**: Intelligent content extraction from public news articles pages
2. **Processing**: AI-powered content cleaning and structuring using LLM or algorithmic routes
3. **Summarization**: 4-stage AI pipeline (RBC → Summary → Critic → Embeddings)
4. **Analysis**: 8-stage cost-optimized pipeline combining free tools (spaCy, langdetect) with targeted LLM usage
5. **Digestion**: Daily digest creation with multiple strategies

<details>
<summary><strong>Pipeline Implementation Details</strong></summary>

### Stage 1: Fetching
- Multi-source aggregation (News API, RSS feeds)
- Content extraction with intelligent fallbacks
- Publication recognition and metadata enrichment

### Stage 2: Processing
- Content cleaning and structuring
- AI-powered content extraction
- Algorithmic fallback processing

### Stage 3: Summarization
- Rich Bullet Compression (RBC)
- Structured summary generation
- Critical review and quality assessment
- Vector embedding generation

### Stage 4: Analysis
- Entity extraction and disambiguation
- Event detection and clustering
- Sentiment analysis
- Topic classification

### Stage 5: Digestion
- Personalized content selection
- Multi-perspective event coverage
- AI-generated introductions and transitions
- Readability optimization

</details>

## 👥 Team Workflow

### Development Process

1. **Task Assignment**: Tasks are assigned through our internal project management system
2. **Branch Creation**: Create a feature branch from `main` using the naming convention `feature/[task-id]-description`
3. **Development**: Implement the feature or fix following our code standards
4. **Testing**: Write tests and ensure all existing tests pass
5. **Code Review**: Submit a pull request for review by at least one team member
6. **Deployment**: After approval, changes are merged and deployed to the staging environment

### Code Standards

- **Python**: Black formatter (88 columns), isort, strict type hints
- **TypeScript**: ESLint, Prettier, strict type checking
- **Tests**: pytest for backend, vitest + React Testing Library for frontend

### Commit Message Format

We follow a standardized commit message format:

```
[type]: Short description (50 chars)

Longer description if needed, explaining the context or why the
change was made. Wrap at 72 characters.

Refs #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Code Review Guidelines

- Review for functionality, code quality, and adherence to standards
- Provide constructive feedback
- Focus on the code, not the person
- Approve only when all issues are addressed

## 📈 Project Status

### Current Focus

We are currently focused on completing Milestone 1 (Core Experience Completion):

- **Pipeline Resilience**: Improving error handling, recovery mechanisms, and monitoring
- **User Experience**: Finalizing profile settings, PWA capabilities, and notification system
- **Performance**: Optimizing event clustering and content processing for production scale
- **Business Model**: Implementing subscription management and usage tracking

## 🗓️ Project Roadmap

Our development plan is structured into clear milestones with specific goals and deliverables. This roadmap may evolve based on user feedback and market demands after initial launch.

### 🚀 Milestone 1: Core Experience Completion (Current)
- **Pipeline Enhancements**
  - Automated content enrichment pipeline with error handling
  - Improved pipeline resilience and recovery mechanisms
  - Monitoring and alerting for pipeline health
- **User Experience**
  - Complete profile and preference settings
  - PWA implementation for offline reading
  - Push notification system for digests and breaking news
- **Business Model**
  - Subscription billing integration
  - Usage limits for free/premium tiers

### 🌐 Milestone 2: Production Deployment
- **Infrastructure**
  - Production environment setup with high availability
  - Database scaling and optimization
  - CDN integration for global content delivery
- **Performance**
  - Load testing and optimization
  - API rate limiting and caching strategies
  - Response time optimization for mobile users

### 🚀 Milestone 3: Launch Preparation & Execution
- **Pre-Launch**
  - Marketing website and landing pages
  - User onboarding flow optimization
  - Beta testing program with feedback collection
- **Launch**
  - Public availability of core features
  - User acquisition campaigns
- **Post-Launch**
  - Usage analytics and tracking implementation
  - In-app feedback collection mechanisms
  - Comprehensive logging and monitoring
  - Rapid iteration based on initial user feedback

### 🔄 Milestone 4: Core Improvements - Phase 1
- **Content Acquisition**
  - Direct publisher integration for real-time content
  - Custom web crawlers for authorized content sources
  - Improved content freshness metrics
- **User Experience**
  - Localization and internationalization
  - Real-time digest updates throughout the day
  - Dynamic article summary refreshes with new developments
- **Content Organization**
  - Enhanced topic mapping and classification
  - Improved content recommendation algorithms
  - Interest graph development for users

### 📈 Milestone 5: Content Source Expansion - Phase 2
- **New Content Types**
  - Blog aggregation with author verification
  - Substack newsletter integration
  - Podcast transcription and summarization
  - YouTube channel content processing
  - Reddit community insights
- **Content Integration**
  - Cross-platform content linking
  - Source credibility scoring
  - Multi-format content presentation

### 🔍 Milestone 6: Specialized Features - Phase 3
- **Tracking & Monitoring**
  - Custom search term monitoring and alerts
  - Financial asset and market news tracking
  - Entity citation tracking across sources
  - Sentiment analysis for tracked entities
- **Professional Tools**
  - API access for enterprise integrations
  - Custom digest creation tools
  - Team collaboration features
  - Export and sharing capabilities

> **Note**: Milestones 4-6 represent our post-launch vision and may be reprioritized based on user feedback, market demands, and emerging opportunities. We maintain a flexible approach to product development that balances our strategic vision with user needs.

### Known Issues

- Pipeline bottleneck in article fetching stage
- Occasional duplicate events in digest generation
- High API costs for certain processing operations
- Limited content source diversity in current version

### Upcoming Features

Our immediate development priorities align with Milestones 1-3:

- **Core Platform**
  - Push notification system for digest delivery and breaking news
  - Mobile PWA with offline reading capabilities
  - Subscription management and billing integration
  
- **Production Readiness**
  - High-availability infrastructure deployment
  - Performance optimization for mobile users
  - Comprehensive monitoring and alerting
  
- **Launch Features**
  - Marketing website and user onboarding flow
  - Usage analytics and feedback collection
  - Initial user acquisition tools

### Recent Achievements

- Successfully implemented retroactive event deduplication
- Updated event semantic matching criteria for better clustering
- Modified content processing pipeline to improve retry mechanism
- Standardized API response format across backend and frontend

---

<p align="center">
  DailyBrief - Internal Team Documentation  
</p># Trigger redeploy with NEXT_PUBLIC_API_URL
