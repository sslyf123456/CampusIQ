import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api/campus': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/ai': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        // SSE 流式响应需要禁用 proxy 缓冲
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            res.setHeader('Cache-Control', 'no-cache')
            res.setHeader('Connection', 'keep-alive')
            res.setHeader('X-Accel-Buffering', 'no')
          })
        },
        ws: false,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
})
