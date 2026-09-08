'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { User } from 'lucide-react';

const NAV_LINKS = [
  { label: 'Analyser', href: '/upload' },
  { label: 'Dashboard', href: '/dashboard' },
];

interface HeaderProps {
  userName?: string;
}

export function Header({ userName = 'Utilisateur' }: HeaderProps) {
  const pathname = usePathname();

  return (
    <header className="bg-black text-white">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-9 h-9 relative flex-shrink-0">
              <Image
                src="/orange-logo.png"
                alt="Orange"
                fill
                className="object-contain"
                priority
              />
            </div>
            <span className="text-xl font-bold tracking-tight">KYC Assistant</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href || pathname?.startsWith(link.href + '/');
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`text-sm font-medium transition-colors ${
                    isActive ? 'text-orange' : 'text-white hover:text-orange'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden sm:block">
            <span className="text-white/70">Bonjour </span>
            <span className="text-orange font-semibold">{userName}</span>
          </div>
        </div>
      </div>
    </header>
  );
}