import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      allow: ['..'],
    },
  },
  worker: {
    format: 'es',
  },
  optimizeDeps: {
    include: ['pdfjs-dist/build/pdf.worker.min.mjs'],
  },
})
