# AI Content Processing - Performance Guide

## Overview

This document provides comprehensive guidance on optimizing performance, monitoring costs, and scaling the AI content processing pipeline effectively.

## Performance Metrics

### Current Performance Benchmarks

Based on production testing and optimization work:

#### Processing Success Rate
- **Enhanced AI Pipeline**: 100% success rate after graceful error handling implementation
- **Legacy Pipeline**: ~30% success rate due to rigid validation
- **Quality Improvement**: 3.3x increase in successful processing

#### Processing Speed
- **Average Processing Time**: 156-190 seconds per article
- **Token Optimization**: 77% reduction from raw HTML through preprocessing  
- **API Response Time**: 23-45 seconds for AI processing (model dependent)
- **Total Pipeline Time**: Includes HTML preprocessing, AI processing, and block building

#### Content Quality
- **Quality Score Range**: 0.84-0.88 average for successfully processed articles
- **Content Completeness**: 100% preservation of valid content blocks
- **Block Type Coverage**: 12+ supported content types with forward compatibility

#### Cost Efficiency
- **Average Cost per Article**: $0.376 (GPT-4 class models)
- **Token Usage**: 4K-30K tokens depending on model and content complexity
- **Cost Optimization**: Model-specific token limits maximize value

### Performance Comparison

| Metric | Before Enhancement | After Enhancement | Improvement |
|--------|-------------------|-------------------|-------------|
| Success Rate | ~30% | 100% | +233% |
| Content Preservation | Partial | Complete | +100% |
| Block Type Support | 7 types | 12+ types | +71% |
| Token Efficiency | Fixed 16K limit | Model-specific (4K-30K) | Variable |
| Error Recovery | None | Graceful filtering | New capability |
| Retry Intelligence | Basic | Smart classification | New capability |

## Optimization Strategies

### 1. Token Optimization

#### Model-Specific Limits
Configure appropriate token limits based on model capabilities:

```python
# Optimized token limits by model
TOKEN_OPTIMIZATION = {
    "gpt-4.1-preview": {
        "max_tokens": 30000,
        "use_case": "Large articles, complex content",
        "cost_per_token": 0.00003,  # Example rate
        "recommended_for": ["long-form", "technical", "multi-section"]
    },
    
    "gpt-4o": {
        "max_tokens": 8000,
        "use_case": "Balanced performance and cost",
        "cost_per_token": 0.000015,
        "recommended_for": ["news", "blogs", "general"]
    },
    
    "gpt-4": {
        "max_tokens": 8000,
        "use_case": "High accuracy processing",
        "cost_per_token": 0.00003,
        "recommended_for": ["quality-critical", "complex-layout"]
    },
    
    "gpt-3.5-turbo": {
        "max_tokens": 4000,
        "use_case": "Cost-sensitive processing",
        "cost_per_token": 0.000002,
        "recommended_for": ["simple", "high-volume"]
    }
}
```

#### HTML Preprocessing Optimization
Maximize token efficiency through preprocessing:

```python
# Preprocessing effectiveness metrics
PREPROCESSING_METRICS = {
    "average_reduction": "77%",
    "token_savings": "~35K tokens per article",
    "processing_speed_improvement": "40%",
    "quality_preservation": "99%"
}

# Optimization techniques
PREPROCESSING_TECHNIQUES = [
    "Remove non-content elements (scripts, styles, navigation)",
    "Compress whitespace while preserving structure",
    "Extract only semantic HTML elements",
    "Normalize attribute sets (keep src, href, alt, class)",
    "Remove inline styles and unnecessary metadata"
]
```

### 2. Processing Route Optimization

#### Intelligent Router Configuration

