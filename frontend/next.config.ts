// Copyright (c) 2025 Adara Screen by Hebron
// Owner: Sujesh M S
// All Rights Reserved
//
// This software is proprietary to Adara Screen by Hebron.
// Unauthorized use, reproduction, or distribution is strictly prohibited.

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
