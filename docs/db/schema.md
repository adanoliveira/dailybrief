# DailyBrief Database Documentation

## Connection Information

### Local Development (Docker)

- **Host:** localhost
- **Port:** 5432
- **Database:** dailybrief
- **Username:** postgres
- **Password:** postgres
- **Connection URL:** `postgresql://postgres:postgres@localhost:5432/dailybrief`

To connect using a SQL client (e.g., DBeaver, pgAdmin, TablePlus):
1. Open your SQL client
2. Create a new PostgreSQL connection
3. Use the connection details above
4. Test and save the connection

### Docker Container Information

The database runs in a Docker container as part of the docker-compose setup:

```bash
# View running containers
docker ps | grep postgres

# Connect to database inside container
docker exec -it dailybrief-db-1 psql -U postgres -d dailybrief

# Export database dump
docker exec -it dailybrief-db-1 pg_dump -U postgres -d dailybrief > dailybrief_backup.sql
```

## Database Schema

The DailyBrief database follows a modular monolith architecture with separate domains (apps) that don't cross-import models.

### Auth Domain

#### auth_user (Django Built-in)
Django's built-in user authentication model.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| username | varchar | User's unique name |
| email | varchar | User's email address |
| password | varchar | Hashed password |
| is_active | boolean | User account status |
| date_joined | timestamp | Account creation date |
| last_login | timestamp | Last authentication timestamp |
| is_staff | boolean | Staff access flag |
| is_superuser | boolean | Admin privileges flag |

### Accounts Domain

#### accounts_userprofile
Extended user profile with additional fields for DailyBrief.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| user_id | integer | Foreign Key to auth_user |
| public_id | uuid | Public identifier (exposed in API) |
| timezone | varchar(50) | User's time zone (default: UTC) |
| onboarding_completed | boolean | Whether user completed onboarding |
| created_at | timestamp | Record creation timestamp |
| updated_at | timestamp | Record update timestamp |

### Articles Domain

#### articles_storygroup
Groups related articles that form a comprehensive story.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| public_id | uuid | Public identifier (exposed in API) |
| title | varchar(255) | Story group title |
| summary | text | Brief summary of the story |
| start_date | timestamp | When the story began |
| end_date | timestamp | When the story concluded (if any) |
| is_ongoing | boolean | Whether the story is still developing |
| created_at | timestamp | Record creation timestamp |
| updated_at | timestamp | Record update timestamp |

#### articles_article
Stores individual news articles.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| public_id | uuid | Public identifier (exposed in API) |
| title | varchar(512) | Article headline |
| description | text | Brief description/summary |
| content | text | Full article content |
| url | varchar(1024) | Original article URL |
| image_url | varchar(1024) | Featured image URL |
| source_name | varchar(255) | Source publication name |
| author | varchar(255) | Article author name |
| published_at | timestamp | Original publication date |
| fetched_at | timestamp | When article was added to our system |
| updated_at | timestamp | Record update timestamp |
| keywords | varchar[] | Array of keywords extracted from content |
| word_count | integer | Total word count |
| read_time_minutes | float | Estimated reading time |
| content_hash | varchar(64) | Hash for deduplication |
| sentiment_score | float | Sentiment analysis score |
| entities | json | Named entities extracted from content |
| popularity_score | float | Popularity ranking score |
| relevance_score | float | Relevance ranking score |
| is_top_headline | boolean | Whether it's a top headline |
| summary_ready | boolean | Whether AI summary is ready |
| publication_id | integer | Foreign Key to feeds_publication |
| language_id | integer | Foreign Key to feeds_language |
| story_group_id | integer | Foreign Key to articles_storygroup |

#### articles_userarticleinteraction
Tracks user interactions with articles for personalization.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| user_id | integer | Foreign Key to auth_user |
| article_id | integer | Foreign Key to articles_article |
| read | boolean | Whether user has read the article |
| read_at | timestamp | When the article was read |
| bookmarked | boolean | Whether user bookmarked the article |
| bookmarked_at | timestamp | When article was bookmarked |
| clicked | boolean | Whether user clicked on the article |
| clicked_at | timestamp | When article was clicked |
| created_at | timestamp | Record creation timestamp |
| updated_at | timestamp | Record update timestamp |

### Feeds Domain

#### feeds_publication
Stores information about news sources.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| name | varchar(255) | Publication name |
| news_api_id | varchar(255) | ID in News API (if applicable) |
| rss_url | varchar(255) | RSS feed URL (if applicable) |
| website_url | varchar(255) | Publication website URL |
| logo_url | varchar(255) | Publication logo URL |
| description | text | Description of the publication |
| authority | float | Weight for ranking (default: 1.0) |
| created_at | timestamp | Record creation timestamp |
| updated_at | timestamp | Record update timestamp |

