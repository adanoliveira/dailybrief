"""
Views for the summarization app API endpoints.

Provides REST API functionality for article summarization features.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

from apps.articles.models import Article
from .models import ArticleEmbedding
from .tasks import find_similar_articles


@csrf_exempt
@require_http_methods(["GET"])
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
    # Enable CORS for development
    response = JsonResponse({})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    
    if request.method == "OPTIONS":
        return response
    
    try:
        # Validate article exists
        article = get_object_or_404(Article, id=article_id)
        
        # Get query parameters
        threshold = float(request.GET.get('threshold', 0.22))
        limit = int(request.GET.get('limit', 5))
        days = request.GET.get('days')
        
        # Validate parameters
        if threshold < 0 or threshold > 1:
            return JsonResponse({
                'success': False,
                'error': 'Threshold must be between 0 and 1'
            }, status=400)
        
        if limit < 1 or limit > 50:
            return JsonResponse({
                'success': False,
                'error': 'Limit must be between 1 and 50'
            }, status=400)
        
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
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=int(days))
                enhanced_articles = [
                    art for art in enhanced_articles 
                    if datetime.fromisoformat(art['published_at'].replace('Z', '+00:00')) > cutoff_date
                ]
            
            return JsonResponse({
                'success': True,
                'article_id': article_id,
                'article_title': article.title,
                'similar_articles': enhanced_articles,
                'total_found': len(enhanced_articles),
                'threshold_used': threshold
            })
        
        elif result['status'] == 'no_embedding':
            return JsonResponse({
                'success': False,
                'error': f'Article {article_id} has no embedding. Run summarization first.',
                'article_id': article_id
            }, status=404)
        
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error occurred'),
                'article_id': article_id
            }, status=500)
    
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'Invalid parameter: {str(e)}'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }, status=500)


def _get_article_abstract(article_id):
    """Helper to get article abstract from summary."""
    try:
        article = Article.objects.get(id=article_id)
        if hasattr(article, 'structured_summary'):
            return article.structured_summary.abstract
        return article.description or ""
    except:
        return ""


@csrf_exempt
@require_http_methods(["GET"])
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
    # Enable CORS
    response = JsonResponse({})
    response["Access-Control-Allow-Origin"] = "*"
    
    try:
        from django.db.models import Count
        from datetime import datetime, timedelta
        
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
        
        return JsonResponse({
            'success': True,
            'total_articles': total_articles,
            'articles_with_summaries': articles_with_summaries,
            'articles_with_embeddings': articles_with_embeddings,
            'embedding_coverage': round(embedding_coverage, 3),
            'recent_embeddings': recent_embeddings,
            'embedding_model': 'text-embedding-3-small'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to get embedding stats: {str(e)}'
        }, status=500)
