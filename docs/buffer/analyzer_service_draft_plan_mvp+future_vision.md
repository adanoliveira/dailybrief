# Article Analyzer Service – MVP Plan (v1.2)

> **Purpose** – Enrich every summarized article with machine-readable labels for topic grouping, entity pages, event linking, region classification, and linguistic analysis. Runs **after** the Summariser; cost target ≤ **US$0.0003/article**.

---

## 1 I/O Contracts

### 1.1 Input (from `article_summary`)

```json
{
  "article_id": 421,
  "headline": "Trump Launches Contest for $TRUMP Meme Coin Holders",
  "abstract": "…",
  "facts": [
    "[FACT] Donald Trump announced a contest for $TRUMP meme coin holders.",
    "[STAT] $TRUMP coin price rose from $11 on May 7 to $31 on May 9."
  ],
  "opinions": ["Trader: …"],
  "impact": ["Concerns about sustainability …"],
  "embed": [0.01, -0.02, …]      // 1 536‑dim OpenAI embedding
}
```

### 1.2 Output Tables

```
article_analysis   – linguistic, region, and quality labels
article_entities   – links to master entities
article_topics     – topic labels
article_event      – link to master events
article_regions    – links to master regions
```

### 1.3 Future Vision

- **Enhanced Input**: Support multi-language articles, richer input formats (e.g., full text, images), and precomputed embeddings from multiple models (e.g., MiniLM, MPNet).
- **Output Expansion**: Include IPTC, IAB, and Reuters taxonomy tags, sentiment, subjectivity, bias, and framing labels. Use JSONB for flexible attribute storage.
- **Knowledge Base Integration**: Link entities and events to external knowledge bases (e.g., Wikidata, Wikipedia) for enriched metadata.
- **Real-Time Processing**: Stream inputs via message queues for near-real-time analysis.

### 1.4 MVP Implementation

- **Input**: Use the current JSON format, ensuring compatibility with the Summariser’s output.
- **Output Tables**: Create `article_analysis` with new fields: `language`, `readability_flesch`, `reading_time_sec`, `style_tone`, `region_primary`, `region`. Add `article_regions` for linking articles to multiple regions.
- **Tools**: Use OpenAI’s GPT-4o-mini for topic classification and region detection to accelerate development. Leverage spaCy for NER and fastText for language detection.
- **Cost Strategy**: Optimize LLM prompts to minimize token usage, use input compression (e.g., truncate abstract to 512 tokens), and fall back to open-source models (e.g., spaCy) where possible.

---

## 2 Master Catalogues & Link Tables

### 2.1 `entities` and `entity_alias`

```sql
CREATE TABLE entities (
  entity_id     BIGSERIAL PRIMARY KEY,
  canonical     TEXT UNIQUE,          -- lower‑case, accent‑stripped
  display_name  TEXT,
  type          TEXT,                 -- PERSON | ORG | GPE | TOKEN …
  wikidata_id   TEXT,
  embed         VECTOR(384)           -- MiniLM sentence embedding
);

CREATE TABLE entity_alias (
  entity_id BIGINT REFERENCES entities,
  alias     TEXT UNIQUE
);
```

### 2.2 `events`

```sql
CREATE TABLE events (
  event_id       BIGSERIAL PRIMARY KEY,
  title          TEXT,
  abstract       TEXT,                 -- generated summary for new events
  facts          TEXT[],               -- key facts from summary
  event_hash     TEXT UNIQUE,          -- SHA‑256 key (first headline + key facts)
  first_seen_at  TIMESTAMPTZ,
  last_seen_at   TIMESTAMPTZ,
  centroid_embed VECTOR(1536),
  article_count  INT DEFAULT 1
);
```

### 2.3 `regions`

```sql
CREATE TABLE regions (
  region_id     BIGSERIAL PRIMARY KEY,
  code          TEXT UNIQUE,          -- ISO-3166-1 code (e.g., US, MX) or 'universal'
  display_name  TEXT
);
```

### 2.4 Link Tables

```sql
CREATE TABLE article_entity (
  article_id BIGINT,
  entity_id  BIGINT
);

CREATE TABLE article_event (
  article_id BIGINT PRIMARY KEY,
  event_id   BIGINT
);

CREATE TABLE event_entity (
  event_id  BIGINT,
  entity_id BIGINT
);

CREATE TABLE article_regions (
  article_id BIGINT,
  region_id  BIGINT
);
```

**Indexes** – HNSW ANN on `entities.embed` and `events.centroid_embed`.

### 2.5 Deduplication Strategy

- **Canonicalisation → Exact match**: Names are lower-cased, accents stripped, corporate suffixes removed (`Ltd`, `Inc`). Ensures `UNIQUE (canonical)` on `entities` catches obvious duplicates.
- **Alias table**: Every alternate spelling or ticker (`$AAPL`) is inserted into `entity_alias`; queries resolve via alias first.
- **Embedding similarity**: If no exact/alias hit, a 384‑dim MiniLM vector is compared via HNSW ANN; distance < 0.10 → existing entity is reused and new alias is stored.
- **Transaction‑safe inserts**: Lookup-or-create wrapped in a single `BEGIN`/`COMMIT`; any race raises `IntegrityError`, triggering a one‑time retry with the new canonical id.
- **Event hash fast path**: Deterministic `SHA-256(headline + top facts)` gives a quick exact dedupe for template rewrites.
- **Semantic merge path**: If hash miss, ANN search on 1 536‑dim embedding against **events in the last 48 h**; accept match when cosine < 0.18 *and* ≥ 2 shared entities.
- **Centroid update**: Matched event’s `centroid_embed` is updated via running mean; `article_count` increments, keeping cluster centroid stable.

