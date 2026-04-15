import { dataManager, type SyncOptions } from './core'

export async function getManagedUserPreferences(options: SyncOptions = {}) {
  return dataManager.getUserPreferences(options)
}
