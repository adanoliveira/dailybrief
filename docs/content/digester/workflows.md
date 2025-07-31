# Digest System Workflows

This document provides step-by-step workflows for common operational scenarios in the Daily Digest System.

## 🚀 Production Workflows

### Daily Digest Generation

Standard workflow for generating daily digests for all users.

#### Morning Digest Generation (Recommended)

```bash
#!/bin/bash
# Daily digest generation script

echo "🌅 Starting daily digest generation..."

# 1. Check system health
./docker.sh django digest_system_status

# 2. Generate digests for all users
./docker.sh django generate_digest \
    --all-users \
    --skip-users-with-digests \
    --max-users 100 \
    --verbosity 1

# 3. Monitor results
./docker.sh django digest_system_status --metrics --recent-activity

echo "✅ Daily digest generation completed"
```

#### Cron Job Setup

```bash
# Add to crontab for automated daily generation
# Run at 6:00 AM UTC daily
0 6 * * * /path/to/dailybrief/scripts/generate_daily_digests.sh

# Alternative: Run at 8:00 AM user local time
0 8 * * * cd /path/to/dailybrief && ./docker.sh django generate_digest --all-users --skip-users-with-digests
```

---

## 🔧 Development Workflows

### Setting Up New Digest Strategy

Step-by-step process for implementing a new digest generation strategy.

#### 1. Create Strategy Class

```python
# backend/apps/content/digest/services/custom_digest_strategy.py

from .abstract_digest_strategy import AbstractDigestStrategy

class CustomDigestStrategy(AbstractDigestStrategy):
    """Custom digest generation strategy."""
    
    def get_display_name(self) -> str:
        return "Custom Digest Strategy"
    
    def generate_digest_content(self, digest, followed_topics, preferences):
        # Implementation details
        pass
```

#### 2. Register Strategy

```python
# backend/apps/content/digest/services/__init__.py

from .custom_digest_strategy import CustomDigestStrategy

# Add to AVAILABLE_STRATEGIES
AVAILABLE_STRATEGIES = {
    'articles_based': ArticlesDigestStrategy,
    'events_based': EventsDigestStrategy,
    'custom': CustomDigestStrategy,  # New strategy
}
```

#### 3. Test Strategy

```bash
# Test the new strategy
./docker.sh django test_digest_routing --user-id 1 --strategy custom

# Compare with existing strategies
./docker.sh django test_digest_routing --user-id 1 --compare

# Validate configuration
./docker.sh django set_digest_strategy --validate
```

#### 4. Deploy Strategy

```bash
# Set as default if testing successful
./docker.sh django set_digest_strategy --strategy custom

# Monitor performance
./docker.sh django digest_system_status --metrics
```

### Testing New Features

Workflow for testing digest system changes.

#### 1. Component Testing

```bash
# Test individual components
./docker.sh django test_digest_components --component content_selector --user-id 1
./docker.sh django test_digest_components --component ai_generator --topic-id 1
./docker.sh django test_digest_components --health-check
```

#### 2. Strategy Testing

```bash
# Test specific strategy
./docker.sh django test_digest_routing --user-id 1 --strategy articles_based --verbosity 2

# Performance comparison
./docker.sh django test_digest_routing --user-id 1 --compare

# Dry run validation
./docker.sh django test_digest_routing --user-id 1 --dry-run
```

#### 3. Integration Testing

```bash
# Generate test digest
./docker.sh django generate_digest --user-id 1 --test --verbosity 3

# Test AI fallbacks
./docker.sh django test_ai_fallback_digest --user-id 1 --test-retries

# Display results
./docker.sh django display_digest --user-id 1 --verbose
```

---

## 🚨 Incident Response Workflows

### Digest Generation Failures

Workflow for diagnosing and resolving digest generation issues.

#### 1. Initial Assessment

```bash
# Check system status
./docker.sh django digest_system_status --detailed

# Review recent errors
./docker.sh django generate_digest --user-id FAILED_USER_ID --test --verbosity 3

# Check component health
./docker.sh django test_digest_components --health-check
```

#### 2. Common Issue Resolution

