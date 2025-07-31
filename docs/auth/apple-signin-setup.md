# Setting Up Apple Sign-in for DailyBrief

This guide will walk you through the process of setting up Sign in with Apple for the DailyBrief application.

## Step 1: Enroll in the Apple Developer Program

1. If you haven't already, enroll in the [Apple Developer Program](https://developer.apple.com/programs/) ($99/year)
2. Sign in to your Apple Developer account

## Step 2: Create an App ID

1. Go to [Certificates, Identifiers & Profiles](https://developer.apple.com/account/resources/identifiers/list)
2. Click the "+" button to register a new identifier
3. Select "App IDs" and click "Continue"
4. Select "App" as the type and click "Continue"
5. Enter the following information:
   - Description: DailyBrief
   - Bundle ID: com.yourcompany.dailybrief (use your own domain)
6. Scroll down to "Capabilities" and check "Sign In with Apple"
7. Click "Continue" and then "Register"

## Step 3: Create a Services ID

1. Go back to the Identifiers page
2. Click the "+" button to register a new identifier
3. Select "Services IDs" and click "Continue"
4. Enter the following information:
   - Description: DailyBrief Web
   - Identifier: com.yourcompany.dailybrief.web (use your own domain, but make it different from your App ID)
5. Click "Continue" and then "Register"
6. Click on the newly created Services ID in the list
7. Check "Sign In with Apple" and click "Configure"
8. Add your domain(s) to the "Domains and Subdomains" section:
   - Development: localhost
   - Production: yourdomain.com
9. Add your Return URLs:
   - Development: https://localhost:3000/api/auth/callback/apple
   - Production: https://yourdomain.com/api/auth/callback/apple
10. Click "Save" and then "Continue"
11. Click "Save" again to update the Services ID

## Step 4: Create a Private Key

1. Go to the "Keys" section in the Certificates, Identifiers & Profiles page
2. Click the "+" button to create a new key
3. Enter the following information:
   - Key Name: DailyBrief Sign In with Apple
   - Check "Sign In with Apple" and click "Configure"
4. Choose the App ID you created earlier
5. Click "Save" and then "Continue"
6. Click "Register" to generate the key
7. Download the key file (it's a one-time download, so save it securely)
8. Note the "Key ID" shown on the page - you'll need it later

## Step 5: Configure NextAuth for Apple Sign-in

1. Open the `.env` file in your frontend directory
2. Update the following environment variables:
   ```
   APPLE_ID=your_services_id_here (e.g., com.yourcompany.dailybrief.web)
   APPLE_TEAM_ID=your_team_id_here (found in the top-right of the Apple Developer page)
   APPLE_KEY_ID=your_key_id_here (from step 4.8)
   APPLE_SECRET_KEY_FILE=path/to/your/key/file.p8 (or alternatively, use APPLE_SECRET)
   # Or alternatively, set the raw private key content if not using a file
   APPLE_SECRET=your_base64_encoded_private_key
   ```

### Converting Apple Key for NextAuth

NextAuth expects the Apple private key in a specific format. You need to:

1. Take the .p8 file you downloaded
2. Convert it to the proper format using the following Terminal command:
   ```bash
   npx node-apple-signin-auth create-private-key /path/to/AuthKey_KEYID.p8
   ```
3. This outputs a Base64-encoded key value which you should set as APPLE_SECRET in your .env file

## Step 6: Add Additional HTTPS Setup for Local Testing

Apple requires HTTPS for the Sign in with Apple flow, even in development. To test locally:

1. Install mkcert:
   ```bash
   # macOS
   brew install mkcert
   mkcert -install
   
   # Windows (with Chocolatey)
   choco install mkcert
   mkcert -install
   ```

2. Create certificates for localhost:
   ```bash
   # Create a directory for certificates
   mkdir -p certificates
   cd certificates
   
   # Generate certificates
   mkcert localhost
   ```

3. Update your Next.js dev server to use HTTPS:
   Update your `package.json` script:
   ```json
   "scripts": {
     "dev": "next dev --experimental-https --experimental-https-key ./certificates/localhost-key.pem --experimental-https-cert ./certificates/localhost.pem",
     // ...other scripts
   }
   ```

## Testing Apple Sign-in

You can test Apple Sign-in by:

1. Start your development server with HTTPS enabled
2. Go to your authentication page (`/auth`)
3. Click "Continue with Apple"
4. Complete the Apple authentication flow
5. You should be redirected back to DailyBrief

## Troubleshooting

If you encounter issues with Apple Sign-in:

1. Ensure all domains and redirect URLs are registered correctly
2. Check that your key ID, team ID, and services ID are correctly set
3. Verify that your private key is correctly formatted and accessible
4. Test with a real Apple device or a macOS system when possible
5. Check browser console for any error messages

## Security Considerations

- Store your Apple private key securely and never commit it to version control
- In production, ensure your redirect URIs use HTTPS
- Apple refresh tokens expire after 6 months, so users may need to reauthenticate occasionally 