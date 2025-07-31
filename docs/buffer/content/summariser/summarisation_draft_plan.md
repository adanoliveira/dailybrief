# News‑Reader Summariser Service – Detailed Build Plan (v1.0)

> **Scope** – MVP service that receives processed article text, emits a compact JSON summary *(headline, abstract, key facts, opinions, impact)* plus a loss‑less Rich Bullet Compression (RBC) artefact and an embedding for downstream search.  Budget‑friendly (< \$0.0005/article) and ready to iterate.

---

## 1  Context & Position in Pipeline

```
Feed API → Fetcher (raw HTML) → Processor (clean_html, clean_text) 
                                             │
                                             ▼
                                    Summariser Service
                                             │
                                             ├─ article_rbc (JSONB)     – full labelled bullets
                                             ├─ article_summary (JSONB) – end‑user payload
                                             └─ article_embed  (vector) – semantic search key
```

*Downstream*: Digest builder, analysis/graph service, UI article view.

---

## 2  Primary JSON Contracts

### 2.1 Rich Bullet Compression (RBC)

```json
{
  "bullets": [
    "[FACT] …",
    "[QUOTE] …"
  ],
  "rbc_v": 1
}
```

* ≤ 25 bullets labelled `[FACT|STAT|QUOTE|OPINION|CONTEXT]`.

### 2.2 Skeleton Summary (version 2)

```json
{
  "headline": "< 15 words >",
  "abstract": "< ≤60 words >",
  "facts": ["…", "…"],        // 3–6 pivotal facts (verbatim from RBC)
  "opinions": ["Speaker: …"],
  "impact": ["⚡ …"],            // ≤3 bullets
  "summary_v": 2,
  "tokens_in": 0,
  "tokens_out": 0
}
```

---

## 3  Database Schema (PostgreSQL + pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE article_status (
  article_id      BIGINT PRIMARY KEY,
  fetched_at      TIMESTAMPTZ,
  processed_at    TIMESTAMPTZ,
  summarised_at   TIMESTAMPTZ,
  analysed_at     TIMESTAMPTZ
);

