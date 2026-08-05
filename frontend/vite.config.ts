import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteStaticCopy } from 'vite-plugin-static-copy'
import path from 'path'

const skipCesiumStaticCopy = process.env.SKIP_CESIUM_COPY === 'true'

export default defineConfig(({ command }) => ({
  plugins: [
    vue(),
    ...(skipCesiumStaticCopy
      ? []
      : [
          viteStaticCopy({
            targets: [
              { src: 'node_modules/cesium/Build/Cesium/Workers/**/*', dest: 'cesium/Workers' },
              { src: 'node_modules/cesium/Build/Cesium/Assets/**/*', dest: 'cesium/Assets' },
              { src: 'node_modules/cesium/Build/Cesium/Widgets/**/*', dest: 'cesium/Widgets' },
              { src: 'node_modules/cesium/Build/Cesium/ThirdParty/**/*', dest: 'cesium/ThirdParty' },
            ],
          }),
        ]),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    CESIUM_BASE_URL: JSON.stringify(command === 'serve' ? '/node_modules/cesium/Build/Cesium' : '/cesium'),
  },
  server: {
    // Polling avoids Windows FSWatcher UNKNOWN errors on some drives;
    // ignore heavy SPX tiles to keep HMR responsive.
    watch: {
      usePolling: true,
      interval: 1000,
      ignored: [
        '**/node_modules/**',
        '**/dist/**',
        '**/data/**',
        '**/server/**',
        '**/public/gis/s1-6/layers/current/spx-tiles/**',
      ],
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/cesium')) {
            return 'cesium'
          }
          if (id.includes('src/modules/traffic-gis-overview')) {
            return 'traffic-gis-overview'
          }
        },
      },
    },
  },
}))