**AI Provider Rate Limits**:
```bash
# Check current costs and usage
./docker.sh django digest_system_status --metrics

# Test AI fallback
./docker.sh django test_ai_fallback_digest --user-id 1

# Temporarily switch strategies
./docker.sh django set_digest_strategy --strategy articles_based
```

**Insufficient Content**:
```bash
# Check article pipeline status
./docker.sh django check_articles --status completed --hours 48

# Verify user topics
./docker.sh django test_digest_components --component content_selector --user-id FAILED_USER_ID

# Test with different time window
./docker.sh django generate_digest --user-id FAILED_USER_ID --test
```

**Database Issues**:
```bash
# Check database connectivity
./docker.sh django digest_system_status --detailed

# Test individual components
./docker.sh django test_digest_components --all --user-id 1

# Restart services if needed
docker-compose restart backend
```

#### 3. Recovery Actions

```bash
# Regenerate failed digests
./docker.sh django generate_digest --user-id FAILED_USER_ID --regenerate

# Bulk regeneration for multiple users
for user_id in 1 2 3; do
    ./docker.sh django generate_digest --user-id $user_id --regenerate
done

# Monitor system recovery
./docker.sh django digest_system_status --recent-activity
```

### Performance Degradation

Workflow for addressing performance issues.

#### 1. Performance Analysis

```bash
# Check current metrics
./docker.sh django digest_system_status --metrics

# Analyze slow digests
./docker.sh django test_digest_routing --user-id SLOW_USER_ID --compare --verbosity 2

# Test component performance
./docker.sh django test_digest_components --all --user-id SLOW_USER_ID
```

#### 2. Optimization Actions

**Strategy Optimization**:
```bash
# Switch to faster strategy
./docker.sh django set_digest_strategy --strategy articles_based

# Test performance improvement
./docker.sh django test_digest_routing --user-id SLOW_USER_ID --strategy articles_based
```

**Content Optimization**:
```bash
# Reduce content scope temporarily
# Update user preferences to limit articles
./docker.sh django generate_digest --user-id SLOW_USER_ID --test
```

---

## 📊 Monitoring Workflows

### Daily Health Checks

Automated monitoring workflow for system health.

#### Health Check Script

```bash
#!/bin/bash
# Daily health check script

echo "🏥 Daily Digest System Health Check"

# 1. System status
STATUS=$(./docker.sh django digest_system_status --metrics 2>&1)
echo "$STATUS"

# 2. Check for alerts
if echo "$STATUS" | grep -q "⚠️"; then
    echo "🚨 Alerts detected - investigate immediately"
    # Send alert to monitoring system
    # curl -X POST https://monitoring.example.com/alerts ...
fi

# 3. Performance metrics
METRICS=$(./docker.sh django digest_system_status --recent-activity 2>&1)
echo "$METRICS"

# 4. Success rate check
SUCCESS_RATE=$(echo "$METRICS" | grep "Success rate" | awk '{print $3}' | sed 's/%//')
if (( $(echo "$SUCCESS_RATE < 95" | bc -l) )); then
    echo "🚨 Success rate below 95% - investigate"
fi

echo "✅ Health check completed"
```

### Performance Monitoring

Weekly performance analysis workflow.

#### Performance Report Script

```bash
#!/bin/bash
# Weekly performance report

echo "📊 Weekly Digest Performance Report"

# 1. System metrics
./docker.sh django digest_system_status --metrics

# 2. Strategy performance comparison
echo "🔍 Strategy Performance Analysis"
for strategy in articles_based events_based; do
    echo "Testing $strategy strategy..."
    ./docker.sh django test_digest_routing --user-id 1 --strategy $strategy
done

# 3. Component health
echo "🔧 Component Health Check"
./docker.sh django test_digest_components --health-check

# 4. Generate sample digest for quality check
echo "📰 Sample Digest Generation"
./docker.sh django generate_digest --user-id 1 --test --verbosity 1

echo "✅ Performance report completed"
```

---

## 🔄 Migration Workflows

### Strategy Migration

Workflow for migrating from one digest strategy to another.

#### 1. Pre-Migration Testing

```bash
# Test new strategy with sample users
./docker.sh django test_digest_routing --user-id 1 --strategy events_based
./docker.sh django test_digest_routing --user-id 2 --strategy events_based
./docker.sh django test_digest_routing --user-id 3 --strategy events_based

# Performance comparison
./docker.sh django test_digest_routing --user-id 1 --compare
```

