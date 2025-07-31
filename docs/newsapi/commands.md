# NewsAPI Management Commands

This document details the management commands available for the NewsAPI integration, providing examples and usage instructions.

## Core Sync Commands

### `test_task`

Allows manual execution of any NewsAPI sync task for testing or ad-hoc syncs.

**Usage:**
```bash
./docker.sh django test_task [task_name]
```

**Available tasks:**
- `sync_headlines` - Sync top headlines
- `sync_recent_by_sources` - Sync recent articles by source
- `sync_by_publication` - Sync articles from specific publications
- `sync_sources` - Update available sources
- `backfill_articles` - Historical backfill of articles

**Examples:**
```bash
# Run the headlines sync task
./docker.sh django test_task sync_headlines

# Run the backfill task
./docker.sh django test_task backfill_articles
```

### `sync_sources_direct`

Updates the list of available sources from NewsAPI and creates or updates Publication records.

**Usage:**
```bash
./docker.sh django sync_sources_direct [options]
```

**Options:**
- `--countries` - Comma-separated list of country codes (default: all)
- `--update-existing` - Update existing publications with new data

**Examples:**
```bash
# Sync sources for all countries
./docker.sh django sync_sources_direct

# Sync sources for US and UK only
./docker.sh django sync_sources_direct --countries=us,gb

# Update existing publications with new metadata
./docker.sh django sync_sources_direct --update-existing
```

## Domain & Publication Management

### `backfill_domains`

Updates the domain field for existing Publication and NewsAPIArticle records by extracting domains from URLs.

**Usage:**
```bash
./docker.sh django backfill_domains [options]
```

**Options:**
- `--batch-size` - Number of records to process in each batch (default: 100)
- `--only` - Only process specific type of records (`publications` or `articles`)

**Examples:**
```bash
# Update domains for all records
./docker.sh django backfill_domains

# Update domains for publications only
./docker.sh django backfill_domains --only=publications

# Process in larger batches
./docker.sh django backfill_domains --batch-size=200
```

### `create_missing_publications`

Creates Publication records for unique domains found in NewsAPIArticle records that don't have a matching publication.

**Usage:**
```bash
./docker.sh django create_missing_publications [options]
```

**Options:**
- `--dry-run` - Show what would happen without making changes
- `--min-articles` - Minimum number of articles required to create a publication (default: 1)

**Examples:**
```bash
# Create publications for all domains with at least one article
./docker.sh django create_missing_publications

# Dry run to show what would happen
./docker.sh django create_missing_publications --dry-run

# Only create publications for domains with at least 5 articles
./docker.sh django create_missing_publications --min-articles=5
```

### `link_articles_to_publications`

Links Article records to Publication records based on matching domains.

**Usage:**
```bash
./docker.sh django link_articles_to_publications [options]
```

**Options:**
- `--batch-size` - Number of records to process in each batch (default: 100)
- `--dry-run` - Show what would happen without making changes
- `--create-missing` - Create new publications for unmatched sources
- `--verbose` - Show detailed diagnostics for unmatched articles

**Examples:**
```bash
# Link articles to publications
./docker.sh django link_articles_to_publications

# Link articles and create publications for unmatched sources
./docker.sh django link_articles_to_publications --create-missing

# Dry run with verbose output
./docker.sh django link_articles_to_publications --dry-run --verbose
```

### `add_publication_logos`

Adds logo URLs to Publication records based on their domains using Google's favicon service.

**Usage:**
```bash
./docker.sh django add_publication_logos [options]
```

**Options:**
- `--force` - Replace existing logos
- `--batch-size` - Number of publications to process in each batch (default: 50)

**Examples:**
```bash
# Add logos to publications without logos
./docker.sh django add_publication_logos

# Replace all logos
./docker.sh django add_publication_logos --force

# Process in smaller batches
./docker.sh django add_publication_logos --batch-size=20
```

## Installation & Setup Commands

These commands are useful when setting up the NewsAPI integration for the first time:

```bash
# Create migrations for domain fields
./docker.sh django makemigrations feeds newsapi

# Apply migrations
./docker.sh migrate

# Set up scheduled tasks
# (configured in settings.py CELERY_BEAT_SCHEDULE)
```

## Common Workflows

### First-Time Setup

```bash
# 1. Apply migrations
./docker.sh migrate

# 2. Sync sources 
./docker.sh django sync_sources_direct

# 3. Run initial sync
./docker.sh django test_task sync_headlines

# 4. Ensure publications have domains
./docker.sh django backfill_domains

# 5. Add logos
./docker.sh django add_publication_logos
```

### Fixing Publication Associations

```bash
# 1. Update domains
./docker.sh django backfill_domains

# 2. Create missing publications
./docker.sh django create_missing_publications

# 3. Link articles to publications
./docker.sh django link_articles_to_publications

# 4. Add logos to new publications
./docker.sh django add_publication_logos
``` 