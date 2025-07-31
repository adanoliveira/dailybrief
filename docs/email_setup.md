# Email Setup with Resend

DailyBrief uses [Resend](https://resend.com) for sending emails, particularly for magic link authentication.

## Why Resend?

- Modern API-first email service
- Excellent deliverability
- Simple interface and API
- Free tier for development (up to 100 emails/day)
- Clean design and good developer experience

## Setting Up Resend

1. Create a free account at [Resend.com](https://resend.com)
2. Verify your domain or use a Resend subdomain for testing
3. Create an API key in the Resend dashboard
4. Add the API key to your `.env` file:

```
RESEND_API_KEY=re_yourAPIKeyHere
EMAIL_FROM=noreply@yourdomain.com
```

## Email Templates

DailyBrief includes custom email templates for various functionalities:

- **Magic Link Authentication**: Beautiful, responsive emails for sign-in links
- **[Future] Digest Notifications**: Emails notifying users of new daily digests
- **[Future] Welcome Emails**: Onboarding emails for new users

## Development Testing

During development, if the Resend API key is not valid or emails cannot be sent, the app will fall back to logging magic links to the console for easy testing.

You'll see log messages like:

```
[DEV] Magic link for user@example.com: http://localhost:3000/api/auth/callback/email?token=123abc...
```

## Customizing Templates

Email templates are found in:
- `frontend/lib/email-templates.ts`

You can customize both the HTML and plain text versions of emails by editing these files. 