These steps run before any insert, guaranteeing that even with concurrent workers the database converges on a single `entity_id`, `event_id`, and `region_id` for each real‑world concept.

### 2.6 Future Vision

- **Knowledge Bases**: Integrate Wikidata and Wikipedia for entity and region metadata enrichment using tools like BLINK or REL.
- **Multi-Taxonomy Support**: Store IPTC, IAB, and Reuters taxonomy mappings in a `taxonomies` table for standardized tagging.
- **Clustering Optimization**: Use FAISS or HDBSCAN for event clustering, incorporating entity-aware embeddings (e.g., Saravanakumar et al., 2021).
- **Scalability**: Implement vector databases (e.g., Milvus) for large-scale similarity search and clustering.

### 2.7 MVP Implementation

- **Schemas**: Use current `entities`, `events`, and link tables. Add `regions` table with ISO-3166-1 codes and `universal` for agnostic articles. Create `article_regions` link table. Extend `events` table with `abstract` and `facts` for new event summaries.
- **Deduplication**: Retain current entity and event deduplication strategies, using spaCy for NER and OpenAI embeddings for events.
- **Regions**: Populate `regions` table with ISO-3166-1 codes (e.g., US, MX) and `universal`. Link articles to regions via `article_regions` using LLM-based geo-NER.
- **Tools**: Use OpenAI’s GPT-4o-mini for region classification and event summaries, spaCy for entity resolution, and fastText for language detection to ensure speed.

---

## 3 Metadata Mixing Board

### 3A Full Attribute Catalogue (future-proof)

| Layer                     | Attribute (column / JSON key)   | Type / Storage         | Example Value                 | Why it matters                                    | Extraction Sketch                                    |
|---------------------------|--------------------------------|------------------------|-------------------------------|--------------------------------------------------|-----------------------------------------------------|
| **0 Provenance**          | `source_domain`                | text                   | `guardian.com`                | Trust & bias scoring                             | crawler → URL parse                                 |
|                           | `canonical_url`                | text (PK)              | …                             | Dedupe key                                       | canonicaliser                                       |
|                           | `paywall`                      | boolean                | `true`                        | Display decision                                 | paywall detector                                    |
|                           | `license`                      | enum                   | `cc-by`                       | Legal display                                    | HTML `<meta>`                                       |
|                           | `published_at`                 | timestamptz            | `2025-06-12 14:05`            | Freshness sorting                                | `<meta property>`                                   |
|                           | `revision_no`                  | int                    | `3`                           | Change tracking                                  | sitemap diff                                        |
| **1 Linguistic**          | `language`                     | ISO-639-1 text         | `en`                          | Locale, TTS                                      | fastText                                            |
|                           | `readability_flesch`           | float 0-100            | `72.1`                        | Accessibility toggle                              | textstat                                            |
|                           | `reading_time_sec`             | int                    | `230`                         | UX progress bar                                  | 200 wpm × word-count                                |
|                           | `style_tone`                   | enum                   | `opinion`                     | Digest tone mix                                  | rule (news vs opinion)                              |
| **2 Entity & Event**      | `entities[]`                   | link tbl → `entities`  | Trump → PERSON                | Person/org pages                                 | spaCy + alias resolver                              |
|                           | `quotes[]`                     | JSONB                  | `{speaker:"Trump",quote:"…"}` | Quote cards                                      | regex + heuristic                                   |
|                           | `event_id`                     | bigint FK              | `1123`                        | Story timeline                                   | resolver (embeddings + overlap)                     |
| **3 Topical**             | `primary_topic`                | text (slug)            | `cryptocurrency`              | Digest section                                   | GPT zero-shot → mapping                             |
|                           | `secondary_topics[]`           | text[]                 | `["us politics"]`             | Search facets                                    | same prompt                                         |
|                           | `free_tags[]`                  | text[]                 | `["reuters__markets"]`        | Flexible filters                                 | rule/regex                                          |
| **4 Contextual Geo**      | `region_primary`               | ISO-3166-1             | `US`                          | Primary geographic focus (UI filters, compliance) | LLM geo-NER on headline + entities or source country |
|                           | `regions[]`                    | ISO-3166-1[]           | `["US","MX"]`                 | List of all countries/regions referenced         | aggregate GPE entities + disambiguation             |
| **5 Quality & Veracity**  | `factuality`                   | float 0-1              | `0.82`                        | Trust weight                                     | heuristics → LLM later                              |
|                           | `subjectivity`                 | float 0-1              | `0.55`                        | Bias dial                                        | sentiment tool                                      |
|                           | `hallucination_risk`           | enum                   | `low`                         | Audit triage                                     | LLM self-critique                                   |
|                           | `structure_score`              | int 0-100              | `87`                          | HTML QA                                          | rule (tags, nesting)                                |
| **6 Sentiment & Emotion** | `sentiment_polarity`           | float -1…1             | `-0.15`                       | Market mood                                      | spacytextblob                                       |
|                           | `emotion`                      | enum                   | `fear`                        | Crisis alerts                                    | emotion model                                       |
| **7 Political Framing**   | `bias_political`               | enum                   | `right`                       | Balanced coverage                                | bias dataset → few-shot LLM                         |
|                           | `framing_devices[]`            | text[]                 | `["populist"]`                | Narrative analytics                              | FramingPOC prompt                                   |
| **8 Engagement Signals**  | `click_ct`                     | int                    | `1321`                        | Re-ranking                                       | analytics ingest                                    |
|                           | `avg_read_time`                | int sec                | `91`                          | Quality feedback                                 | same                                                |
|                           | `shares_social`                | int                    | `54`                          | Virality score                                   | share webhook                                       |
| **9 Relational / Graph**  | `related_articles[]`           | bigint[]               | `[420,418]`                   | Cross-read                                       | ANN on embeddings                                   |
|                           | `cross_source_event_links[]`   | bigint[]               | `[143]`                       | Consensus / variance                              | claim matcher                                       |
|                           | `contradictory_claims[]`       | JSONB                  | `["article x contradicts y"]` | Fact-check surfacing                             | openAI compare-claims                               |

