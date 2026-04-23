-- Pipeline Cost Optimization: consolidate duplicate high-volume feeds
-- Safe to re-run; no rows are deleted.

-- Disable duplicate G1 feed (keep G1 Top News)
UPDATE rssfeeds_rssfeed
SET status = 'paused'
WHERE title = 'G1 Ciência e Saúde'
  AND status <> 'paused';

-- Disable duplicate Folha feed (keep Em Cima da Hora)
UPDATE rssfeeds_rssfeed
SET status = 'paused'
WHERE title = 'Folha Esporte'
  AND status <> 'paused';

-- Disable NYT specialty feeds (keep NYT Homepage)
UPDATE rssfeeds_rssfeed
SET status = 'paused'
WHERE title IN ('NYT Sports', 'NYT Health', 'NYT Science')
  AND status <> 'paused';
