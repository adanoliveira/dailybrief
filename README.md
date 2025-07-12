# DailyBrief - AI-Powered News Reader

> **CS50 Web Programming Final Project**  
> A modern news aggregation platform that goes beyond course specifications to practice contemporary web development approaches while complying with capstone requirements.

[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green?logo=django)](https://djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?logo=postgresql)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)](https://docker.com/)

DailyBrief is an intelligent news reader that transforms how users consume information by providing AI-generated summaries, personalized daily digests, and a clean mobile-first interface. The platform aggregates news from multiple sources and processes them through a sophisticated 4-stage AI pipeline to deliver concise, relevant content.

## 🎯 Distinctiveness and Complexity

### **Distinctiveness from Course Projects**

DailyBrief is different from previous CS50 Web projects:

- **Not a social network**: Unlike projects focused on user interactions, posts, and social features, DailyBrief is a content aggregation and AI processing platform
- **Not e-commerce**: No shopping cart, payments, or product catalog functionality
- **Unique value proposition**: AI-powered news summarization and digest generation with sophisticated content processing

**Core Innovation**: A 5-stage AI content pipeline that fetches, processes, summarizes, analyzes and digests news articles to create personalized daily digests.

### **Technical Complexity Beyond Course Requirements**

#### **1. Advanced Architecture (Multiple Django Apps)**
```
📁 Modular Monolith Architecture
├── accounts/     → User management & authentication
├── feeds/        → RSS feed management & publication tracking  
├── articles/     → Article storage & metadata
├── content/
│   ├── fetcher/     → News source aggregation
│   ├── processor/   → AI content processing
│   ├── summariser/  → AI-powered summarization
│   ├── analyzer/    → Event clustering & analysis
│   └── digest/      → Daily digest generation
├── newsapi/      → External API integration
├── aiproviders/  → AI model configuration
└── notifications/ → User notification system (TBD)
```

#### **2. Sophisticated AI Processing Pipeline**
- **Stage 1**: Multi-source content fetching: RSS (TBD) and NewsAPI
- **Stage 2**: AI-powered content processing and extraction
- **Stage 3**: Intelligent summarization with configurable models
- **Stage 4**: Semantic event clustering and article feature extraction

#### **3. Modern Full-Stack Implementation**
- **Backend**: Django 5 REST API with Celery task processing
- **Frontend**: Next.js 15 with React 19 Server Components
- **Database**: PostgreSQL with vector embeddings (pgvector)
- **Authentication**: NextAuth.js with Google, Apple (TBD), Email magic links
- **Deployment**: Docker containerization (for ease of deployment)

#### **4. Production-Ready Features**
- Mobile PWA with service worker and offline capabilities (TBD)
- Real-time background processing with Redis/Celery
- Comprehensive error handling and logging
- API rate limiting and CORS management
- Responsive design with Tailwind CSS and shadcn/ui

## 📁 Project Structure

### **Backend (`/backend/`)**

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

### **Frontend (`/frontend/`)**

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

### **Key Configuration Files**

- **`docker-compose.yml`**: Multi-service development environment
- **`docker.sh`**: Development command wrapper script
- **`.gitignore`**: Comprehensive ignore patterns for development files
- **`/docs/`**: Project documentation and implementation planning
- **`/infra/`**: Infrastructure and deployment configurations

## 🚀 How to Run the Application

### **Prerequisites**

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (if running without Docker)
- **Node.js 18+** (if running without Docker)  
- **PostgreSQL 15+** (if running without Docker)
- **Redis** (for Celery task processing)

### **Option 1: Docker Development (Recommended)**

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd dailybrief
   ```

2. **Environment setup**:
   ```bash
   # Copy environment template
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   
   # Edit environment files with your API keys
   # Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, NEWS_API_KEY
   ```

3. **Start all services**:
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

### **Option 2: Local Development**

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

2. **Frontend setup** (in new terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Celery workers** (in new terminal):
   ```bash
   cd backend
   celery -A dailybrief worker --loglevel=info
   celery -A dailybrief beat --loglevel=info
   ```

### **Initial Data Population**

```bash
# Fetch latest articles
./docker.sh django fetch_articles

# Process articles through AI pipeline
./docker.sh django process_articles

# Generate summaries
./docker.sh django generate_summaries

# Create daily digest
./docker.sh django generate_digest
```

## 🔧 Development Commands

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
./docker.sh postgres                        # PostgreSQL shell

# Content pipeline
./docker.sh django fetch_articles           # Fetch new articles
./docker.sh django process_articles         # AI processing
./docker.sh django generate_summaries       # Create summaries
./docker.sh django analyze_events           # Event clustering
./docker.sh django generate_digest          # Daily digest

# System maintenance
./docker.sh django cleanup_stuck_articles   # Reset failed processing
./docker.sh django reset_failed_to_fetch_pending  # Retry failed articles
```

## 🏗️ Architecture & Technical Implementation

### **AI Processing Pipeline**

The core innovation of DailyBrief is its 5-stage content processing pipeline:

1. **Fetching**: Multi-source aggregation: News API, RSS feeds (TBD)
2. **Processing**: AI content extraction and structuring
3. **Summarization**: Intelligent summary generation
4. **Analysis**: Semantic event clustering and article feature extraction
5. **Digestion**: Daily digest creation

### **Authentication Flow**

- **NextAuth.js** integration with Google, Apple (TBD), and Email providers
- **Magic link** email authentication (no passwords)
- **JWT tokens** for API authentication
- **Session management** across frontend and backend

### **Mobile PWA Features (TBD)**

- **Service Worker** for offline content access
- **App manifest** for home screen installation
- **Responsive design** optimized for mobile consumption
- **Touch-friendly** interface with gesture navigation

### **Data Management**

- **PostgreSQL** with pgvector extension for semantic search
- **Vector embeddings** for article similarity and clustering
- **Complex relationships** between articles, events, and digests
- **Automated cleanup** and data retention policies

## 📱 User Experience

### **Onboarding Flow**
1. **Authentication**: Sign in with Google, Apple, or Email
2. **Language Selection**: Choose preferred languages
3. **Publication Preferences**: Select trusted news sources
4. **Region Settings**: Customize geographical focus

### **Daily Workflow**
1. **Morning Digest**: AI-generated summary of yesterday's news
2. **Headlines**: Real-time top stories with AI summaries
3. **Category Browsing**: Explore World, Technology, Business news
4. **Article Reading**: Clean, distraction-free reading experience

### **Key Features**
- **Daily Digests**: AI-generated summary of yesterday's news
- **AI Summaries**: Every article includes intelligent summary
- **Event Clustering**: Related articles grouped into events
- **Offline Reading**: PWA capabilities for offline access
- **Personalization**: Customizable feeds and preferences

## 🔑 Environment Variables

### **Backend (`backend/.env`)**
```bash
# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# News Sources  
NEWS_API_KEY=your_newsapi_key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dailybrief

# Redis
REDIS_URL=redis://localhost:6379/0

# Django
SECRET_KEY=your_secret_key
DEBUG=True
```

### **Frontend (`frontend/.env`)**
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret

# OAuth Providers
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## 📄 License & Usage Restrictions

This project is developed as a CS50 Web Programming final project and is **shared for evaluation purposes only**. 

**⚠️ IMPORTANT NOTICE:**
- This code is provided exclusively for academic evaluation by CS50 course staff
- **Copying, sharing, or distributing this code is strictly prohibited**
- The code cannot be used as reference material for other CS50 submissions
- All rights reserved by the author

This project demonstrates original work created specifically for CS50 Web Programming capstone requirements and maintains academic integrity standards.

---

- **Created by**: Adan Oliveira
- **Course**: CS50 Web Programming with Python and JavaScript  
- **Year**: 2025

---

> This project demonstrates advanced full-stack development skills by implementing a production-ready news platform with AI integration, modern authentication, and mobile PWA capabilities, exceeding course project scope while meeting all capstone requirements. TypeScript and Next.js are used as modern applications of JavaScript, following contemporary industry practices.