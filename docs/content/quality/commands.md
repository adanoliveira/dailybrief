# Command Reference

> **Complete reference for all Content Quality Assessment management commands**

## Overview

The Content Quality Assessment System provides a comprehensive set of Django management commands for evaluation, analysis, and optimization. All commands are designed to work within the Docker environment and provide detailed output for operational use.

## Command Execution Format

All commands use the following format:
```bash
./docker.sh django <command_name> [options]
```

## Core Evaluation Commands

### evaluate_quality

**Purpose**: Evaluate content quality for single articles or batches

**Location**: `backend/apps/content/quality/management/commands/evaluate_quality.py`

#### Basic Usage

```bash
# Evaluate a single article by public ID
./docker.sh django evaluate_quality --article-id abc123-def456

# Evaluate multiple articles by public ID
./docker.sh django evaluate_quality --article-ids abc123,def456,ghi789

# Evaluate recent articles (limit by count)
./docker.sh django evaluate_quality --limit 10

# Evaluate recent articles with specific model
./docker.sh django evaluate_quality --limit 5 --model gpt-4o-mini
```

#### Advanced Options

```bash
# Full evaluation with HTML preprocessing
./docker.sh django evaluate_quality \
  --article-id abc123-def456 \
  --include-html \
  --verbose \
  --model gpt-4o-mini

# Batch evaluation with rate limiting
./docker.sh django evaluate_quality \
  --limit 20 \
  --delay 3 \
  --model gpt-4o-mini \
  --template comprehensive_quality_evaluation_v3.1

# Evaluate specific quality class for testing
./docker.sh django evaluate_quality \
  --quality-class good \
  --max-examples 5 \
  --verbose
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--article-id` | string | - | Specific article public ID to evaluate |
| `--article-ids` | string | - | Comma-separated list of public IDs |
| `--limit` | int | 5 | Number of recent articles to evaluate |
| `--model` | string | gpt-4o-mini | AI model to use for evaluation |
| `--template` | string | active | Template ID to use |
| `--include-html` | flag | False | Include HTML in evaluation |
| `--delay` | float | 2.0 | Delay between evaluations (seconds) |
| `--verbose` | flag | False | Detailed output |
| `--quality-class` | string | - | Filter by quality class |
| `--max-examples` | int | 10 | Maximum examples to process |

#### Output Example

```
📊 Content Quality Evaluation Results
══════════════════════════════════════════════════════════════════

✅ Article: "Latest Tech News Update" (ID: abc123-def456)
┌─────────────────┬─────────┬──────────────────────────────────────┐
│ Dimension       │ Score   │ Assessment                           │
├─────────────────┼─────────┼──────────────────────────────────────┤
│ Overall         │  0.742  │ GOOD (High quality with minor issues)│
│ Completeness    │  0.85   │ Most content captured                │
│ Purity          │  0.90   │ Very clean extraction                │
│ Structure       │  0.70   │ Good structure preservation          │
│ Readability     │  0.75   │ Well formatted and readable          │
└─────────────────┴─────────┴──────────────────────────────────────┘

💡 Key Insights:
  • Strong content extraction with minimal noise
  • Minor structural formatting issues
  • Missing some image captions and metadata

⏱️  Processing: 22.3s | 🎯 Confidence: 0.89 | 💰 Cost: $0.010
```

---

### evaluate_batch_by_ids

**Purpose**: Evaluate specific articles by database ID with comprehensive statistics

**Location**: `backend/apps/content/quality/management/commands/evaluate_batch_by_ids.py`

#### Usage

```bash
# Evaluate specific articles by database ID
./docker.sh django evaluate_batch_by_ids \
  --ids "15999,15997,15996,15994,15989" \
  --model gpt-4o-mini \
  --delay 2 \
  --verbose

# Evaluate with custom template
./docker.sh django evaluate_batch_by_ids \
  --ids "15999,15997,15996" \
  --template structured_rubric_evaluation_v2025-05-v3 \
  --model gpt-4o-mini \
  --include-html

# Fast evaluation without HTML
./docker.sh django evaluate_batch_by_ids \
  --ids "15999,15997" \
  --no-include-html \
  --delay 1
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--ids` | string | Yes | Comma-separated database IDs |
| `--model` | string | No | AI model (default: gpt-4o-mini) |
| `--template` | string | No | Template ID (default: active) |
| `--delay` | float | No | Delay between requests (default: 2.0) |
| `--include-html` | flag | No | Include HTML in evaluation |
| `--no-include-html` | flag | No | Explicitly exclude HTML |
| `--verbose` | flag | No | Detailed per-article output |

