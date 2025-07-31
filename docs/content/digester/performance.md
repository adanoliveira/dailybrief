# Digest System Performance

This document provides performance analysis, optimization strategies, and monitoring guidance for the Daily Digest System.

## 📊 Performance Overview

The Daily Digest System is designed for efficient, scalable news digest generation with multiple performance profiles based on strategy selection.

### Performance Targets

| Metric | Articles Strategy | Events Strategy | Target |
|--------|------------------|----------------|---------|
| **Generation Time** | <30 seconds | <75 seconds | <30s (articles), <75s (events) |
| **Success Rate** | >99% | >95% | >95% |
| **Cost per Digest** | $0.05-0.08 | $0.12-0.18 | <$0.20 |
| **Concurrent Users** | 100+ | 50+ | Scale based on needs |
| **Memory Usage** | <500MB peak | <800MB peak | <1GB |
| **Database Queries** | 15-25 | 35-50 | <50 per digest |

## 🏃‍♂️ Strategy Performance Analysis

### Articles-Based Strategy

**Performance Characteristics**:
- **Fast Generation**: ~30 seconds average
- **High Reliability**: 99.5% success rate
- **Low AI Costs**: 4-6 LLM calls per digest
- **Efficient Queries**: 15-25 database queries
- **Predictable Resource Usage**: Consistent memory and CPU patterns

**Bottlenecks**:
- Article filtering and selection
- AI topic summary generation
- Database joins for related content

**Optimization Points**:
```python
# Database query optimization
articles_query = Article.objects.filter(
    published_at__gte=start_date,
    published_at__lte=end_date,
    analyzer_status='completed',
    summarization_status='completed'
).select_related(
    'primary_topic', 
    'primary_region', 
    'publication', 
    'structured_summary'
).prefetch_related(
    'topics',
    'regions'
)[:max_articles]
```

### Events-Based Strategy

**Performance Characteristics**:
- **Complex Generation**: ~75 seconds average
- **Good Reliability**: 95% success rate
- **Higher AI Costs**: 10-15 LLM calls per digest
- **Complex Queries**: 35-50 database queries
- **Variable Resource Usage**: Depends on event clustering complexity

**Bottlenecks**:
- Event detection and clustering
- Semantic similarity calculations
- Event enhancement with related articles
- Multiple AI generation calls

**Optimization Points**:
```python
# Event clustering optimization
@lru_cache(maxsize=1000)
def calculate_event_similarity(event1_id: int, event2_id: int) -> float:
    """Cached similarity calculation for frequent comparisons."""
    # Implementation with caching
    
# Batch AI processing
def batch_generate_event_summaries(events: List[Event]) -> List[Dict]:
    """Process multiple events in single AI call."""
    # Batch processing implementation
```

## 🔍 Performance Monitoring

### Key Performance Indicators (KPIs)

#### System-Level Metrics

```python
# Performance metrics tracked in Digest model
class Digest(models.Model):
    generation_duration_ms = models.IntegerField(default=0)
    generation_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    articles_processed = models.IntegerField(default=0)
    events_included = models.IntegerField(default=0)
    topics_included = models.IntegerField(default=0)
    
    # AI metadata
    ai_model_used = models.CharField(max_length=50, blank=True)
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
```

#### Component-Level Metrics

**Content Selection Performance**:
```python
# Monitor query execution time
def get_topic_articles_with_timing(topic: Topic, target_date: datetime.date) -> Tuple[List[Article], float]:
    start_time = time.time()
    articles = get_topic_articles_for_fallback_digest(topic, target_date)
    execution_time = time.time() - start_time
    
    logger.info(f"Content selection for {topic.name}: {execution_time:.2f}s, {len(articles)} articles")
    return articles, execution_time
```

**AI Generation Performance**:
```python
# Track AI provider performance
def generate_with_metrics(prompt: str, **kwargs) -> Dict[str, Any]:
    start_time = time.time()
    try:
        result = ai_provider.generate(prompt, **kwargs)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)
    
    metrics = {
        'duration_ms': int((time.time() - start_time) * 1000),
        'success': success,
        'error': error,
        'tokens_input': result.get('tokens_input', 0) if result else 0,
        'tokens_output': result.get('tokens_output', 0) if result else 0,
        'cost': result.get('cost', 0) if result else 0
    }
    
    return result, metrics
```

