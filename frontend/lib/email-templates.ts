import { SendVerificationRequestParams } from "next-auth/providers/email";

export function createMagicLinkEmailHtml({ url, host }: { url: string; host: string }) {
  // Using light theme brand tokens from globals.css
  const backgroundColor = "#ffffff"; // --background (0 0% 100%)
  const foregroundColor = "#09090b"; // --foreground (0 0% 3.9%)
  const cardColor = "#ffffff"; // --card (0 0% 100%)
  const cardForegroundColor = "#09090b"; // --card-foreground (0 0% 3.9%)
  const secondaryColor = "#f5f5f5"; // --secondary (0 0% 96.1%)
  const mutedForeground = "#737373"; // --muted-foreground (0 0% 45.1%)
  const borderColor = "#e5e5e5"; // --border (0 0% 89.8%)
  
  // Primary color - correct app primary (black/very dark)
  const primaryColor = "#171717"; // --primary (0 0% 9%)
  const primaryForegroundColor = "#fafafa"; // --primary-foreground (0 0% 98%)
  
  // Brand colors 
  const warningColor = "#f97316"; // Orange warning
  const warningBgColor = "#7c2d12"; // Background for warning notice

  // Get the absolute URL for logo - use NEXTAUTH_URL or fall back to production domain
  const baseUrl = process.env.NEXTAUTH_URL || 'https://www.dailybrief.press';
  const logoUrl = `${baseUrl}/logo-horizontal-white.svg`;

  return `
    <html>
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="color-scheme" content="light">
        <meta name="supported-color-schemes" content="light">
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
          
          body {
            font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            margin: 0;
            padding: 0;
            width: 100%;
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
          }
          
          .btn-primary {
            padding: 0.75rem 1.25rem;
            background-color: #171717;
            color: white;
            border-radius: 0.375rem;
            font-weight: 500;
            text-decoration: none;
            display: inline-block;
            line-height: 1;
            text-align: center;
          }
          
          .security-notice {
            border-left: 4px solid #f97316;
            padding: 1rem;
            background-color: #451a03;
            border-radius: 0.375rem;
            margin-bottom: 1.5rem;
            color: #fdba74;
          }
          
          @media only screen and (max-width: 620px) {
            .container {
              width: 100% !important;
            }
            
            .main {
              border-radius: 0 !important;
              border-left: none !important;
              border-right: none !important;
            }
          }
        </style>
      </head>
      <body style="background-color: #f5f5f5; margin: 0; padding: 0;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="width: 100%; margin: 0; padding: 0;">
          <tr>
            <td align="center" style="padding: 20px 0;">
              <!-- Container -->
              <table class="container" width="600" border="0" cellspacing="0" cellpadding="0" style="width: 600px; max-width: 600px; margin: 0 auto;">
                <!-- Header -->
                <tr>
                  <td align="center" style="padding: 20px 0;">
                    <a href="${process.env.NEXT_PUBLIC_APP_URL}" style="text-decoration: none; display: inline-block;">
                      <img src="${logoUrl}" alt="DailyBrief" style="width: 160px; height: auto; vertical-align: middle;" />
                    </a>
                  </td>
                </tr>
                
                <!-- Main Content -->
                <tr>
                  <td>
                    <table class="main" width="100%" border="0" cellspacing="0" cellpadding="0" style="border-radius: 8px; background-color: ${cardColor}; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid ${borderColor}; overflow: hidden;">
                      <tr>
                        <td style="padding: 30px;">
                          <h1 style="color: ${foregroundColor}; font-size: 24px; font-weight: 600; margin: 0 0 20px 0; line-height: 1.25;">Sign in to DailyBrief</h1>
                          
                          <p style="color: ${foregroundColor}; font-size: 16px; line-height: 1.5; margin: 0 0 24px 0;">
                            Click the button below to sign in to DailyBrief. This magic link will expire in 15 minutes and can only be used once.
                          </p>
                          
                          <!-- Button -->
                          <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom: 24px;">
                            <tr>
                              <td align="center">
                                <table border="0" cellspacing="0" cellpadding="0">
                                  <tr>
                                    <td align="center" style="border-radius: 6px; background-color: ${primaryColor};">
                                      <a href="${url}" target="_blank" style="border: none; border-radius: 6px; color: ${primaryForegroundColor}; cursor: pointer; display: inline-block; font-size: 16px; font-weight: 500; margin: 0; padding: 12px 24px; text-decoration: none;">Sign in to DailyBrief</a>
                                    </td>
                                  </tr>
                                </table>
                              </td>
                            </tr>
                          </table>
                          
                          <p style="color: ${mutedForeground}; font-size: 14px; line-height: 1.5; margin: 0 0 12px 0;">
                            If the button doesn't work, you can copy and paste this URL into your browser:
                          </p>
                          
                          <p style="color: ${mutedForeground}; font-size: 14px; line-height: 1.5; margin: 0 0 24px 0; word-break: break-all;">
                            <a href="${url}" style="color: ${primaryColor}; text-decoration: none; word-break: break-all;">${url}</a>
                          </p>
                          
                          <!-- Security Notice -->
                          <div style="border-left: 4px solid ${warningColor}; padding: 16px; background-color: ${warningBgColor}; border-radius: 4px; margin-bottom: 24px;">
                            <p style="color: ${warningColor}; font-size: 16px; font-weight: 600; margin: 0 0 8px 0;">
                              Security Notice
                            </p>
                            <ul style="color: #fdba74; font-size: 14px; line-height: 1.5; margin: 0; padding-left: 20px;">
                              <li style="margin-bottom: 4px;">This link is unique to you and should not be shared with anyone</li>
                              <li style="margin-bottom: 4px;">DailyBrief staff will never ask for this link</li>
                              <li>If you didn't request this email, please ignore it</li>
                            </ul>
                          </div>
                          
                          <p style="color: ${foregroundColor}; font-size: 16px; line-height: 1.5; margin: 0;">
                            Thanks,<br>
                            The DailyBrief Team
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                
                <!-- Footer -->
                <tr>
                  <td align="center" style="padding: 20px 0; color: ${mutedForeground}; font-size: 12px; line-height: 1.5;">
                    <p style="margin: 0 0 8px 0;">DailyBrief, Inc.</p>
                    <p style="margin: 0;">
                      <a href="${process.env.NEXT_PUBLIC_APP_URL}/terms" style="color: ${mutedForeground}; text-decoration: underline; margin-right: 8px;">Terms</a>
                      <a href="${process.env.NEXT_PUBLIC_APP_URL}/privacy" style="color: ${mutedForeground}; text-decoration: underline;">Privacy</a>
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
  `;
}

export function createMagicLinkEmailText({ url, host }: { url: string; host: string }) {
  return `Sign in to DailyBrief

Click the link below to sign in to DailyBrief. 
This magic link will expire in 15 minutes and can only be used once.

${url}

SECURITY NOTICE:
- This link is unique to you and should not be shared with anyone
- DailyBrief staff will never ask for this link
- If you didn't request this email, please ignore it

Thanks,
The DailyBrief Team
`;
} 