#### Comprehensive Statistics Output

```
📈 Batch Evaluation Summary
══════════════════════════════════════════════════════════════════

📊 Quality Distribution (20 articles):
┌─────────────────────┬───────────┬────────────┬─────────────────┐
│ Quality Class       │ Count     │ Percentage │ Score Range     │
├─────────────────────┼───────────┼────────────┼─────────────────┤
│ 🟢 Excellent (≥0.8) │ 1         │ 5%         │ 0.8 to 1.0     │
│ 🟢 Good (0.5-0.8)   │ 1         │ 5%         │ 0.5 to 0.8     │
│ ⚪ Fair (0.2-0.5)    │ 0         │ 0%         │ 0.2 to 0.5     │
│ 🟡 Poor (-0.2-0.2)  │ 4         │ 20%        │ -0.2 to 0.2    │
│ 🔴 Failed (<-0.2)   │ 14        │ 70%        │ -1.0 to -0.2   │
└─────────────────────┴───────────┴────────────┴─────────────────┘

📊 Average Scores:
┌─────────────┬─────────┬─────────────────────────────────────────┐
│ Dimension   │ Average │ Quality Assessment                      │
├─────────────┼─────────┼─────────────────────────────────────────┤
│ Overall     │ -0.342  │ 🔴 FAILED - Significant extraction issues│
│ Completeness│  0.325  │ 🟡 POOR - Missing substantial content   │
│ Purity      │  0.255  │ 🟡 POOR - High noise contamination     │
│ Structure   │  0.380  │ 🟡 POOR - Structural degradation       │
│ Readability │  0.443  │ ⚪ FAIR - Moderate formatting issues    │
└─────────────┴─────────┴─────────────────────────────────────────┘

💰 Cost Analysis:
┌─────────────────────┬──────────────┐
│ Total Articles      │ 20           │
│ Successful Evals    │ 20 (100%)    │
│ Total Cost          │ $0.20        │
│ Average Cost/Eval   │ $0.010       │
│ Total Tokens Used   │ 1,540,000    │
│ Average Tokens/Eval │ 77,000       │
└─────────────────────┴──────────────┘
```

---

## Template Analysis Commands

### compare_templates

**Purpose**: A/B test different prompt templates for accuracy optimization

**Location**: `backend/apps/content/quality/management/commands/compare_templates.py`

#### Usage Examples

```bash
# Compare all available templates
./docker.sh django compare_templates

# Compare specific templates on good quality examples
./docker.sh django compare_templates \
  --templates comprehensive_quality_evaluation_v3.1,structured_rubric_evaluation_v2025-05-v3 \
  --quality-class good \
  --verbose

# Comprehensive comparison by quality class
./docker.sh django compare_templates \
  --by-class \
  --max-examples 2 \
  --model gpt-4o-mini

# Quick template comparison with specific model
./docker.sh django compare_templates \
  --templates comprehensive_quality_evaluation_v3.1,structured_rubric_evaluation_v2025-05-v3 \
  --quality-class imperfect \
  --max-examples 1 \
  --model gpt-4o-mini \
  --delay 3
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--templates` | string | all | Comma-separated template IDs to compare |
| `--quality-class` | string | - | Specific quality class (perfect, good, imperfect, awful) |
| `--by-class` | flag | False | Compare across all quality classes |
| `--max-examples` | int | 1 | Maximum examples per quality class |
| `--model` | string | gpt-4o-mini | AI model for evaluation |
| `--delay` | float | 2.0 | Delay between API calls |
| `--verbose` | flag | False | Detailed per-article comparison |

#### Detailed Comparison Output

