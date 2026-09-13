import { defineConfig } from "vite";

export default defineConfig({
  // Addons import 'three'; resolve it to the same core as the WebGPU renderer.
  resolve: { alias: [{ find: /^three$/, replacement: "three/webgpu" }] },
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 600,
  },
  server: {
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true,
      },
    },
  },
});
