// frontend/app/layout.tsx
import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'revove – Bozeman eats, rethought',
  description: 'Search Bozeman restaurant reviews by item and place.',
};

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/places', label: 'Places' },
  { href: '/search', label: 'Search reviews' },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap"
        />
      </head>
      <body className="min-h-screen">
        <div className="max-w-6xl mx-auto px-4">
          <header className="flex items-center justify-between py-6">
            <Link href="/" className="text-2xl font-semibold tracking-tight text-white">
              revove
            </Link>
            <nav className="flex items-center gap-6 text-sm font-medium text-slate-200">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="transition hover:text-cyan-200"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </header>

          <main className="pb-16">{children}</main>
        </div>
      </body>
    </html>
  );
}
