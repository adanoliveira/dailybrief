import Link from "next/link"
import { Button } from "@/components/ui/button"
import { LogoHorizontal } from "@/components/ui/logo"

export default function PrivacyPage() {
  return (
    <div className="container max-w-3xl py-12">
      <div className="mb-8 flex justify-center">
        <Link href="/">
          <LogoHorizontal width={200} priority />
        </Link>
      </div>

      <h1 className="mb-8 text-3xl font-bold">Privacy Policy</h1>

      <div className="space-y-6 text-muted-foreground">
        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">1. Introduction</h2>
          <p>
            At DailyBrief, we value your privacy and are committed to protecting your personal data. This Privacy Policy explains how we collect, use, and safeguard your information when you use our news reader service.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">2. Information We Collect</h2>
          <p>
            We collect the following types of information:
          </p>
          <ul className="list-disc pl-6 pt-2">
            <li><strong>Account Information:</strong> Email address and authentication data when you sign up</li>
            <li><strong>Profile Information:</strong> Your preferences for news topics, regions, publications, and languages</li>
            <li><strong>Usage Data:</strong> Information about how you interact with our service, such as articles read, digests viewed, and features used</li>
            <li><strong>Device Information:</strong> Data about your device, browser, and how you access our service</li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">3. How We Use Your Information</h2>
          <p>
            We use your information to:
          </p>
          <ul className="list-disc pl-6 pt-2">
            <li>Provide, maintain, and improve our services</li>
            <li>Personalize your news feed and daily digests based on your preferences</li>
            <li>Send you important notifications and updates</li>
            <li>Analyze usage patterns to enhance our service</li>
            <li>Ensure the security of our platform</li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">4. Third-Party Services</h2>
          <p>
            Our service integrates with third-party services, including:
          </p>
          <ul className="list-disc pl-6 pt-2">
            <li><strong>News Sources:</strong> We aggregate content from various news providers</li>
            <li><strong>Authentication Providers:</strong> Google, Apple, and email services for account authentication</li>
            <li><strong>AI Services:</strong> For article summarization and digest generation</li>
          </ul>
          <p className="mt-2">
            Each third-party service has its own privacy policy governing how they handle your data.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">5. Data Storage and Security</h2>
          <p>
            We implement appropriate security measures to protect your personal information. Your data is stored securely in our database and is accessed only by authorized personnel. While we strive to use commercially acceptable means to protect your data, no method of transmission over the internet or electronic storage is 100% secure.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">6. Your Rights</h2>
          <p>
            Depending on your location, you may have rights regarding your personal data, including:
          </p>
          <ul className="list-disc pl-6 pt-2">
            <li>Accessing and receiving a copy of your data</li>
            <li>Correcting inaccurate data</li>
            <li>Requesting deletion of your data</li>
            <li>Restricting or objecting to processing</li>
            <li>Data portability</li>
          </ul>
          <p className="mt-2">
            To exercise these rights, please contact us using the information provided below.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">7. Children's Privacy</h2>
          <p>
            Our service is not intended for individuals under the age of 13. We do not knowingly collect personal information from children under 13. If you are a parent or guardian and believe your child has provided us with personal information, please contact us.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">8. Changes to This Privacy Policy</h2>
          <p>
            We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "last updated" date. You are advised to review this Privacy Policy periodically for any changes.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">9. Contact Us</h2>
          <p>
            If you have any questions about this Privacy Policy, please contact us at:
          </p>
          <p className="mt-2">
            Email: privacy@dailybrief.com
          </p>
        </section>
      </div>

      <div className="mt-10 flex justify-center">
          <Link className="bg-primary/10 hover:bg-primary/20 text-primary px-4 py-2 rounded-md" href="/auth">Return to Sign In</Link>
      </div>
    </div>
  )
} 