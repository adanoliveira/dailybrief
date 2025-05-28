"""
Content Filtering Utilities for Step 2 Processing
Filters out ads, navigation, and irrelevant content from processed articles.
"""

from typing import List, Dict
from bs4 import Tag


class ContentFilter:
    """
    Filters content blocks and media assets to remove irrelevant content.
    Used in Step 2 processing to clean up extracted content.
    """
    
    def is_content_relevant(self, element: Tag) -> bool:
        """
        Determine if an element contains relevant article content.
        Filters out ads, navigation, UI elements, etc.
        """
        if not element or not hasattr(element, 'name'):
            return False
            
        # Skip script, style, and other non-content tags
        if element.name in ['script', 'style', 'noscript', 'iframe', 'embed', 'object']:
            return False
            
        # Get element attributes for analysis
        element_class = ' '.join(element.get('class', [])).lower()
        element_id = (element.get('id') or '').lower()
        element_text = element.get_text(strip=True).lower()
        
        # Common ad/navigation/UI patterns to exclude
        exclude_patterns = [
            # Ads and promotional content
            'ad', 'ads', 'advertisement', 'promo', 'sponsored', 'affiliate',
            'banner', 'popup', 'modal', 'overlay', 'interstitial',
            
            # Navigation and UI elements
            'nav', 'navigation', 'menu', 'header', 'footer', 'sidebar',
            'breadcrumb', 'pagination', 'toolbar', 'controls',
            
            # Social and sharing
            'social', 'share', 'sharing', 'follow', 'subscribe', 'newsletter',
            'facebook', 'twitter', 'instagram', 'linkedin', 'youtube',
            
            # Comments and user content
            'comment', 'comments', 'discussion', 'reply', 'replies',
            'user-content', 'ugc', 'review', 'rating',
            
            # Related content and recommendations
            'related', 'recommended', 'trending', 'popular', 'more-stories',
            'you-might-like', 'dont-miss', 'also-read',
            
            # Widgets and embeds
            'widget', 'plugin', 'embed', 'iframe-container',
            'video-player-controls', 'audio-controls',
            
            # Cookie and privacy notices
            'cookie', 'privacy', 'gdpr', 'consent', 'notice',
            
            # Skip/hide elements
            'skip', 'hidden', 'invisible', 'screen-reader', 'sr-only',
            
            # Paywall and subscription
            'paywall', 'subscription', 'premium', 'member', 'login',
            'register', 'signup', 'sign-up'
        ]
        
        # Check if element contains exclude patterns
        for pattern in exclude_patterns:
            if (pattern in element_class or 
                pattern in element_id or 
                pattern in element_text[:100]):  # Check first 100 chars of text
                return False
        
        # Additional checks for specific element types
        if element.name == 'div':
            # Skip divs that are likely containers for ads/widgets
            if any(attr in element_class for attr in ['container', 'wrapper', 'box']) and \
               any(ad_term in element_class for ad_term in ['ad', 'promo', 'widget']):
                return False
                
        # Check for suspicious link patterns (likely ads/promos)
        if element.name == 'a':
            href = (element.get('href') or '').lower()
            if any(term in href for term in ['utm_', 'affiliate', 'promo', 'ad-', 'ads.']):
                return False
                
        # Skip elements with very little text (likely decorative)
        if element.name in ['div', 'span', 'section'] and len(element_text) < 10:
            return False
            
        # Skip elements that are mostly links (likely navigation)
        links = element.find_all('a')
        if len(links) > 3 and len(element_text) < len(links) * 20:
            return False
            
        return True
    
    def filter_content_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """
        Filter content blocks to remove irrelevant content.
        """
        filtered_blocks = []
        
        for block in blocks:
            # Skip blocks with suspicious content
            if block.get('type') == 'paragraph':
                text = block.get('content', '').lower()
                
                # Skip very short paragraphs (likely UI text)
                if len(text.strip()) < 20:
                    continue
                    
                # Skip paragraphs that are mostly promotional
                promo_indicators = [
                    'click here', 'learn more', 'read more', 'subscribe',
                    'follow us', 'share this', 'advertisement', 'sponsored'
                ]
                if any(indicator in text for indicator in promo_indicators) and len(text) < 100:
                    continue
                    
            # Skip suspicious image blocks
            elif block.get('type') == 'image':
                alt_text = (block.get('alt', '') or '').lower()
                src = (block.get('src', '') or '').lower()
                
                # Skip images that are likely ads/logos
                ad_indicators = ['ad', 'logo', 'banner', 'promo', 'sponsor']
                if any(indicator in alt_text or indicator in src for indicator in ad_indicators):
                    continue
                    
                # Skip very small images (likely icons/decorative)
                metadata = block.get('metadata', {})
                width = metadata.get('width', 0)
                height = metadata.get('height', 0)
                if width > 0 and height > 0 and (width < 100 or height < 100):
                    continue
                    
            filtered_blocks.append(block)
            
        return filtered_blocks
    
    def clean_media_assets(self, media_assets: List[Dict]) -> List[Dict]:
        """
        Clean media assets to remove ads, tracking pixels, and irrelevant media.
        """
        cleaned_assets = []
        
        for asset in media_assets:
            src = asset.get('src', '').lower()
            alt = (asset.get('alt', '') or '').lower()
            
            # Skip tracking pixels and analytics images
            if asset.get('type') == 'image':
                # Skip 1x1 tracking pixels
                metadata = asset.get('metadata', {})
                width = metadata.get('width', 0)
                height = metadata.get('height', 0)
                if width == 1 and height == 1:
                    continue
                    
                # Skip images from known ad/tracking domains
                tracking_domains = [
                    'doubleclick', 'googleadservices', 'googlesyndication',
                    'facebook.com/tr', 'google-analytics', 'googletagmanager',
                    'scorecardresearch', 'quantserve', 'outbrain', 'taboola'
                ]
                if any(domain in src for domain in tracking_domains):
                    continue
                    
                # Skip images with ad-related alt text
                ad_terms = ['advertisement', 'sponsored', 'promo', 'ad ', 'banner']
                if any(term in alt for term in ad_terms):
                    continue
                    
            # Skip videos from ad networks
            elif asset.get('type') in ['video', 'video_embed']:
                ad_video_domains = ['doubleclick', 'googlevideo', 'youtube.com/ads']
                if any(domain in src for domain in ad_video_domains):
                    continue
                    
            cleaned_assets.append(asset)
            
        return cleaned_assets 