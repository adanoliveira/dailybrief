import { dataManager, type SyncOptions } from './core'

export async function getManagedArticleDetail(articleId: string, options: SyncOptions = {}) {
  return dataManager.getArticleDetail(articleId, options)
}

export async function markManagedArticleAsRead(articleId: string): Promise<void> {
  return dataManager.markArticleAsRead(articleId)
}

export async function toggleManagedArticleSaved(articleId: string): Promise<boolean> {
  return dataManager.toggleArticleSaved(articleId)
}
