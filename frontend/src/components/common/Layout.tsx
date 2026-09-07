import { Header } from './Header';
import { Footer } from './Footer';

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Header />
      <main className="px-6 py-8 flex-1">{children}</main>
      <Footer />
    </div>
  );
}