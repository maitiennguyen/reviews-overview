// frontend/app/layout.tsx
import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'revove – Bozeman recommendations',
  description: 'AI-powered what-to-order suggestions for Bozeman restaurants',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-100 min-h-screen text-slate-800">
        <header className="bg-white shadow">
          <div className="container mx-auto px-4 py-3 flex items-center justify-between">
            <Link href="/" className="text-xl font-bold">
              revove
            </Link>
            <nav className="space-x-4">
              <Link href="/places" className="text-blue-600 hover:underline">
                Places
              </Link>
            </nav>
          </div>
        </header>
        <main className="container mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
