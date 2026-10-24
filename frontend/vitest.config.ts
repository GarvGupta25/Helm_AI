import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig({ plugins: [react()], test: { environment: 'jsdom', include: ['src/journey/wizard/*.test.tsx', 'src/ui/*.test.tsx', 'src/marketing/chat/*.test.tsx'] } });
