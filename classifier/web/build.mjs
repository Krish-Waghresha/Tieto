import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { build } from 'esbuild'
import octicons from '@primer/octicons'

const source = process.argv[2] ? resolve(process.argv[2]) : fileURLToPath(new URL('../out/analysis.json', import.meta.url))
const destination = process.argv[3] ? resolve(process.argv[3]) : fileURLToPath(new URL('../out/graph.html', import.meta.url))
const data = JSON.parse(await readFile(source, 'utf8'))
const accessScenario = data.policy?.version === 'evidence-v2'
	? JSON.parse(await readFile(new URL('../fixtures/invoice-import/experience.json', import.meta.url), 'utf8')).retry
	: JSON.parse(await readFile(new URL('../fixtures/order-flow/access-review.json', import.meta.url), 'utf8'))
let accessAudio = ''
if (process.platform === 'darwin') {
	const audioHash = createHash('sha256').update('Samantha:165:22050:' + accessScenario.narration).digest('hex').slice(0, 16)
	const audioPath = fileURLToPath(new URL(`../out/audio/access-${audioHash}.wav`, import.meta.url))
	await mkdir(dirname(audioPath), { recursive: true })
	let audioBytes
	try { audioBytes = await readFile(audioPath) } catch (error) {
		if (error.code !== 'ENOENT') throw error
		execFileSync('say', ['-v', 'Samantha', '-r', '165', '--file-format=WAVE', '--data-format=LEI16@22050', '-o', audioPath], { input: accessScenario.narration, timeout: 60000, stdio: ['pipe', 'ignore', 'pipe'] })
		audioBytes = await readFile(audioPath)
	}
	accessAudio = `data:audio/wav;base64,${audioBytes.toString('base64')}`
}
let pullRequest = null
if (data.github) {
	const binding = data.github
	if (!/^[\w.-]+\/[\w.-]+$/.test(binding.repository) || !Number.isSafeInteger(binding.number) || binding.number < 1) throw new Error('Invalid PR binding')
	const response = JSON.parse(execFileSync('gh', ['api', `repos/${binding.repository}/pulls/${binding.number}`], { encoding: 'utf8', timeout: 30000, maxBuffer: 2 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] }))
	if (response.number !== binding.number || response.base.repo.full_name !== binding.repository || response.base.sha !== binding.base || response.head.sha !== binding.head) throw new Error('PR revision differs from the analysis; rebuild the analysis before updating its header')
	pullRequest = {
		repository: binding.repository, number: response.number, title: response.title,
		state: response.merged ? 'merged' : response.state === 'closed' ? 'closed' : response.draft ? 'draft' : 'open',
		author: response.user.login, baseBranch: response.base.ref, headBranch: response.head.ref,
		baseRepository: response.base.repo.full_name, headRepository: response.head.repo?.full_name ?? null,
		commits: response.commits, changedFiles: response.changed_files,
		base: binding.base, head: binding.head,
	}
}
const css = await readFile(new URL('./style.css', import.meta.url), 'utf8')
const template = (await readFile(new URL('./index.html', import.meta.url), 'utf8')).replace(/__ICON_([A-Z_]+)__/g, (placeholder, name) => octicons[name.toLowerCase().replaceAll('_', '-')].toSVG({ 'aria-hidden': 'true', focusable: 'false' }))
const result = await build({ entryPoints: [new URL('./app.js', import.meta.url).pathname], bundle: true, write: false, format: 'iife', minify: true, target: 'es2022' })
const script = result.outputFiles[0].text
const hash = value => `'sha256-${createHash('sha256').update(value).digest('base64')}'`
const csp = `default-src 'none'; script-src ${hash(script)}; style-src ${hash(css)}; style-src-attr 'unsafe-hashes' ${hash('overflow: hidden; ')}; img-src data:; media-src data:; base-uri 'none'; form-action 'none'`
const values = { CSP: csp, STYLE: css, SCRIPT: script, ANALYSIS: JSON.stringify(data).replaceAll('<', '\\u003c'), PR_METADATA: JSON.stringify(pullRequest).replaceAll('<', '\\u003c') }
values.ACCESS_AUDIO = accessAudio
const output = template.replace(/__(CSP|STYLE|SCRIPT|ANALYSIS|PR_METADATA|ACCESS_AUDIO)__/g, (placeholder, name) => values[name])
await mkdir(dirname(destination), { recursive: true })
await writeFile(destination, output)
console.log(`Built ${destination} from ${data.nodes.length} extracted nodes, ${data.edges.length} edges. Mode: ${data.mode}.`)