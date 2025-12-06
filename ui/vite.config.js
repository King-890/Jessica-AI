import react from '@vitejs/plugin-react'
import path from 'node:path'

// https://vite.dev/config/
export default {
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
}