### Monitoring Commands

#### Real-time Performance Monitoring

```bash
# System performance overview
./docker.sh django digest_system_status --metrics

# Recent performance trends
./docker.sh django digest_system_status --recent-activity

# Strategy-specific performance
./docker.sh django test_digest_routing --user-id 1 --compare --verbosity 2
```

#### Performance Analysis Scripts

```bash
#!/bin/bash
# Performance analysis script

echo "📊 Digest System Performance Analysis"

# 1. Overall system metrics
echo "📈 System Metrics (Last 24h)"
./docker.sh django digest_system_status --metrics

# 2. Strategy performance comparison
echo "🔍 Strategy Performance"
./docker.sh django test_digest_routing --user-id 1 --compare

# 3. Component performance
echo "🔧 Component Performance"
./docker.sh django test_digest_components --all --user-id 1

# 4. Database performance
echo "💾 Database Performance"
./docker.sh django dbshell -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    seq_scan,
    idx_scan
FROM pg_stat_user_tables 
WHERE tablename LIKE 'digest_%';"

echo "✅ Performance analysis completed"
```

## 🚀 Optimization Strategies

### Database Optimization

#### Query Optimization

**Before Optimization**:
```python
# Inefficient - N+1 queries
digest_topics = DigestTopic.objects.filter(digest=digest)
for topic in digest_topics:
    stories = topic.stories.all()  # N+1 query
    for story in stories:
        articles = story.recommended_articles.all()  # N+1 query
```

**After Optimization**:
```python
# Efficient - Single query with prefetch
digest_topics = DigestTopic.objects.filter(digest=digest).prefetch_related(
    'stories__recommended_articles__publication',
    'stories__event',
    'topic'
).select_related('digest')
```

#### Index Optimization

```sql
-- Critical indexes for performance
CREATE INDEX CONCURRENTLY idx_digest_user_date ON digest_digest(user_id, date);
CREATE INDEX CONCURRENTLY idx_digest_status ON digest_digest(generation_status);
CREATE INDEX CONCURRENTLY idx_digesttopic_order ON digest_digesttopic(digest_id, order);
CREATE INDEX CONCURRENTLY idx_digeststory_order ON digest_digeststory(digest_topic_id, order);

-- Composite indexes for complex queries
CREATE INDEX CONCURRENTLY idx_articles_topic_status_date 
ON articles_article(primary_topic_id, analyzer_status, summarization_status, published_at);
```

### Application-Level Optimization

#### Caching Strategy

```python
from django.core.cache import cache
from functools import wraps

def cache_digest_content(timeout=3600):
    """Cache digest content for repeated access."""
    def decorator(func):
        @wraps(func)
        def wrapper(digest_id, *args, **kwargs):
            cache_key = f"digest_content_{digest_id}"
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            result = func(digest_id, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

@cache_digest_content(timeout=1800)  # 30 minutes
def get_digest_with_content(digest_id: str) -> Dict[str, Any]:
    """Get digest with full content, cached for performance."""
    # Implementation
```

#### Connection Pooling

```python
# Database connection optimization
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dailybrief',
        'USER': 'user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        },
        'CONN_MAX_AGE': 600,  # 10 minutes
    }
}
```

### AI Provider Optimization

#### Request Batching

```python
def batch_ai_requests(requests: List[Dict]) -> List[Dict]:
    """Batch multiple AI requests for efficiency."""
    
    # Group requests by model and parameters
    batched_requests = defaultdict(list)
    for req in requests:
        key = (req['model'], req['max_tokens'], req['temperature'])
        batched_requests[key].append(req)
    
    results = []
    for (model, max_tokens, temperature), batch in batched_requests.items():
        # Combine prompts with separators
        combined_prompt = "\n---SEPARATOR---\n".join([req['prompt'] for req in batch])
        
        # Single AI call for multiple requests
        batch_result = ai_provider.generate(
            prompt=combined_prompt,
            model=model,
            max_tokens=max_tokens * len(batch),
            temperature=temperature
        )
        
        # Split results back to individual responses
        individual_results = batch_result['content'].split('---SEPARATOR---')
        results.extend(individual_results)
    
    return results
```

#### Response Caching