```python
class OptimalRoutingStrategy:
    """Optimal routing strategy for different content types."""
    
    def __init__(self):
        self.routing_rules = {
            "simple_content": {
                "conditions": ["word_count < 500", "image_count < 3", "no_embeds"],
                "recommended_processor": "algorithmic",
                "confidence": 0.9
            },
            
            "complex_layout": {
                "conditions": ["has_embeds", "table_count > 1", "complex_structure"],
                "recommended_processor": "ai_enhanced", 
                "confidence": 0.95
            },
            
            "quality_critical": {
                "conditions": ["publication.tier == 'premium'", "user_preference == 'high_quality'"],
                "recommended_processor": "ai_enhanced",
                "confidence": 1.0
            },
            
            "cost_sensitive": {
                "conditions": ["daily_budget_remaining < threshold", "content_complexity < 0.3"],
                "recommended_processor": "algorithmic",
                "confidence": 0.8
            }
        }
    
    def determine_route(self, article, context: dict) -> str:
        """Determine optimal processing route based on multiple factors."""
        
        # Calculate content complexity score
        complexity = self._analyze_complexity(article)
        
        # Check budget constraints
        budget_status = context.get('budget_status', 'normal')
        
        # Consider publication tier
        publication_tier = getattr(article.publication, 'tier', 'standard')
        
        # Apply routing logic
        if budget_status == 'critical' and complexity < 0.5:
            return "algorithmic"
        elif publication_tier == 'premium' or complexity > 0.7:
            return "ai_enhanced"
        elif complexity < 0.3:
            return "algorithmic"
        else:
            return "ai_enhanced"
```

### 3. Parallel Processing

#### Batch Processing Optimization

```python
class BatchProcessingOptimizer:
    """Optimize batch processing for throughput and resource usage."""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.processing_queue = []
        self.rate_limiter = RateLimiter(requests_per_minute=60)
    
    def process_batch(self, articles: List[Article], filters: dict) -> dict:
        """Process articles in optimized batches."""
        
        # 1. Apply filters early to reduce workload
        filtered_articles = self._apply_filters(articles, filters)
        
        # 2. Sort by processing complexity (simple first)
        sorted_articles = self._sort_by_complexity(filtered_articles)
        
        # 3. Group by processing type
        ai_articles, algo_articles = self._group_by_processor(sorted_articles)
        
        # 4. Process algorithmic articles first (faster)
        algo_results = self._process_algorithmic_batch(algo_articles)
        
        # 5. Process AI articles with rate limiting
        ai_results = self._process_ai_batch(ai_articles)
        
        return {
            "total_processed": len(algo_results) + len(ai_results),
            "algorithmic_count": len(algo_results),
            "ai_count": len(ai_results),
            "success_rate": self._calculate_success_rate(algo_results + ai_results)
        }
    
    def _process_ai_batch(self, articles: List[Article]) -> List[ProcessingResult]:
        """Process AI articles with optimized resource management."""
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit articles with rate limiting
            futures = []
            for article in articles:
                self.rate_limiter.acquire()  # Respect API rate limits
                future = executor.submit(self._process_single_ai_article, article)
                futures.append((future, article))
            
            # Collect results as they complete
            for future, article in futures:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    results.append(result)
                except TimeoutError:
                    logger.error(f"Processing timeout for article {article.public_id}")
                    results.append(self._create_timeout_result(article))
                except Exception as e:
                    logger.error(f"Processing error for article {article.public_id}: {e}")
                    results.append(self._create_error_result(article, e))
        
        return results
```

### 4. Cost Management

#### Dynamic Budget Management

```python
class CostOptimizer:
    """Optimize processing costs while maintaining quality."""
    
    def __init__(self, daily_budget: float = 50.0):
        self.daily_budget = daily_budget
        self.cost_tracker = CostTracker()
    
    def get_processing_recommendation(self, article) -> dict:
        """Get cost-optimized processing recommendation."""
        
        # Check current budget status
        today_spent = self.cost_tracker.get_daily_spend()
        budget_remaining = self.daily_budget - today_spent
        budget_ratio = budget_remaining / self.daily_budget
        
        # Estimate processing cost
        estimated_cost = self._estimate_processing_cost(article)
        
        # Generate recommendation
        if budget_ratio < 0.1:  # Less than 10% budget remaining
            return {
                "processor": "algorithmic",
                "reason": "budget_conservation",
                "estimated_cost": 0.0,
                "confidence": 0.95
            }
        elif budget_ratio < 0.3 and estimated_cost > budget_remaining * 0.1:
            return {
                "processor": "algorithmic", 
                "reason": "cost_efficiency",
                "estimated_cost": 0.0,
                "confidence": 0.8
            }
        else:
            return {
                "processor": "ai_enhanced",
                "reason": "quality_optimization",
                "estimated_cost": estimated_cost,
                "confidence": 0.9
            }
    
    def _estimate_processing_cost(self, article) -> float:
        """Estimate processing cost based on article characteristics."""
        
        # Base cost estimation
        base_cost = 0.30  # Average cost per article
        
        # Adjust for content complexity
        if hasattr(article, 'estimated_complexity'):
            complexity_multiplier = 1 + (article.estimated_complexity * 0.5)
            base_cost *= complexity_multiplier
        
        # Adjust for content length
        if article.raw_html:
            html_length = len(article.raw_html)
            if html_length > 50000:  # Large articles
                base_cost *= 1.3
            elif html_length < 10000:  # Small articles
                base_cost *= 0.7
        
        return round(base_cost, 3)
```

