"""
Views for the summarization app API endpoints.

Provides REST API functionality for article summarization features.
"""
from datetime import datetime, timedelta

from apps.core.api_utils import (
    api_view, create_response, create_error_response,
    create_success_response
)
from apps.articles.models import Article
from .models import ArticleEmbedding
from .tasks import find_similar_articles


@api_view(['GET'], authenticate=False)
def similar_articles(request, article_id):
    """
    Find articles similar to the given article using embeddings.
    
    Implements the related-articles feature from the original plan:
    Returns articles with cosine similarity > threshold, ordered by similarity.
    
    URL: /api/content/similar/{article_id}/
    
    Query Parameters:
        - threshold: Similarity threshold (default: 0.22)
        - limit: Maximum results (default: 5)
        - days: Only include articles from last N days (optional)
    
    Response:
        {
            "success": true,
            "article_id": 15158,
            "similar_articles": [
                {
                    "article_id": 20863,
                    "headline": "Tech Workers Face Job Market Anxiety",
                    "abstract": "...",
                    "similarity_score": 0.174,
                    "published_at": "2025-01-15T12:00:00Z",
                    "url": "/article/20863/"
                }
            ],
            "total_found": 1
        }
    """
    try:
        # Validate article exists
        article = Article.objects.get(id=article_id)
        
        # Get and validate query parameters
        try:
            threshold = float(request.GET.get('threshold', 0.22))
            limit = int(request.GET.get('limit', 5))
        except ValueError:
            return create_error_response(
                "Invalid parameter format",
                status=400,
                error_code="INVALID_PARAMETER_FORMAT",
                details={
                    "threshold": "Must be a float between 0 and 1",
                    "limit": "Must be an integer between 1 and 50"
                }
            )
        
        days = request.GET.get('days')
        
        # Validate parameters
        if threshold < 0 or threshold > 1:
            return create_error_response(
                "Threshold must be between 0 and 1",
                status=400,
                error_code="INVALID_THRESHOLD",
                details={
                    "threshold": threshold,
                    "valid_range": "0.0 to 1.0"
                }
            )
        
        if limit < 1 or limit > 50:
            return create_error_response(
                "Limit must be between 1 and 50",
                status=400,
                error_code="INVALID_LIMIT",
                details={
                    "limit": limit,
                    "valid_range": "1 to 50"
                }
            )
        
        # Use the Celery task for similarity search
        result = find_similar_articles(
            article_id=article_id,
            similarity_threshold=threshold,
            limit=limit
        )
        
        if result['status'] == 'success':
            # Enhance results with additional data for frontend
            enhanced_articles = []
            
            for similar in result['similar_articles']:
                enhanced_articles.append({
                    'article_id': similar['article_id'],
                    'headline': similar['headline'],
                    'abstract': _get_article_abstract(similar['article_id']),
                    'similarity_score': similar['similarity_score'],
                    'published_at': similar['published_at'],
                    'url': f"/article/{similar['article_id']}/"
                })
            
            # Apply days filter if specified
            if days:
                try:
                    days_int = int(days)
                    cutoff_date = datetime.now() - timedelta(days=days_int)
                    enhanced_articles = [
                        art for art in enhanced_articles 
                        if datetime.fromisoformat(art['published_at'].replace('Z', '+00:00')) > cutoff_date
                    ]
                except ValueError:
                    return create_error_response(
                        "Days parameter must be an integer",
                        status=400,
                        error_code="INVALID_DAYS_PARAMETER"
                    )
            
            return create_success_response(
                {
                    'article_id': article_id,
                    'article_title': article.title,
                    'similar_articles': enhanced_articles,
                    'total_found': len(enhanced_articles),
                    'threshold_used': threshold,
                    'filters_applied': {
                        'threshold': threshold,
                        'limit': limit,
                        'days': days
                    }
                },
                message=f"Found {len(enhanced_articles)} similar articles"
            )
        
        elif result['status'] == 'no_embedding':
            return create_error_response(
                f"Article {article_id} has no embedding. Run summarization first.",
                status=404,
                error_code="NO_EMBEDDING_AVAILABLE",
                details={
                    "article_id": article_id,
                    "solution": "Process the article through the summarization pipeline first"
                }
            )
        
        else:
            return create_error_response(
                "Failed to find similar articles",
                status=500,
                error_code="SIMILARITY_SEARCH_FAILED",
                details={
                    "article_id": article_id,
                    "error": result.get('error', 'Unknown error occurred')
                }
            )
    
    except Article.DoesNotExist:
        return create_error_response(
            f"Article {article_id} not found",
            status=404,
            error_code="ARTICLE_NOT_FOUND",
            details={"article_id": article_id}
        )
    
    except ValueError as e:
        return create_error_response(
            f"Invalid parameter: {str(e)}",
            status=400,
            error_code="INVALID_PARAMETER",
            details={"parameter_error": str(e)}
        )
    
    except Exception as e:
        return create_error_response(
            "Internal server error while finding similar articles",
            status=500,
            error_code="INTERNAL_ERROR",
            details={"error_type": type(e).__name__}
        )


def _get_article_abstract(article_id):
    """Helper to get article abstract from summary."""
    try:
        article = Article.objects.get(id=article_id)
        if hasattr(article, 'structured_summary'):
            return article.structured_summary.abstract
        return article.description or ""
    except:
        return ""


@api_view(['GET'], authenticate=False)
def embedding_stats(request):
    """
    Get embedding statistics for monitoring.
    
    URL: /api/content/embedding-stats/
    
    Response:
        {
            "success": true,
            "total_articles": 1000,
            "articles_with_summaries": 850,
            "articles_with_embeddings": 800,
            "embedding_coverage": 0.94,
            "recent_embeddings": 50
        }
    """
    try:
        from django.db.models import Count
        
        # Get statistics
        total_articles = Article.objects.count()
        articles_with_summaries = Article.objects.filter(
            structured_summary__isnull=False
        ).count()
        articles_with_embeddings = ArticleEmbedding.objects.count()
        
        # Calculate coverage percentage
        embedding_coverage = (
            articles_with_embeddings / articles_with_summaries 
            if articles_with_summaries > 0 else 0
        )
        
        # Recent embeddings (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_embeddings = ArticleEmbedding.objects.filter(
            created_at__gte=yesterday
        ).count()
        
        # Additional statistics
        week_ago = datetime.now() - timedelta(days=7)
        weekly_embeddings = ArticleEmbedding.objects.filter(
            created_at__gte=week_ago
        ).count()
        
        return create_success_response(
            {
                'total_articles': total_articles,
                'articles_with_summaries': articles_with_summaries,
                'articles_with_embeddings': articles_with_embeddings,
                'embedding_coverage': round(embedding_coverage, 3),
                'recent_embeddings': recent_embeddings,
                'weekly_embeddings': weekly_embeddings,
                'embedding_model': 'text-embedding-3-small',
                'statistics_generated_at': datetime.now().isoformat()
            },
            message=f"Embedding statistics retrieved successfully"
        )
    
    except Exception as e:
        return create_error_response(
            "Failed to get embedding statistics",
            status=500,
            error_code="STATS_GENERATION_FAILED",
            details={
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
