import { NextApiRequest, NextApiResponse } from 'next';
import { getSession } from 'next-auth/react';
import apiClient from '@/lib/api-client';

// Type for user status response
interface UserStatusResponse {
  user_id: number;
  public_id: string;
  email: string;
  name: string;
  has_completed_onboarding: boolean;
}

/**
 * API route to update the session after onboarding completion
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // Get the current session
    const session = await getSession({ req });
    
    if (!session) {
      return res.status(401).json({ message: 'Not authenticated' });
    }
    
    // Force a fresh check of the user's onboarding status
    const userStatus = await apiClient.get<UserStatusResponse>('/accounts/sync/', { 
      forceRefresh: true,
      headers: { 'Cache-Control': 'no-cache' }
    });
    
    console.log('Session-update API: Fetched fresh user status:', userStatus);
    
    // Return the updated user status
    return res.status(200).json({ 
      success: true,
      has_completed_onboarding: userStatus.has_completed_onboarding,
      user: {
        ...session.user,
        has_completed_onboarding: userStatus.has_completed_onboarding
      }
    });
  } catch (error) {
    console.error('Error updating session:', error);
    return res.status(500).json({ message: 'Failed to update session' });
  }
} 