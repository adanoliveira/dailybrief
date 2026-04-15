import { dataManager, type SyncOptions } from './core'

export async function getManagedLatestDigest(options: SyncOptions = {}) {
  return dataManager.getLatestDigest(options)
}

export async function getManagedDigestByDate(date: string, options: SyncOptions = {}) {
  return dataManager.getDigestByDate(date, options)
}

export async function listManagedDigests(page: number = 1, pageSize: number = 10, options: SyncOptions = {}) {
  return dataManager.listDigests(page, pageSize, options)
}

export async function markManagedDigestAsRead(digestId: string): Promise<void> {
  return dataManager.markDigestAsRead(digestId)
}

export async function backgroundSyncManagedDigests(userId: string): Promise<void> {
  return dataManager.backgroundSyncDigests(userId)
}

export async function invalidateManagedDigestCache(): Promise<void> {
  return dataManager.invalidateDigestCache()
}

export async function forceRefreshManagedLatestDigest() {
  return dataManager.forceRefreshLatestDigest()
}