CREATE TABLE article_rbc (
  article_id  BIGINT PRIMARY KEY REFERENCES article_status(article_id),
  bullets     JSONB,
  rbc_v       SMALLINT DEFAULT 1,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE article_summary (
  article_id  BIGINT PRIMARY KEY REFERENCES article_status(article_id),
  body        JSONB,
  summary_v   SMALLINT DEFAULT 2,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE article_embed (
  article_id  BIGINT PRIMARY KEY REFERENCES article_status(article_id),
  embed       VECTOR(1536),
  model       TEXT DEFAULT 'text-embedding-4-small',
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ON article_embed USING hnsw (embed vector_l2_ops);
```

---

## 4  Micro‑service Architecture

| Component           | Tech / Key Points                                                    |
| ------------------- | -------------------------------------------------------------------- |
| **FastAPI Gateway** | `/summarise?article_id=` returns Skeleton JSON or 202 if queued.     |
| **Celery Worker**   | Task chain executes prompts & writes DB rows. 1 retry on rate‑limit. |
| **Redis Cache**     | Key `(article_id, summary_v)` avoids double spend. Expire = 30 days. |
| **OpenAI client**   | GPT‑4o‑mini for LLM passes, `text-embedding-4-small` for embeddings. |

Environment vars: `OPENAI_API_KEY`, `PG_DSN`, `REDIS_URL`, `OPENAI_MODEL=gpt-4o-mini`.

---

## 5  Prompt Suite

| Pass                | Trigger                                                        | Model & Params                            | Output               | Notes                                                |
| ------------------- | -------------------------------------------------------------- | ----------------------------------------- | -------------------- | ---------------------------------------------------- |
| **1 RBC**           | `article.clean_text` (≤6 000 chars)                            | `gpt-4o‑mini` – *T=0.3, max\_tokens=256*  | ≤25 labelled bullets | Dense compression keeps \~90 % info.                 |
| **2 Skeleton**      | RBC JSON                                                       | `gpt-4o‑mini` – *T=0.25, max\_tokens=180* | Summary JSON v2      | Facts pulled verbatim from RBC.                      |
| **3 Critic**        | Abstract >60 words **OR** len(facts)<3 **OR** “UNCERTAIN” flag | `gpt-4o‑mini` – *T=0.0, max\_tokens=120*  | `{faithful,…}`       | Light rule‑based pre‑check avoids unnecessary spend. |
| **4 Repair** (opt.) | `faithful=false`                                               | Same model, *T=0.2*                       | Revised summary      | Single retry, else flag `summarise_error`.           |
| **5 Embed**         | Always, after summary commit                                   | `text‑embedding‑4‑small` – 1 536 dims     | vector               | Text = `headline + " - " + abstract`                 |

**Chunking rule** — Articles >6 000 chars: truncate tail *after* last full sentence; long‑form handling slated for v2.0.

---

## 5  Prompt Templates  📜

### 5.1 `rbc_prompt`

```
SYSTEM  You are BulletCompressor‑GPT. Summarise the article into ≤25 compact bullets.
LABEL each bullet: [FACT] [STAT] [QUOTE] [OPINION] [CONTEXT].
RULES  • Keep numbers/names/dates verbatim; one clause per bullet.
       • Output JSON  {"bullets":["[FACT] …"]}
USER    {{ ARTICLE_TEXT }}
```

### 5.2 `skeleton_prompt_v2`

```
SYSTEM  You are NewsDigest‑GPT. Using ONLY the bullets below:
1. Copy 3–6 pivotal [FACT]/[STAT] bullets verbatim into "facts".
2. Write:
   • "headline" ≤15 words
   • "abstract" ≤60 words, neutral tone
   • ≤5 "opinions" bullets  ("Speaker: remark")
   • ≤3 "impact" bullets prefixed ⚡
Return JSON {headline, abstract, facts, opinions, impact}
USER    {{ RBC_JSON }}
```

### 5.3 `critic_prompt`

```
SYSTEM  You are SummaryGuard. Audit draft for hallucinations.
Return JSON {faithful: true|false, issues: []}
CRITERIA  • Every number/date in abstract appears verbatim in facts.
          • Abstract ≤60 words.
USER
SOURCE_BULLETS = {{ RBC_JSON }}
DRAFT = {{ SKELETON_JSON }}
```
If `faithful=false` → feed `issues` + draft back with instruction: *“Revise to fix issues. Keep structure.”*

### 5.4 `repair_prompt`  (only if needed)

```
SYSTEM  Revise the draft to fix issues below. Keep field names & JSON structure.
USER
DRAFT = {{ SKELETON_JSON }}
ISSUES = {{ ISSUES_ARRAY }}
```

---

## 6  Embedding Process  🔍

1. **Text Selection** – combine `headline` and `abstract` (avg ≈ 100 tokens). *Facts* intentionally skipped to keep semantics broad & vector DB small.
2. **Client Call** – `openai.embeddings.create(model="text-embedding-4-small", input=[text])`
3. **Batching** – Celery task batches up to 96 summaries/request; saves \~20 % tokens on shared context window.
4. **Persistence** – Write to `article_embed` table; ON CONFLICT DO UPDATE to allow re‑embedding after model upgrade.
5. **Index** – pgvector HNSW (*m=16, ef\_construction=128*) → 10 M rows fits in 8 GB RAM.
6. **Query Example**  (related‑article card)

```sql
SELECT a2.article_id, s.body->>'headline'
FROM   article_embed      e1
JOIN   article_embed      e2  ON e1.embed <-> e2.embed < 0.22
JOIN   article_summary    s   ON s.article_id = e2.article_id
JOIN   article_status     st  ON st.article_id = e2.article_id
WHERE  e1.article_id = :target
  AND  st.summarised_at > now() - interval '14 days'
ORDER  BY e1.embed <-> e2.embed
LIMIT  5;

7. **Retrain / Re‑index** – When OpenAI ships cheaper/better embedding model, bulk‑re‑embed in chronological shards; concurrent index rebuild per shard.

---


## 7  Pipeline Implementation (Async Chain)

```python
@celery.task
def summarise(article_id: int):
    art = db.fetch_article(article_id)
    text = truncate_at_sentence(art.clean_text, 6000)

    # 1 RBC
    rbc = call_llm("rbc_prompt", text, temp=0.3, max_tokens=256)
    db.upsert("article_rbc", article_id, rbc)

    # 2 Skeleton
    skeleton = call_llm("skeleton_prompt_v2", rbc, temp=0.25, max_tokens=180)

    # 3 Critic / optional repair
    if needs_guard(skeleton):
        guard = call_llm("critic_prompt", rbc, skeleton, temp=0, max_tokens=120)
        if not guard["faithful"]:
            skeleton = call_llm("repair_prompt", skeleton, guard["issues"], temp=0.2, max_tokens=180)

    db.insert("article_summary", article_id, skeleton)
    db.mark_status(article_id, "summarised_at")

    # 4 Embedding (batched by Celery chord)
    vec_text = f"{skeleton['headline']} - {skeleton['abstract']}"
    enqueue_embed(article_id, vec_text)
```

`enqueue_embed` collects up to 96 payloads → single embeddings call.

---

## 7  Cost & Latency Estimates

| Pass              | Avg tokens in/out | \$ per article | p95 latency |
| ----------------- | ----------------- | -------------- | ----------- |
| RBC               | 1 200 / 150       | \$0.00023      | 1.5 s       |
| Skeleton          | 350 / 120         | \$0.00007      | 0.8 s       |
| Critic (20 % hit) | 300 / 80          | \$0.00006      | 0.7 s       |
| **Embedding**     | 100 / 0           | \$0.00002      | 0.2 s       |
| **Total (avg)**   | —                 | **\$0.00038**  | \~2.5 s     |

Budget 10 k articles/day ⇒ ≈ **\$3.80/day** summarisation.

---

## 8  Testing & QA

* **Unit** – Prompt response → `jsonschema` validate, assert ≤60‑word abstract.
* **Golden Set** – 200 manually‑scored articles (RAG‑stored). Check ROUGE‑L ≥ 0.4 vs human summary.
* **Monitoring** – Store `tokens_in/out`, latency, failure rate. Grafana dashboard with cost projection.
* **Fallback** – On JSON parse error → retry prompt with `temperature=0` once, else flag `summarise_error`.

---

## 9  Deployment

* Docker image `summariser:1.0` (uvicorn, gunicorn workers 2×CPU).
* Helm chart with horizontal pod autoscale on >80 % CPU or queue > 100.
* PG & Redis in same VPC; TLS to OpenAI.
* Cron health‑check hits `/summarise?dry_run=1` hourly.

---

## 10  Road‑Map Extensions

| Version | Feature                                              | Benefit                       |
| ------- | ---------------------------------------------------- | ----------------------------- |
| **1.1** | Streaming partial response (headline/abstract first) | Faster UX.                    |
| **1.2** | Local 7‑B model for RBC                              | Drop cost 50 %.               |
| **2.0** | Section‑aware RBC + hierarchical embeddings          | Better recall on long‑form.   |
| **2.x** | Personalised skeleton prompt (user\_focus)           | Higher CTR.                   |
| **3.x** | Multimodal (article + video transcript)              | Podcast/newsletter summaries. |

---

*Document created June 11 2025 – adjust tokens/prices when models or pricing change.*