```python
import hashlib
from django.core.cache import cache

def cached_ai_generation(prompt: str, model: str, **kwargs) -> Dict[str, Any]:
    """Cache AI responses for identical prompts."""
    
    # Create cache key from prompt and parameters
    cache_key_data = f"{prompt}_{model}_{sorted(kwargs.items())}"
    cache_key = f"ai_response_{hashlib.md5(cache_key_data.encode()).hexdigest()}"
    
    # Check cache first
    cached_response = cache.get(cache_key)
    if cached_response:
        logger.info(f"AI response cache hit for key: {cache_key[:16]}...")
        return cached_response
    
    # Generate new response
    response = ai_provider.generate(prompt=prompt, model=model, **kwargs)
    
    # Cache for 1 hour
    cache.set(cache_key, response, 3600)
    logger.info(f"AI response cached for key: {cache_key[:16]}...")
    
    return response
```

## 📈 Performance Benchmarks

### Baseline Performance Tests

#### Articles Strategy Benchmark

```bash
# Run performance benchmark for articles strategy
./docker.sh django test_digest_routing --user-id 1 --strategy articles_based --verbosity 2
```

**Expected Results**:
```
🧪 Testing digest routing for user: testuser
📅 Target date: 2024-12-21
🎯 Strategy: Articles-Based Digest

✅ Strategy Test Results:
   ⏱️  Generation time: 28.3s (Target: <30s) ✅
   📊 Topics generated: 4
   📰 Stories created: 4
   📖 Articles processed: 24
   💰 Total cost: $0.067 (Target: <$0.10) ✅
   🤖 AI model: gpt-4o-mini

🔍 Performance Breakdown:
   📊 Content selection: 3.2s (11.3%)
   🤖 AI generation: 22.1s (78.1%)
   💾 Database operations: 2.8s (9.9%)
   🔄 Post-processing: 0.2s (0.7%)

📈 Resource Usage:
   💾 Peak memory: 387MB
   🔄 CPU usage: 45%
   📊 Database queries: 18
```

#### Events Strategy Benchmark

```bash
# Run performance benchmark for events strategy
./docker.sh django test_digest_routing --user-id 1 --strategy events_based --verbosity 2
```

**Expected Results**:
```
🧪 Testing digest routing for user: testuser
📅 Target date: 2024-12-21
🎯 Strategy: Events-Based Digest

✅ Strategy Test Results:
   ⏱️  Generation time: 71.2s (Target: <75s) ✅
   📊 Topics generated: 4
   📰 Stories created: 12
   📖 Articles processed: 28
   💰 Total cost: $0.142 (Target: <$0.20) ✅
   🤖 AI model: gpt-4o-mini

🔍 Performance Breakdown:
   📊 Content selection: 5.8s (8.1%)
   🔍 Event detection: 12.4s (17.4%)
   🧠 Event clustering: 8.9s (12.5%)
   🤖 AI generation: 41.3s (58.0%)
   💾 Database operations: 2.6s (3.7%)
   🔄 Post-processing: 0.2s (0.3%)

📈 Resource Usage:
   💾 Peak memory: 612MB
   🔄 CPU usage: 67%
   📊 Database queries: 42
```

### Load Testing

#### Concurrent User Testing

```bash
#!/bin/bash
# Concurrent digest generation test

echo "🔄 Load Testing: Concurrent Digest Generation"

# Test with 10 concurrent users
for i in {1..10}; do
    ./docker.sh django generate_digest --user-id $i --test &
done

# Wait for all processes to complete
wait

echo "✅ Concurrent test completed"
```

#### Stress Testing

```bash
#!/bin/bash
# Stress test script

echo "💪 Stress Testing: High Volume Generation"

# Generate 50 digests rapidly
start_time=$(date +%s)

for i in {1..50}; do
    user_id=$((i % 10 + 1))  # Cycle through 10 users
    ./docker.sh django generate_digest --user-id $user_id --regenerate &
    
    # Limit concurrent processes
    if (( i % 5 == 0 )); then
        wait
    fi
done

wait

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "📊 Stress test completed in ${duration}s"
echo "📈 Average: $((duration / 50))s per digest"
```

## 🎯 Performance Tuning

### Memory Optimization

#### Memory Usage Patterns

