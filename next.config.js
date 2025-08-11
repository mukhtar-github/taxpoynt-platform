/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Exclude directories from TypeScript checking and compilation
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  experimental: {
    // Exclude specific directories from compilation
    externalDir: true,
  }
}

module.exports = nextConfig