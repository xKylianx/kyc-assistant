'use client';

import Link from 'next/link';
import { BarChart3 } from 'lucide-react';

export function Header() {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-4 py-4 max-w-7xl">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">KYC Assistant</span>
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              href="/upload"
              className="text-gray-600 hover:text-orange-500 transition-colors"
            >
              Analyser
            </Link>
            <Link
              href="/dashboard"
              className="text-gray-600 hover:text-orange-500 transition-colors"
            >
              Dashboard
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}