#### feeds_topic
Categories/topics for content classification.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| name | varchar(100) | Topic name (unique) |
| slug | varchar(100) | URL-friendly name for the topic |
| created_at | timestamp | Record creation timestamp |

#### feeds_region
Geographic regions for content classification.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| code | varchar(5) | Region code (e.g., country code) |
| name | varchar(100) | Region name |
| created_at | timestamp | Record creation timestamp |

#### feeds_language
Supported languages.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| iso_code | varchar(5) | ISO language code |
| name | varchar(100) | Language name |
| created_at | timestamp | Record creation timestamp |

#### feeds_usertopic
User's preferred topics.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| user_id | integer | Foreign Key to auth_user |
| topic_id | integer | Foreign Key to feeds_topic |
| weight | float | Personalized ranking weight (default: 1.0) |
| created_at | timestamp | Record creation timestamp |

#### feeds_userpublication
User's preferred publications.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| user_id | integer | Foreign Key to auth_user |
| publication_id | integer | Foreign Key to feeds_publication |
| weight | float | Personalized ranking weight (default: 1.0) |
| created_at | timestamp | Record creation timestamp |

#### feeds_userregion
User's preferred regions.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| user_id | integer | Foreign Key to auth_user |
| region_id | integer | Foreign Key to feeds_region |
| weight | float | Personalized ranking weight (default: 1.0) |
| created_at | timestamp | Record creation timestamp |

#### feeds_userlanguage
User's preferred languages.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| user_id | integer | Foreign Key to auth_user |
| language_id | integer | Foreign Key to feeds_language |
| weight | float | Personalized ranking weight (default: 1.0) |
| created_at | timestamp | Record creation timestamp |

### Summariser Domain

#### summariser_articlesummary
Stores AI-generated summaries for articles.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| article_id | integer | Foreign Key to articles_article |
| abstract | text | Short abstract of the article (1-3 sentences) |
| key_points | text | Key points extracted from the article |
| full_summary | text | Full detailed summary of the article |
| is_translated | boolean | Whether the summary is translated |
| original_language | varchar(5) | Original language code of the article |
| ai_provider | varchar(50) | AI service used for summary generation |
| prompt_tokens | integer | Number of input tokens processed |
| completion_tokens | integer | Number of output tokens generated |
| processing_time | float | Time taken to generate summary (seconds) |
| created_at | timestamp | Record creation timestamp |
| updated_at | timestamp | Record update timestamp |

#### summariser_summarizationrequest
Tracks requests for article summarization.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| article_id | integer | Foreign Key to articles_article |
| status | varchar(20) | Status of request (pending/processing/completed/failed) |
| attempts | integer | Number of processing attempts |
| max_attempts | integer | Maximum attempts before giving up |
| last_error | text | Last error message (if any) |
| created_at | timestamp | Record creation timestamp |
| updated_at | timestamp | Record update timestamp |
| completed_at | timestamp | When summarization completed |

### Digest Domain

#### digest_digest
A daily digest of news articles for a user.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| public_id | uuid | Public identifier (exposed in API) |
| user_id | integer | Foreign Key to auth_user |
| title | varchar(255) | Digest title |
| date | date | Date this digest covers |
| introduction | text | AI-generated introduction |
| html_content | text | Full HTML content of the digest |
| is_published | boolean | Whether digest is published |
| is_sent | boolean | Whether digest was sent to user |
| sent_at | timestamp | When digest was sent |
| created_at | timestamp | Record creation timestamp |
| updated_at | timestamp | Record update timestamp |

#### digest_digeststory
A clustered story within a digest.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| digest_id | integer | Foreign Key to digest_digest |
| title | varchar(255) | Story title |
| summary | text | Story summary |
| order | integer | Display order in the digest |
| created_at | timestamp | Record creation timestamp |
| updated_at | timestamp | Record update timestamp |

### Notifications Domain

#### notifications_usernotificationsettings
User preferences for notifications.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| user_id | integer | Foreign Key to auth_user |
| email_digest | boolean | Send daily digest via email |
| email_news_updates | boolean | Send email for important news updates |
| push_enabled | boolean | Enable push notifications |
| push_digest | boolean | Send push notification for daily digest |
| push_news_updates | boolean | Send push for important news updates |
| preferred_time | time | Preferred time to receive digest |
| created_at | timestamp | Record creation timestamp |
| updated_at | timestamp | Record update timestamp |

#### notifications_pushsubscription
User's push notification subscriptions.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| user_id | integer | Foreign Key to auth_user |
| endpoint | varchar(500) | Web Push API endpoint URL |
| p256dh | varchar(255) | P256DH key for Web Push API |
| auth | varchar(255) | Auth key for Web Push API |
| browser | varchar(100) | Browser name |
| device | varchar(100) | Device name/type |
| is_active | boolean | Whether subscription is active |
| created_at | timestamp | Record creation timestamp |
| last_used | timestamp | When subscription was last used |

