import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      {
        find: '@/lib',
        replacement: resolve(__dirname, 'src/lib')
      },
      {
        find: '@',
        replacement: resolve(__dirname, 'src')
      },
      {
        find: '@/contexts',
        replacement: resolve(__dirname, 'src/contexts')
      },
      {
        find: '@/components',
        replacement: resolve(__dirname, 'src/components')
      },
      {
        find: '@/types',
        replacement: resolve(__dirname, 'src/types')
      }
    ],
    extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          api: ['axios'],
          supabase: ['@supabase/supabase-js'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-popover', '@radix-ui/react-slot']
        }
      }
    }
  }
})
