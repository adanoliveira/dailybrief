import { api } from './api';

/**
 * Unwrap standardized API response from axios
 */
function unwrapAxiosResponse<T = any>(response: any): T {
  const responseData = response.data;
  if (responseData && typeof responseData === 'object' && 'success' in responseData && responseData.success === true) {
    return responseData.data;
  }
  return responseData;
}

export interface Topic {
  id: string;
  name: string;
  slug: string;
}

export interface Region {
  id: string;
  name: string;
  code: string;
}

export interface Language {
  id: string;
  name: string;
  iso_code: string;
}

export interface Publication {
  id: string;
  name: string;
  description: string;
  website_url: string;
  logo_url?: string;
  news_api_id: string;
  authority?: number;
  // Relationships - only included when expanded
  topics?: Topic[];
  regions?: Region[];
  languages?: Language[];
}

export interface ReferenceData {
  topics: Topic[];
  regions: Region[];
  languages: Language[];
  publications: Publication[];
}

/**
 * Get all reference data for onboarding
 */
export async function getReferenceData(): Promise<ReferenceData> {
  try {
    console.log('Requesting reference data from endpoint: /feeds/basic-data/');
    const response = await api.get('/feeds/basic-data/');
    console.log('Reference data response received:', response.status);
    return unwrapAxiosResponse<ReferenceData>(response);
  } catch (error) {
    console.error('Failed to fetch reference data:', error);
    throw error;
  }
}

/**
 * Get all available topics
 */
export async function getTopics(): Promise<Topic[]> {
  try {
    const response = await api.get('/feeds/topics/');
    return unwrapAxiosResponse<Topic[]>(response);
  } catch (error) {
    console.error('Failed to fetch topics:', error);
    throw error;
  }
}

/**
 * Get all available regions
 */
export async function getRegions(): Promise<Region[]> {
  try {
    const response = await api.get('/feeds/regions/');
    return unwrapAxiosResponse<Region[]>(response);
  } catch (error) {
    console.error('Failed to fetch regions:', error);
    throw error;
  }
}

/**
 * Get all available languages
 */
export async function getLanguages(): Promise<Language[]> {
  try {
    const response = await api.get('/feeds/languages/');
    return unwrapAxiosResponse<Language[]>(response);
  } catch (error) {
    console.error('Failed to fetch languages:', error);
    throw error;
  }
}

/**
 * Get all available publications
 */
export async function getPublications(): Promise<Publication[]> {
  try {
    const response = await api.get('/feeds/publications/');
    return unwrapAxiosResponse<Publication[]>(response);
  } catch (error) {
    console.error('Failed to fetch publications:', error);
    throw error;
  }
} 