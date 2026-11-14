import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { viteSingleFile } from 'vite-plugin-singlefile'

// One self-contained HTML file: the Python bot injects the ledger + CSP hashes later (no Node needed in CI).
export default defineConfig({
  plugins: [react(), tailwindcss(), viteSingleFile({ removeViteModuleLoader: true })],
  build: { assetsInlineLimit: 100_000_000, cssCodeSplit: false, modulePreload: false, target: 'es2022' },
})
