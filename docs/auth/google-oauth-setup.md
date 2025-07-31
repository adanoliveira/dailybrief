# Setting Up Google OAuth for DailyBrief

This guide will walk you through the process of setting up Google OAuth 2.0 for the DailyBrief application.

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page and select "New Project"
3. Enter a name for your project (e.g., "DailyBrief")
4. Click "Create" to create the project
5. Make sure your new project is selected in the dropdown

## Step 2: Configure the OAuth Consent Screen

1. In the left-hand menu, go to "APIs & Services" > "OAuth consent screen"
2. Select "External" as the user type and click "Create"
3. Fill in the required information:
   - App name: DailyBrief
   - User support email: Your email address
   - Developer contact information: Your email address
4. Click "Save and Continue"
5. On the Scopes page, add the following scopes:
   - `./auth/userinfo.email`
   - `./auth/userinfo.profile`
6. Click "Save and Continue"
7. Add test users if needed for development, then click "Save and Continue"
8. Review your settings and click "Back to Dashboard"

## Step 3: Create OAuth 2.0 Credentials

1. In the left-hand menu, go to "APIs & Services" > "Credentials"
2. Click the "Create Credentials" button and select "OAuth client ID"
3. Select "Web application" as the application type
4. Enter a name for the OAuth client (e.g., "DailyBrief Web Client")
5. Add Authorized JavaScript origins:
   - Development: `http://localhost:3000`
   - Production: Your production URL (e.g., `https://dailybrief.example.com`)
6. Add Authorized redirect URIs:
   - Development: `http://localhost:3000/api/auth/callback/google`
   - Production: Your production URL (e.g., `https://dailybrief.example.com/api/auth/callback/google`)
7. Click "Create"
8. A popup will show your client ID and client secret - copy these values

## Step 4: Configure DailyBrief to Use Google OAuth

1. Open the `.env` file in your frontend directory
2. Update the following environment variables:
   ```
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```
3. Restart your development server for the changes to take effect

## Testing Google Sign-in

You can test Google Sign-in by:

1. Starting your development server
2. Go to the authentication page (`/auth`)
3. Click "Continue with Google"
4. You should be redirected to Google's authentication page
5. After authentication, you should be redirected back to DailyBrief

## Troubleshooting

If you encounter issues with Google Sign-in:

1. Check that your redirect URIs are correctly configured
2. Verify that your Client ID and Client Secret are correctly set in the `.env` file
3. Ensure that the OAuth consent screen is configured with the necessary scopes
4. Check the browser console for any error messages
5. Make sure your development server is running on the correct port (default: 3000)

## Security Considerations

- Never commit your Google Client Secret to version control
- Use environment variables or a secure secrets manager to store your credentials
- In production, ensure your redirect URIs use HTTPS 