#### notifications_notification
Record of notifications sent to users.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| public_id | uuid | Public identifier (exposed in API) |
| user_id | integer | Foreign Key to auth_user |
| notification_type | varchar(20) | Type of notification (digest/news_update/system) |
| title | varchar(255) | Notification title |
| body | text | Notification body content |
| action_url | varchar(255) | URL for notification action |
| email_sent | boolean | Whether notification was sent via email |
| push_sent | boolean | Whether notification was sent via push |
| in_app_shown | boolean | Whether notification was shown in-app |
| status | varchar(20) | Status (pending/sent/failed/read) |
| error_message | text | Error message if delivery failed |
| created_at | timestamp | Record creation timestamp |
| sent_at | timestamp | When notification was sent |
| read_at | timestamp | When notification was read |

### Many-to-Many Join Tables

#### articles_article_topics
Links articles to topics (many-to-many).

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| article_id | integer | Foreign Key to articles_article |
| topic_id | integer | Foreign Key to feeds_topic |

#### articles_article_regions
Links articles to regions (many-to-many).

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| article_id | integer | Foreign Key to articles_article |
| region_id | integer | Foreign Key to feeds_region |

#### articles_article_related_articles
Self-referential many-to-many for related articles.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| from_article_id | integer | Foreign Key to articles_article |
| to_article_id | integer | Foreign Key to articles_article |

#### feeds_publication_topics
Links publications to topics (many-to-many).

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| publication_id | integer | Foreign Key to feeds_publication |
| topic_id | integer | Foreign Key to feeds_topic |

#### feeds_publication_languages
Links publications to languages (many-to-many).

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| publication_id | integer | Foreign Key to feeds_publication |
| language_id | integer | Foreign Key to feeds_language |

#### feeds_publication_regions
Links publications to regions (many-to-many).

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| publication_id | integer | Foreign Key to feeds_publication |
| region_id | integer | Foreign Key to feeds_region |

#### digest_digeststory_articles
Links digest stories to articles (many-to-many).

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary Key |
| digeststory_id | integer | Foreign Key to digest_digeststory |
| article_id | integer | Foreign Key to articles_article |

## Design Principles

1. **INT PK + UUID public_id** - All tables use an auto-incrementing integer primary key for efficient indexing and joining, while exposing only UUIDs in APIs for security.

2. **Modularity** - Tables are organized by domain (accounts, articles, feeds, summariser, digest, notifications) maintaining separation of concerns.

3. **No cross-importing models** - Each domain is self-contained with well-defined interfaces.

4. **Optimized indexes** - Tables have strategic indexes for common query patterns (e.g., user interactions, content hashes).

5. **Rich content metadata** - Articles store extensive metadata for advanced filtering, recommendation, and search capabilities.

## Common Database Operations

```sql
-- Get all top headlines with publication info
SELECT a.*, p.name as publication_name, p.logo_url
FROM articles_article a
LEFT JOIN feeds_publication p ON a.publication_id = p.id
WHERE a.is_top_headline = true
ORDER BY a.published_at DESC;

-- Get user bookmarks
SELECT a.*, ui.bookmarked_at
FROM articles_article a
JOIN articles_userarticleinteraction ui ON a.id = ui.article_id
WHERE ui.user_id = 1 AND ui.bookmarked = true
ORDER BY ui.bookmarked_at DESC;

-- Find articles by topic
SELECT a.*
FROM articles_article a
JOIN articles_article_topics at ON a.id = at.article_id
JOIN feeds_topic t ON at.topic_id = t.id
WHERE t.name = 'Technology'
ORDER BY a.published_at DESC;

-- Get article with its summary
SELECT a.*, s.abstract, s.key_points
FROM articles_article a
LEFT JOIN summariser_articlesummary s ON a.id = s.article_id
WHERE a.public_id = 'b8082edf-2ead-46e8-8273-9547173e0f05';

-- Get user's latest digest
SELECT d.*, COUNT(ds.id) as story_count
FROM digest_digest d
LEFT JOIN digest_digeststory ds ON d.id = ds.digest_id
WHERE d.user_id = 1 AND d.is_published = true
GROUP BY d.id
ORDER BY d.date DESC
LIMIT 1;

-- Get user notification preferences
SELECT u.username, u.email, ns.*
FROM auth_user u
JOIN notifications_usernotificationsettings ns ON u.id = ns.user_id
WHERE u.id = 1;
```

The database schema follows a domain-driven design approach, with clear boundaries between different functional areas of the application. Each domain has its own set of tables, and cross-domain relationships are established through foreign keys. 