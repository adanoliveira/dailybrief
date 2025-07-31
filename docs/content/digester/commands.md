# Digest Management Commands

This document provides complete reference for all management commands available in the Daily Digest System.

## 🚀 Generation Commands

### generate_digest

Generate daily digests for users.

#### Basic Usage

```bash
# Generate digest for specific user
./docker.sh django generate_digest --user-id 1

# Generate digest for user by username
./docker.sh django generate_digest --username john.doe

# Generate for all active users
./docker.sh django generate_digest --all-users

# Generate for specific date
./docker.sh django generate_digest --user-id 1 --date 2024-12-21

# Force regeneration of existing digest
./docker.sh django generate_digest --user-id 1 --regenerate
```

#### Advanced Options

```bash
# Test mode (dry run validation)
./docker.sh django generate_digest --user-id 1 --test

# Limit number of users processed
./docker.sh django generate_digest --all-users --max-users 10

# Skip users who already have digests
./docker.sh django generate_digest --all-users --skip-users-with-digests

# Verbose output
./docker.sh django generate_digest --user-id 1 --verbosity 2
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--user-id` | Integer | Generate for specific user ID | None |
| `--username` | String | Generate for specific username | None |
| `--all-users` | Flag | Generate for all active users | False |
| `--date` | String | Target date (YYYY-MM-DD format) | Today |
| `--regenerate` | Flag | Regenerate existing digest | False |
| `--test` | Flag | Test mode - validate but don't generate | False |
| `--max-users` | Integer | Maximum users to process | 50 |
| `--skip-users-with-digests` | Flag | Skip users with existing digests | False |

#### Examples

```bash
# Daily digest generation for all users
./docker.sh django generate_digest --all-users --skip-users-with-digests

# Regenerate yesterday's digest for user
./docker.sh django generate_digest --user-id 1 --date 2024-12-20 --regenerate

# Test digest generation for user
./docker.sh django generate_digest --user-id 1 --test --verbosity 2

# Generate historical digests
for date in 2024-12-15 2024-12-16 2024-12-17; do
    ./docker.sh django generate_digest --user-id 1 --date $date
done
```

#### Output

```
🚀 Starting digest generation...
📅 Target date: 2024-12-21
👥 Users to process: 1
🔄 Regenerate: False

✅ john.doe: Generated digest in 32,500ms
   📊 Topics: 4, Stories: 12, Articles: 28
   💰 Cost: $0.089
   🎯 Strategy: Articles-Based Digest

📊 Summary: 1 digests generated, 0 failed, 32.5s total time
```

---

## 🧪 Testing Commands

### test_digest_routing

Test digest generation strategies and routing.

#### Basic Usage

```bash
# Test specific strategy for user
./docker.sh django test_digest_routing --user-id 1 --strategy articles_based

# Compare both strategies
./docker.sh django test_digest_routing --user-id 1 --compare

# Test both strategies sequentially
./docker.sh django test_digest_routing --user-id 1 --test-both

# Dry run validation
./docker.sh django test_digest_routing --user-id 1 --dry-run
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--user-id` | Integer | User to test with | Required |
| `--strategy` | String | Specific strategy to test | User's preference |
| `--compare` | Flag | Compare all available strategies | False |
| `--test-both` | Flag | Test articles and events strategies | False |
| `--dry-run` | Flag | Validate configuration only | False |
| `--date` | String | Target date for testing | Today |

#### Examples

```bash
# Test user's default strategy
./docker.sh django test_digest_routing --user-id 1

# Performance comparison
./docker.sh django test_digest_routing --user-id 1 --compare

# Test specific strategy with verbose output
./docker.sh django test_digest_routing --user-id 1 --strategy events_based --verbosity 2

# Validate configuration
./docker.sh django test_digest_routing --user-id 1 --dry-run
```

#### Output

```
🧪 Testing digest routing for user: john.doe
📅 Target date: 2024-12-21
🎯 Strategy: Articles-Based Digest

✅ Strategy Test Results:
   ⏱️  Generation time: 32.5s
   📊 Topics generated: 4
   📰 Stories created: 12
   📖 Articles processed: 28
   💰 Total cost: $0.089
   🤖 AI model: gpt-4o-mini

🔍 Content Quality:
   ✅ Introduction: Generated (156 words)
   ✅ Conclusion: Generated (79 words)
   ✅ All topics have content
   ✅ All stories have summaries

📊 Performance Metrics:
   🎯 Target: <30s (✅ PASS)
   💰 Target: <$0.15 (✅ PASS)
   📊 Content coverage: 100%
```

