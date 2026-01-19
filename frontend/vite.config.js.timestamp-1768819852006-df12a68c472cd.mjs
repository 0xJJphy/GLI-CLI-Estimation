// vite.config.js
import { defineConfig } from "file:///C:/Users/Pedro/Documents/GitHub/GLI-CLI-Estimation/frontend/node_modules/vite/dist/node/index.js";
import { svelte } from "file:///C:/Users/Pedro/Documents/GitHub/GLI-CLI-Estimation/frontend/node_modules/@sveltejs/vite-plugin-svelte/src/index.js";
var vite_config_default = defineConfig({
  plugins: [svelte()],
  build: {
    // Increase chunk size warning limit (plotly.js alone is ~3MB)
    chunkSizeWarningLimit: 1e3,
    rollupOptions: {
      output: {
        // Manual chunks for better code splitting
        manualChunks: {
          // Heavy charting libraries in their own chunk
          "plotly": ["plotly.js-dist-min"],
          "lightweight-charts": ["lightweight-charts"],
          // Core vendor libs
          "vendor": ["svelte"]
        }
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxQZWRyb1xcXFxEb2N1bWVudHNcXFxcR2l0SHViXFxcXEdMSS1DTEktRXN0aW1hdGlvblxcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiQzpcXFxcVXNlcnNcXFxcUGVkcm9cXFxcRG9jdW1lbnRzXFxcXEdpdEh1YlxcXFxHTEktQ0xJLUVzdGltYXRpb25cXFxcZnJvbnRlbmRcXFxcdml0ZS5jb25maWcuanNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0M6L1VzZXJzL1BlZHJvL0RvY3VtZW50cy9HaXRIdWIvR0xJLUNMSS1Fc3RpbWF0aW9uL2Zyb250ZW5kL3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcbmltcG9ydCB7IHN2ZWx0ZSB9IGZyb20gJ0BzdmVsdGVqcy92aXRlLXBsdWdpbi1zdmVsdGUnXG5cbi8vIGh0dHBzOi8vdml0ZS5kZXYvY29uZmlnL1xuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcbiAgcGx1Z2luczogW3N2ZWx0ZSgpXSxcbiAgYnVpbGQ6IHtcbiAgICAvLyBJbmNyZWFzZSBjaHVuayBzaXplIHdhcm5pbmcgbGltaXQgKHBsb3RseS5qcyBhbG9uZSBpcyB+M01CKVxuICAgIGNodW5rU2l6ZVdhcm5pbmdMaW1pdDogMTAwMCxcbiAgICByb2xsdXBPcHRpb25zOiB7XG4gICAgICBvdXRwdXQ6IHtcbiAgICAgICAgLy8gTWFudWFsIGNodW5rcyBmb3IgYmV0dGVyIGNvZGUgc3BsaXR0aW5nXG4gICAgICAgIG1hbnVhbENodW5rczoge1xuICAgICAgICAgIC8vIEhlYXZ5IGNoYXJ0aW5nIGxpYnJhcmllcyBpbiB0aGVpciBvd24gY2h1bmtcbiAgICAgICAgICAncGxvdGx5JzogWydwbG90bHkuanMtZGlzdC1taW4nXSxcbiAgICAgICAgICAnbGlnaHR3ZWlnaHQtY2hhcnRzJzogWydsaWdodHdlaWdodC1jaGFydHMnXSxcbiAgICAgICAgICAvLyBDb3JlIHZlbmRvciBsaWJzXG4gICAgICAgICAgJ3ZlbmRvcic6IFsnc3ZlbHRlJ10sXG4gICAgICAgIH1cbiAgICAgIH1cbiAgICB9XG4gIH1cbn0pXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQWlYLFNBQVMsb0JBQW9CO0FBQzlZLFNBQVMsY0FBYztBQUd2QixJQUFPLHNCQUFRLGFBQWE7QUFBQSxFQUMxQixTQUFTLENBQUMsT0FBTyxDQUFDO0FBQUEsRUFDbEIsT0FBTztBQUFBO0FBQUEsSUFFTCx1QkFBdUI7QUFBQSxJQUN2QixlQUFlO0FBQUEsTUFDYixRQUFRO0FBQUE7QUFBQSxRQUVOLGNBQWM7QUFBQTtBQUFBLFVBRVosVUFBVSxDQUFDLG9CQUFvQjtBQUFBLFVBQy9CLHNCQUFzQixDQUFDLG9CQUFvQjtBQUFBO0FBQUEsVUFFM0MsVUFBVSxDQUFDLFFBQVE7QUFBQSxRQUNyQjtBQUFBLE1BQ0Y7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