#### 2. Gradual Rollout

```bash
# Update small percentage of users first
# (This would require custom management command for user-specific strategy setting)

# Monitor performance
./docker.sh django digest_system_status --metrics

# Check for issues
./docker.sh django digest_system_status --recent-activity
```

#### 3. Full Migration

```bash
# Set new default strategy
./docker.sh django set_digest_strategy --strategy events_based

# Validate configuration
./docker.sh django set_digest_strategy --validate

# Monitor system after migration
./docker.sh django digest_system_status --detailed
```

#### 4. Rollback Procedure

```bash
# If issues detected, rollback immediately
./docker.sh django set_digest_strategy --strategy articles_based

# Regenerate failed digests
./docker.sh django generate_digest --all-users --regenerate

# Verify system stability
./docker.sh django digest_system_status --metrics
```

---

## 🧪 Quality Assurance Workflows

### Content Quality Review

Workflow for reviewing digest content quality.

#### 1. Sample Generation

```bash
# Generate sample digests for review
./docker.sh django generate_digest --user-id 1 --regenerate
./docker.sh django generate_digest --user-id 2 --regenerate
./docker.sh django generate_digest --user-id 3 --regenerate
```

#### 2. Content Analysis

```bash
# Display digests for manual review
./docker.sh django display_digest --user-id 1 --verbose
./docker.sh django display_digest --user-id 2 --format json > review_digest_2.json
./docker.sh django display_digest --user-id 3 --export review_digest_3.html
```

#### 3. Quality Metrics Collection

```bash
# Strategy comparison for quality assessment
./docker.sh django test_digest_routing --user-id 1 --compare --verbosity 2

# Performance metrics
./docker.sh django digest_system_status --metrics
```

### A/B Testing Workflow

Workflow for testing different digest approaches.

#### 1. Setup Test Groups

```bash
# Test Group A: Articles strategy
./docker.sh django generate_digest --user-id 1 --test
./docker.sh django test_digest_routing --user-id 1 --strategy articles_based

# Test Group B: Events strategy  
./docker.sh django generate_digest --user-id 2 --test
./docker.sh django test_digest_routing --user-id 2 --strategy events_based
```

#### 2. Collect Metrics

```bash
# Performance comparison
./docker.sh django test_digest_routing --user-id 1 --compare

# Content analysis
./docker.sh django display_digest --user-id 1 --format json > group_a_digest.json
./docker.sh django display_digest --user-id 2 --format json > group_b_digest.json
```

#### 3. Analysis and Decision

```bash
# System performance review
./docker.sh django digest_system_status --metrics

# Make strategy decision based on results
./docker.sh django set_digest_strategy --strategy WINNING_STRATEGY
```

---

## 📋 Maintenance Workflows

### Regular Maintenance

Weekly maintenance tasks for optimal performance.

#### Maintenance Checklist

```bash
#!/bin/bash
# Weekly maintenance script

echo "🔧 Weekly Digest System Maintenance"

# 1. Health check
./docker.sh django digest_system_status --detailed

# 2. Performance analysis
./docker.sh django digest_system_status --metrics

# 3. Component testing
./docker.sh django test_digest_components --health-check

# 4. Strategy validation
./docker.sh django set_digest_strategy --validate

# 5. Clean up old test data (if applicable)
# ./docker.sh django cleanup_test_digests --older-than 30

# 6. Performance optimization check
./docker.sh django test_digest_routing --user-id 1 --compare

echo "✅ Maintenance completed"
```

### Database Maintenance

Periodic database optimization for digest models.

```bash
# Database optimization (run during low-traffic periods)
./docker.sh django dbshell -c "ANALYZE digest_digest, digest_digesttopic, digest_digeststory;"

# Index maintenance
./docker.sh django dbshell -c "REINDEX INDEX digest_digest_user_id_date_idx;"

# Statistics update
./docker.sh django dbshell -c "UPDATE pg_stat_user_tables SET n_tup_ins=0 WHERE relname LIKE 'digest_%';"
```

This comprehensive workflows documentation provides operational guidance for all aspects of the Daily Digest System, from daily operations to incident response and quality assurance.
