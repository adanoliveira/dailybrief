import Link from "next/link"
import { Button } from "@/components/ui/button"
import { LogoHorizontal } from "@/components/ui/logo"

export default function TermsPage() {
  return (
    <div className="container max-w-3xl py-12">
      <div className="mb-8 flex justify-center">
        <Link href="/">
          <LogoHorizontal width={200} priority />
        </Link>
      </div>

      <h1 className="mb-8 text-3xl font-bold">Terms of Service</h1>

      <div className="space-y-6 text-muted-foreground">
        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">1. Introduction</h2>
          <p>
            Welcome to DailyBrief ("we," "our," or "us"). By accessing or using our web application and services, you agree to be bound by these Terms of Service ("Terms"). Please read these Terms carefully.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">2. Services Description</h2>
          <p>
            DailyBrief is an AI news reader that aggregates news from various sources, generates summaries, and provides personalized daily digests based on user preferences. Our service may include content from third-party news providers and utilize artificial intelligence technologies to summarize and organize information.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">3. User Accounts</h2>
          <p>
            To access certain features of our service, you may be required to register for an account. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You must provide accurate and complete information when creating an account and keep your information updated.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">4. User Privacy</h2>
          <p>
            Your privacy is important to us. Our Privacy Policy explains how we collect, use, and protect your personal information. By using our services, you consent to our data practices as described in our Privacy Policy.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">5. Intellectual Property</h2>
          <p>
            Our service and its contents, features, and functionality are owned by DailyBrief and are protected by copyright, trademark, and other intellectual property laws. News articles and content from third-party providers remain the property of their respective owners.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">6. Limitations of Use</h2>
          <p>
            You agree not to:
          </p>
          <ul className="list-disc pl-6 pt-2">
            <li>Scrape, copy, or redistribute content from our service</li>
            <li>Attempt to access, tamper with, or use non-public areas of our service</li>
            <li>Circumvent any measures we use to prevent or restrict access to our service</li>
            <li>Use our service for any illegal purpose or in violation of any laws</li>
            <li>Use our service to distribute harmful software or content</li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">7. Content Disclaimer</h2>
          <p>
            While we strive to provide accurate and reliable information, we do not guarantee the accuracy, completeness, or reliability of content accessible through our service. AI-generated summaries may occasionally contain errors or omissions. We are not responsible for the content of third-party news sources.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">8. Termination</h2>
          <p>
            We reserve the right to terminate or suspend your account and access to our service at our discretion, without notice, for conduct that we believe violates these Terms or is harmful to other users, us, or third parties, or for any other reason.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">9. Changes to Terms</h2>
          <p>
            We may modify these Terms at any time. We will notify you of material changes by posting the new Terms on our site or through other communications. Your continued use of our service after changes become effective constitutes your acceptance of the changed Terms.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold text-foreground">10. Contact Information</h2>
          <p>
            If you have any questions about these Terms, please contact us at support@dailybrief.com.
          </p>
        </section>
      </div>

      <div className="mt-10 flex justify-center">
        <Button asChild>
          <Link className="bg-primary/10 hover:bg-primary/20 text-primary px-4 py-2 rounded-md" href="/auth">Return to Login</Link>
        </Button>
      </div>
    </div>
  )
} 