*Taxonomy prefix rule*: `iptc__`, `reuters__`, `iab__`, for house tags.

#### 3A.1 Future Vision

- **Comprehensive Attributes**: Implement all attributes using advanced models (e.g., BERT for sentiment, OpenFraming for framing, SummaC for factuality).
- **Multi-Taxonomy Tagging**: Support IPTC, IAB, and Reuters taxonomies with dedicated fields (e.g., `iptc_topics`, `iab_category`).
- **Granular Analysis**: Use NRCLex for emotion detection, fine-tuned transformers for bias, and hierarchical classification for topics.
- **Quality Metrics**: Develop structure and logic flow scoring using research tools like FactCC and NLI models.

#### 3A.2 MVP Implementation

- **Attributes**: Focus on `source_domain`, `published_at`, `language`, `readability_flesch`, `reading_time_sec`, `style_tone`, `entities`, `primary_topic`, `topics`, `region_primary`, `regions`, `event_hash`, `event_id`.
- **Tools**: Use GPT-4o-mini for topic and region classification, spaCy for NER, fastText for language, textstat for readability, and rule-based heuristics for style tone.
- **Cost**: Optimize LLM prompts to reduce tokens (e.g., use headline + first 3 facts for topics). Use open-source tools for linguistic analysis to minimize costs.

### 3B Initial MVP Subset (cost-minimal)

| Attribute                                   | Layer | Why first                          | Extraction                                | Incremental cost |
|--------------------------------------------|-------|------------------------------------|-------------------------------------------|------------------|
| `language`, `source_domain`, `published_at` | 0, 1  | Mandatory hygiene                  | fastText, crawler                         | **free**         |
| `readability_flesch`                       | 1     | Accessibility toggle                | textstat                                  | **free**         |
| `reading_time_sec`                         | 1     | UX progress bar                    | 200 wpm × word-count                      | **free**         |
| `style_tone`                               | 1     | Digest tone mix                    | rule-based (news vs opinion)              | **free**         |
| `entities`                                 | 2     | Topic & entity pages, event dedupe | spaCy NER + resolver                      | CPU-only         |
| `primary_topic`, `topics` (≤3)             | 3     | Digest sections                    | GPT-4o-mini zero-shot                     | ≈ $0.00014       |
| `region_primary`, `regions[]`              | 4     | Region filters & compliance        | GPT-4o-mini geo-NER + source country      | ≈ $0.00005       |
| `event_hash` + `event_id`                  | 2     | Dedupe & timelines                 | SHA-256 hash + ANN search                 | **free**         |

**Estimated runtime per article**: < 1 s; **average cost** ≈ $0.00019 (driven by GPT-4o-mini calls for topics and regions).

#### 3B.1 Future Vision

- **Expanded Subset**: Include `sentiment_polarity`, `subjectivity`, `factuality`, `bias_political`, and `framing_devices` using transformer models (e.g., DistilBERT, RoBERTa).
- **Cost Optimization**: Fine-tune open-source models (e.g., MiniLM) to replace LLMs, reducing inference costs.
- **Granular Tagging**: Support multi-taxonomy tags and fine-grained region classification.

#### 3B.2 MVP Implementation

- **Attributes**: Implement the updated subset, adding linguistic (`language`, `readability_flesch`, `reading_time_sec`, `style_tone`) and region (`region_primary`, `regions`) fields.
- **Tools**: Use fastText (`lid.176.bin`) for language, textstat for readability, GPT-4o-mini for topics and regions, spaCy for entities, and SHA-256 for event hashes.
- **Prompt Optimization**: Limit GPT input to headline + abstract (truncated to 512 tokens) for cost efficiency.

### 3C Entity Type Taxonomy (v1, mutually exclusive & collectively exhaustive)

| Code              | Label                     | Definition / Scope                                                                                                         | Maps to spaCy / Wikidata         |
|-------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `PERSON`          | Person                    | Individual human beings, or clearly-named multi-person stage names (e.g., *Daft Punk*).                                    | `PERSON`, `Q5`                   |
| `ORGANIZATION`    | Organization              | Companies, NGOs, government agencies, sports teams, universities.                                                          | `ORG`, `Q43229` / `Q79913`       |
| `LOCATION`        | Location                  | Geographical regions, countries, cities, physical landmarks when location is primary identity.                             | `GPE` + `LOC`, `Q2221906`        |
| `FACILITY`        | Facility / Infrastructure | Man-made physical structures: airports, bridges, factories, power plants.                                                  | `FAC`, `Q13226383`               |
| `EVENT`           | Event                     | Named historical or scheduled happenings (elections, conferences, wars, sports tournaments).                               | `EVENT`, `Q1190554`              |
| `WORK`            | Creative Work             | Books, movies, music albums, artworks, software titles.                                                                    | `WORK_OF_ART`, `Q838948`         |
| `PRODUCT`         | Product / Tech            | Consumer goods, devices, vehicles, weapon systems, pharmaceuticals, software products where commercial identity dominates. | subset of `PRODUCT`, `Q2424752`  |
| `FINANCIAL_ASSET` | Financial Asset           | Currencies, stocks, commodities, crypto tokens.                                                                            | (custom), `Q8142`, `Q388`        |
| `LAW`             | Law / Regulation          | Bills, acts, treaties, court cases, constitutions, official resolutions.                                                   | `LAW`, `Q820655`                 |
| `PROGRAM`         | Program / Policy          | Named government or corporate initiatives, missions, schemes (e.g., *Green New Deal*, *Apollo Program*).                   | `PROGRAM` (custom), `Q14204246`  |
| `OTHER`           | Other                     | Entities not fitting above but surfaced by NER; placeholder until taxonomy expansion.                                      | —                                |