```
🔬 Template Comparison Analysis
══════════════════════════════════════════════════════════════════

📊 Template Performance Summary:
┌─────────────────────────────────────────┬─────────────┬─────────────┐
│ Template                                │ Total MAE   │ Ranking     │
├─────────────────────────────────────────┼─────────────┼─────────────┤
│ 🥇 comprehensive_quality_evaluation_v3.1│ 0.078       │ Winner      │
│ 🥈 structured_rubric_evaluation_v2025-..│ 0.121       │ Runner-up   │
└─────────────────────────────────────────┴─────────────┴─────────────┘

📈 Detailed Performance by Quality Class:

🟢 GOOD Quality Examples (3 articles):
┌─────────────────────────────────────────┬─────────────┬─────────────┐
│ Template                                │ MAE         │ Performance │
├─────────────────────────────────────────┼─────────────┼─────────────┤
│ comprehensive_quality_evaluation_v3.1   │ 0.005       │ Excellent   │
│ structured_rubric_evaluation_v2025-05-v3│ 0.060       │ Very Good   │
└─────────────────────────────────────────┴─────────────┴─────────────┘

⚪ IMPERFECT Quality Examples (6 articles):
┌─────────────────────────────────────────┬─────────────┬─────────────┐
│ Template                                │ MAE         │ Performance │
├─────────────────────────────────────────┼─────────────┼─────────────┤
│ comprehensive_quality_evaluation_v3.1   │ 0.196       │ Good        │
│ structured_rubric_evaluation_v2025-05-v3│ 0.303       │ Acceptable  │
└─────────────────────────────────────────┴─────────────┴─────────────┘

🔴 AWFUL Quality Examples (2 articles):
┌─────────────────────────────────────────┬─────────────┬─────────────┐
│ Template                                │ MAE         │ Performance │
├─────────────────────────────────────────┼─────────────┼─────────────┤
│ structured_rubric_evaluation_v2025-05-v3│ 0.000       │ Perfect     │
│ comprehensive_quality_evaluation_v3.1   │ 0.362       │ Poor        │
└─────────────────────────────────────────┴─────────────┴─────────────┘

🎯 Recommendations:
• Use comprehensive_quality_evaluation_v3.1 for general evaluation
• Use structured_rubric_evaluation_v2025-05-v3 for quality filtering
• Consider multi-template strategy for optimal results
```

---

## Reference Data Commands

### create_reference_examples

**Purpose**: Create and manage reference quality examples for few-shot learning

**Location**: `backend/apps/content/quality/management/commands/create_reference_examples.py`

#### Usage

```bash
# Create reference example interactively
./docker.sh django create_reference_examples --interactive

# Create from specific article with manual scores
./docker.sh django create_reference_examples \
  --article-id abc123-def456 \
  --quality-class good \
  --completeness 0.85 \
  --purity 0.90 \
  --structure 0.75 \
  --readability 0.80 \
  --explanation "High quality extraction with minor formatting issues"

# Bulk create from CSV file
./docker.sh django create_reference_examples --from-csv reference_examples.csv

# List existing reference examples
./docker.sh django create_reference_examples --list
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `--interactive` | flag | Interactive reference example creation |
| `--article-id` | string | Article public ID for reference |
| `--quality-class` | string | Quality class (perfect, good, imperfect, awful) |
| `--completeness` | float | Completeness score (0-1) |
| `--purity` | float | Purity score (0-1) |
| `--structure` | float | Structure score (0-1) |
| `--readability` | float | Readability score (0-1) |
| `--explanation` | string | Detailed explanation of assessment |
| `--from-csv` | string | Import from CSV file |
| `--list` | flag | List existing examples |

---

### calibrate_quality_evaluator

**Purpose**: Calibrate evaluator accuracy against reference examples

**Location**: `backend/apps/content/quality/management/commands/calibrate_quality_evaluator.py`

#### Usage

```bash
# Full calibration across all examples
./docker.sh django calibrate_quality_evaluator

# Calibrate specific template
./docker.sh django calibrate_quality_evaluator \
  --template comprehensive_quality_evaluation_v3.1 \
  --model gpt-4o-mini

# Calibrate specific quality class
./docker.sh django calibrate_quality_evaluator \
  --quality-class good \
  --max-examples 5 \
  --verbose

# Generate calibration report
./docker.sh django calibrate_quality_evaluator \
  --report-only \
  --output-file calibration_report.json
```

---

## Utility Commands

### show_prompt_example

**Purpose**: Display prompt examples for development and debugging

**Location**: `backend/apps/content/quality/management/commands/show_prompt_example.py`

#### Usage

```bash
# Show prompt for specific template and article
./docker.sh django show_prompt_example \
  --template comprehensive_quality_evaluation_v3.1 \
  --article-id abc123-def456

# Show prompt with HTML preprocessing
./docker.sh django show_prompt_example \
  --template structured_rubric_evaluation_v2025-05-v3 \
  --article-id abc123-def456 \
  --include-html \
  --show-token-count

# Export prompt to file
./docker.sh django show_prompt_example \
  --template comprehensive_quality_evaluation_v3.1 \
  --article-id abc123-def456 \
  --output-file prompt_example.txt
```

#### Output Example

```
🔍 Prompt Template Example
══════════════════════════════════════════════════════════════════

Template: comprehensive_quality_evaluation_v3.1
Article: "AI Breakthrough in Medical Diagnosis" (abc123-def456)
Token Count: 76,543 tokens

