import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy API calls to the FastAPI backend in dev — avoids CORS issues
    proxy: {
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/resume': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  define: {
    // Make env vars available without import.meta.env boilerplate everywhere
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
})
