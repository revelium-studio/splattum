import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable larger file uploads
  experimental: {
    serverActions: {
      bodySizeLimit: "50mb",
    },
  },
  // Explicitly disable automatic redirects - accept requests from any host
  // This ensures the app works when served behind a router
  async redirects() {
    return []; // No redirects
  },
  // Allow serving PLY files from public directory
  async headers() {
    return [
      {
        source: "/outputs/:path*",
        headers: [
          {
            key: "Access-Control-Allow-Origin",
            value: "*",
          },
          {
            key: "Content-Type",
            value: "application/octet-stream",
          },
        ],
      },
      {
        source: "/api/:path*",
        headers: [
          {
            key: "Access-Control-Allow-Origin",
            value: "https://lab.revelium.studio",
          },
          {
            key: "Access-Control-Allow-Methods",
            value: "GET, POST, OPTIONS",
          },
          {
            key: "Access-Control-Allow-Headers",
            value: "Content-Type, Authorization, Accept, X-Requested-With",
          },
          {
            key: "Access-Control-Allow-Credentials",
            value: "true",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
