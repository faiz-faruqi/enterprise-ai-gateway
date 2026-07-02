/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    // Required for standalone output to include all necessary files
  },
};

module.exports = nextConfig;
