import { dataManager } from './core'

export async function getManagedStorageInfo() {
  return dataManager.getStorageInfo()
}

export async function cleanupManagedStorage() {
  return dataManager.cleanupStorage()
}

export async function clearManagedUserData(userId: string) {
  return dataManager.clearUserData(userId)
}

export async function forceRefreshManagedData(): Promise<void> {
  return dataManager.forceRefreshAll()
}

export async function getManagedSyncStatus() {
  return dataManager.getSyncStatus()
}
