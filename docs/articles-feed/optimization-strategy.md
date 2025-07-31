# Article Fetching Optimization Strategy

## Current Situation

Currently, DailyBrief makes separate API calls for articles every time:
- The home/world feed components load
- User changes between topic tabs
- User navigates between pages

This approach is inefficient for our use case since:
1. Our article content only updates twice daily (overnight UTC and at 2pm UTC)
2. The app is designed as a PWA that will be installed on users' devices
3. We want to minimize unnecessary network requests

## Optimization Goals

1. Reduce backend API calls
2. Improve perceived performance for users
3. Enable offline functionality
4. Maintain data freshness according to our update schedule
5. Support proper updates when user preferences change

## Potential Approaches

### 1. Client-Side Data Management with React Query

**Implementation:**
- Use React Query library to handle data fetching and caching
- Configure with long stale times (6-12 hours) to match our update frequency
- Use deduplication to prevent duplicate requests when navigating between tabs

**Benefits:**
- Built-in cache invalidation and revalidation strategies
- Automatic background revalidation at configurable intervals
- Handles loading/error states elegantly
- Minimal code changes required

**Drawbacks:**
- Still makes occasional validation calls to check for updates

### 2. Global State + Persistent Storage

**Implementation:**
- Store all fetched articles in Redux/Zustand/Jotai
- Persist complete article dataset to IndexedDB/localStorage
- Implement a timestamp-based refresh strategy
- Add a pull-to-refresh for manual updates

**Benefits:**
- Minimal network requests
- Works offline after initial load
- Very fast tab switching with no loading states

**Drawbacks:**
- More complex state management
- Requires careful synchronization with backend

### 3. Service Worker + Cache API Strategy

**Implementation:**
- Intercept API requests with Service Worker
- Store responses in Cache API
- Schedule background sync at our update times (overnight/2pm UTC)
- Update cache programmatically

**Benefits:**
- True offline functionality
- Native to PWA architecture
- No JavaScript main thread overhead

**Drawbacks:**
- Most complex setup of the options
- Requires careful cache invalidation

### 4. Backend-Driven Feed with Efficient Diff Updates

**Implementation:**
- Initial full data load on app start
- Endpoint that returns only new/changed articles since timestamp
- Implement efficient diffing algorithm to merge updates

**Benefits:**
- Minimal data transfer after initial load
- Server handles the "heavy lifting" of determining what's new
- Smaller network payloads for updates

**Drawbacks:**
- Requires backend changes
- More complex data merging logic

## Recommended Approach

For the DailyBrief MVP, we recommend a combination of approaches #1 and #2:

### React Query + Persistence Solution

This combined approach gives us the best of both worlds:
- The simplicity of React Query's API
- The persistency benefits of local storage

#### Implementation Plan:

1. **Setup React Query with persistence:**
```tsx
import { QueryClient, QueryClientProvider } from 'react-query'
import { persistQueryClient } from 'react-query/persistQueryClient-experimental'
import { createWebStoragePersistor } from 'react-query/createWebStoragePersistor-experimental'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 6 * 60 * 60 * 1000, // 6 hours
      cacheTime: 24 * 60 * 60 * 1000, // 1 day
    }
  }
})

// Add persistence
const persistor = createWebStoragePersistor({ storage: window.localStorage })
persistQueryClient({ queryClient, persistor })
```

2. **Create custom hooks for article fetching:**
```tsx
// Custom hook for personalized feed
export function usePersonalizedFeed(params: ArticleQueryParams = {}) {
  return useQuery(
    ['personalizedFeed', params],
    () => getPersonalizedFeed(params),
    {
      refetchOnWindowFocus: false,
      refetchOnMount: false,
    }
  )
}

// Custom hook for world feed
export function useWorldFeed(params: ArticleQueryParams = {}) {
  return useQuery(
    ['worldFeed', params],
    () => getWorldFeed(params),
    {
      refetchOnWindowFocus: false,
      refetchOnMount: false,
    }
  )
}
```

3. **Add invalidation triggers:**
- When user updates preferences: `queryClient.invalidateQueries(['personalizedFeed'])`
- Add pull-to-refresh with invalidation
- Add periodic refresh at our scheduled times

## Future Enhancements

Once the MVP is established, we can enhance our approach by:

1. Implementing a proper Service Worker for offline support
2. Adding backend-driven diff updates to minimize data transfer
3. Developing a more sophisticated caching strategy based on user behavior

## Conclusion

The combined React Query + Persistence approach provides the optimal balance of:
- Developer experience (simple API)
- User experience (fast, works offline)
- Performance (minimal network requests)
- Maintainability (leverages established libraries)

This strategy will enable DailyBrief to function more like a native app with instantaneous navigation between feeds and topics while maintaining data freshness according to our update schedule. 