import apiClient from './api-client';

export interface Topic {
  id: number;
  name: string;
  slug: string;
}

export interface Region {
  code: string;
  name: string;
}

export interface Language {
  iso_code: string;
  name: string;
}

export interface Publication {
  id: number;
  name: string;
  website_url: string;
  logo_url: string | null;
  description: string;
  authority: number;
  news_api_id?: string;
  topic_ids?: number[];
  region_ids?: number[];
  language_ids?: number[];
}

export interface OnboardingOptions {
  topics: Topic[];
  regions: Region[];
  languages: Language[];
  publications: Publication[];
}

export interface UserPreferences {
  topics: number[];      // Backend returns integers (topic IDs)
  regions: string[];     // Backend returns strings (region codes)
  languages: string[];   // Backend returns strings (ISO codes)
  publications: number[]; // Backend returns integers (publication IDs)
  // Extended fields from backend response
  topics_details?: Array<{id: number, name: string, slug: string}>;
  has_completed_onboarding?: boolean;
  user_id?: number;
  public_id?: string;
  email?: string;
  name?: string;
}

export interface PaginatedResponse<T> {
  results: T[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
  };
}

interface OnboardingResponse {
  success: boolean;
  message?: string;
}

// Fetch all options for the onboarding process
export async function fetchOnboardingOptions(): Promise<OnboardingOptions> {
  try {
    console.log('Fetching onboarding options from backend');
    
    // Use the basic-data endpoint which returns all reference data in one call
    // Removing extra api prefix as it's now properly handled by apiClient
    const data = await apiClient.get<{
      topics: Topic[];
      regions: Region[];
      languages: Language[];
      publications: Publication[];
    }>('/feeds/basic-data');
    
    console.log('Successfully fetched onboarding options');
    
    return {
      topics: data.topics || [],
      regions: data.regions || [],
      languages: data.languages || [],
      publications: data.publications || []
    };
  } catch (error) {
    console.error('Error fetching onboarding options:', error);
    throw new Error('Failed to load onboarding options');
  }
}

// Fetch popular publications (pre-filtered for faster loading)
export async function fetchPopularPublications(): Promise<Publication[]> {
  try {
    const publications = await apiClient.get<Publication[]>('/feeds/publications');
    
    // Filter to popular publications (high authority rating)
    return publications.filter(pub => pub.authority >= 4.0).slice(0, 25);
  } catch (error) {
    console.error('Error fetching popular publications:', error);
    return [];
  }
}

// Save user preferences and mark onboarding as complete
export async function saveUserPreferences(preferences: UserPreferences): Promise<OnboardingResponse> {
  try {
    console.log('Saving user preferences:', JSON.stringify(preferences));
    const response = await apiClient.post('/accounts/preferences/', preferences);
    console.log('Preferences saved successfully, response:', response);
    return { success: true };
  } catch (error) {
    console.error('Error saving preferences:', error);
    throw new Error('Failed to save preferences');
  }
}

// Get all publication IDs matching user's preferences (no pagination)
export async function fetchAllPublicationIds(filters: {
  topicIds?: number[];
  regionCodes?: string[];
  languageCode?: string;
  filterMode?: 'recommended' | 'other';
}): Promise<{
  publication_ids: number[];
  total_count: number;
  filter_mode: string;
  topic_ids: string[];
  region_codes: string[];
  language_code: string | null;
}> {
  try {
    const queryParams = new URLSearchParams();
    
    // Add filter mode
    if (filters.filterMode) {
      queryParams.append('filter_mode', filters.filterMode);
    }
    
    // Add topic IDs
    if (filters.topicIds && filters.topicIds.length > 0) {
      filters.topicIds.forEach(id => {
        queryParams.append('topic_id', id.toString());
      });
    }
    
    // Add region codes
    if (filters.regionCodes && filters.regionCodes.length > 0) {
      filters.regionCodes.forEach(code => {
        queryParams.append('region_code', code);
      });
    }
    
    // Add language code (if any)
    if (filters.languageCode) {
      queryParams.append('language_code', filters.languageCode);
    }
    
    // Make API request
    const url = `/feeds/publication-ids?${queryParams.toString()}`;
    console.log(`Fetching all publication IDs: ${url}`);
    
    const response = await apiClient.get<{
      publication_ids: number[];
      total_count: number;
      filter_mode: string;
      topic_ids: string[];
      region_codes: string[];
      language_code: string | null;
    }>(url);
    
    console.log(`Received ${response.total_count} publication IDs for filter mode: ${response.filter_mode}`);
    
    return response;
  } catch (error) {
    console.error('Error fetching publication IDs:', error);
    throw new Error('Failed to fetch publication IDs');
  }
}

