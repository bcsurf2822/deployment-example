"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";
import NavbarItems from "./NavbarItems";

interface NavbarProps {
  title?: string;
}

export default function Navbar({ title = "RAG Studio" }: NavbarProps) {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <nav className="w-full border-b border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex-shrink-0 flex items-center">
            <Link
              href="/"
              className="text-xl font-bold text-gray-900 hover:text-gray-700"
            >
              {title}
            </Link>
          </div>

          <div className="flex items-center space-x-6">
            <NavbarItems currentPath={pathname} />

            {user && (
              <div className="flex items-center space-x-4 pl-6 border-l border-gray-200">
                <span className="text-sm text-gray-600">{user.email}</span>
                <form action="/auth/signout" method="post">
                  <button
                    type="submit"
                    className="bg-gray-100 hover:bg-red-200 text-gray-700 px-3 py-1.5 rounded-md text-sm font-medium transition-colors cursor-pointer"
                  >
                    Sign Out
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