*Guidelines*

- Resolver maps spaCy labels → this table; ambiguous cases resolved by keyword rules.
- Each entity receives **exactly one** type; hierarchy collapses fine‑grained spaCy into this 10‑slot set to stay simple yet expressive.

#### 3C.1 Future Vision

- **Expanded Taxonomy**: Include finer-grained types (e.g., `GPE` for geopolitical entities) and support multi-type entities.
- **Coreference Resolution**: Use tools like spaCy’s Coreferee to merge pronouns and aliases, improving deduplication.
- **Knowledge Base Linking**: Map entities to Wikidata/Wikipedia using BLINK or REL for enriched metadata.

#### 3C.2 MVP Implementation

- **Taxonomy**: Use the current 10-slot taxonomy, mapping spaCy labels to types.
- **Tools**: Use spaCy’s `en_core_web_lg` for NER, with rule-based disambiguation for ambiguous cases.
- **Deduplication**: Retain current resolver logic, ensuring unique `entity_id` per real-world concept.

### 3D Linguistic Analysis Attributes

| Attribute             | Type / Storage | Example Value | Why it matters                       | Extraction Sketch                     |
|-----------------------|----------------|---------------|--------------------------------------|---------------------------------------|
| `language`            | ISO-639-1 text | `en`          | Locale, TTS                          | fastText                              |
| `readability_flesch`  | float 0-100    | `72.1`        | Accessibility toggle                  | textstat                              |
| `reading_time_sec`    | int            | `230`         | UX progress bar                      | 200 wpm × word-count                  |
| `style_tone`          | enum           | `factual`     | Digest tone mix                      | GPT-4o-mini zero-shot classification  |

*Style Tone Glossary*: `factual` (objective reporting), `opinion` (editorial or commentary), `narrative` (storytelling or personal experience, without sensationalism), `analytical` (in-depth analysis or forecasting), `satirical` (humorous or ironic), `sensational` (dramatic, emotionally charged, or celebrity-focused with a gossipy or exaggerated tone).

*Cost Note*: `style_tone` classification via GPT-4o-mini incurs an estimated cost of $0.00005/article (based on 512-token input, 20-token output).


#### 3D.1 Future Vision
- **Advanced Metrics**: Calculate lexical diversity, syntactic complexity, and coherence scores.
- **Multi-Language**: Support non-Latin scripts using multilingual models (e.g., LaBSE).
- **Tone Granularity**: Use transformer-based models (e.g., Flair) for fine-grained tone classification.

#### 3D.2 MVP Implementation
- **Attributes**: Implement all listed attributes.
- **Tools**: Use fastText for language, textstat for readability, word count for reading time, and GPT-4o-mini for `style_tone` classification.
- **Prompt**: Design a zero-shot prompt for `style_tone`, using headline + abstract (truncated to 512 tokens) to classify into one of the five styles (see §6).
- **Validation**: Ensure `style_tone` accuracy > 95% via manual spot-checks (see §8).

### 3E Region Classification Attributes

| Attribute         | Type / Storage   | Example Value    | Why it matters                              | Extraction Sketch                            |
|-------------------|------------------|------------------|---------------------------------------------|----------------------------------------------|
| `region_primary`  | ISO-3166-1       | `US`             | Primary geographic focus (UI filters, compliance) | LLM geo-NER + source country                 |
| `regions[]`       | ISO-3166-1[]     | `["US","MX"]`    | List of all countries/regions referenced    | aggregate GPE entities + disambiguation      |

#### 3E.1 Future Vision

- **Granular Regions**: Support sub-national regions (e.g., US-CA for California) and thematic regions (e.g., EU).
- **Automated Disambiguation**: Use REL or BLINK to resolve ambiguous GPEs (e.g., Paris, FR vs. Paris, TX).
- **Geo-Clustering**: Cluster articles by geographic proximity using embeddings.

#### 3E.2 MVP Implementation

- **Attributes**: Implement `region_primary` (ISO-3166-1 or `universal`) and `regions` (list of ISO-3166-1 codes).
- **Tools**: Use GPT-4o-mini for geo-NER, extracting primary region from headline + abstract and all regions from entities.
- **Rules**: Default to `universal` if no clear region is identified; use source country as a fallback for `region_primary`.

---

## 4 Processing Pipeline

