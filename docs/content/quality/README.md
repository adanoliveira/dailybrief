# Content Quality Assessment System

> **AI-powered content extraction quality evaluation with domain-specific scoring**

A comprehensive system for assessing the quality of content extraction from raw HTML sources, designed to optimize the DailyBrief content processing pipeline through intelligent evaluation, template-based assessment, and programmatic scoring.

## 📖 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Recent Achievements](#recent-achievements)
- [Current Status](#current-status)

## Overview

The Content Quality Assessment System evaluates how well content was extracted from HTML sources across four key dimensions:

- **Completeness** (0-1): How much important content was captured
- **Purity** (0-1): How clean the content is (minimal noise)
- **Structure** (0-1): How well original structure is preserved
- **Readability** (0-1): How readable and well-formatted the output is

### Key Features

✅ **Consistent Scoring**: Domain-specific formula ensures reliable quality metrics  
✅ **Template-Based Evaluation**: Multiple prompt templates for different use cases  
✅ **HTML Structure Preservation**: Advanced preprocessing maintains document hierarchy  
✅ **Few-Shot Learning**: Reference examples calibrate AI evaluations  
✅ **Batch Processing**: Efficient evaluation of multiple articles  
✅ **Cost Optimization**: Smart preprocessing reduces token usage  
✅ **Template Comparison**: A/B testing framework for prompt optimization  

## Quick Start

### Evaluate a Single Article

```bash
# Using default template and model
./docker.sh django evaluate_quality --article-id abc123-def456

# Using specific template and model
./docker.sh django evaluate_quality --article-id abc123-def456 --model gpt-4o-mini
```

### Batch Evaluation

```bash
# Evaluate specific articles by ID
./docker.sh django evaluate_batch_by_ids --ids "15999,15997,15996" --model gpt-4o-mini

# Evaluate recent articles
./docker.sh django evaluate_quality --limit 10 --model gpt-4o-mini
```

### Template Comparison

```bash
# Compare templates on specific quality class
./docker.sh django compare_templates --quality-class good --verbose

# Compare all templates across all examples
./docker.sh django compare_templates --by-class
```

## Architecture

```
Content Quality System
├── Core Assessment
│   ├── prompt_templates.py     # Template management & scoring logic
│   ├── evaluator.py           # Main evaluation orchestration
│   ├── models.py              # Domain scoring formula & data models
│   └── html_preprocessor.py   # HTML optimization for evaluation
├── Reference System
│   ├── ReferenceQualityExample # Curated examples for calibration
│   └── Few-shot learning      # Template-based example formatting
├── Management Commands
│   ├── evaluate_batch_by_ids.py   # Batch evaluation by article IDs
│   ├── compare_templates.py       # Template A/B testing
│   ├── calibrate_quality_evaluator.py # Accuracy calibration
│   └── create_reference_examples.py   # Reference curation
└── Supporting Infrastructure
    ├── AI Service Integration  # OpenAI/Anthropic abstraction
    └── Cost Tracking          # Token usage & pricing analysis
```

## Documentation

### 📋 Core Documentation
- **[Architecture Overview](./architecture.md)** - System design and component relationships
- **[Implementation Guide](./implementation.md)** - Technical implementation details
- **[API Reference](./api-reference.md)** - Classes, methods, and interfaces

### 🔧 Operational Guides  
- **[Process Workflows](./workflows.md)** - End-to-end evaluation processes
- **[Command Reference](./commands.md)** - Management command documentation
- **[Template System](./templates.md)** - Prompt template architecture

### 📊 Analysis & Results
- **[Performance Analysis](./performance.md)** - Evaluation results and insights
- **[Template Comparison](./template-comparison.md)** - A/B testing methodology and results
- **[Optimization Strategy](./optimization.md)** - Future improvements and roadmap

## Recent Achievements

### ✅ **Consistent Scoring Architecture** *(December 2024)*
- **Problem**: Inconsistent overall score calculation between templates
- **Solution**: Moved calculation to programmatic domain-specific formula
- **Impact**: 100% scoring consistency, eliminated LLM mathematical errors

### ✅ **HTML Structure Preservation** *(December 2024)*  
- **Problem**: Plain text preprocessing lost document structure
- **Solution**: Enhanced HTML preprocessor with structure preservation
- **Impact**: Better content quality assessment, preserved semantic hierarchy

### ✅ **Template Optimization** *(December 2024)*
- **Problem**: Templates requested overall scores from LLM
- **Solution**: Updated templates to only request 4 dimension scores
- **Impact**: More reliable assessments, reduced token usage

### ✅ **Comprehensive Evaluation Framework** *(December 2024)*
- **Problem**: No systematic way to compare template performance
- **Solution**: Built template comparison command with statistical analysis
- **Impact**: Data-driven template optimization, A/B testing capability

## Current Status

### 🎯 **Template Performance** *(Latest Results)*

**Best Performing Templates:**
- **Good Quality Content**: `comprehensive_quality_evaluation_v3.1` (MAE: 0.078)
- **Poor Quality Content**: `structured_rubric_evaluation_v2025-05-v3` (MAE: 0.000)

### 📊 **Extraction Pipeline Analysis** *(20 Recent Articles)*

```
Quality Distribution:
├── Excellent (≥0.8): 1 article  (5%)
├── Good (0.5-0.8):   1 article  (5%)  
├── Fair (0.2-0.5):   0 articles (0%)
├── Poor (-0.2-0.2):  4 articles (20%)
└── Failed (<-0.2):   14 articles (70%)

Average Scores:
├── Overall: -0.342 (needs improvement)
├── Completeness: 0.325 (missing content)
├── Purity: 0.255 (high noise levels)
├── Structure: 0.380 (formatting issues)
└── Readability: 0.443 (moderate quality)
```

**⚠️ Key Finding**: Content extraction pipeline needs significant improvements in noise filtering and content detection.

### 💰 **Cost Efficiency**
- **Average Cost**: $0.010 per article evaluation
- **Token Usage**: ~77K tokens per article (optimized for gpt-4o-mini)
- **Processing Time**: ~23 seconds per article with rate limiting

## What's Next

### 🔧 **Immediate Priorities**
1. **Content Extraction Improvements** - Address noise filtering and completeness issues
2. **Site-Specific Extractors** - Custom logic for major news sources
3. **Token Management** - Handle large articles exceeding context limits

### 🚀 **Future Enhancements**
1. **Real-time Quality Monitoring** - Live quality dashboards
2. **Automated Template Optimization** - ML-driven template improvement
3. **Quality-based Routing** - Dynamic processing based on content complexity

---

## Contributing

See individual documentation files for detailed implementation guides and contribution patterns.

## Related Systems

- **[Articles Feed System](../articles-feed/)** - Content ingestion and processing
- **[Content Processor](../../backend/apps/content/processor/)** - Extraction algorithms
- **[AI Providers](../../backend/apps/aiproviders/)** - LLM service abstraction 