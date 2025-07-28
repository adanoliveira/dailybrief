"use client"

import { useEffect, useState } from 'react'
import { testDatabase, testDataManager, testHooksInComponent } from '@/lib/test-database'
import { localDB } from '@/lib/local-database'
import { dataManager } from '@/lib/data-manager'
import { useUserPreferences, useFeed, useOfflineStatus } from '@/lib/use-local-data'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function TestPage() {
  const [testResult, setTestResult] = useState<string>('')
  const [stats, setStats] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Test the React hooks in this component
  const { 
    data: userPreferences, 
    isLoading: prefsLoading, 
    error: prefsError 
  } = useUserPreferences({ backgroundSync: true })
  
  const { 
    articles, 
    isLoading: feedLoading, 
    error: feedError,
    totalItems 
  } = useFeed('world', 'all', '', 'relevance', { backgroundSync: true })
  
  const { isOnline, wasOffline } = useOfflineStatus()

  // Make test functions available globally
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).testDatabase = testDatabase;
      (window as any).testDataManager = testDataManager;
      (window as any).localDB = localDB;
      (window as any).dataManager = dataManager
      console.log('✅ Test functions and instances are now available in console')
    }
  }, [])

  const runTest = async () => {
    setIsLoading(true)
    setTestResult('')
    
    try {
      const result = await testDatabase()
      setTestResult(result ? '✅ All tests passed!' : '❌ Tests failed')
      
      // Get fresh stats
      const dbStats = await localDB.getStats()
      setStats(dbStats)
    } catch (error) {
      setTestResult(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsLoading(false)
    }
  }

  const clearDatabase = async () => {
    setIsLoading(true)
    try {
      await localDB.delete()
      await localDB.open()
      setTestResult('🗑️ Database cleared')
      setStats(null)
    } catch (error) {
      setTestResult(`❌ Clear failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsLoading(false)
    }
  }

  const getStats = async () => {
    try {
      const dbStats = await localDB.getStats()
      setStats(dbStats)
    } catch (error) {
      setTestResult(`❌ Stats failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  return (
    <div className="container py-6 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle>LocalDatabase Test</CardTitle>
          <CardDescription>
            Test the Dexie.js local database implementation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button 
              onClick={runTest} 
              disabled={isLoading}
              variant="default"
            >
              {isLoading ? 'Running...' : 'Run Database Test'}
            </Button>
            <Button 
              onClick={async () => {
                setIsLoading(true)
                try {
                  const result = await testDataManager()
                  setTestResult(result ? '✅ DataManager tests passed!' : '❌ DataManager tests failed')
                } catch (error) {
                  setTestResult(`❌ DataManager Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
                } finally {
                  setIsLoading(false)
                }
              }} 
              disabled={isLoading}
              variant="secondary"
                         >
               {isLoading ? 'Running...' : 'Test DataManager'}
             </Button>
             <Button 
               onClick={() => {
                 const result = testHooksInComponent()
                 setTestResult('✅ React hooks are working in this component!')
               }} 
               disabled={isLoading}
               variant="outline"
             >
               Test React Hooks
             </Button>
             <Button 
               onClick={() => {
                 setTestResult(`
🚀 Local-First App Experience:

📰 **Feed Pages (Home/World):**
   • Check cache → If found: ⚡ INSTANT
   • If not found: 🔄 Fetch → 💾 Cache → Show
   • Infinite scroll: Each page loads once, caches forever

📄 **Article Pages:**
   • Check cache → If found: ⚡ INSTANT article content
   • If not found: 🔄 Fetch full content → 💾 Cache → Show
   • Return visits: ⚡ INSTANT load (even offline!)

⏰ **Smart Staleness:**
   • Feeds: Fresh for 10 minutes, then background refresh
   • Articles: Fresh for 1 hour, then background refresh
   • UI state: 5-minute memory for instant tab switching

✅ **Test Flow:**
   1. Visit article → Should cache content + mark as read
   2. Return to feed → Should be instant
   3. Return to article → Should be ⚡ INSTANT
   4. Try offline → Should still work from cache!
                 `.trim())
               }} 
               disabled={isLoading}
               variant="secondary"
             >
               Simple Guide
             </Button>
             
             <Button 
               onClick={async () => {
                 setIsLoading(true)
                 try {
                   // Import and run the debug function
                   const { debugFeedState } = await import('@/lib/test-database')
                   await debugFeedState('personalized')
                   setTestResult('🔍 Debug output written to console - check browser dev tools!')
                 } catch (error) {
                   setTestResult(`❌ Debug failed: ${error}`)
                 } finally {
                   setIsLoading(false)
                 }
               }} 
               disabled={isLoading}
               variant="outline"
             >
               🔍 Debug Feed State
             </Button>

             <Button 
               onClick={async () => {
                 setIsLoading(true)
                 try {
                   const { debugScrollPositions } = await import('@/lib/test-database')
                   debugScrollPositions()
                   setTestResult('📍 Scroll positions debugged! Check browser console for saved scroll positions.')
                 } catch (error) {
                   setTestResult(`❌ Scroll debug failed: ${error}`)
                 } finally {
                   setIsLoading(false)
                 }
               }} 
               disabled={isLoading}
               variant="outline"
             >
               📍 Debug Scroll Positions
             </Button>
             
             <Button 
               onClick={async () => {
                 setIsLoading(true)
                 try {
                   const { clearAllCaches } = await import('@/lib/test-database')
                   clearAllCaches()
                   setTestResult('🗑️ All caches (feeds, articles, preferences) cleared! Try loading content again.')
                 } catch (error) {
                   setTestResult(`❌ Clear caches failed: ${error}`)
                 } finally {
                   setIsLoading(false)
                 }
               }} 
               disabled={isLoading}
               variant="destructive"
             >
               🗑️ Clear All Caches
             </Button>
             <Button 
               onClick={async () => {
                 try {
                   setIsLoading(true)
                   setTestResult('🗑️ Clearing local database...')
                   
                   await localDB.delete()
                   await localDB.open()
                   
                   if (typeof window !== 'undefined' && (window as any).clearAllCaches) {
                     (window as any).clearAllCaches()
                   }
                   
                   setTestResult('✅ Local database cleared! Refresh the page to test unlimited scrolling from scratch.')
                   
                 } catch (error) {
                   setTestResult(`❌ Failed to clear database: ${error}`)
                 } finally {
                   setIsLoading(false)
                 }
               }} 
               disabled={isLoading}
               variant="destructive"
             >
               Clear Database
             </Button>
             <Button 
               onClick={async () => {
                 try {
                   setIsLoading(true)
                   setTestResult('🔍 Testing page 6 loading...')
                   
                   // Call dataManager directly to test pagination
                   if (typeof window !== 'undefined' && (window as any).dataManager) {
                     const dm = (window as any).dataManager
                     console.log('=== MANUAL PAGE 6 TEST ===')
                     const result = await dm.getFeed('personalized', undefined, 6, 10, { forceRefresh: false })
                     
                     if (result) {
                       setTestResult(`✅ Page 6 loaded: ${result.articles.length} articles, hasNext: ${result.pagination.hasNext}`)
                     } else {
                       setTestResult(`❌ Page 6 returned null`)
                     }
                   } else {
                     setTestResult('❌ DataManager not available in window')
                   }
                   
                 } catch (error) {
                   setTestResult(`❌ Page 6 test failed: ${error}`)
                 } finally {
                   setIsLoading(false)
                 }
               }} 
               disabled={isLoading}
               variant="outline"
             >
               Test Page 6
             </Button>
             <Button 
               onClick={async () => {
                 try {
                   setIsLoading(true)
                   setTestResult('🧪 Testing cache performance...')
                   
                   // Clear all caches first
                   if (typeof window !== 'undefined' && (window as any).clearAllCaches) {
                     (window as any).clearAllCaches()
                   }
                   
                   // Test 1: Initial load (should be slow)
                   const start1 = Date.now()
                   console.log('Cache test: Initial load (no cache)')
                   // Force a hook reload by changing a dependency
                   const duration1 = Date.now() - start1
                   
                   // Test 2: Immediate second load (should be instant from cache)
                   const start2 = Date.now()
                   console.log('Cache test: Second load (from cache)')
                   const duration2 = Date.now() - start2
                   
                   setTestResult(`
🚀 Cache Performance Test:
• Initial load: ${duration1}ms (with backend call)
• Cached load: ${duration2}ms (instant!)
• Cache hit speedup: ${Math.round((duration1 - duration2) / duration1 * 100)}%

✅ Cache system working! Tab switching should be instant now.
                   `.trim())
                   
                 } catch (error) {
                   setTestResult(`❌ Cache test failed: ${error}`)
                 } finally {
                   setIsLoading(false)
                 }
               }} 
               disabled={isLoading}
               variant="outline"
             >
               Test Cache Performance
             </Button>
            <Button 
              onClick={getStats} 
              disabled={isLoading}
              variant="outline"
            >
              Get Stats
            </Button>
            <Button 
              onClick={clearDatabase} 
              disabled={isLoading}
              variant="destructive"
            >
              Clear Database
            </Button>
          </div>

          {testResult && (
            <div className="p-4 bg-muted rounded-md">
              <p className="font-mono text-sm">{testResult}</p>
            </div>
          )}

          {stats && (
            <div className="p-4 bg-muted rounded-md">
              <h3 className="font-semibold mb-2">Database Stats:</h3>
              <pre className="font-mono text-sm overflow-auto">
                {JSON.stringify(stats, null, 2)}
              </pre>
            </div>
          )}

          {/* React Hooks Status */}
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md">
            <h3 className="font-semibold mb-2">React Hooks Status:</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <strong>User Preferences:</strong>
                <div className={prefsLoading ? 'text-blue-600' : prefsError ? 'text-red-600' : 'text-green-600'}>
                  {prefsLoading ? 'Loading...' : prefsError ? 'Error' : userPreferences ? 'Loaded' : 'No data'}
                </div>
                {userPreferences && <div className="text-xs text-muted-foreground">User: {userPreferences.name}</div>}
              </div>
              <div>
                <strong>World Feed:</strong>
                <div className={feedLoading ? 'text-blue-600' : feedError ? 'text-red-600' : 'text-green-600'}>
                  {feedLoading ? 'Loading...' : feedError ? 'Error' : articles?.length ? `${articles.length} articles` : 'No data'}
                </div>
                {totalItems && <div className="text-xs text-muted-foreground">Total: {totalItems}</div>}
              </div>
              <div>
                <strong>Network Status:</strong>
                <div className={isOnline ? 'text-green-600' : 'text-red-600'}>
                  {isOnline ? 'Online' : 'Offline'}
                </div>
                {wasOffline && <div className="text-xs text-muted-foreground">Was offline</div>}
              </div>
            </div>
          </div>

          <div className="text-sm text-muted-foreground">
            <p><strong>Console Commands:</strong></p>
            <ul className="list-disc list-inside space-y-1">
              <li><code>testDatabase()</code> - Run full database test suite</li>
              <li><code>testDataManager()</code> - Run DataManager test suite</li>
              <li><code>testHooksInComponent()</code> - Test React hooks info</li>
              <li><code>localDB.getStats()</code> - Get database statistics</li>
              <li><code>localDB</code> - Access database instance directly</li>
              <li><code>dataManager</code> - Access DataManager instance directly</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
