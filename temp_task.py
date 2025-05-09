from apps.newsapi.tasks import sync_headlines; result = sync_headlines.delay(); print(f'Task ID: {result.id}')