### test_digest_components

Test individual digest system components.

#### Basic Usage

```bash
# Test content selector
./docker.sh django test_digest_components --component content_selector --user-id 1

# Test AI generator
./docker.sh django test_digest_components --component ai_generator --topic-id 1

# Test all components
./docker.sh django test_digest_components --all --user-id 1

# Component health check
./docker.sh django test_digest_components --health-check
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--component` | String | Component to test | None |
| `--user-id` | Integer | User context for testing | None |
| `--topic-id` | Integer | Topic context for testing | None |
| `--all` | Flag | Test all components | False |
| `--health-check` | Flag | Basic health check | False |

#### Available Components

- `content_selector`: Article selection and filtering
- `ai_generator`: LLM content generation
- `digest_router`: Strategy routing
- `event_enhancer`: Event clustering and scoring

---

## ⚙️ Configuration Commands

### set_digest_strategy

Manage digest generation strategies.

#### Basic Usage

```bash
# Show current default strategy
./docker.sh django set_digest_strategy --show-current

# Set default strategy
./docker.sh django set_digest_strategy --strategy articles_based

# List available strategies
./docker.sh django set_digest_strategy --list

# Validate configuration
./docker.sh django set_digest_strategy --validate
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--strategy` | String | Strategy to set as default | None |
| `--show-current` | Flag | Show current default strategy | False |
| `--list` | Flag | List available strategies | False |
| `--validate` | Flag | Validate configuration | False |

#### Available Strategies

- `articles_based`: Simple, reliable article-based generation
- `events_based`: Advanced event-based generation with clustering

#### Examples

```bash
# Check current configuration
./docker.sh django set_digest_strategy --show-current

# Switch to events-based strategy
./docker.sh django set_digest_strategy --strategy events_based

# List all available strategies
./docker.sh django set_digest_strategy --list

# Validate system configuration
./docker.sh django set_digest_strategy --validate
```

#### Output

```
🎯 Current Default Strategy: Articles-Based Digest

📋 Available Strategies:
   ✅ articles_based - Articles-Based Digest (Current)
   🧪 events_based - Events-Based Digest

⚙️  Configuration Status:
   ✅ DigestService: Initialized
   ✅ DigestRouter: 2 strategies registered
   ✅ AI Providers: OpenAI, Anthropic available
   ✅ Database: Models migrated
```

---

## 📊 Display Commands

### display_digest

Display existing digest content in formatted output.

#### Basic Usage

```bash
# Display latest digest for user
./docker.sh django display_digest --user-id 1

# Display specific digest by date
./docker.sh django display_digest --user-id 1 --date 2024-12-21

# Display with details
./docker.sh django display_digest --user-id 1 --verbose

# Export to file
./docker.sh django display_digest --user-id 1 --export digest.html
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--user-id` | Integer | User whose digest to display | Required |
| `--date` | String | Specific date (YYYY-MM-DD) | Latest |
| `--verbose` | Flag | Show detailed information | False |
| `--export` | String | Export to file | None |
| `--format` | String | Output format (text, html, json) | text |

#### Examples

```bash
# Display latest digest
./docker.sh django display_digest --user-id 1

# Display specific date with details
./docker.sh django display_digest --user-id 1 --date 2024-12-21 --verbose

# Export as HTML
./docker.sh django display_digest --user-id 1 --export digest.html --format html

# Display as JSON
./docker.sh django display_digest --user-id 1 --format json
```

#### Output

```
📰 Daily Brief for December 21, 2024
👤 User: john.doe
📅 Generated: 2024-12-21 08:30:15 UTC
⏱️  Generation time: 32.5s
💰 Cost: $0.089

🌟 INTRODUCTION
Here's what's happening today across the topics you follow...

📊 TECHNOLOGY
📝 Abstract: Major developments in AI and tech continue to shape the industry...

💡 Key Facts:
   • OpenAI releases GPT-5 with improved capabilities
   • Apple announces new MacBook Pro with M4 chip
   • Meta introduces advanced VR headset

🔍 Perspectives:
   • Industry analysts see this as transformative
   • Critics worry about implementation challenges

📖 Stories:
   1. OpenAI's GPT-5 Breakthrough
      OpenAI today announced the release of GPT-5...
      
   2. Apple's M4 MacBook Pro
      Apple unveiled its latest MacBook Pro...

🎯 CONCLUSION
Today's developments in technology, business, and science show...
```

---

