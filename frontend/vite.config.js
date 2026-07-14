import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite configuration for the React frontend.
// The dev server runs on port 5173 by default — this matches the
// CORS_ORIGINS setting in the backend's .env file.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
})