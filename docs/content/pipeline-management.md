# Pipeline Management Commands

This document provides comprehensive documentation for all content pipeline management commands in DailyBrief. The content pipeline consists of four main stages: **Fetching** → **Processing** → **Summarization** → **Analysis**.

## Quick Reference

### Core Pipeline Commands
```bash
# Monitor pipeline status
./docker.sh django test_pipeline --status

# Run full pipeline
./docker.sh django process_top_headlines_pipeline

# Clean up stuck articles (enhanced with time controls)
./docker.sh django cleanup_stuck_articles [options]

# Reset failed articles for retry
./docker.sh django reset_failed_to_fetch_pending
```

### Emergency Commands
```bash
# Reset specific article statuses
./docker.sh django reset_article_status --article-ids "123,456"

# Force reprocessing with AI
./docker.sh django reprocess_with_ai --article-ids "123,456"

# Bulk processing commands
./docker.sh django bulk_process_recent --ai
```

---

## 🔍 Monitoring & Status Commands

### test_pipeline
**Monitor pipeline status and run individual stages**

```bash
# Check pipeline status
./docker.sh django test_pipeline --status

# Run specific pipeline stage  
./docker.sh django test_pipeline --run-fetch
./docker.sh django test_pipeline --run-process
./docker.sh django test_pipeline --run-summarize
./docker.sh django test_pipeline --run-analyze
```

**Output Example:**
```
📊 Content Enrichment Pipeline Status
============================================================
📰 Total Top Headlines: 124
✅ Fully Processed: 76 (61.3%)

🔄 Stage 1: Content Fetching
  • Pending: 0
  • Processing: 0
  • Completed: 124
  • Failed: 0

🧠 Stage 2: AI Processing  
  • Pending: 0
  • Processing: 0
  • Completed: 113
  • Failed: 11

📝 Stage 3: Summarization
  • Pending: 0
  • Processing: 0
  • Completed: 113
  • Failed: 0

🔍 Stage 4: Analysis
  • Pending: 0
  • Processing: 37
  • Completed: 76
  • Failed: 0
```

---

## 🧹 Cleanup & Recovery Commands

### cleanup_stuck_articles (Enhanced)
**Clean up articles stuck in processing with flexible time controls**

#### Basic Usage
```bash
# Check for stuck articles (default: 2h timeout)
./docker.sh django cleanup_stuck_articles --check-only

# Actually reset stuck articles
./docker.sh django cleanup_stuck_articles

# Show detailed information
./docker.sh django cleanup_stuck_articles --check-only --verbose
```

#### Time Window Controls

**Convenience Presets:**
```bash
# Aggressive (30 minutes for all stages)
./docker.sh django cleanup_stuck_articles --aggressive

# Conservative (6 hours for all stages)  
./docker.sh django cleanup_stuck_articles --conservative
```

**Global Timeouts:**
```bash
# Set all stages to 1 hour
./docker.sh django cleanup_stuck_articles --timeout 1

# Set all stages to 45 minutes
./docker.sh django cleanup_stuck_articles --timeout-minutes 45
```

**Individual Stage Timeouts (Hours):**
```bash
./docker.sh django cleanup_stuck_articles \
  --fetch-timeout 1 \
  --process-timeout 2 \
  --summarization-timeout 3 \
  --analysis-timeout 4
```

**Individual Stage Timeouts (Minutes):**
```bash
# Minute precision for specific stages
./docker.sh django cleanup_stuck_articles \
  --analysis-timeout-minutes 30 \
  --process-timeout-minutes 45
```

**Combined Examples:**
```bash
# Use conservative preset but override analysis to 45 minutes
./docker.sh django cleanup_stuck_articles --conservative --analysis-timeout-minutes 45

# Set global 30 minutes but allow 2 hours for analysis
./docker.sh django cleanup_stuck_articles --timeout-minutes 30 --analysis-timeout 2
```

**Timeout Precedence (highest to lowest):**
1. Individual minute timeouts (`--*-timeout-minutes`)
2. Global timeouts (`--timeout`, `--timeout-minutes`)  
3. Presets (`--aggressive`, `--conservative`)
4. Individual hour timeouts (`--*-timeout`)
5. Defaults (2 hours for all stages)

