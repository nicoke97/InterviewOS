import dns from 'node:dns'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Windows often resolves "localhost" to IPv6 (::1) while the API listens on
// 127.0.0.1. Prefer IPv4 so the page and the /api proxy actually connect.
dns.setDefaultResultOrder('ipv4first')

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '127.0.0.1',
    port: 5174,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8011',
        changeOrigin: true,
      },
    },
  },
})
