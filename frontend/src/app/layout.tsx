import type { Metadata } from 'next';
import { Public_Sans } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';
import GradientBackdrop from '@/components/glass/GradientBackdrop';
import GlassTabBar from '@/components/glass/GlassTabBar';
import Footer from '@/components/Footer';
import MainContentWrapper from '@/components/layout/MainContentWrapper';
import { I18nProvider } from '@/lib/i18n';
import { ToastProvider } from '@/components/ui/Toast';
import QueryProvider from '@/lib/providers/QueryProvider';
import { SupabaseAuthProvider } from '@/lib/supabase/auth';

const publicSans = Public_Sans({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-public-sans',
});

export const metadata: Metadata = {
  title: 'CivicFix — AI-Powered City Infrastructure Reporting & Operations',
  description: 'Smart municipal infrastructure reporting, computer vision issue classification, duplicate detection, and dispatch management.',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/logo.webp', sizes: '512x512', type: 'image/webp' },
    ],
    apple: [
      { url: '/apple-icon.png', sizes: '180x180', type: 'image/png' },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-translucency="regular" className={publicSans.variable}>
      <body className="bg-surface-canvas text-content-primary min-h-screen flex flex-col antialiased relative selection:bg-md-gold-subtle selection:text-md-black font-sans">
        {/* Skip to Main Content Link (WCAG B10 Ship Requirement) */}
        <a 
          href="#main-content" 
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#1b1c19] focus:text-white focus:rounded-xl focus:font-bold focus:shadow-xl focus:ring-2 focus:ring-[#ffc72c]"
        >
          Skip to main content
        </a>
        <QueryProvider>
          <SupabaseAuthProvider>
            <I18nProvider>
              <ToastProvider>
                {/* Soft Drifting Maryland Mesh Gradient Atmosphere */}
                <GradientBackdrop />

                {/* Floating Liquid Glass Navigation Bar */}
                <Navbar />

                {/* Main Content (Responsive app shell wrapper) */}
                <MainContentWrapper>
                  {children}
                </MainContentWrapper>

                {/* Mobile Floating Glass Tab Bar (Thumb Zone) */}
                <GlassTabBar />

                {/* Solid White/Warm-White Footer (Hidden automatically on /map) */}
                <Footer />
              </ToastProvider>
            </I18nProvider>
          </SupabaseAuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
