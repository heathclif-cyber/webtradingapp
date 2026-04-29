/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  // Railway sets PORT automatically
  ...(process.env.PORT && {
    server: { port: parseInt(process.env.PORT) },
  }),
};

module.exports = nextConfig;
