import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    // Allow LAN access by IP/hostname from other devices in local network.
    allowedHosts: true,
  },
});