| # | Stage                       | Tool / Logic                                                | Key Outputs                    |
|---|-----------------------------|-------------------------------------------------------------|--------------------------------|
| 1 | Language ID                 | fastText `lid.176.bin`                                      | `language`                     |
| 2 | Linguistic Analysis         | textstat, word count, GPT-4o-mini for `style_tone`           | `readability_flesch`, `reading_time_sec`, `style_tone` |
| 3 | Named-entity, ticker regex  | spaCy 3.7 `en_core_web_lg` + `re.findall(r"\$[A-Z]{2,6}")` | raw entities                   |
| 4 | Entity resolve              | lookup-or-create (see §5.1)                                 | canonical `entity_id[]`        |
| 5 | Event extraction            | GPT-4o-mini zero-shot (prompt §5.4)                         | `main_event`, `events[]`       |
| 6 | Geo scope (region)          | GPT-4o-mini geo-NER + source country                        | `region_primary`, `regions`    |
| 7 | Topic classification        | GPT-4o-mini zero-shot (prompt §6)                           | `primary_topic`, `topics[]`    |
| 8 | Event resolve               | event_hash match → else ANN + entity overlap (see §5.2)     | `event_id`                     |
| 9 | Persist                     | insert into all tables                                      | —                              |

**Avg cost**: $0.00029/article (GPT-4o-mini calls for topics, regions, `style_tone`, and event extraction).

### 4.1 Future Vision
- **Advanced Pipeline**: Integrate transformer models (e.g., RoBERTa for topics, DistilBERT for sentiment), coreference resolution (Coreferee), and factuality checks (SummaC, FactCC).
- **Clustering**: Use FAISS and HDBSCAN for event and article clustering, incorporating entity-aware embeddings (e.g., Saravanakumar et al., 2021).
- **Multi-Taxonomy**: Classify IPTC, IAB, and Reuters tags in parallel using fine-tuned models like the Multilingual IPTC News Topic Classifier.
- **Real-Time**: Process articles in streaming mode with asynchronous tasks, leveraging vector databases like Milvus for similarity search.

### 4.2 MVP Implementation
- **Steps**: Implement the simplified 8-step pipeline, focusing on speed with LLMs and open-source tools.
- **Tools**: Use fastText for language detection, textstat for readability scores, spaCy for NER, GPT-4o-mini for topic, region, and `style_tone` classification, and SHA-256/ANN for event resolution.
- **Optimization**: Truncate inputs to 512 tokens for GPT-4o-mini calls to reduce costs, cache embeddings for reuse, and run spaCy on CPU for cost efficiency.
- **Event Extraction**: Use GPT-4o-mini to identify main and secondary events (see §5.4), passing the main event to the resolver.
- **Style Tone**: Use a dedicated GPT-4o-mini prompt for `style_tone` (see §6.3), classifying into one of five mutually exclusive styles.
- **Event Summaries**: For new events, use GPT-4o-mini to generate a summary (title, abstract, facts) and compute its embedding using OpenAI’s API. Store summaries in the `events` table for tracking story evolution.
- **Execution**: Process articles sequentially in a Celery task, ensuring transaction-safe database inserts for deduplication.

---

## 5 Dedup-Safe Lookup-or-Create Algorithms

### 5.1 Entity Resolver

```python
from hashlib import sha256
from scipy.spatial.distance import cosine

MIN_SIM = 0.10  # embedding distance threshold

def canonicalise(name: str) -> str:
    import unidecode, re
    name = unidecode.unidecode(name.lower())
    return re.sub(r"[^\w\s$]", "", name).strip()

def resolve_entity(name: str, ent_type: str) -> int:
    canon = canonicalise(name)

    # 1. exact canonical hit
    row = db.one("SELECT entity_id FROM entities WHERE canonical=%s", canon)
    if row:
        return row.entity_id

    # 2. alias hit
    row = db.one("SELECT entity_id FROM entity_alias WHERE alias=%s", canon)
    if row:
        return row.entity_id

    # 3. embedding similarity
    vec = embed_name(canon)           # MiniLM 384‑dim
    sim = db.one("""
        SELECT entity_id, embed
        FROM entities
        ORDER BY embed <-> %s LIMIT 1""", vec)
    if sim and cosine(sim.embed, vec) < MIN_SIM:
        db.insert_ignore("entity_alias", entity_id=sim.entity_id, alias=canon)
        return sim.entity_id

    # 4. create new
    return db.insert_returning("entities",
        canonical=canon, display_name=name, type=ent_type, embed=vec)
```

### 5.2 Event Resolver

```python
EV_WINDOW_H = 48       # hours considered
EV_SIM      = 0.18     # cosine threshold

def resolve_event(summ: dict, ent_ids: list[int], art_vec: list[float]) -> int:
    facts = summ['facts']
    h_base = (summ['headline'] + (facts[0] if facts else "") + (facts[1] if len(facts)>1 else "")).lower()
    h = sha256(h_base.encode()).hexdigest()[:20]

    row = db.one("SELECT event_id FROM events WHERE event_hash=%s", h)
    if row:
        return row.event_id

    matches = db.all("""
        SELECT event_id, centroid_embed, article_count
        FROM events
        WHERE last_seen_at > now() - interval '%s hours'
        ORDER BY centroid_embed <-> %s LIMIT 3""", (EV_WINDOW_H, art_vec))

    for ev in matches:
        if cosine(ev.centroid_embed, art_vec) < EV_SIM and shared_entities(ev.event_id, ent_ids) >= 2:
            db.exec("""
                UPDATE events
                SET last_seen_at = now(), article_count = article_count+1,
                    centroid_embed = (centroid_embed*article_count + %s)/(article_count+1)
                WHERE event_id = %s""", (art_vec, ev.event_id))
            return ev.event_id

    # Generate summary for new event
    event_summary = gpt_event_summary(summ)
    return db.insert_returning("events",
        title=summ['headline'],
        abstract=event_summary['abstract'],
        facts=event_summary['facts'],
        event_hash=h,
        first_seen_at="now()", last_seen_at="now()",
        centroid_embed=art_vec)
```

