import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: '@testing-library/jest-dom', replacement: fileURLToPath(new URL('./node_modules/@testing-library/jest-dom/dist/index.mjs', import.meta.url)) },
      { find: '@testing-library/react', replacement: fileURLToPath(new URL('./node_modules/@testing-library/react/dist/index.js', import.meta.url)) },
      { find: 'react/jsx-dev-runtime', replacement: fileURLToPath(new URL('./node_modules/react/jsx-dev-runtime.js', import.meta.url)) },
      { find: 'react/jsx-runtime', replacement: fileURLToPath(new URL('./node_modules/react/jsx-runtime.js', import.meta.url)) },
      { find: /^react$/, replacement: fileURLToPath(new URL('./node_modules/react/index.js', import.meta.url)) },
      { find: /^react-dom$/, replacement: fileURLToPath(new URL('./node_modules/react-dom/index.js', import.meta.url)) },
      { find: 'vitest', replacement: fileURLToPath(new URL('./node_modules/vitest/dist/index.js', import.meta.url)) },
    ],
  },
  server: {
    host: '127.0.0.1',
    port: 6310,
    strictPort: true,
    fs: {
      allow: ['..'],
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:6320',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['../tests/frontend/**/*.test.{ts,tsx}'],
  },
});