## 🔧 Utility Commands

### test_ai_fallback_digest

Test AI fallback mechanisms and error handling.

#### Basic Usage

```bash
# Test AI provider fallback
./docker.sh django test_ai_fallback_digest --user-id 1

# Test with specific provider failure
./docker.sh django test_ai_fallback_digest --user-id 1 --simulate-failure openai

# Test retry mechanisms
./docker.sh django test_ai_fallback_digest --user-id 1 --test-retries
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--user-id` | Integer | User context for testing | Required |
| `--simulate-failure` | String | Simulate provider failure | None |
| `--test-retries` | Flag | Test retry mechanisms | False |
| `--max-retries` | Integer | Maximum retry attempts | 3 |

---

## 📈 Monitoring Commands

### digest_system_status

Check digest system health and status.

#### Basic Usage

```bash
# System health check
./docker.sh django digest_system_status

# Detailed component status
./docker.sh django digest_system_status --detailed

# Performance metrics
./docker.sh django digest_system_status --metrics

# Check recent activity
./docker.sh django digest_system_status --recent-activity
```

#### Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--detailed` | Flag | Show detailed component status | False |
| `--metrics` | Flag | Show performance metrics | False |
| `--recent-activity` | Flag | Show recent digest activity | False |

#### Output

```
🏥 Digest System Health Check

⚙️  Core Components:
   ✅ DigestService: Operational
   ✅ DigestRouter: 2 strategies available
   ✅ ContentSelector: Database connected
   ✅ AIGenerator: OpenAI ✅, Anthropic ✅

📊 Recent Performance (Last 24h):
   📰 Digests generated: 142
   ✅ Success rate: 98.6%
   ⏱️  Average generation time: 28.3s
   💰 Total cost: $12.47
   🤖 Primary AI model: gpt-4o-mini

🔄 Strategy Usage:
   📊 Articles-based: 89% (126 digests)
   🧪 Events-based: 11% (16 digests)

⚠️  Alerts:
   None - all systems operational
```

---

## 🚨 Error Handling

### Common Error Scenarios

#### User Configuration Issues

```bash
# User has no followed topics
❌ Error: User 'john.doe' has no followed topics
💡 Solution: Have user complete onboarding and select topics

# User preferences invalid
❌ Error: Invalid time_window preference: '96h'
💡 Solution: Use valid time window: 24h, 48h, 72h, full_previous_day, full_previous_2_days
```

#### Content Issues

```bash
# Insufficient content
❌ Error: Insufficient content for digest generation
💡 Solution: Check article pipeline status and content availability

# AI generation failure
❌ Error: Failed to generate topic summary: Rate limit exceeded
💡 Solution: Check AI provider status and rate limits
```

#### System Issues

```bash
# Database connectivity
❌ Error: Database connection failed
💡 Solution: Check database status and connectivity

# Missing dependencies
❌ Error: 'DigestService' object has no attribute 'content_selector'
💡 Solution: Restart services and check initialization
```

### Debugging Commands

```bash
# Enable debug logging
./docker.sh django generate_digest --user-id 1 --verbosity 3

# Test individual components
./docker.sh django test_digest_components --component content_selector --user-id 1

# Validate configuration
./docker.sh django set_digest_strategy --validate

# Check system status
./docker.sh django digest_system_status --detailed
```

---

## 📋 Command Cheat Sheet

### Daily Operations

```bash
# Generate digests for all users
./docker.sh django generate_digest --all-users --skip-users-with-digests

# Check system health
./docker.sh django digest_system_status

# Display recent digest
./docker.sh django display_digest --user-id 1
```

### Development & Testing

```bash
# Test user digest generation
./docker.sh django test_digest_routing --user-id 1 --compare

# Test specific strategy
./docker.sh django test_digest_routing --user-id 1 --strategy events_based

# Component testing
./docker.sh django test_digest_components --all --user-id 1
```

### Configuration Management

```bash
# Check current strategy
./docker.sh django set_digest_strategy --show-current

# Switch strategy
./docker.sh django set_digest_strategy --strategy articles_based

# Validate configuration
./docker.sh django set_digest_strategy --validate
```

### Troubleshooting

```bash
# Debug generation
./docker.sh django generate_digest --user-id 1 --test --verbosity 3

# Test AI fallback
./docker.sh django test_ai_fallback_digest --user-id 1

# Check component health
./docker.sh django test_digest_components --health-check
```

This comprehensive command reference provides all the tools needed to manage, test, and troubleshoot the Daily Digest System effectively.
