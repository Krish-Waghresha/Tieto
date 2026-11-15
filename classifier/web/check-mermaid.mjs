import assert from 'node:assert/strict'
import { readFile, mkdir } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { build } from 'esbuild'
import { chromium } from '@playwright/test'

const source = process.argv[2] ?? fileURLToPath(new URL('../out/pr-2/comment.md', import.meta.url))
const markdown = await readFile(source, 'utf8')
const diagram = /```mermaid\n([\s\S]*?)\n```/.exec(markdown)?.[1]
assert.ok(diagram, 'No Mermaid diagram found in the review comment')
const bundled = await build({ stdin: { contents: 'import mermaid from "mermaid"; window.mermaid = mermaid;', resolveDir: fileURLToPath(new URL('..', import.meta.url)) }, bundle: true, write: false, format: 'iife', minify: true })
const browser = await chromium.launch({ headless: true })
try {
  const page = await browser.newPage({ viewport: { width: 1250, height: 800 } })
  await page.setContent('<!doctype html><html><body><main id="graph"></main></body></html>')
  await page.addScriptTag({ content: bundled.outputFiles[0].text })
  const rendered = await page.evaluate(async definition => {
    window.mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'neutral', flowchart: { htmlLabels: true } })
    await window.mermaid.parse(definition)
    const result = await window.mermaid.render('native-review', definition)
    document.getElementById('graph').innerHTML = result.svg
    return { nodes: document.querySelectorAll('g.node').length, edges: document.querySelectorAll('path.flowchart-link').length }
  }, diagram)
  assert.equal(rendered.nodes, 7)
  assert.equal(rendered.edges, 6)
  for (const [color, expected] of Object.entries({ red: 'rgb(180, 35, 50)', green: 'rgb(35, 122, 70)', amber: 'rgb(156, 101, 0)', gray: 'rgb(91, 100, 114)' })) {
    const fill = await page.locator(`g.node.${color} rect`).first().evaluate(element => getComputedStyle(element).fill)
    assert.equal(fill, expected, `Wrong ${color} block fill`)
  }
  const destination = new URL('../test-results/', import.meta.url)
  await mkdir(destination, { recursive: true })
  await page.locator('#graph').screenshot({ path: fileURLToPath(new URL('github-mermaid.png', destination)) })
  console.log(JSON.stringify({ passed: true, ...rendered, colors: ['green', 'amber', 'red', 'gray'], note: 'Mermaid rendered locally; GitHub applies its own renderer/theme.' }, null, 2))
} finally { await browser.close() }