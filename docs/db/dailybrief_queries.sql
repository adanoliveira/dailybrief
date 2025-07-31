SELECT * from articles_article aa
	LEFT JOIN articles_article_topics aat
		ON aa.id = aat.article_id
	LEFT JOIN feeds_topic ft
		ON ft.id = aat.topic_Id
	LEFT JOIN articles_article_regions aar
		ON aa.id = aar.article_id
	LEFT JOIN feeds_region fr
		ON fr.id = aar.region_id
WHERE is_top_headline = TRUE
ORDER BY aa.published_at DESC LIMIT 20;


-- Get number of top headlines per day in specified regions and topics

SELECT published_at::date, COUNT(*)
FROM(
	SELECT * from articles_article aa
		LEFT JOIN articles_article_topics aat
			ON aa.id = aat.article_id
		LEFT JOIN feeds_topic ft
			ON ft.id = aat.topic_Id
		LEFT JOIN articles_article_regions aar
			ON aa.id = aar.article_id
		LEFT JOIN feeds_region fr
			ON fr.id = aar.region_id
	WHERE is_top_headline = TRUE) as atr
-- ) as atr
WHERE code IN ('us', 'br') 
	and published_at > '2025-06-01'
	-- and atr.slug IN ('technology', 'general', 'business', 'science')
-- WHERE published_at > '2025-06-01'
GROUP BY published_at::date
ORDER BY published_at::date
;


-- Content processing monitoring
SELECT 
    a.id,
    a.public_id,
    a.title,
    a.url,
    a.published_at,
    a.fetched_at,
    a.updated_at,
	a.content_hash,
	a.primary_topic_id,
	a.primary_region_id,
    
    -- Source information
    a.source_name,
    p.name AS publication_name,
    a.author,
    
    -- Step 1: Fetch Status
    a.fetch_status,
    a.fetch_attempts,
    a.last_fetch_attempt,
    a.fetch_duration_ms,
    a.fetch_error_message,
    a.paywall_detected,
    
    -- Step 2: Processing Status  
    a.process_status,
    a.process_route,
    a.process_attempts,
    a.last_process_attempt,
    a.process_duration_ms,
    a.process_cost_usd,
    a.process_error_message,
    
    -- Step 3: Summarization Status
    a.summarization_status,
    a.summarization_attempts,
    a.last_summarization_attempt,
    a.summarized_at,
    a.summarization_duration_ms,
    a.summarization_cost_usd,
    a.summarization_error_message,
    a.summary_content_source,
    
    -- Step 4: Analysis Status
    a.analyzer_status,
    a.analyzer_attempts,
    a.last_analyzer_attempt,
    a.analyzed_at,
    a.analyzer_duration_ms,
    a.analyzer_cost_usd,
    a.analyzer_error_message,
    
    -- Content availability flags
    CASE 
        WHEN LENGTH(a.raw_html) > 100 THEN true 
        ELSE false 
    END AS has_raw_html,
    
    CASE 
        WHEN LENGTH(a.basic_content) > 50 THEN true 
        ELSE false 
    END AS has_basic_content,
    
    CASE 
        WHEN LENGTH(a.clean_content) > 100 THEN true 
        ELSE false 
    END AS has_clean_content,
    
    -- Overall pipeline progress
    CASE 
        WHEN a.analyzer_status = 'completed' THEN 'fully_processed'
        WHEN a.summarization_status = 'completed' THEN 'summarized'
        WHEN a.process_status = 'completed' THEN 'processed'
        WHEN a.fetch_status = 'completed' THEN 'fetched'
        ELSE 'pending'
    END AS pipeline_stage,
    
    -- Status flags
    a.is_top_headline,
    a.summary_ready
    
FROM articles_article a
LEFT JOIN feeds_publication p ON a.publication_id = p.id
WHERE is_top_headline = TRUE
ORDER BY a.published_at DESC
LIMIT 100
;


-- Reset all articles from the last 48 hours to analysis pending
-- This will allow them to be re-analyzed for event extraction

UPDATE articles_article 
SET 
    analyzer_status = 'pending',
    analyzer_attempts = 0,
    analyzed_at = NULL,
    last_analyzer_attempt = NULL,
    analyzer_error_message = '',
    analyzer_duration_ms = NULL,
    analyzer_cost_usd = NULL
WHERE 
    published_at >= NOW() - INTERVAL '72 hours'
    AND is_top_headline = true;

-- Optional: Show the count of articles that will be affected
-- SELECT COUNT(*) as articles_to_reset 
-- FROM articles_article 
-- WHERE published_at >= NOW() - INTERVAL '48 hours' 
--     AND is_top_headline = true;