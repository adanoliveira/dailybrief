/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
    domains: ['railway.app', 'supabase.co', 'vercel.app'], // Allow images from these domains
  },
  // Use standalone for production builds (required for Railway deployment if needed)
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,
  // Enable SWC minification in production
  swcMinify: process.env.NODE_ENV === 'production',
  // Production optimizations
  poweredByHeader: false,
  generateEtags: false,
  compress: true,
  // Environment variables that should be available to the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  // Webpack configuration
  webpack: (config, { dev, isServer }) => {
    // Development-specific webpack settings
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    
    // Production optimizations
    if (!dev && !isServer) {
      config.optimization.splitChunks.chunks = 'all';
    }
    
    return config;
  },
}

module.exports = nextConfig 