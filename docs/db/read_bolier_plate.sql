SELECT schema_name
FROM information_schema.schemata;

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

SELECT * from articles_article aa
	LEFT JOIN articles_article_topics aat
		ON aa.id = aat.article_id
	LEFT JOIN feeds_topic ft
		ON ft.id = aat.topic_Id
ORDER BY aa.id DESC LIMIT 20;

SELECT COUNT(*) from articles_article aa
WHERE publication_id IS NOT NULL
;



SELECT * FROM articles_article_topics;


SELECT * FROM feeds_publication fp
	LEFT JOIN feeds_publication_regions fpr
		ON fp.id = fpr.publication_id
	LEFT JOIN feeds_region fr
		ON fr.id = fpr.region_id
-- WHERE fr.name = 'Brazil'
ORDER BY fp.name ASC
;

SELECT COUNT(*) FROM feeds_publication
;


SELECT country, COUNT(*)
FROM
	(SELECT fr.name as country, * FROM feeds_publication fp
		LEFT JOIN feeds_publication_regions fpr
			ON fp.id = fpr.publication_id
		LEFT JOIN feeds_region fr
			ON fr.id = fpr.region_id) as pubs
GROUP BY country
ORDER BY country
;


SELECT 
(SELECT * from articles_article aa
	LEFT JOIN articles_article_topics aat
		ON aa.id = aat.article_id
	LEFT JOIN feeds_topic ft
		ON ft.id = aat.topic_Id
ORDER BY aa.id ASC)
;

SELECT COUNT(*) FROM feeds_region
;

SELECT * FROM feeds_region
;

SELECT endpoint
	, params
	, success
	, total_results
	, results_fetched
	, created_at
FROM newsapi_newsapirequest 
ORDER BY created_at DESC 
-- LIMIT 5
;


SELECT news_api_id FROM feeds_publication;

SELECT * FROM feeds_publication;

SELECT news_api_id FROM feeds_publication WHERE news_api_id IS NOT NULL AND news_api_id != '';


SELECT * FROM feeds_publication ORDER BY domain;

SELECT * FROM articles_article;


SELECT * FROM newsapi_newsapiarticle ORDER BY id DESC;

