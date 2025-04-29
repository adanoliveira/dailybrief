# DailyBrief - RSS Digest

An AI-powered news reader that makes getting informed easier with article summaries and a daily digest of yesterday's news.

## 📱 Features

- **Personalized News Feed**: Select your preferred topics, publications, and regions
- **AI Summaries**: Get the gist of each article without reading the whole thing
- **Daily Digest**: Receive a consolidated summary of yesterday's important stories
- **Multi-lingual Support**: Read news in your preferred languages
- **PWA Support**: Install on your device for a native-like experience

## 🛠️ Tech Stack

- **Backend**: Django 5 REST API with modular monolith architecture
- **Frontend**: Next.js 15 with App Router, React 19, and shadcn/ui
- **Database**: PostgreSQL (via Supabase in production)
- **Authentication**: NextAuth.js with Google, Apple, and Email magic links
- **Task Processing**: Celery with Redis
- **AI Integration**: OpenAI and Anthropic for summaries and digests

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/adanoliveira/dailybrief.git
   cd dailybrief
   ```

2. Start the application with Docker:
   ```bash
   ./docker.sh up
   ```

3. Visit the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🧰 Development

The project includes a helper script `docker.sh` for common operations:

- **Start all services**: `./docker.sh up`
- **Stop all services**: `./docker.sh down`
- **Rebuild services**: `./docker.sh build`
- **View logs**: `./docker.sh logs`
- **Run Django commands**: `./docker.sh django <command>`
- **Run database migrations**: `./docker.sh migrate`
- **Install npm packages**: `./docker.sh npm install <package>`

## 📝 Project Structure

```
dailybrief/
├── backend/                 # Django backend
│   ├── dailybrief/          # Project settings
│   ├── apps/                # Modular applications
│   │   ├── accounts/        # User management
│   │   ├── feeds/           # RSS/News fetching
│   │   ├── articles/        # Article storage
│   │   ├── digest/          # Daily digest generation
│   │   ├── summariser/      # Article summarization
│   │   ├── newsapi/         # News API integration
│   │   ├── aiproviders/     # AI model providers
│   │   └── notifications/   # User notifications
│   └── requirements.txt     # Python dependencies
├── frontend/                # Next.js frontend
│   ├── src/                 # Source code
│   │   ├── app/             # Next.js App Router
│   │   ├── components/      # React components
│   │   └── lib/             # Utility functions
│   └── tailwind.brand.ts    # Brand colors
├── infra/                   # Infrastructure files
│   └── celery_worker.sh     # Celery worker script
├── docker-compose.yml       # Docker Compose configuration
└── docker.sh                # Docker helper script
```

## 🔄 Workflow

1. News is fetched hourly from News API
2. Articles are stored in the database
3. AI summarizes articles asynchronously
4. Daily, a digest of yesterday's news is generated
5. Users can browse their personalized feed and digests