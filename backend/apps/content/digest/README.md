# Daily Digest System

The Daily Digest system generates personalized news summaries for users using an intelligent routing mechanism that can switch between different digest generation strategies.

## Architecture Overview

The digest system uses a **strategy pattern** with a central router that can switch between different digest generation approaches:

### Core Components

1. **DigestService** - Main orchestrator that handles user requests
2. **DigestRouter** - Routes requests to appropriate strategies
3. **DigestStrategy** (Abstract Base) - Base class for all strategies
4. **ArticlesDigestStrategy** - Simple, reliable article-based generation
5. **EventsDigestStrategy** - Complex event-based generation with clustering

## Available Strategies

### 1. Articles-Based Digest (Primary)
**Status**: ✅ **Current Default**

**Description**: Generates digests by directly processing articles grouped by topic without complex event detection.

**Features**:
- Direct article-to-topic mapping
- AI-powered topic summaries from multiple article abstracts
- Simple, reliable content selection
- Fast generation (~30 seconds)
- High reliability

**Use Case**: Production-ready, reliable digest generation

### 2. Events-Based Digest (Advanced)
**Status**: 🔬 **Experimental**

**Description**: Generates digests by processing articles through event detection, clustering, and semantic analysis.

**Features**:
- Event detection and clustering
- Semantic similarity analysis  
- Multi-article event synthesis
- Complex scoring and ranking
- Slower generation (~75 seconds)
- More sophisticated but potentially less reliable

**Use Case**: Advanced digest generation when event clustering is working well

## Configuration

### Default Strategy
The system defaults to **articles-based** strategy for reliability. This can be changed:

```bash
# Check current default
./docker.sh django set_digest_strategy --show-current

# Change default strategy  
./docker.sh django set_digest_strategy --strategy articles_based
./docker.sh django set_digest_strategy --strategy events_based

# List available strategies
./docker.sh django set_digest_strategy --list
```

### User-Specific Strategy
Individual users can have strategy preferences in their digest settings:

```python
# In user's digest_preferences
{
    "digest_strategy": "articles_based",  # or "events_based"
    "max_topics": 6,
    "max_articles_per_topic": 30,  # Feed all available articles to LLM (up to 30)
    # ... other preferences
}
```

### Django Settings Override
For persistent configuration across server restarts:

```python
# In settings.py
DIGEST_DEFAULT_STRATEGY = 'articles_based'  # or 'events_based'
```

## Usage

### Regular Digest Generation
```bash
# Uses default strategy (articles-based)
./docker.sh django generate_digest --user-id 1

# Force regeneration
./docker.sh django generate_digest --user-id 1 --regenerate
```

### Testing Strategies
```bash
# Test specific strategy
./docker.sh django test_digest_routing --user-id 1 --strategy articles_based

# Compare both strategies
./docker.sh django test_digest_routing --user-id 1 --compare

# Test both strategies sequentially
./docker.sh django test_digest_routing --user-id 1 --test-both

# Validate configuration
./docker.sh django test_digest_routing --user-id 1 --dry-run
```

## Strategy Details

### Articles-Based Strategy
```
Flow:
1. Get articles by topic for the time window
2. Generate AI topic summaries from article abstracts
3. Create one story per topic using the AI summary
4. Generate digest introduction

Output:
- 1 story per topic (e.g., "Business Today", "Technology Today")
- AI-synthesized content from multiple articles
- Focus on breadth across topics
```

### Events-Based Strategy  
```
Flow:
1. Get articles by topic for the time window
2. Detect and cluster events from articles
3. Score and rank events by importance
4. Enhance events with related articles
5. Generate topic summaries from events
6. Create stories for each event
7. Generate digest introduction

Output:
- Multiple stories per topic based on events
- Event-focused narratives (e.g., "Bitcoin ETF Developments", "Apple Product Launches")
- Focus on depth within topics
```

## Performance Comparison

| Metric | Articles-Based | Events-Based |
|--------|---------------|--------------|
| **Speed** | ~30 seconds | ~75 seconds |
| **Reliability** | Very High | Medium |
| **Content Depth** | Medium | High |
| **Content Breadth** | High | Medium |
| **Complexity** | Low | High |
| **AI Calls** | 5 (4 topics + intro) | 10+ (topics + events + enhancements) |

## Error Handling

The router includes automatic fallback:

1. **Primary Strategy Fails** → Automatic fallback to articles-based strategy
2. **Fallback Strategy Fails** → Error propagated to user
3. **Strategy Not Found** → Fallback to default strategy

## Monitoring

Check digest generation logs for strategy usage:
```
INFO digest_router: Selected strategy 'Articles-Based Digest' for user username
INFO digest_service: Successfully generated digest using Articles-Based Digest in 30000ms
```

## Future Development

### Planned Improvements
1. **Event Detection Refinement** - Improve event clustering accuracy
2. **Hybrid Strategy** - Combine benefits of both approaches
3. **User Learning** - Automatic strategy selection based on user engagement
4. **A/B Testing Framework** - Compare strategy effectiveness

### Migration Path
As the events-based strategy improves:
1. Test with subset of users
2. Monitor quality metrics
3. Gradually increase adoption
4. Eventually make events-based the default

## Troubleshooting

### Common Issues

**Strategy Not Working**
```bash
# Validate configuration
./docker.sh django set_digest_strategy --validate

# Check available strategies
./docker.sh django set_digest_strategy --list
```

**Performance Issues**
- Articles-based: Check AI provider rate limits
- Events-based: Check event detection performance

**Content Quality Issues**  
- Test different strategies for comparison
- Review AI prompt templates
- Check source article quality

### Logs to Check
- `digest_router` - Strategy selection and routing
- `articles_digest_strategy` - Articles-based generation
- `events_digest_strategy` - Events-based generation  
- `digest_service` - Overall orchestration 