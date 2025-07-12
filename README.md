# DailyBrief - AI-Powered News Reader

> **CS50 Web Programming Final Project**  
> A modern news aggregation platform that goes beyond course specifications to practice contemporary web development approaches while complying with capstone requirements.

[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green?logo=django)](https://djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?logo=postgresql)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)](https://docker.com/)

## Introduction

DailyBrief is an intelligent news reader that transforms how users consume information by providing AI-generated summaries, personalized daily digests, and a clean mobile-first interface. The platform aggregates news from multiple sources and processes them through a sophisticated 5-stage AI pipeline to deliver concise, relevant content.

### Project Motivation

I decided to create a project that would come as close as possible to a real-world application that I could extend and potentially publish to real users. The goal was to apply modern tech stack and architecture patterns, keeping the implementation as lean and simple as possible for a proof of concept while demonstrating advanced full-stack development skills that satisfies and even exceed the capstone project scope.

This approach allowed me to practice contemporary web development techniques including service-oriented architecture concepts, AI integration, real-time processing, and production-ready patterns while building something genuinely useful and innovative.

## Distinctiveness and Complexity

### Distinctiveness from Course Projects

DailyBrief is fundamentally different from previous CS50 Web projects:

- **Not a social network**: Unlike projects focused on user interactions, posts, and social features, DailyBrief is a content aggregation and AI processing platform
- **Not e-commerce**: No shopping cart, payments, or product catalog functionality
- **Unique value proposition**: AI-powered news summarization and digest generation with sophisticated content processing

**Core Innovation**: A 5-stage AI content pipeline that fetches, processes, summarizes, analyzes and digests news articles to create personalized daily digests.

### Technical Complexity Beyond Course Requirements

**Advanced Architecture (Multiple Django Apps)**:
DailyBrief implements a modular monolith architecture that combines the simplicity of a single deployable unit with the organizational benefits of microservices. This approach provides better code maintainability and organization while keeping operational overhead low. The complete architectural details are covered in the Implementation Details section.
```
Modular Monolith Architecture
├── accounts/
├── feeds/
├── articles/
├── content/
│   ├── fetcher/
│   ├── processor/
│   ├── summariser/
│   ├── analyzer/
│   └── digest/
├── newsapi/
├── aiproviders/
└── notifications/
```

**Sophisticated AI Processing Pipeline**:
1. **Fetching**: Multi-source news aggregation from News API, RSS feeds (TBD)
2. **Processing**: AI content extraction and structuring
3. **Summarization**: Intelligent summary generation
4. **Analysis**: Semantic event clustering and article feature extraction
5. **Digestion**: Daily digest creation

**Modern Full-Stack Implementation**:
- **Backend**: Django 5 REST API with Celery task processing
- **Frontend**: Next.js 15 with React 19 Server Components
- **Database**: PostgreSQL with vector embeddings (pgvector)
- **Authentication**: NextAuth.js with Google, Apple (TBD), Email magic links
- **Deployment**: Docker containerization for ease of deployment

**Production-Ready Features**:
- Mobile PWA with service worker and offline capabilities (TBD)
- Real-time background processing with Redis/Celery
- Comprehensive error handling and logging
- API rate limiting and CORS management
- Responsive design with Tailwind CSS and shadcn/ui

## Implementation Details

### Technology Stack and Dependencies

**Backend Architecture**:
- **Django 5**: REST API with modular monolith architecture
- **Celery + Redis**: Background task processing and scheduling  
- **PostgreSQL + pgvector**: Database with vector embeddings for semantic search
- **OpenAI & Anthropic APIs**: AI content processing and summarization
- **News API**: External news source integration
- **spaCy + langdetect**: Cost-optimized natural language processing

**Frontend Architecture**:
- **Next.js 15**: React framework with App Router and Server Components
- **TypeScript**: Type-safe JavaScript development throughout
- **NextAuth.js**: Authentication with Google and Email magic links (Apple - TBD)
- **Tailwind CSS + shadcn/ui**: Modern UI components and responsive design
- **Prisma**: Database ORM for frontend authentication layer

**Key Dependencies Justification**:
- **Django over FastAPI**: Not only a capstone requirement: provides mature ORM, admin UI, and extensive ecosystem
- **Custom API layer over DRF**: Avoids serialization complexity, provides explicit control
- **Next.js 15 with App Router**: Enables React Server Components and optimized performance
- **TypeScript everywhere**: Provides type safety crucial for large codebase maintenance. TypeScript and Next.js are used as modern applications of JavaScript, following contemporary industry practices.
- **Celery**: Essential for background AI processing tasks that take minutes to complete
- **pgvector**: Required for semantic article clustering and similarity matching

### Project Architecture

**Modular Monolith Approach**:

DailyBrief implements a modular monolith architecture that combines the simplicity of a single deployable unit with the organizational benefits of microservices.

**Modular Monolith Structure**:
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
├── notifications/     → User notification system (TBD)
└── core/              → Shared API utilities & authentication
```

**5-Stage Content Processing Pipeline**:
1. **Fetching**: Intelligent content extraction from public news articles pages
2. **Processing**: AI-powered content cleaning and structuring using LLM or algorithmic routes
3. **Summarization**: 4-stage AI pipeline (RBC → Summary → Critic → Embeddings)
4. **Analysis**: 8-stage cost-optimized pipeline combining free tools (spaCy, langdetect) with targeted LLM usage
5. **Digestion**: Daily digest creation with multiple strategies

### Project Structure

**Backend (`/backend/`)**:

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

**Frontend (`/frontend/`)**:

```bash
frontend/
├── app/                  # Next.js 15 App Router
│   ├── (authenticated)/  # Protected route groups
│   │   ├── (main)/       # Main app navigation
│   │   │   ├── home/     # Dashboard & recent articles
│   │   │   ├── headlines/ # Top news headlines (currently inactive: to be migrated from world)
│   │   │   └── world/    # World news category (currently active: to be migrated to world)
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

**Key Configuration Files**:

- **`docker-compose.yml`**: Multi-service development environment
- **`docker.sh`**: Development command wrapper script
- **`.gitignore`**: Comprehensive ignore patterns for development files
- **`/docs/`**: Project documentation and implementation planning
- **`/infra/`**: Infrastructure and deployment configurations

### Data Models and Relationships

**Core Models Overview**:

**User Management**:
- **User**: Django's built-in user model extended with profile
- **UserProfile**: User preferences, timezone, onboarding status, digest settings
  - Key fields: `public_id` (UUID), `timezone`, `onboarding_completed`, `digest_preferences` (JSON)

**Content Classification**:
- **Publication**: News sources with metadata and authority scoring
  - Key fields: `name`, `news_api_id`, `domain`, `authority`, `logo_url`
  - Relationships: Many-to-many with Topic, Language, Region
- **Topic**: Content categories (business, technology, sports, etc.)
- **Region**: Geographic classification (US, BR, UK, etc.)  
- **Language**: Supported languages with ISO codes

**Article Pipeline**:
- **Article**: Central content model with 4-stage processing status
  - Core fields: `title`, `content`, `url`, `published_at`, `image_url`
  - Processing status: `fetch_status`, `process_status`, `summarization_status`, `analyzer_status`
  - Classification: Foreign keys to `Publication`, `Language`; Many-to-many with `Topic`, `Region`
  - AI analysis: `keywords`, `entities` (JSON), `sentiment_score`, `readability_score`
  - Content versions: `raw_html`, `basic_content`, `clean_content`

**AI Processing Models**:
- **ArticleRBC**: Rich Bullet Compression (first summarization stage)
  - Fields: `bullets` (JSON), `processing_metrics`, `quality_indicators`
- **ArticleSummary**: Structured summary output
  - Key fields: `headline`, `abstract`, `longer_abstract`, `facts` (JSON), `opinions` (JSON), `impact` (JSON)
- **ArticleEmbedding**: Vector embeddings for semantic similarity
  - Fields: `embedding` (VectorField 1536-dim), `model_used`, `similarity_threshold`

**Analysis and Events**:
- **Entity**: Master entity catalog with deduplication
  - Fields: `canonical_name`, `display_name`, `entity_type`, `embedding` (VectorField)
  - Types: Person, Organization, Location, Event, etc.
- **Event**: Clustered article groupings representing real-world events
  - Fields: `title`, `description`, `event_hash`, `centroid_embed` (Vector), `article_count`
  - Relationships: Many-to-many with Article, Entity
- **ArticleAnalysis**: Comprehensive analysis metadata
  - Fields: `language_detected`, `readability_score`, `style_tone`, `processing_cost`

**Digest System**:
- **Digest**: Daily personalized news summary
  - Fields: `title`, `date`, `introduction`, `html_content`, `generation_status`
  - Metrics: `reading_time_minutes`, `events_included`, `generation_cost_usd`
- **DigestTopic**: Topic sections within digests
- **DigestStory**: Individual stories with AI-enhanced summaries
  - Fields: `enhanced_abstract`, `key_facts` (JSON), `perspectives` (JSON)

**Infrastructure Models**:
- **AIProviderUsage**: Tracks AI costs and performance across providers
- **FetchLog**: Content fetching attempts and success rates  
- **ProcessingLog**: AI processing performance and error tracking
- **QualityScoring**: Content quality assessment results

**Key Relationships**:
- `Publication` → `Article` (one-to-many): Source attribution
- `Article` → `ArticleSummary` (one-to-one): AI-generated summaries
- `Article` → `Event` (many-to-many): Event clustering for related stories
- `Event` → `DigestStory` (one-to-one): Events featured in daily digests
- `User` → `Digest` (one-to-many): Personalized daily summaries

### Architecture Patterns Applied

**SOLID Principles Implementation**:
- **Single Responsibility**: Each Django app handles one domain (articles, summarization, analysis)
- **Open/Closed**: Extensible AI provider system via strategy pattern
- **Liskov Substitution**: AI providers implement common interface
- **Interface Segregation**: Focused service contracts per domain
- **Dependency Inversion**: Services depend on abstractions, not concrete implementations

**Design Patterns**:
- **Strategy Pattern**: Multiple AI providers (OpenAI, Anthropic) with unified `AIProviderService`
- **Factory Pattern**: Dynamic AI client instantiation based on configuration
- **Service Layer Pattern**: Domain services (SummarizationService, AnalyzerService) encapsulate business logic
- **Repository Pattern**: Django models with service layer abstraction
- **Observer Pattern**: Pipeline stages trigger subsequent processing

**Development Practices**:
- **API-First Design**: Custom `@api_view` decorator with automatic CORS and authentication
- **Type Safety**: TypeScript frontend, Python type hints throughout backend
- **Error Handling**: Comprehensive logging with structured error responses
- **Cost Optimization**: Intelligent routing between free tools and paid AI services
- **Monitoring**: Detailed usage tracking for AI providers and processing performance

## User Experience

### Onboarding Flow
1. **Authentication**: Sign in with Google, Apple (TBD), or Email magic link
2. **Language Selection**: Choose preferred languages for content consumption
3. **Topic & Region Settings**: Customize content focus areas and geographic scope
4. **Publication Preferences**: Select trusted news sources from curated list

### Daily Workflow
1. **Morning Digest**: AI-generated summary of yesterday's most important news, personalized by user preferences
2. **Headlines Feed**: Real-time top stories with AI-generated summaries from followed sources
3. **Category Browsing**: Explore General, Technology, Business, Science, Health and Sports news with intelligent filtering
4. **Article Reading**: Clean, distraction-free reading experience with structured AI summaries

### Key Features
- **Personalized Daily Digests**: AI-curated summary of yesterday's news with multi-perspective coverage
- **Intelligent Summaries**: Every article includes structured summaries (headline, abstract, key facts, opinions, impact)
- **Offline Reading**: PWA capabilities for offline content access (TBD)

## How to Run the Application

### Prerequisites

- **Docker & Docker Compose** (recommended for development)
- **Python 3.11+** and **Node.js 18+** (if running without Docker)  
- **PostgreSQL 15+** with pgvector extension (if running without Docker)
- **Redis** (for Celery task processing)

### Environment Configuration

**Required API Keys**:
```bash
OPENAI_API_KEY=your_openai_key          # For AI content processing
ANTHROPIC_API_KEY=your_anthropic_key    # Alternative AI provider  
NEWS_API_KEY=your_newsapi_key           # For news article fetching
```

### Option 1: Docker Development (Recommended)

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd dailybrief
   
   # Copy environment templates
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   
   # Edit .env files with your API keys
   ```

2. **Start application**:
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

3. **Access points**:
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000

### Option 2: Local Development

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

### Development Commands

```bash
# Development workflow
./docker.sh up              # Start all services
./docker.sh down            # Stop all services
./docker.sh django <cmd>    # Run Django management commands
./docker.sh logs <service>  # View service logs

# Database operations
./docker.sh django migrate                    # Apply migrations
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

### Key Configuration Files

**Backend Configuration**:
- `backend/.env`: API keys, database URL, Redis URL, Django settings
- `backend/requirements.txt`: Python dependencies with AI/ML libraries
- `backend/dailybrief/settings.py`: Django configuration with modular app setup
- `backend/dailybrief/celery.py`: Background task processing configuration
- `docker-compose.yml`: Multi-service development environment

**Frontend Configuration**:
- `frontend/.env`: NextAuth configuration, API endpoints
- `frontend/package.json`: Node.js dependencies and build scripts
- `frontend/next.config.js`: Next.js configuration with API routes
- `frontend/tailwind.config.js`: Tailwind CSS with custom design system
- `frontend/lib/auth.ts`: NextAuth.js provider configuration

**Infrastructure**:
- `docker.sh`: Development command wrapper script for common operations
- `.gitignore`: Comprehensive ignore patterns for development files
- `docs/`: Project documentation and implementation planning

### Environment Variables

**Backend (`backend/.env`)**:
```bash
# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# News Sources  
NEWS_API_KEY=your_newsapi_key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dailybrief

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Django
SECRET_KEY=your_secret_key
DEBUG=True
```

**Frontend (`frontend/.env`)**:
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret

# OAuth Providers
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## License & Usage Restrictions

This project is developed as a CS50 Web Programming final project and is **shared for evaluation purposes only**. 

**Important Notice:**
- This code is provided exclusively for academic evaluation by CS50 course staff
- **Copying, sharing, or distributing this code is strictly prohibited**
- The code cannot be used as reference material for other CS50 submissions
- All rights reserved by the author

This project demonstrates original work created specifically for CS50 Web Programming capstone requirements and maintains academic integrity standards.

---

This project serves as both a capstone demonstration and a foundation for a potentially viable news aggregation service, embodying the goal of building something genuinely useful while mastering complex web development concepts.

---

**Created by**: Adan Oliveira  
**Course**: CS50 Web Programming with Python and JavaScript  
**Year**: 2025