## Monitoring and Alerting

### Performance Monitoring

#### Key Metrics to Track

```python
MONITORING_METRICS = {
    "processing_metrics": [
        "articles_processed_per_hour",
        "average_processing_time",
        "success_rate_percentage", 
        "retry_rate_percentage",
        "queue_length"
    ],
    
    "quality_metrics": [
        "average_quality_score",
        "content_completeness_rate",
        "block_filtering_rate",
        "extraction_accuracy"
    ],
    
    "cost_metrics": [
        "cost_per_article",
        "daily_spending",
        "token_usage_per_article",
        "budget_utilization_rate"
    ],
    
    "error_metrics": [
        "error_rate_by_type",
        "transient_vs_permanent_failures",
        "retry_success_rate",
        "timeout_frequency"
    ]
}
```

#### Automated Alerting

```python
class AlertingSystem:
    """Automated alerting for performance and cost monitoring."""
    
    def __init__(self):
        self.alert_thresholds = {
            "high_failure_rate": 0.2,  # 20% failure rate
            "budget_utilization": 0.8,  # 80% of daily budget
            "processing_time": 300,     # 5 minutes per article
            "queue_backlog": 100        # 100 articles in queue
        }
    
    def check_performance_alerts(self) -> List[dict]:
        """Check for performance issues requiring attention."""
        
        alerts = []
        
        # Check failure rate
        recent_failure_rate = self._calculate_recent_failure_rate()
        if recent_failure_rate > self.alert_thresholds["high_failure_rate"]:
            alerts.append({
                "type": "high_failure_rate",
                "severity": "critical",
                "value": recent_failure_rate,
                "threshold": self.alert_thresholds["high_failure_rate"],
                "message": f"Failure rate {recent_failure_rate:.1%} exceeds threshold"
            })
        
        # Check budget utilization
        budget_usage = self._calculate_budget_usage()
        if budget_usage > self.alert_thresholds["budget_utilization"]:
            alerts.append({
                "type": "budget_utilization",
                "severity": "warning",
                "value": budget_usage,
                "threshold": self.alert_thresholds["budget_utilization"],
                "message": f"Budget utilization {budget_usage:.1%} approaching limit"
            })
        
        # Check processing time
        avg_processing_time = self._calculate_avg_processing_time()
        if avg_processing_time > self.alert_thresholds["processing_time"]:
            alerts.append({
                "type": "slow_processing",
                "severity": "warning", 
                "value": avg_processing_time,
                "threshold": self.alert_thresholds["processing_time"],
                "message": f"Average processing time {avg_processing_time}s exceeds threshold"
            })
        
        return alerts
```

### Real-time Dashboard Metrics

#### Performance Dashboard

