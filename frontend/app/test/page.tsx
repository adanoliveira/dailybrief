"use client"

import { useEffect, useState } from 'react'
import { testDatabase, testDataManager } from '@/lib/test-database'
import { localDB } from '@/lib/local-database'
import { dataManager } from '@/lib/data-manager'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function TestPage() {
  const [testResult, setTestResult] = useState<string>('')
  const [stats, setStats] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)

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

          <div className="text-sm text-muted-foreground">
            <p><strong>Console Commands:</strong></p>
            <ul className="list-disc list-inside space-y-1">
              <li><code>testDatabase()</code> - Run full database test suite</li>
              <li><code>testDataManager()</code> - Run DataManager test suite</li>
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