#### Output Example
```bash
./docker.sh django cleanup_stuck_articles --check-only --analysis-timeout-minutes 30 --verbose
```
```
🔍 Checking stuck articles across all pipeline stages...
⏱️  Timeout Configuration:
   • Fetch: 2.0h
   • Process: 2.0h
   • Summarization: 2.0h
   • Analysis: 0.5h

   ✅ No articles stuck in Fetching status
   ✅ No articles stuck in Processing status
   ✅ No articles stuck in Summarization status
   ⚠️  Found 28 articles stuck in Analysis status

   📋 Stuck Analysis Articles Details:
      • ID: 43185, Attempts: 1, Last: 2025-06-23 15:02:31
      • ID: 43205, Attempts: 1, Last: 2025-06-23 15:01:50
      • ID: 43186, Attempts: 1, Last: 2025-06-23 15:01:45
      ... and 25 more

📊 Summary: 28 stuck articles would be reset across all stages
   💡 Run without --check-only to actually reset these articles
```

### reset_failed_to_fetch_pending  
**Reset failed articles back to fetch pending for retry**

```bash
# Reset all failed articles
./docker.sh django reset_failed_to_fetch_pending --dry-run

# Reset specific articles
./docker.sh django reset_failed_to_fetch_pending --article-ids "40119,40120"

# Reset articles failed in last N hours
./docker.sh django reset_failed_to_fetch_pending --hours 24
```

### reset_article_status
**Reset specific article statuses for targeted recovery**

```bash
# Reset specific articles to pending
./docker.sh django reset_article_status --article-ids "123,456" --fetch-status pending

# Reset analysis status
./docker.sh django reset_article_status --article-ids "123,456" --analyzer-status pending
```

---

## 🏃‍♂️ Pipeline Execution Commands

### process_top_headlines_pipeline
**Execute the full 4-stage pipeline on recent articles**

```bash
# Run full pipeline (default: 50 articles per stage)
./docker.sh django process_top_headlines_pipeline

# Run with custom limits
./docker.sh django process_top_headlines_pipeline --limit 100
```

### run_full_pipeline
**Comprehensive pipeline execution with detailed reporting**

```bash
# Run full content processing pipeline
./docker.sh django run_full_pipeline

# Run with AI processing
./docker.sh django run_full_pipeline --processor ai --limit 50

# Skip fetching, only process
./docker.sh django run_full_pipeline --skip-fetch
```

---

## 📝 Stage-Specific Commands

### Stage 1: Fetching Commands

#### fetch_content
```bash
# Fetch content for specific articles
./docker.sh django fetch_content --article-ids "123,456"

# Fetch content by date range
./docker.sh django fetch_content --start-date 2025-01-01 --end-date 2025-01-02
```

#### test_fetcher
```bash
# Test fetching functionality
./docker.sh django test_fetcher --article-id 123
```

### Stage 2: Processing Commands

#### process_ready_articles
```bash
# Process articles with AI
./docker.sh django process_ready_articles --processor ai --limit 50

# Process articles algorithmically  
./docker.sh django process_ready_articles --processor algorithmic --limit 50

# Force reprocessing
./docker.sh django process_ready_articles --force
```

#### bulk_ai_process
```bash
# Bulk AI processing
./docker.sh django bulk_ai_process --limit 100

# Process with enhanced mode
./docker.sh django bulk_ai_process --enhanced-mode
```

#### reprocess_with_ai
```bash
# Reprocess specific articles with AI
./docker.sh django reprocess_with_ai --article-ids "123,456"

# Reprocess failed articles
./docker.sh django reprocess_with_ai --failed-only
```

### Stage 3: Summarization Commands

#### summarize_articles
```bash
# Summarize pending articles
./docker.sh django summarize_articles --limit 50

# Summarize specific articles
./docker.sh django summarize_articles --article-ids "123,456"
```

### Stage 4: Analysis Commands

#### run_analyzer
```bash
# Analyze pending articles
./docker.sh django run_analyzer --limit 50

# Analyze specific article
./docker.sh django run_analyzer --article-id 123

# Force reanalysis
./docker.sh django run_analyzer --force --article-id 123
```

