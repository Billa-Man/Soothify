import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import Image from "next/image";
import ThemeToggle from "./theme/Toggle";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
  preload: true,
});

export const metadata: Metadata = {
  title: "Soothify - Your Mental Health Companion",
  description: "Assessment, dashboard, resources, and AI chat",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light-theme" suppressHydrationWarning>
      <body className={`${inter.variable} antialiased`}>
        <header className="sticky top-0 z-40 border-b bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60">
          <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-medium">
              <Image src="/media/mainlogo.png" alt="Soothify" width={28} height={28} />
              <span>Soothify</span>
            </Link>
            <nav className="hidden md:flex items-center gap-4 text-sm">
              <Link href="/assessment" className="hover:text-indigo-600">Assessment</Link>
              <Link href="/chat" className="hover:text-indigo-600">AI Chat</Link>
              <Link href="/dashboard" className="hover:text-indigo-600">Dashboard</Link>
              <Link href="/hume" className="hover:text-indigo-600">Hume Voice</Link>
              <Link href="/facilities" className="hover:text-indigo-600">Facilities</Link>
              <Link href="/exercises" className="hover:text-indigo-600">Exercises</Link>
              <Link href="/blogs" className="hover:text-indigo-600">Blogs</Link>
            </nav>
            <div className="flex items-center gap-3">
              <ThemeToggle />
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-6">
          {children}
        </main>

        <footer className="mt-8 border-t">
          <div className="mx-auto max-w-6xl px-4 py-6 text-sm text-slate-600 flex flex-col md:flex-row items-center justify-between gap-2">
            <p>© {new Date().getFullYear()} Soothify</p>
            <div className="flex items-center gap-4">
              <a className="hover:text-indigo-600" href="/blogs">Resources</a>
              <a className="hover:text-indigo-600" href="/exercises">Exercises</a>
              <a className="hover:text-indigo-600" href="/facilities">Find Help</a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
