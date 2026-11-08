import type { Metadata } from 'next';
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

export const metadata: Metadata = {
  title: 'CivicFix — AI-Powered City Infrastructure Reporting & Operations',
  description: 'Smart municipal infrastructure reporting, computer vision issue classification, duplicate detection, and dispatch management.',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/logo.png', sizes: '1024x1024', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-translucency="regular">
      <body className="bg-surface-canvas text-content-primary min-h-screen flex flex-col antialiased relative selection:bg-md-gold-subtle selection:text-md-black">
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
