import type { NextConfig } from "next";

const apiUpstream = process.env.API_UPSTREAM ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  agentRules: false,
  output: "standalone",
  turbopack: {
    root: process.cwd(),
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiUpstream}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