// Get current user preferences (for existing users)
export async function getUserPreferences(forceRefresh: boolean = false): Promise<UserPreferences | null> {
  try {
    const response = await apiClient.get<UserPreferences>('/accounts/preferences', { forceRefresh });
    return response;
  } catch (error) {
    console.error('Error fetching user preferences:', error);
    return null;
  }
}

// Helper function to get sensible defaults based on available options
export function getDefaultPreferences(options: OnboardingOptions): UserPreferences {
  // Find the General topic ID
  const generalTopic = options.topics.find(t => t.slug === 'general');
  
  // Find the US region code
  const usRegion = options.regions.find(r => r.code === 'us');
  
  return {
    // Default topic: general (or first one if not available)
    topics: generalTopic 
      ? [generalTopic.id]
      : options.topics.length > 0 ? [options.topics[0].id] : [],
      
    // Default region: US (or first one if not available)
    regions: usRegion
      ? [usRegion.code]
      : options.regions.length > 0 ? [options.regions[0].code] : [],
      
    // Default language: English (or first language if not available)
    languages: options.languages.some(l => l.iso_code === 'en') 
      ? ['en'] 
      : options.languages.slice(0, 1).map(l => l.iso_code),
      
    // Default publications: High-authority sources (top 5)
    publications: options.publications
      .sort((a, b) => b.authority - a.authority)
      .slice(0, 5)
      .map(p => p.id)
  };
}

// Fetch paginated publications with optional filters
export async function fetchPaginatedPublications(
  page: number = 1, 
  pageSize: number = 20,
  filters?: {
    topicIds?: number[];
    regionCodes?: string[];
    languageCode?: string;
    filterMode?: 'recommended' | 'other';
    sortBy?: string;
  }
): Promise<PaginatedResponse<Publication>> {
  try {
    // Build query parameters
    const queryParams = new URLSearchParams();
    queryParams.append('page', page.toString());
    queryParams.append('page_size', pageSize.toString());
    
    if (filters) {
      // Set filter mode (recommended or other)
      if (filters.filterMode) {
        queryParams.append('filter_mode', filters.filterMode);
      }
      
      // Add topic IDs
      if (filters.topicIds && filters.topicIds.length > 0) {
        filters.topicIds.forEach(id => {
          queryParams.append('topic_id', id.toString());
        });
      }
      
      // Add region codes
      if (filters.regionCodes && filters.regionCodes.length > 0) {
        filters.regionCodes.forEach(code => {
          queryParams.append('region_code', code);
        });
      }
      
      // Add language code (if any)
      if (filters.languageCode) {
        queryParams.append('language_code', filters.languageCode);
      }
      
      // Add sort option (if any)
      if (filters.sortBy) {
        queryParams.append('sort_by', filters.sortBy);
      }
    }
    
    // Make API request
    const url = `/feeds/publications?${queryParams.toString()}`;
    console.log(`Fetching publications: ${url}`);
    
    const response = await apiClient.get<PaginatedResponse<Publication>>(url);
    
    // Ensure topic_ids and region_ids are always arrays
    response.results.forEach(pub => {
      pub.topic_ids = pub.topic_ids || [];
      pub.region_ids = pub.region_ids || [];
      pub.language_ids = pub.language_ids || [];
    });
    
    return response;
  } catch (error) {
    console.error('Error fetching publications:', error);
    // Return an empty response with pagination metadata
    return {
      results: [],
      pagination: {
        page,
        page_size: pageSize,
        total_count: 0,
        total_pages: 0
      }
    };
  }
} 