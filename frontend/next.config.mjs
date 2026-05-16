/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
  transpilePackages: [
    'antd',
    '@ant-design/pro-components',
    '@ant-design/pro-layout',
    '@ant-design/pro-table',
    '@ant-design/icons',
    'leaflet',
    'react-leaflet',
  ],
  images: {
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost', port: '8000' },
    ],
  },
};

export default nextConfig;