### 5.3 Region Resolver

```python
def resolve_region(code: str) -> int:
    # 1. exact code hit
    row = db.one("SELECT region_id FROM regions WHERE code=%s", code)
    if row:
        return row.region_id

    # 2. create new (if not universal or ISO-3166-1)
    return db.insert_returning("regions",
        code=code, display_name=code)
```

### 5.4 Event Extraction Strategy
**Purpose**: Identify events in an article, select the main event, and prepare for deduplication and linking to support story connection.

```python
def extract_events(summ: dict) -> dict:
    # GPT-4o-mini prompt to extract events
    event_data = gpt_extract_events(summ)
    events = event_data['events']
    
    # Select main event based on prominence
    if not events:
        return {'main_event': None, 'events': []}
    
    # Rank by headline mention or frequency
    main_event = max(events, key=lambda e: (
        1 if e['title'].lower() in summ['headline'].lower() else 0,
        len([f for f in summ['facts'] if e['title'].lower() in f.lower()])
    ))
    
    return {
        'main_event': main_event,
        'events': events
    }
```

**GPT Prompt for Event Extraction**:
```plaintext
SYSTEM
You are EventExtractor‑GPT. Identify events mentioned in the article, including a title, brief description, and involved entities. Select up to 3 events, prioritizing the most prominent. Return STRICT JSON:
{
  "events": [
    {
      "title": "event title",
      "description": "brief description",
      "entities": ["entity1", "entity2"]
    }
  ]
}

USER
HEADLINE: {{ headline }}
ABSTRACT: {{ abstract }}
FACTS:
{% for f in facts[:3] %}- {{ f }}
{% endfor %}
```

Params: *temperature 0 · max_tokens 50*.

**Implementation Details**:
- **Event Identification**: GPT-4o-mini processes headline, abstract, and up to 3 facts to extract events as structured JSON, including title, description, and entities.
- **Main Event Selection**: Rank events by:
  1. Presence in headline (highest priority).
  2. Frequency of mention in facts.
  3. If tied, select the first event listed.
- **Deduplication**: Pass the main event to the event resolver (5.2) for SHA-256 hash check or ANN search with entity overlap.
- **Storage**: Store secondary events (if any) in a temporary table for future clustering; only the main event is linked to `article_event`.
- **Cost**: ~$0.00005/article for GPT-4o-mini call (512-token input, 50-token output).
- **Validation**: Ensure at least one event is extracted for > 90% of articles, with manual checks for accuracy (see §8).

### 5.5 Future Vision

- **Advanced Deduplication**: Use FAISS for efficient similarity search, BLINK or REL for entity linking to Wikidata/Wikipedia, and HDBSCAN for dynamic event clustering.
- **Coreference Resolution**: Integrate spaCy’s Coreferee to merge pronouns and aliases, reducing duplicate entities.
- **Region Disambiguation**: Use REL to resolve ambiguous GPEs (e.g., Paris, FR vs. Paris, TX) and support sub-national regions.
- **Event Clustering**: Incorporate entity-aware contextual embeddings (Saravanakumar et al., 2021) for improved event similarity detection.
- **Event Extraction**: Use fine-tuned transformers (e.g., T5) for event extraction, supporting multi-language and granular event types.

### 5.6 MVP Implementation

- **Algorithms**: Use existing entity and event resolvers, with added region resolver for ISO-3166-1 codes or `universal`.
- **Tools**: Leverage spaCy for entity resolution, OpenAI embeddings for event clustering, GPT-4o-mini for event extraction and summaries, and direct SQL lookups for regions.
- **Event Extraction**: Use GPT-4o-mini to identify and rank events, selecting the main event for resolution.
- **Event Summaries**: For new events, generate summaries (title, abstract, facts) using GPT-4o-mini, storing them in the `events` table to support story tracking.
- **Optimization**: Cache embeddings to avoid recomputation, use transaction-safe inserts to handle concurrent workers.

---

## 6 GPT Prompt – Topic Classifier

```plaintext
SYSTEM
You are TopicTagger‑GPT. Choose **one primary topic** and up to **three secondary topics** from the list:
cryptocurrency | us politics | markets | tech | ai | healthcare | climate | sports | entertainment | world

Return STRICT JSON: {"primary_topic":"topic1","topics":["topic2","topic3"]}

USER
HEADLINE: {{ headline }}
ABSTRACT: {{ abstract }}
FACTS:
{% for f in facts[:3] %}- {{ f }}
{% endfor %}
```

Params: *temperature 0 · max_tokens 40*.

### 6.1 Future Vision
- **Multi-Taxonomy**: Extend prompt to classify IPTC, IAB, and Reuters taxonomies in parallel using zero-shot or fine-tuned models (e.g., Multilingual IPTC News Topic Classifier).
- **Zero-Shot**: Leverage models like XNLI or fine-tuned BART for custom taxonomies without training data.
- **Hierarchical Classification**: Predict top-level and sub-level topics using hierarchical models, mapping to IPTC’s 1,200 categories.
- **Cost Efficiency**: Replace LLM with fine-tuned open-source models (e.g., MiniLM) for production.