📝 Generated Prompt:
══════════════════════════════════════════════════════════════════

You are a content quality expert evaluating how well article content 
was extracted from its original HTML source...

[Full prompt content displayed]

📊 Reference Examples Included:
┌─────────────────┬────────────┬─────────────────────────────────┐
│ Quality Class   │ Count      │ Example Articles                │
├─────────────────┼────────────┼─────────────────────────────────┤
│ Perfect         │ 1          │ "Tech Innovation Showcase"      │
│ Good            │ 1          │ "Climate Change Analysis"       │
│ Imperfect       │ 1          │ "Market Updates Today"          │
│ Awful           │ 1          │ "Breaking News Alert"           │
└─────────────────┴────────────┴─────────────────────────────────┘

💾 Prompt saved to: prompt_example.txt
```

---

## Global Options

### Common Parameters

All commands support these common options:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--model` | string | gpt-4o-mini | AI model selection |
| `--template` | string | active | Template ID to use |
| `--delay` | float | 2.0 | Rate limiting delay |
| `--verbose` | flag | False | Detailed output |
| `--help` | flag | False | Show command help |

### Available AI Models

| Model | Cost/Eval | Context | Best Use Case |
|-------|-----------|---------|---------------|
| `gpt-4o-mini` | $0.013 | 128K | Production (recommended) |
| `gpt-4.1-mini` | $0.048 | 2M | Large content, reliability |
| `gpt-4.1-nano` | $0.012 | 2M | Budget optimization |
| `gpt-4.1-full` | $0.242 | 2M | Maximum accuracy |

### Available Templates

| Template ID | Version | Best For |
|-------------|---------|----------|
| `comprehensive_quality_evaluation_v3.1` | v3.1 | General evaluation, production |
| `structured_rubric_evaluation_v2025-05-v3` | v3 | Quality filtering, extremes |
| `few_shot_example_v1.0` | v1.0 | Example formatting |

## Error Handling

### Common Error Patterns

1. **Rate Limiting Errors**
   ```
   Error: OpenAI API rate limit exceeded
   Solution: Increase --delay parameter (try 3-5 seconds)
   ```

2. **Model Context Exceeded**
   ```
   Error: Token limit exceeded for model
   Solution: Use gpt-4.1-mini or gpt-4.1-nano for large content
   ```

3. **Article Not Found**
   ```
   Error: Article with ID 'abc123' not found
   Solution: Verify article ID and processing status
   ```

4. **Template Not Found**
   ```
   Error: Template 'invalid_template' not found
   Solution: Use --help to list available templates
   ```

### Debugging Commands

```bash
# Check system status
./docker.sh django shell -c "from apps.content.quality.evaluator import ContentQualityEvaluator; print('System OK')"

# List available templates
./docker.sh django shell -c "from apps.content.quality.prompt_templates import AVAILABLE_TEMPLATES; print(list(AVAILABLE_TEMPLATES.keys()))"

# Verify article exists
./docker.sh django shell -c "from apps.articles.models import Article; print(Article.objects.filter(public_id='abc123').exists())"
```

## Command Chaining Examples

### Daily Quality Monitoring

```bash
#!/bin/bash
# Daily quality check script

echo "🌅 Daily Quality Check - $(date)"

# Check recent article quality
./docker.sh django evaluate_quality --limit 10 --verbose

# Compare template performance weekly
if [ $(date +%u) -eq 1 ]; then
    echo "📊 Weekly Template Comparison"
    ./docker.sh django compare_templates --by-class
fi

# Monthly calibration
if [ $(date +%d) -eq 1 ]; then
    echo "🎯 Monthly Calibration"
    ./docker.sh django calibrate_quality_evaluator --report-only
fi
```

### Content Pipeline Analysis

```bash
#!/bin/bash
# Analyze content extraction pipeline

# Get recent article IDs
RECENT_IDS=$(./docker.sh django shell -c "
from apps.articles.models import Article
articles = Article.objects.filter(process_status='completed').order_by('-id')[:20]
print(','.join(str(a.id) for a in articles))
")

# Evaluate batch
./docker.sh django evaluate_batch_by_ids \
  --ids "$RECENT_IDS" \
  --model gpt-4o-mini \
  --verbose

echo "📊 Pipeline analysis complete"
```

---

## Related Documentation

- **[Process Workflows](./workflows.md)** - End-to-end evaluation processes
- **[Implementation Guide](./implementation.md)** - Technical implementation details
- **[Architecture Overview](./architecture.md)** - System design and components 