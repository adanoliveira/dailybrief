import { dataManager, type SyncOptions } from './core'

export async function getManagedFeed(
  feedType: 'personalized' | 'world',
  topicSlug?: string,
  page: number = 1,
  pageSize: number = 10,
  options: SyncOptions = {}
) {
  return dataManager.getFeed(feedType, topicSlug, page, pageSize, options)
}

export async function getManagedPublicFeed(topicSlug?: string, page: number = 1, pageSize: number = 10) {
  return dataManager.getPublicFeed(topicSlug, page, pageSize)
}

export async function backgroundSyncManagedFeed(
  userId: string,
  feedType: 'personalized' | 'world',
  topicSlug?: string
) {
  return dataManager.backgroundSyncFeed(userId, feedType, topicSlug)
}

export async function loadManagedPendingArticles(feedSyncId: number): Promise<void> {
  return dataManager.loadPendingArticles(feedSyncId)
}

export async function getManagedPendingArticlesCount(
  userId: string,
  feedType: 'personalized' | 'world',
  topicSlug?: string
): Promise<{ newArticlesCount: number; updatedArticlesCount: number }> {
  return dataManager.getPendingArticlesCount(userId, feedType, topicSlug)
}
