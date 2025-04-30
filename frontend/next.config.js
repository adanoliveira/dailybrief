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
  },
  // Only use standalone for production builds
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,
  // Disable SWC minification in development for better compatibility
  swcMinify: process.env.NODE_ENV === 'production',
  // Increase webpack's memory limit
  webpack: (config) => {
    config.watchOptions = {
      poll: 1000,
      aggregateTimeout: 300,
    };
    return config;
  },
}

module.exports = nextConfig 