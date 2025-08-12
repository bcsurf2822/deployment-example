'use client';

import { usePathname } from 'next/navigation';
import Navbar from '@/components/nav/Navbar.component';

interface LayoutContentProps {
  children: React.ReactNode;
  title?: string;
}

export default function LayoutContent({ children, title = "RAG Studio" }: LayoutContentProps) {
  const pathname = usePathname();
  
  // List of paths where navbar should be hidden
  const hideNavbarPaths = ['/auth/login', '/auth/callback', '/auth/signout', '/auth/auth-code-error'];
  const shouldHideNavbar = hideNavbarPaths.some(path => pathname?.startsWith(path));
  
  return (
    <>
      {!shouldHideNavbar && <Navbar title={title} />}
      <main className="min-h-screen">{children}</main>
    </>
  );
}