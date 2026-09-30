import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The browser only ever talks to the Vite origin; /api/* is forwarded to FastAPI with the
// prefix stripped. Same-origin keeps the (Phase 2) httpOnly auth cookie simple.
const apiTarget = process.env.API_URL ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
