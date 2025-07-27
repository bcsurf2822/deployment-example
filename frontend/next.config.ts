import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Remove static export configuration to allow dynamic rendering with Supabase auth
  // output: 'export',
  // trailingSlash: true,
  // skipTrailingSlashRedirect: true,
  // distDir: 'out',
  images: {
    unoptimized: true
  }
};

export default nextConfig;
