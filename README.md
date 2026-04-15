# DailyBrief

Personalized daily news digests — AI-summarized stories from dozens of sources, grouped by topic, so staying informed takes minutes instead of hours.

<p align="center">
  <!-- Screenshots / demo GIFs to be added -->
  <em>Screenshots and demo video: coming soon.</em>
</p>

## About

DailyBrief is a [CS50W](https://cs50.harvard.edu/web/) capstone — a practice project, but one deliberately aimed at real-app architectural ambition. It's the second project in a self-directed software-engineering track after [BestWish](https://github.com/adanoliveira/bestwish), and a step up from BestWish's single-service Flask app into a multi-service architecture: Django + Next.js + Celery + PostgreSQL with pgvector, multi-stage LLM processing, and a DB-driven AI provider layer.

The use case is concrete: keeping informed on specific topics without reading every article every day. The app ingests articles from RSS feeds and a news API twice a day, runs each article through a four-stage content pipeline (fetch → process → summarise → analyse), clusters related articles into events via vector similarity, and assembles a per-user daily digest from the user's selected topics and publications.

The goal was not a toy — the attention went to the things that separate "works" from "works well": background processing, status-machine-driven restarts, provider abstraction, and cost-aware use of LLMs.

## Tech stack

CS50W requires a Django backend, JavaScript on the frontend, at least one database model, and mobile responsiveness. Everything else was a free choice, explained in the *Why* column.

| Layer | Choice | Why |
| ----- | ------ | --- |
| Backend | Django 5 (modular monolith) | Required by CS50W. Structured as per-domain Django apps (`articles`, `feeds`, `content`, `aiproviders`, `notifications`) rather than one monolithic app, so boundaries are legible. |
| API | Custom decorator layer over Django views (`@api_view`) | Free choice. Lightweight alternative to full DRF viewsets — sufficient for a read-heavy JSON API without the framework overhead. |
| Database | PostgreSQL 15 + pgvector | At least one model was required; Postgres was a free choice over SQLite. pgvector enables 1536-dim embedding similarity for entity deduplication and story clustering in the same database as the domain data. |
| Async pipeline | Celery + Redis, Celery Beat, Flower | Free choice. News ingestion and LLM calls are slow and bursty; running them off the request thread is the only way to keep user-facing reads responsive once real article volume lands. |
| AI providers | OpenAI + Anthropic, routed via a DB-configured `AIProviderConfig` table | Free choice. Operation names (`rbc_compression`, `entity_extraction`, …) map to `(provider, model)` tuples in the DB. Model/provider swaps ship as config changes, not code changes. |
| NLP tooling | spaCy, fasttext (language ID), langdetect, sentence-transformers | Free choice. Cheap free tooling handles language detection and entity canonicalization; LLMs are reserved for work where they measurably outperform heuristics. |
| Frontend | Next.js 15 (App Router) + TypeScript | JavaScript was required; framework choice was free. App Router + Server Components is current-generation React and supports per-route server rendering cleanly. |
| Styling | Tailwind CSS + shadcn/ui | Mobile-responsive was required. shadcn provides a consistent component baseline without pulling in a full design system. |
| Auth | NextAuth (Google OAuth + email magic link) + Prisma adapter | Free choice. Passwordless + OAuth over a self-rolled password flow. Prisma owns the auth-adapter schema; Django owns domain data — the two ORMs don't overlap. |
| Infra | Docker Compose (dev); Railway (backend + workers) + Vercel (frontend) | Free choice. The full stack — Postgres, Redis, Django, Celery worker + Beat, Flower, Next.js — runs locally with one command; deployment is split across the two managed platforms that fit each service best. |

## Architecture

A multi-service monorepo. Django owns the domain data and the async content pipeline; Next.js is a separate service that reads assembled digests over a JSON API. Ingestion is scheduled by Celery Beat; workers run each article through four stages and persist state on the Article row (not in the queue), so the pipeline is restartable mid-flight and stage failures don't cascade.

```
   ┌──────────────────────────┐       schedule
   │  RSS feeds + News API    │◄──── Celery Beat (twice daily)
   └───────────┬──────────────┘
               │ enqueue fetch batch
               ▼
   ┌────────────────────────────────────────────────────────────┐
   │  Content pipeline — Celery workers, 4 stages per article   │
   │                                                             │
   │   Fetch ─► Process ─► Summarise ─► Analyse                  │
   │   raw     cleaned    RBC + headline +    entities, events,  │
   │   HTML    content    abstract + critic   topics, regions    │
   │                      + conditional                           │
   │                      repair                                  │
   └───────────┬────────────────────────────────────┬────────────┘
               │ writes article rows + embeddings   │ LLM calls
               ▼                                     ▼
   ┌──────────────────────────┐      ┌─────────────────────────────┐
   │  PostgreSQL 15 + pgvec   │◄────►│  AIProviderService          │
   │  Article, ArticleSummary │      │  OpenAI / Anthropic,        │
   │  Entity, Event,          │      │  per-operation routing,     │
   │  ArticleEmbedding,       │      │  per-call token + cost log  │
   │  Digest, DigestTopic     │      └─────────────────────────────┘
   └───────────┬──────────────┘
               │
               │ Django REST (JWT-authenticated JSON)
               ▼
   ┌──────────────────────────┐
   │  Next.js 15 (App Router) │
   │  NextAuth + Prisma       │
   │  Per-user daily digest   │
   │  filtered by topic /     │
   │  region / publication    │
   └──────────────────────────┘
```

A separate per-user digest-assembly job runs after the analyse stage completes, groups related articles into events via centroid embeddings in pgvector, and composes the daily digest against the user's saved preferences.

## Key capabilities

- **Runs a four-stage content pipeline driven by status columns on the Article row**, not Celery chains. Each stage queries for articles where the previous stage completed and this stage hasn't started, processes a batch, and updates status + attempts counters. The pipeline is restartable mid-flight, survives worker restarts, and stage failures don't cascade — bad articles fail out after N attempts and the rest of the pipeline keeps moving.
- **Routes every LLM call through a DB-configured provider abstraction**. `AIProviderConfig(operation, provider, model, config)` maps operation names to concrete model tuples. Swapping providers or models is a config update, not a deploy. Every call is persisted to `AIProviderUsage` with token counts, response time, and a cost estimate — observability over LLM spend comes for free.
- **Generates, critiques, and repairs summaries in four LLM calls** per article — rich-bullet compression (temperature 0.3) → skeleton summary (0.25) → faithfulness critique (0.0, deterministic) → conditional repair (0.2). The critic step catches hallucinations and length drift before the summary reaches the digest.
- **Deduplicates entities and clusters stories via pgvector**. Entity dedup is two-tier: canonical-name match first, then 1536-dim vector similarity as fallback. Related articles about the same underlying news event are grouped via centroid embeddings, so the daily digest collapses "5 sites covering the same story" into a single entry.
- **Keeps LLM cost down by mixing free tooling with targeted calls**. Language detection (fasttext + langdetect) and entity canonicalization (spaCy) run as free heuristics; LLM calls happen only at stages where they measurably beat the cheaper approach.
- **Splits frontend and backend into independent services**. Next.js 15 (App Router) handles auth, UI, and per-user routing via Server Components; Django REST handles domain data and the pipeline. NextAuth issues the JWT that bridges them. Either service redeploys independently — the frontend can ship UI fixes without touching the backend and vice versa.
- **Boots the full stack locally with `docker compose up`**. Postgres + pgvector, Redis, Django, Celery worker, Celery Beat, Flower, and Next.js all wired together with health checks. Required secrets fail fast (`${VAR:?…}`); optional API keys degrade gracefully.

## What I learned

- **Multi-service architecture pays for itself the moment anything in the pipeline gets slow.** Background processing isn't optional once an LLM call enters the hot path — users see ingestion lag once per day, never a spinner in the middle of a read.
- **Status machines on the domain row beat Celery chains** for anything that needs to be restartable. A status enum + attempts counter on `Article` survives worker restarts, DB reboots, and mid-stage failures without custom recovery code — the next worker picks up where the last one left off.
- **Provider abstraction earns its keep earlier than expected.** Pricing changes, rate-limit tweaks, and model deprecations all hit within the build window; a DB-driven operation-to-model map made each one a config edit instead of a patch.
- **The gap between "works" and "works well" is timeouts, retries, observability, and cost tracking** — not features. Most of the post-first-pass engineering went into those four concerns, and each one is load-bearing once real content volume is flowing through the pipeline.
- **AI pipelines need an eval harness before they need more features.** Without a way to measure summary faithfulness across prompt edits, every prompt change is a guess. Building the harness is the first thing this repo would need for serious iteration — and it's still a known gap (below).

## Known gaps / next steps

Kept out of scope for the capstone:

- **Not a shipped product.** No real users, no uptime SLA, no billing. The app runs for demonstration and for personal use.
- **Web-first delivery is suboptimal for the use case.** A Chrome new-tab replacement, a morning email, or a WhatsApp push would fit "daily briefing" better than a destination site. The web app was the deliberate choice for CS50W scope and full-stack web practice — in a product version, the delivery channel would change first.
- **No evaluation harness for summary quality.** The critic / repair loop catches obvious faithfulness breaks, but there's no dataset-backed regression eval, so summaries can drift between prompt edits without anything noticing.
- **Test coverage is thin.** Backend contract tests cover the algorithmic processor only; the rest of the pipeline and most of the frontend are untested end-to-end.
- **Email deliverability not fully wired** ([#1](https://github.com/adanoliveira/dailybrief/issues/1)) — domain verification on the transactional sender is still pending.
- **Onboarding polish** ([#4](https://github.com/adanoliveira/dailybrief/issues/4), [#7](https://github.com/adanoliveira/dailybrief/issues/7), [#14](https://github.com/adanoliveira/dailybrief/issues/14)) — publication search needs backend pagination, a few preferences are missing, and margins drift on small screens.
- **Newsfeed UX refinements** ([#8](https://github.com/adanoliveira/dailybrief/issues/8), [#11](https://github.com/adanoliveira/dailybrief/issues/11)) — minor behavioral items on the article and digest pop-over.
- **Frontend state domain decomposition** ([#23](https://github.com/adanoliveira/dailybrief/issues/23)) — the local-state and data-manager modules were structurally split into barrels, but most of the logic still lives in a single file per domain; the per-feature migration is incomplete.

## Running locally

Requires Docker and Docker Compose. The stack boots Postgres + pgvector, Redis, the Django API, Celery worker + Beat, Flower, and the Next.js frontend.

```bash
# 1. Clone
git clone https://github.com/adanoliveira/dailybrief.git
cd dailybrief

# 2. Configure environment
cp .env.example .env
cp frontend/.env.example frontend/.env.local
# then edit .env to fill in at minimum:
#   SECRET_KEY, NEXTAUTH_SECRET, SUPABASE_DB_PASSWORD, DATABASE_URL,
#   GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
#   and one of OPENAI_API_KEY / ANTHROPIC_API_KEY
# news ingestion additionally needs NEWS_API_KEY

# 3. Bring up the stack
docker compose up --build

# 4. First-boot migrations and reference data
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py loaddata \
  apps/feeds/fixtures/production_feeds.json
```

Services after boot:

- Next.js frontend — http://localhost:3000
- Django API — http://localhost:8000/api/
- Flower (Celery monitoring) — http://localhost:5555

If external API keys are missing, the app still boots locally — news ingestion and AI processing features will be unavailable until they are provided.

## License

MIT — see [LICENSE](LICENSE).
