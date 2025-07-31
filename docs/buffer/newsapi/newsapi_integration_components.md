
# NewsAPI Integration Components

## 1. NewsAPIService (newsapi_service.py)

This is the core API client that interacts directly with the NewsAPI. 

**Key responsibilities:**
- Initializes and manages the NewsAPI client with API keys
- Provides methods to fetch data from different NewsAPI endpoints
- Tracks API requests in the database for monitoring usage and rate limits

**Main endpoints called:**
1. `/v2/everything` - Accessed via `get_everything()`: Returns articles from a wide variety of sources
2. `/v2/top-headlines` - Accessed via `get_top_headlines()`: Returns breaking news headlines
3. `/v2/top-headlines/sources` - Accessed via `get_sources()`: Returns available news sources

**Helper methods:**
- `fetch_articles_by_date_range()`: Queries the `/everything` endpoint with date filters
- `fetch_recent_articles()`: Gets articles published in the last X hours

**Parameters used:**
- Date filters: `from_param`, `to` (formatted as YYYY-MM-DD)
- Source filters: `sources` (comma-separated source IDs)
- Location filters: `country` (country code)
- Category filters: `category` (e.g., business, technology)
- Language filters: `language` (e.g., en)
- Query filters: `q` (search query)

## 2. ArticleProcessor (article_processor.py)

This service transforms NewsAPI response data into our domain models.

**Key responsibilities:**
- Maps NewsAPI sources to our Publication model
- Creates/updates Article and NewsAPIArticle models
- Calculates article metrics (word count, read time, etc.)
- Extracts keywords and content hash for deduplication

**Flow of article processing:**
1. `process_articles()`: Processes a batch of articles from a NewsAPI response
2. `_get_or_create_article()`: Checks if article already exists or creates new one
3. `_create_article_pair()`: Creates both an Article (domain model) and NewsAPIArticle (API-specific data)
4. `_calculate_content_metrics()`: Computes metrics like word count and extracts keywords

**Key article mappings:**
- NewsAPI article → Article (domain model) + NewsAPIArticle (API-specific data)
- Source ID → Publication
- Language code → Language
- NewsAPI article content → Enhanced with metrics and keywords

## 3. SyncManager (sync_manager.py)

This orchestrates the entire synchronization process.

**Key responsibilities:**
- Coordinates between NewsAPIService and ArticleProcessor
- Manages different sync strategies (backfill, recent, top headlines, by publication)
- Tracks sync operations in SyncLog model
- Handles error recovery and reporting

**Main sync operations:**
1. `backfill_articles()`: Fetches historical articles from the past X days
2. `sync_recent_articles()`: Fetches articles published in the last X hours
3. `sync_top_headlines()`: Fetches current breaking news headlines
4. `sync_everything_by_publication()`: Fetches recent articles from specific publications

Each operation:
- Creates a SyncLog entry
- Calls the appropriate NewsAPIService methods
- Passes data to ArticleProcessor
- Updates the SyncLog with results

## 4. Backfill Command (backfill_articles.py)

This Django management command provides a CLI for backfilling articles.

**Key responsibilities:**
- Accepts command-line arguments for customizing the backfill
- Shows recent sync history
- Invokes the SyncManager to perform the backfill
- Reports results back to the user

**Main parameters:**
- `--days`: Number of days to look back (default: 30)
- `--chunk-size`: Size of each date chunk in days (default: 7)
- `--language`: Language code for articles (default: en)
- `--query`: Optional search query to filter articles

## Article Flow from NewsAPI to Database

The flow of articles works like this:

1. **API Fetch**: SyncManager calls NewsAPIService to fetch articles from NewsAPI
2. **Processing**: ArticleProcessor transforms NewsAPI data into our models:
   - Creates an Article model (domain model)
   - Creates a NewsAPIArticle model (API-specific data)
   - Links them via foreign key relationship
3. **Metrics & Enhancement**: During processing, we:
   - Calculate metrics (word count, read time)
   - Generate content hash for deduplication
   - Extract keywords from content
   - Link to Publications, Topics, and Regions
4. **Logging**: Each operation is tracked in SyncLog

## Scheduled Updates

The application runs three main scheduled updates:

1. **Top Headlines (Every hour at :00)**
   - Calls `/v2/top-headlines` endpoint
   - Uses parameters: `country`, `category`
   - Purpose: Fetch breaking news and trending stories
   - Marks articles as `is_top_headline=True`

2. **Recent Articles (Every hour at :30)**
   - Calls `/v2/everything` endpoint
   - Uses parameters: `from_param`, `to` (last hour), `language`
   - Purpose: Keep the feed updated with latest articles

3. **Publication-specific (Daily at 2:00 AM)**
   - Calls `/v2/everything` endpoint
   - Uses parameters: `sources` (specific publication IDs), `from_param`, `to` (last day)
   - Purpose: Ensures we have complete coverage of important publications

These different sync strategies ensure:
1. We have comprehensive article coverage
2. Breaking news is identified quickly
3. We maintain a complete archive of articles from key publications
4. We don't exceed NewsAPI rate limits by spacing out requests
