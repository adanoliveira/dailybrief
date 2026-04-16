# DailyBrief

Personalized daily news digests — AI-summarized stories from dozens of sources, grouped by topic, so staying informed takes minutes instead of hours.

<p align="center">
  <!-- Demo GIFs: replace with actual paths when available -->
  <em>Demo GIFs coming soon.</em>
</p>

**Live:** [dailybrief.press](https://dailybrief.press)

## About

DailyBrief is a practice project — the second in a self-directed software-engineering track after [BestWish](https://github.com/adanoliveira/bestwish), and a [CS50W](https://cs50.harvard.edu/web/) capstone submission.

Users pick topics and publications they care about; the app ingests articles twice a day, summarizes each one with AI, clusters related coverage into single stories, and delivers a personalized daily digest. Staying up to date takes minutes instead of hours.

Architecturally a deliberate step up from BestWish's single-service Flask app: a multi-service system with background processing, a multi-stage AI pipeline, and a modern frontend. The stack, architecture, and design choices are broken down in the sections below.

## Tech stack

| Layer | Choice |
| ----- | ------ |
| Backend | Django 5, modular monolith with per-domain apps *(capstone required: Django + ≥1 model)* |
| API | Custom `@api_view` decorator layer over Django views |
| Database | PostgreSQL 15 + pgvector |
| Async pipeline | Celery + Redis, Celery Beat, Flower |
| AI providers | OpenAI + Anthropic, routed via a DB-configured `AIProviderConfig` table |
| NLP tooling | spaCy, fasttext (language ID), langdetect, sentence-transformers |
| Frontend | Next.js 15 (App Router) + TypeScript *(capstone required: JavaScript frontend, mobile-responsive)* |
| Styling | Tailwind CSS + shadcn/ui |
| Auth | NextAuth (Google OAuth + email magic link) + Prisma adapter |
| Infra | Docker Compose (dev); Railway (backend + workers) + Vercel (frontend) |

## Architecture

A multi-service monorepo. Django owns the domain data and the async content pipeline; Next.js is a separate service that reads assembled digests over a JSON API. Ingestion is scheduled by Celery Beat; workers run each article through four stages and persist state on the Article row, so the pipeline is restartable and stage failures don't cascade.

```
   ┌──────────────────────────┐       schedule
   │  RSS feeds + News API    │◄──── Celery Beat (twice daily)
   └───────────┬──────────────┘
               │ enqueue fetch batch
               ▼
   ┌────────────────────────────────────────────────────────────┐
   │  Content pipeline — Celery workers, 4 stages per article   │
   │                                                            │
   │   Fetch ─► Process ─► Summarise ─► Analyse                 │
   │   raw     cleaned    RBC + headline +    entities, events, │
   │   HTML    content    abstract + critic   topics, regions   │
   │                      + conditional                         │
   │                      repair                                │
   └───────────┬────────────────────────────────────┬───────────┘
               │ writes rows + embeddings           │ LLM calls
               ▼                                     ▼
   ┌──────────────────────────┐      ┌─────────────────────────────┐
   │  PostgreSQL 15 + pgvec   │◄────►│  AIProviderService          │
   │  Article, ArticleSummary │      │  OpenAI / Anthropic,        │
   │  Entity, Event,          │      │  per-operation routing,     │
   │  ArticleEmbedding,       │      │  per-call token + cost log  │
   │  Digest, DigestTopic     │      └─────────────────────────────┘
   └───────────┬──────────────┘
               │ Django REST (JWT)
               ▼
   ┌──────────────────────────┐
   │  Next.js 15 (App Router) │
   │  NextAuth + Prisma       │
   │  Per-user daily digest   │
   └──────────────────────────┘
```

A separate per-user digest-assembly job runs after analyse, groups related articles into events via centroid embeddings, and composes the digest against the user's saved preferences.

## Key capabilities

- **Four-stage content pipeline.** Fetch → process → summarise → analyse, one article at a time. State lives on the Article row (status enum + attempts counter), not in Celery chains — the pipeline is restartable and stage failures don't cascade.
- **DB-configured LLM provider abstraction.** `AIProviderConfig` maps operation names to `(provider, model)` tuples. Swapping providers or models is a config update, not a deploy. Every call logs tokens and cost to `AIProviderUsage`.
- **Summarise → critique → repair.** Four LLM calls per article: rich-bullet compression, skeleton summary, faithfulness critique at temperature 0.0, conditional repair. The critic catches length drift and hallucination before the digest is assembled.
- **Entity dedup and story clustering via pgvector.** Canonical-name match first, 1536-dim vector similarity as fallback. Articles covering the same underlying event are grouped via centroid embeddings, so the digest collapses "5 sites covering the same story" into one entry.
- **Independent frontend and backend services.** Next.js 15 handles auth, UI, and per-user routing; Django REST handles domain data and the pipeline. NextAuth JWT bridges the two. Either service redeploys independently.

## What I learned

Working fluency with a modern web stack that could serve as a starting architecture for real products — relatively simple setups, each chosen for concrete benefits.

- **Modular monolith backend.** Per-domain Django apps (`articles`, `feeds`, `content`, `aiproviders`, `notifications`). Keeps each domain's models, views, and logic isolated; makes it easier to reason about changes, test in isolation, and split into separate services later if needed.
- **Modern frontend with Next.js App Router.** Server Components, file-based routing, per-route loading states, client-side data caching with stale-while-revalidate. Pages load faster, navigation feels instant, the server handles heavy rendering so the client stays light, and the result is an app-like experience — smooth transitions, no full-page reloads, responsive on mobile and desktop.
- **Background processing with Celery.** Long-running work (API calls, LLM inference, content fetching) runs off the request thread, so users never wait on slow operations. Beat handles scheduling, workers handle retries and timeouts, Flower provides visibility into what's running and what failed.
- **Docker Compose for local development.** The full stack (Postgres, Redis, Django, Celery worker + Beat, Flower, Next.js) boots with a single command. New contributors get a working environment without installing services individually, and the setup is consistent across machines.
- **Multi-stage AI pipelines.** Instead of a single LLM call per article, a four-stage pipeline (fetch → process → summarise → analyse) with a critique-and-repair step and vector-based story clustering. Each stage adds structure — summaries are checked for faithfulness, related articles are grouped, entities are deduplicated — so the final digest is more useful and less noisy than raw model output.
- **Design system with Tailwind + shadcn/ui.** Reusable component primitives that keep the UI consistent without building a full design system from scratch. Faster to build new views, easier to maintain visual coherence across pages.

## Known gaps

The goal was a lean proof of concept with good UX and a solid base for expansion — not full coverage. The natural form factor for a daily digest is a native mobile app with push notifications, plus delivery through channels users already check (WhatsApp, email). Starting with web was a deliberate trade-off — faster to build, enough to exercise a full modern web stack, and usable as a CS50W capstone submission — the priority was practice and validation of the core experience, not platform coverage. The realistic progression from there: PWA as an installable, offline-capable intermediate step, then native if engagement justified the investment. News currently comes from a news aggregation API, chosen for initial velocity and simplicity; RSS integration, which is more complex, was pushed to the backlog. The original vision also included content sources beyond news outlets — podcasts, blogs, Substacks, X feeds, YouTube — so users could get a unified summary of everything they follow. That scope was deferred to keep the first version focused and shippable. Test coverage and summary quality evaluation are also thin and would need investment before serious iteration.

## Running locally

Requires Docker and Docker Compose.

```bash
# 1. Clone
git clone https://github.com/adanoliveira/dailybrief.git
cd dailybrief

# 2. Configure environment
cp .env.example .env
cp frontend/.env.example frontend/.env.local
# then fill in SECRET_KEY, NEXTAUTH_SECRET, SUPABASE_DB_PASSWORD, DATABASE_URL,
# GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and one of
# OPENAI_API_KEY / ANTHROPIC_API_KEY (news ingestion also needs NEWS_API_KEY)

# 3. Bring up the stack
docker compose up --build

# 4. First-boot migrations and reference data
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py loaddata \
  apps/feeds/fixtures/production_feeds.json
```

Services:
- Next.js — http://localhost:3000
- Django API — http://localhost:8000/api/
- Flower — http://localhost:5555

If external API keys are missing, the app still boots locally — news ingestion and AI features will be unavailable until they are provided.

## License

MIT — see [LICENSE](LICENSE).
