import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Remove static export configuration to allow dynamic rendering with Supabase auth
  // output: 'export',
  // trailingSlash: true,
  // skipTrailingSlashRedirect: true,
  // distDir: 'out',
  images: {
    unoptimized: true
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Exclude server-only packages from client bundle
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        url: false,
        zlib: false,
        http: false,
        https: false,
        assert: false,
        os: false,
        path: false,
      };

      // Exclude Google Drive and authentication packages from client bundle
      config.externals = config.externals || [];
      config.externals.push({
        '@googleapis/drive': '@googleapis/drive',
        'google-auth-library': 'google-auth-library',
        'gaxios': 'gaxios',
        'google-p12-pem': 'google-p12-pem',
      });
    }
    return config;
  },
  experimental: {
    serverComponentsExternalPackages: [
      '@googleapis/drive',
      'google-auth-library',
    ],
  },
};

export default nextConfig;
