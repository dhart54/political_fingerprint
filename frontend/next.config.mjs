import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  ...(process.env.ENABLE_HEALTH_CHOICE_REVIEW === "1" ? { devIndicators: false } : {}),
  outputFileTracingRoot: path.join(__dirname, ".."),
};

export default nextConfig;