### 6.2 MVP Implementation
- **Prompt**: Use the updated prompt, focusing on 10 in-house topics (cryptocurrency, us politics, etc.).
- **Tools**: Use GPT-4o-mini for zero-shot classification, truncating abstract to 512 tokens to minimize costs.
- **Output**: Store `primary_topic` in `article_analysis` and `topics` in `article_topics` table.
- **Validation**: Ensure at least one topic is assigned per article, with alerts for topic-empty cases (see §8).

### 6.3 GPT Prompt – Style Tone Classifier

```plaintext
SYSTEM
You are StyleToneTagger‑GPT. Choose **one style tone** from the list:
factual | opinion | narrative | analytical | satirical | sensational

Return STRICT JSON: {"style_tone":"style"}

USER
HEADLINE: {{ headline }}
ABSTRACT: {{ abstract }}
FACTS:
{% for f in facts[:3] %}- {{ f }}
{% endfor %}
```

Params: *temperature 0 · max_tokens 20*.

### 6.4 Future Vision
- **Granular Classification**: Use fine-tuned transformers (e.g., Flair, RoBERTa) for nuanced tone detection, supporting multi-label tones if needed.
- **Multi-Language**: Extend to non-Latin scripts using multilingual models (e.g., LaBSE).
- **Contextual Analysis**: Incorporate full article text or quotes for improved accuracy.

### 6.5 MVP Implementation
- **Prompt**: Use the style tone prompt, classifying into one of six mutually exclusive styles.
- **Tools**: Use GPT-4o-mini, truncating input to 512 tokens for cost efficiency.
- **Output**: Store `style_tone` in `article_analysis` table.
- **Validation**: Ensure `style_tone` is assigned for all articles, with accuracy > 95% via manual checks (see §8).

---

## 7 Analyzer Celery Task (simplified)

```python
@celery.task
def analyze(article_id: int):
    summ, art_vec = db.get_summary_embed(article_id)

    # Language gate
    lang = fasttext_lang(summ['headline'] + " " + summ['abstract'])
    if lang != 'en':
        return

    # Linguistic analysis
    text = summ['headline'] + " " + summ['abstract']
    readability = textstat.flesch_reading_ease(text)
    word_count = len(text.split())
    reading_time = word_count * 60 / 200  # 200 wpm
    style_tone = gpt_style_tone(summ)  # GPT-4o-mini zero-shot classification

    # Entities
    ents_raw = extract_entities(text)
    ent_ids = [resolve_entity(name, typ) for name, typ in ents_raw]
    db.bulk_insert("article_entity", [(article_id, e) for e in ent_ids])

    # Event extraction
    event_data = extract_events(summ)
    main_event = event_data['main_event']
    if not main_event:
        return  # Skip if no event identified

    # Regions
    region_data = gpt_regions(summ)
    region_primary = region_data['region_primary']
    regions = region_data['regions']
    region_ids = [resolve_region(code) for code in regions]
    db.bulk_insert("article_regions", [(article_id, r) for r in region_ids])

    # Topics
    topic_data = gpt_topics(summ)
    primary_topic = topic_data['primary_topic']
    topics = topic_data['topics']
    db.bulk_insert("article_topics", [(article_id, t) for t in [primary_topic] + topics])

    # Event resolution
    ev_id = resolve_event(main_event, ent_ids, art_vec)
    db.insert("article_event", article_id=article_id, event_id=ev_id)

    # Persist
    db.insert("article_analysis",
              article_id=article_id,
              language=lang,
              readability_flesch=readability,
              reading_time_sec=reading_time,
              style_tone=style_tone,
              region_primary=region_primary,
              primary_topic=primary_topic,
              event_hash=hash_event(main_event),
              analyzer_v="1.2")
```

### 7.1 Future Vision
- **Asynchronous Processing**: Run heavy tasks (e.g., bias detection, clustering) asynchronously using Celery queues.
- **Batch Optimization**: Process articles in batches to reduce LLM and database overhead, leveraging FAISS for similarity search.
- **Model Integration**: Replace GPT-4o-mini with fine-tuned transformers (e.g., DistilBERT, MiniLM) for all tasks, minimizing LLM dependency.
- **Monitoring**: Integrate real-time metrics for pipeline performance, using tools like Prometheus.

### 7.2 MVP Implementation
- **Task**: Implement the task, handling linguistic, region, topic, entity, and event attributes, with new event extraction step.
- **Tools**: Use GPT-4o-mini for regions, topics, `style_tone`, event extraction, and summaries; spaCy for entities; fastText for language; textstat for readability.
- **Optimization**: Cache embeddings, truncate GPT inputs to 512 tokens, reuse database connections.
- **Event Extraction**: Extract main and secondary events using GPT-4o-mini (see §5.4), resolve main event.
- **Style Tone**: Use GPT-4o-mini prompt to classify into one of six styles.
- **Error Handling**: Log failures and retry up to 3 times with exponential backoff.

---

## 8 QA & Monitoring

- **Entity dedupe ratio**: `COUNT(DISTINCT canonical) / COUNT(*)` (aim > 0.95).
- **Event singleton share**: `SUM(article_count=1) / COUNT(*)` daily (< 40%).
- **Topic-empty rate**: Alert if > 5% articles return no `primary_topic`.
- **Region-empty rate**: Alert if > 10% articles have no `region_primary`.
- **Language accuracy**: Manual spot-checks on 100 articles/week to ensure fastText accuracy (> 98%).
- **Style tone accuracy**: Manual validation of 50 articles/week to verify GPT-4o-mini `style_tone` classification, including `sensational` style, (> 95%).

