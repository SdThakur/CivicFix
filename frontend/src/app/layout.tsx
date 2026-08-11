import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';

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
    <html lang="en" className="dark">
      <body className="bg-[#0b0f19] text-slate-100 min-h-screen flex flex-col antialiased">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <footer className="border-t border-slate-800/80 bg-[#080c14] py-8 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-300">CivicFix Platform</span>
              <span>— Municipal Operations Engine</span>
            </div>
            <p>© 2026 CivicFix. Powered by Computer Vision, PostGIS & Machine Intelligence.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
