import type { NextConfig } from "next";
import fs from "fs";

// Patch for Windows FAT32 filesystem where readlink throws EISDIR on regular files
const origReadlinkSync = fs.readlinkSync;
fs.readlinkSync = ((path: fs.PathLike, options?: any) => {
  try {
    return origReadlinkSync(path, options);
  } catch (err: any) {
    if (err && err.code === "EISDIR") {
      const e = new Error(`EINVAL: invalid argument, readlink '${path}'`);
      (e as any).code = "EINVAL";
      throw e;
    }
    throw err;
  }
}) as any;

const origReadlink = fs.readlink;
fs.readlink = ((path: fs.PathLike, options: any, callback?: any) => {
  const cb = typeof options === "function" ? options : callback;
  const opt = typeof options === "function" ? undefined : options;
  return origReadlink(path, opt, (err: any, linkString: any) => {
    if (err && err.code === "EISDIR") {
      const e = new Error(`EINVAL: invalid argument, readlink '${path}'`);
      (e as any).code = "EINVAL";
      return cb(e);
    }
    return cb(err, linkString);
  });
}) as any;

if (fs.promises && fs.promises.readlink) {
  const origPromisesReadlink = fs.promises.readlink;
  fs.promises.readlink = (async (path: fs.PathLike, options?: any) => {
    try {
      return await origPromisesReadlink(path, options);
    } catch (err: any) {
      if (err && err.code === "EISDIR") {
        const e = new Error(`EINVAL: invalid argument, readlink '${path}'`);
        (e as any).code = "EINVAL";
        throw e;
      }
      throw err;
    }
  }) as any;
}

const nextConfig: NextConfig = {
  // Strict React mode
  reactStrictMode: true,

  eslint: {
    ignoreDuringBuilds: true,
  },

  webpack: (config) => {
    config.resolve.symlinks = false;
    return config;
  },

  // API proxying during development - routes /api/* to FastAPI backend
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.INTERNAL_BACKEND_URL ?? "http://127.0.0.1:8000/api"}/:path*`,
      },
    ];
  },

};

export default nextConfig;