#### deduplicate_events
```bash
# Run event deduplication (preview)
./docker.sh django deduplicate_events --dry-run

# Run deduplication on recent articles
./docker.sh django deduplicate_events --recent-days 7

# Force deduplication (aggressive)
./docker.sh django deduplicate_events --force
```

---

## 🔧 Diagnostic & Debug Commands

### check_article_status
```bash
# Check status of specific articles
./docker.sh django check_article_status --article-ids "123,456"
```

### analyze_ai_feedback
```bash
# Analyze AI processing feedback
./docker.sh django analyze_ai_feedback --days 7
```

### test_analyzer_debug
```bash
# Debug analyzer issues
./docker.sh django test_analyzer_debug --article-id 123
```

---

## 📊 Quality & Performance Commands

### evaluate_quality
```bash
# Evaluate content quality
./docker.sh django evaluate_quality --limit 50

# Evaluate specific articles
./docker.sh django evaluate_quality --article-ids "123,456"
```

### quality_benchmark
```bash
# Run quality benchmarks
./docker.sh django quality_benchmark --sample-size 100
```

---

## 🎯 Digest Generation Commands

### generate_digest
```bash
# Generate daily digest
./docker.sh django generate_digest

# Generate for specific date
./docker.sh django generate_digest --date 2025-01-01

# Generate with custom parameters
./docker.sh django generate_digest --max-events 10 --min-articles 3
```

### display_digest
```bash
# Display latest digest
./docker.sh django display_digest

# Display specific digest
./docker.sh django display_digest --date 2025-01-01
```

---

## 🚨 Emergency Procedures

### Pipeline Completely Stuck
```bash
# 1. Check status
./docker.sh django test_pipeline --status

# 2. Aggressive cleanup (30-minute timeout)
./docker.sh django cleanup_stuck_articles --aggressive

# 3. Reset failed articles
./docker.sh django reset_failed_to_fetch_pending

# 4. Restart pipeline
./docker.sh django process_top_headlines_pipeline
```

### Specific Stage Issues

**Fetching Issues:**
```bash
./docker.sh django cleanup_stuck_articles --fetch-timeout-minutes 15
./docker.sh django fetch_content --article-ids "stuck_ids"
```

**Processing Issues:**
```bash
./docker.sh django cleanup_stuck_articles --process-timeout-minutes 30
./docker.sh django reprocess_with_ai --failed-only
```

**Analysis Issues:**
```bash
./docker.sh django cleanup_stuck_articles --analysis-timeout-minutes 30
./docker.sh django run_analyzer --force --limit 50
```

---

## 📋 Best Practices

### Monitoring
- Run `test_pipeline --status` regularly to monitor pipeline health
- Use `--check-only` before running cleanup commands
- Monitor logs for error patterns

### Timeouts
- **Default (2h)**: Good for normal operations
- **Conservative (6h)**: Use during heavy AI processing periods  
- **Aggressive (30min)**: Use for quick recovery during outages
- **Custom minutes**: Use for fine-tuned control during debugging

### Recovery Strategy
1. **Identify** stuck stage with `test_pipeline --status`
2. **Preview** cleanup with `cleanup_stuck_articles --check-only`
3. **Reset** stuck articles with appropriate timeouts
4. **Restart** pipeline processing
5. **Monitor** progress and repeat if needed

### Rate Limiting Considerations
- Current AI rate limit: 8 calls/min (very conservative)
- Adjust cleanup timeouts accordingly during high-load periods
- Use `--analysis-timeout-minutes 45` when hitting rate limits

---

## 🔄 Automated Cleanup (Celery Tasks)

The following cleanup tasks run automatically:

### Scheduled Cleanup Tasks
- **cleanup_stuck_analyzer_articles**: Every 2 hours
- **cleanup_stuck_summarization_articles**: Every 2 hours  
- **cleanup_processing_data**: Every 2 hours
- **retry-failed-pipeline-stages**: Every 6 hours

### Manual Trigger
```bash
# Trigger specific cleanup task
./docker.sh django shell -c "
from apps.content.analyzer.tasks import cleanup_stuck_analyzer_articles
result = cleanup_stuck_analyzer_articles.delay()
print(f'Task queued: {result.id}')
"
```

---

This documentation covers all pipeline management commands with practical examples and troubleshooting guidance. Use the quick reference section for common operations and refer to specific sections for detailed usage patterns. 