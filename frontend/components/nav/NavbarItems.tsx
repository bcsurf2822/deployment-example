"use client";

import Link from "next/link";

interface NavbarItemsProps {
  currentPath: string;
}

interface NavItem {
  name: string;
  href: string;
}

const navItems: NavItem[] = [
  { name: "Home", href: "/" },
  { name: "About", href: "/about" },
  { name: "Chat", href: "/chat" },
  { name: "RAG Pipelines", href: "/rag-pipelines" },
  { name: "Documents", href: "/documents" },
  { name: "Settings", href: "/settings" },
];

export default function NavbarItems({ currentPath }: NavbarItemsProps) {
  return (
    <div className="flex items-center space-x-1">
      {navItems.map((item) => {
        const isActive =
          item.href === "/"
            ? currentPath === "/"
            : currentPath === item.href ||
              currentPath.startsWith(item.href + "/");

        return (
          <Link
            key={item.name}
            href={item.href}
            className={`
              inline-block px-4 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer
              ${
                isActive
                  ? "bg-gray-900 text-white"
                  : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              }
            `}
          >
            {item.name}
          </Link>
        );
      })}
    </div>
  );
}
