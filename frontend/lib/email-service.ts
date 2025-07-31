import { Resend } from 'resend';
import { createMagicLinkEmailHtml, createMagicLinkEmailText } from './email-templates';

// Initialize Resend with API key
const resendApiKey = process.env.RESEND_API_KEY;
const resend = resendApiKey ? new Resend(resendApiKey) : null;

interface SendMagicLinkEmailParams {
  email: string;
  url: string;
}

export async function sendMagicLinkEmail({ email, url }: SendMagicLinkEmailParams): Promise<void> {
  try {
    // Debug: Log the URL to see what NextAuth is passing
    console.log(`[DEBUG] sendMagicLinkEmail called with URL: "${url}"`);
    
    // Check if we have a resend instance (API key available)
    if (!resend) {
      console.warn('Resend API key not configured - falling back to debug mode');
      if (process.env.NODE_ENV === 'development') {
        console.log(`[DEV] Magic link for ${email}: ${url}`);
        return;
      } else {
        throw new Error('Resend API key not configured');
      }
    }

    // Validate URL before parsing
    if (!url || typeof url !== 'string') {
      throw new Error(`Invalid URL passed to sendMagicLinkEmail: ${url}`);
    }

    const host = new URL(url).host;
    const fromEmail = process.env.EMAIL_FROM || 'dailybrief@resend.dev';
    
    try {
      // Use Resend to send the email
      const { data, error } = await resend.emails.send({
        from: `DailyBrief <${fromEmail}>`,
        to: email,
        subject: 'Sign in to DailyBrief',
        html: createMagicLinkEmailHtml({ url, host }),
        text: createMagicLinkEmailText({ url, host }),
      });

      if (error) {
        console.error('Error sending magic link email:', error);
        
        // Fall back to logging in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`[DEV] Magic link for ${email}: ${url}`);
          return;
        }
        
        throw new Error(`Failed to send magic link email: ${error.message}`);
      }

      console.log('Magic link email sent successfully:', data?.id);
    } catch (sendError) {
      console.error('Error in resend.emails.send:', sendError);
      
      // Always fall back to logging the magic link in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`[DEV] Magic link for ${email}: ${url}`);
        return;
      }
      
      throw sendError;
    }
  } catch (error) {
    console.error('Error in sendMagicLinkEmail:', error);
    
    // In development, always fall back to logging the magic link
    if (process.env.NODE_ENV === 'development') {
      console.log(`[DEV] Magic link for ${email}: ${url}`);
      return;
    }
    
    throw error;
  }
} 