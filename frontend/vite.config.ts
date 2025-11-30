import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite configuration aligned with React 19 and TypeScript 5.9
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  preview: {
    port: 4173,
  },
});
