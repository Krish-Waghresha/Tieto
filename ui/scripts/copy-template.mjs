// Copy the single-file build into the bot as its HTML template.
import { copyFileSync, statSync } from 'node:fs'
const out = '../reviewbot/static/review-app.template.html'
copyFileSync('dist/index.html', out)
console.log(`template -> ${out} (${(statSync(out).size / 1024).toFixed(0)} KB)`)