```python
import psutil
import gc
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        """Monitor memory usage during digest generation."""
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate digest with memory monitoring
        for i in range(10):
            # Force garbage collection
            gc.collect()
            
            # Generate digest
            digest = generate_user_digest(user_id=1, force_regenerate=True)
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = current_memory - initial_memory
            
            self.stdout.write(
                f"Digest {i+1}: {current_memory:.1f}MB (+{memory_delta:.1f}MB)"
            )
```

#### Memory Leak Prevention

```python
def generate_digest_with_cleanup(user: User, date: datetime.date) -> Digest:
    """Generate digest with explicit cleanup."""
    
    try:
        # Generate digest
        result = digest_service.generate_user_digest(user, date)
        
        # Explicit cleanup
        if hasattr(django.db, 'connections'):
            django.db.connections.close_all()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        return result
        
    except Exception as e:
        # Cleanup on error
        django.db.connections.close_all()
        gc.collect()
        raise
```

### CPU Optimization

#### Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

def parallel_topic_generation(
    topics_with_articles: List[Tuple[Topic, List[Article]]]
) -> List[Dict[str, Any]]:
    """Generate topic summaries in parallel."""
    
    def generate_single_topic(topic_articles_pair):
        topic, articles = topic_articles_pair
        return ai_generator.generate_topic_summary_from_articles(articles, topic)
    
    # Use thread pool for I/O-bound AI operations
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        future_to_topic = {
            executor.submit(generate_single_topic, pair): pair[0] 
            for pair in topics_with_articles
        }
        
        # Collect results as they complete
        results = []
        for future in as_completed(future_to_topic):
            topic = future_to_topic[future]
            try:
                result = future.result(timeout=60)  # 60 second timeout
                results.append((topic, result))
            except Exception as e:
                logger.error(f"Failed to generate summary for {topic.name}: {e}")
                # Add fallback result
                results.append((topic, create_fallback_summary(topic)))
        
        return results
```

### Network Optimization

#### Connection Reuse

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class OptimizedAIProvider:
    def __init__(self):
        # Configure session with connection pooling
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Mount adapter with retry and connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Keep connections alive
        self.session.headers.update({'Connection': 'keep-alive'})
```

## 📊 Performance Monitoring Dashboard

### Metrics Collection

```python
# Custom metrics for monitoring
from django.db import models
from django.utils import timezone

class DigestPerformanceMetric(models.Model):
    """Track digest generation performance metrics."""
    
    date = models.DateField(default=timezone.now)
    strategy = models.CharField(max_length=50)
    
    # Performance metrics
    avg_generation_time_ms = models.IntegerField()
    max_generation_time_ms = models.IntegerField()
    min_generation_time_ms = models.IntegerField()
    
    # Volume metrics
    total_digests = models.IntegerField()
    successful_digests = models.IntegerField()
    failed_digests = models.IntegerField()
    
    # Cost metrics
    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=6)
    avg_cost_per_digest = models.DecimalField(max_digits=8, decimal_places=6)
    
    # Resource metrics
    avg_memory_usage_mb = models.FloatField()
    avg_cpu_usage_percent = models.FloatField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('date', 'strategy')
        ordering = ['-date', 'strategy']
```

### Performance Alerts

```python
def check_performance_thresholds():
    """Check performance metrics against thresholds and alert if needed."""
    
    from datetime import date, timedelta
    
    # Get today's metrics
    today = date.today()
    metrics = DigestPerformanceMetric.objects.filter(date=today)
    
    alerts = []
    
    for metric in metrics:
        # Check generation time
        if metric.avg_generation_time_ms > 30000 and metric.strategy == 'articles_based':
            alerts.append(f"Articles strategy exceeding 30s average: {metric.avg_generation_time_ms/1000:.1f}s")
        
        if metric.avg_generation_time_ms > 75000 and metric.strategy == 'events_based':
            alerts.append(f"Events strategy exceeding 75s average: {metric.avg_generation_time_ms/1000:.1f}s")
        
        # Check success rate
        success_rate = (metric.successful_digests / metric.total_digests) * 100
        if success_rate < 95:
            alerts.append(f"{metric.strategy} success rate below 95%: {success_rate:.1f}%")
        
        # Check cost
        if metric.avg_cost_per_digest > 0.20:
            alerts.append(f"{metric.strategy} cost exceeding $0.20: ${metric.avg_cost_per_digest:.3f}")
    
    return alerts
```

This comprehensive performance documentation provides the foundation for monitoring, optimizing, and scaling the Daily Digest System effectively.
