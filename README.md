# DailyBrief

Personalized daily news digests — AI-summarized stories from dozens of sources, grouped by topic, so staying informed takes minutes instead of hours.

<p align="center">
  <!-- Screenshots / demo GIFs to be added -->
  <em>Screenshots and demo video: coming soon.</em>
</p>

## About

DailyBrief is a practice project — the second in a self-directed software-engineering track after [BestWish](https://github.com/adanoliveira/bestwish), and the one that also served as a [CS50W](https://cs50.harvard.edu/web/) capstone submission. The app ingests articles from RSS feeds and a news API, runs each one through a four-stage AI pipeline (fetch → process → summarise → analyse), clusters related stories via pgvector similarity, and assembles a per-user daily digest from selected topics and publications.

Architecturally it's a deliberate step up from BestWish's single-service Flask app: Django + Next.js + Celery, PostgreSQL with pgvector, multi-stage LLM processing, a DB-driven provider layer, and a containerized dev + split-deploy setup.

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

Mostly about the jump from BestWish's single-service Flask app to a multi-service system — how the new moving parts fit together, and what gets harder once they are wired.

- **Docker Compose for a full local stack.** Postgres, Redis, Django, Celery worker + Beat, Flower, and Next.js all booting with a single command. Services declaring their dependencies and health checks properly is the difference between "sometimes works" and "always works."
- **Modular monolith.** Per-domain Django apps (`articles`, `feeds`, `content`, `aiproviders`, `notifications`) instead of one big app — a simple shape to start with that also keeps the option to split services later.
- **Background work with Celery.** Queues, Beat schedules, worker pools, soft and hard time limits, retries, Flower for monitoring. Moving slow work off the request thread is the easy part; making it restartable and observable is the rest.
- **Multi-stage AI pipelines.** Beyond a single LLM call — chaining fetch → process → summarise → analyse, adding a critic step, generating embeddings, clustering related articles via pgvector. Each stage is fine in isolation; running them in sequence is where cost and failure modes show up.
- **Modern frontend with Next.js App Router.** Server Components, file-based routing, per-route loading states, and client-side data caching with stale-while-revalidate. Better UX and perceived performance than BestWish's Jinja + vanilla JS.
- **Split deployment.** Railway for Django + workers, Vercel for the Next.js frontend. Two deploy targets, two sets of environment variables, cross-origin auth via JWT — more pieces than Vercel-only, also closer to how real systems are deployed.
- **A design system on top of Tailwind.** shadcn/ui primitives gave the UI consistency without owning a full design system — noticeably cleaner visually than BestWish's Bootstrap baseline.
- **"Works" and "works well" are different milestones.** The first-pass version runs, but observability, retry semantics, deployment hardening, eval coverage, and UI edge cases all need their own iteration after the happy path lights up.

Overall: built and deployed a meaningfully more complex system than BestWish, with more fluency across the stack and a much clearer sense of the rough edges that are still open (see below).

## Known gaps

Kept out of scope for this project:

- **Not a shipped product.** No real users, no uptime SLA, no billing.
- **Web-first delivery is suboptimal for the use case.** A Chrome new-tab replacement, a morning email, or a WhatsApp push would fit "daily briefing" better than a destination site.
- **No evaluation harness for summary quality.** The critic / repair loop catches obvious breaks, but there's no dataset-backed regression eval, so summaries can drift silently.
- **Test coverage is thin.** Contract tests cover the algorithmic processor only; the rest of the pipeline and most of the frontend are untested end-to-end.
- **Email deliverability not fully wired** ([#1](https://github.com/adanoliveira/dailybrief/issues/1)).
- **Onboarding polish** ([#4](https://github.com/adanoliveira/dailybrief/issues/4), [#7](https://github.com/adanoliveira/dailybrief/issues/7), [#14](https://github.com/adanoliveira/dailybrief/issues/14)).
- **Newsfeed UX refinements** ([#8](https://github.com/adanoliveira/dailybrief/issues/8), [#11](https://github.com/adanoliveira/dailybrief/issues/11)).
- **Frontend state domain decomposition** ([#23](https://github.com/adanoliveira/dailybrief/issues/23)).

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