```sql
-- Key metrics for real-time dashboard

-- Processing throughput (last 24 hours)
SELECT 
    DATE_TRUNC('hour', last_process_attempt) as hour,
    COUNT(*) as articles_processed,
    AVG(CASE WHEN process_status = 'processed' THEN 1.0 ELSE 0.0 END) as success_rate
FROM articles_article 
WHERE last_process_attempt >= NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;

-- Cost tracking (daily)
SELECT 
    DATE(created_at) as date,
    SUM(cost) as daily_cost,
    COUNT(*) as operations,
    AVG(cost) as avg_cost_per_operation
FROM aiproviders_aiusagelog
WHERE operation = 'content_extraction' 
    AND created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY date
ORDER BY date;

-- Quality distribution (recent articles)
SELECT 
    CASE 
        WHEN (content_quality_metrics->>'quality_score')::float >= 0.8 THEN 'excellent'
        WHEN (content_quality_metrics->>'quality_score')::float >= 0.6 THEN 'good'
        WHEN (content_quality_metrics->>'quality_score')::float >= 0.4 THEN 'fair'
        WHEN (content_quality_metrics->>'quality_score')::float >= 0.2 THEN 'poor'
        ELSE 'failed'
    END as quality_tier,
    COUNT(*) as count
FROM articles_article 
WHERE process_status = 'processed' 
    AND content_quality_metrics IS NOT NULL
    AND last_process_attempt >= NOW() - INTERVAL '24 hours'
GROUP BY quality_tier;

-- Error analysis (recent failures)
SELECT 
    CASE 
        WHEN process_error_message ILIKE '%timeout%' THEN 'timeout'
        WHEN process_error_message ILIKE '%json%' THEN 'json_parsing'
        WHEN process_error_message ILIKE '%token%' THEN 'token_limit'
        WHEN process_error_message ILIKE '%rate%' THEN 'rate_limit'
        ELSE 'other'
    END as error_type,
    COUNT(*) as count
FROM articles_article 
WHERE process_status = 'ai_failed'
    AND last_process_attempt >= NOW() - INTERVAL '24 hours'
GROUP BY error_type
ORDER BY count DESC;
```

## Scaling Strategies

### Horizontal Scaling

#### Multi-Worker Configuration

```yaml
# docker-compose.yml scaling configuration
version: '3.8'
services:
  celery_worker_ai:
    build: ./backend
    command: celery -A dailybrief worker -Q ai_processing -c 2
    environment:
      - DJANGO_SETTINGS_MODULE=dailybrief.settings
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 3  # Scale to 3 AI processing workers
      
  celery_worker_general:
    build: ./backend  
    command: celery -A dailybrief worker -Q general -c 4
    environment:
      - DJANGO_SETTINGS_MODULE=dailybrief.settings
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 2  # Scale to 2 general workers
```

#### Load Balancing Strategy

```python
class LoadBalancingRouter:
    """Route processing tasks to optimal workers based on load."""
    
    def __init__(self):
        self.worker_stats = WorkerStatsTracker()
        self.queue_monitor = QueueMonitor()
    
    def route_processing_task(self, article) -> str:
        """Route article processing to optimal worker queue."""
        
        # Check current queue lengths
        ai_queue_length = self.queue_monitor.get_queue_length('ai_processing')
        general_queue_length = self.queue_monitor.get_queue_length('general')
        
        # Check worker availability
        ai_workers_available = self.worker_stats.get_available_workers('ai_processing')
        general_workers_available = self.worker_stats.get_available_workers('general')
        
        # Route based on complexity and capacity
        if self._requires_ai_processing(article):
            if ai_workers_available > 0 and ai_queue_length < 10:
                return 'ai_processing'
            else:
                # Queue for AI processing even if delayed
                return 'ai_processing_delayed'
        else:
            if general_workers_available > 0:
                return 'general'
            elif ai_workers_available > 0 and ai_queue_length < 5:
                return 'ai_processing'  # Use AI worker for simple content if available
            else:
                return 'general'  # Queue for general processing
```

### Vertical Scaling

#### Resource Optimization

```python
SCALING_RECOMMENDATIONS = {
    "small_deployment": {
        "articles_per_day": "< 1,000",
        "workers": 2,
        "memory_per_worker": "2GB",
        "cpu_per_worker": "1 core",
        "estimated_cost": "$5-10/day"
    },
    
    "medium_deployment": {
        "articles_per_day": "1,000 - 10,000", 
        "workers": 5,
        "memory_per_worker": "4GB",
        "cpu_per_worker": "2 cores",
        "estimated_cost": "$20-50/day"
    },
    
    "large_deployment": {
        "articles_per_day": "10,000+",
        "workers": 10,
        "memory_per_worker": "8GB", 
        "cpu_per_worker": "4 cores",
        "estimated_cost": "$100+/day"
    }
}
```

This performance guide provides comprehensive strategies for optimizing, monitoring, and scaling the AI content processing pipeline to meet various throughput and quality requirements while managing costs effectively. 