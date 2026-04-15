import apiClient from './api-client';
import { getSession } from 'next-auth/react';

/**
 * User preferences data structure - updated to match backend API
 */
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

/**
 * Save the user's preferences after onboarding
 */
export async function saveUserPreferences(preferences: UserPreferences): Promise<{ success: boolean; error?: string }> {
  try {
    await apiClient.post<any>('/api/accounts/preferences/', preferences);
    return { success: true };
  } catch (error) {
    console.error('Failed to save user preferences:', error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'An unknown error occurred'
    };
  }
}

/**
 * Get the user's current preferences
 */
export async function getUserPreferences(): Promise<UserPreferences | null> {
  try {
    const data = await apiClient.get<UserPreferences>('/api/accounts/preferences/');
    
    // Check if we have topic data
    if (data && data.topics) {
      return data;
    } else {
      console.log('User has no preferences set');
      return null;
    }
  } catch (error) {
    console.error('Failed to get user preferences:', error);
    return null;
  }
}

/**
 * Check if the user has completed onboarding by getting their status
 */
export async function hasCompletedOnboarding(): Promise<boolean> {
  try {
    interface UserStatus {
      has_completed_onboarding: boolean;
    }
    
    const data = await apiClient.get<UserStatus>('/api/accounts/user/status/');
    return data.has_completed_onboarding;
  } catch (error) {
    console.error('Failed to check onboarding status:', error);
    return false;
  }
} 