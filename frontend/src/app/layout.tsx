import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';
import GradientBackdrop from '@/components/glass/GradientBackdrop';
import GlassTabBar from '@/components/glass/GlassTabBar';
import { I18nProvider } from '@/lib/i18n';
import { ToastProvider } from '@/components/ui/Toast';

export const metadata: Metadata = {
  title: 'CivicFix — AI-Powered City Infrastructure Reporting & Operations',
  description: 'Smart municipal infrastructure reporting, computer vision issue classification, duplicate detection, and dispatch management.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-translucency="regular">
      <body className="bg-surface-canvas text-content-primary min-h-screen flex flex-col antialiased relative selection:bg-md-gold-subtle selection:text-md-black">
        <I18nProvider>
          <ToastProvider>
            {/* Soft Drifting Maryland Mesh Gradient Atmosphere */}
            <GradientBackdrop />

            {/* Floating Liquid Glass Navigation Bar */}
            <Navbar />

            {/* Main Content (Scrolls cleanly underneath floating chrome) */}
            <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 relative z-10 pb-24 md:pb-12">
              {children}
            </main>

            {/* Mobile Floating Glass Tab Bar (Thumb Zone) */}
            <GlassTabBar />

            {/* Solid White/Warm-White Footer */}
            <footer className="border-t border-surface-border bg-surface-card-subtle py-8 text-center text-xs text-content-muted relative z-10">
              <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-content-primary tracking-tight">CivicFix Platform</span>
                  <span className="text-content-muted">— Municipal Operations Engine</span>
                </div>
                <p className="text-content-secondary">
                  © 2026 CivicFix. Powered by Computer Vision, PostGIS & Machine Intelligence.
                </p>
              </div>
            </footer>
          </ToastProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
