import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  build: {
    // Increase chunk size warning limit (plotly.js alone is ~3MB)
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // Manual chunks for better code splitting
        manualChunks: {
          // Heavy charting libraries in their own chunk
          'plotly': ['plotly.js-dist-min'],
          'lightweight-charts': ['lightweight-charts'],
          // Core vendor libs
          'vendor': ['svelte'],
        }
      }
    }
  }
})