### 8.1 Future Vision
- **Comprehensive Metrics**: Monitor sentiment, subjectivity, bias, and factuality accuracy using datasets like AllSides and Media Frames Corpus.
- **Automated Alerts**: Use anomaly detection to flag pipeline failures (e.g., high hallucination risk, low factuality scores).
- **User Feedback**: Incorporate engagement signals (e.g., `click_ct`, `avg_read_time`) to validate metadata quality.
- **Factuality Checks**: Implement SummaC or FactCC to verify summary consistency in production.

### 8.2 MVP Implementation
- **Metrics**: Implement all listed metrics, with automated SQL queries for dedupe ratio, singleton share, topic-empty, and region-empty rates.
- **Tools**: Use PostgreSQL for metric calculations, manual spot-checks for language and `style_tone` accuracy.
- **Alerts**: Set up threshold-based alerts via email/Slack for topic-empty (> 5%) and region-empty (> 10%) rates.
- **Validation**: Conduct weekly manual checks to ensure GPT-4o-mini `style_tone` outputs, including `sensational`, align with article content (> 95% accuracy).

---

## 
## 9 Roadmap

- **1.1** – Add linguistic (`language`, `readability_flesch`, `reading_time_sec`, `style_tone`) and region (`region_primary`, `regions`) classification using GPT-4o-mini (Q3 2025).
- **1.2** – Implement event extraction and summary generation using GPT-4o-mini (Q4 2025).
- **1.3** – Replace GPT-4o-mini with fine-tuned open-source models (e.g., MiniLM, DistilBERT) for topics, regions, `style_tone`, and event extraction (Q1 2026).
- **2.0** – Add sentiment (`sentiment_polarity`, `emotion`), subjectivity, factuality, bias, and framing analysis using transformer models (Q2 2026).
- **2.1** – Support IPTC, IAB, and Reuters taxonomies with dedicated fields and fine-tuned models (Q3 2026).
- **2.2** – Implement graph-based relationships for filtering, search, recommendation, and story coverage using Neo4j or Milvus (Q4 2026).
- **2.3** – Develop timeline UI and entity reports powered by `events`, `event_entity`, and graph connections (Q1 2027).

### 9.1 Future Vision
- **Advanced Analytics**: Integrate sentiment, subjectivity, bias, and framing using transformer models and datasets like AllSides, Media Frames Corpus, and FEVER.
- **Scalability**: Deploy vector databases (e.g., Milvus) and streaming pipelines for real-time processing.
- **Quality Assurance**: Use SummaC and FactCC for summary factuality checks, OpenFraming for framing detection.
- **Multi-Language**: Support non-Latin scripts and multilingual taxonomies using models like LaBSE.
- **Graph-Based Enhancements**: Build knowledge graphs for entities, events, and articles to enable advanced filtering, recommendation, and story clustering (see §10).

### 9.2 MVP Implementation
- **Priorities**: Deliver v1.1 with linguistic, region, topic, entity, and event analysis by Q3 2025, including event extraction by Q4 2025.
- **Timeline**: Complete model replacement by Q1 2026, plan graph enhancements for Q4 2026.
- **Evolution**: Lay foundation for post-MVP enhancements (sentiment, bias, factuality, graphs) in v2.0.

---

## 10 Graph-Based Relationships and News Consumption

### 10.1 Future Vision
- **Graph Structure**: Model entities, events, and articles as nodes in a knowledge graph, with edges representing relationships (e.g., entity-in-event, article-covers-event, entity-mentions-entity). Use graph databases (e.g., Neo4j) or vector databases (e.g., Milvus) for storage and querying.
- **Applications**:
  - **Filtering**: Enable users to filter news by entity (e.g., “Tesla”), event (e.g., “2024 election”), or topic, using graph traversal to retrieve related articles.
  - **Search**: Support graph-based search for articles connected by entities or events, improving relevance (e.g., “Trump’s recent speeches”).
  - **Recommendation**: Suggest articles based on user interests, leveraging graph-based collaborative filtering (e.g., “Users who read about X also read Y”) and engagement signals (`click_ct`, `avg_read_time`).
  - **Clustering**: Group articles into story clusters using FAISS or HDBSCAN, with entity and event overlap as features, to present comprehensive story timelines (e.g., “Presidential election coverage”).
  - **Entity Reports**: Generate dynamic summaries of entity activities (e.g., “Elon Musk’s recent news”) by aggregating related events and articles.
  - **Story Coverage**: Provide holistic views of major stories by connecting all articles linked to an event, ensuring diverse perspectives (e.g., Reuters vs. BBC on elections).
- **Implementation Ideas**:
  - Use entity-aware embeddings (Saravanakumar et al., 2021) for graph node representations.
  - Implement graph algorithms (e.g., PageRank, community detection) to identify influential entities or events.
  - Integrate engagement data to personalize recommendations and prioritize high-impact stories.
  - Support real-time updates with streaming pipelines and vector search for new articles.
- **Benefits**: Enhance user engagement by delivering relevant, interconnected news content, uncovering unexpected connections (e.g., linking a corporate merger to a political event), and providing comprehensive story coverage.

### 10.2 MVP Implementation
- **Foundation**: Current MVP lays the groundwork with `entities`, `events`, `article_entity`, `article_event`, and `event_entity` tables, enabling basic relationship tracking.
- **Next Steps**: Store secondary events from event extraction (see §5.4) in a temporary table to support future graph development.
- **Evolution**: Plan for graph database integration in v2.2 (Q4 2026), starting with basic entity-event-article connections.

---