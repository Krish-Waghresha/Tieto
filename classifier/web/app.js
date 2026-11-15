import dagre from '@dagrejs/dagre'
import svgPanZoom from 'svg-pan-zoom'
import { diffLines } from 'diff'
import shippingScenario from '../fixtures/order-flow/shipping-review.json'
import accessScenario from '../fixtures/order-flow/access-review.json'
import { createAccessReview } from './access-review.js'
import { invoiceGraph, invoiceCard, invoiceRetry, invoiceAttention, createInvoiceReview, createOverallReview } from './invoice-review.js'
import { createReviewSession } from './review-session.js'

const analysis = JSON.parse(document.getElementById('analysis').textContent)
const isInvoice = analysis.policy?.version === 'evidence-v2'
document.body.classList.toggle('invoice-review', isInvoice)
const graph = isInvoice ? invoiceGraph(analysis) : analysis
const labels = isInvoice ? invoiceAttention : { green: 'Light review', amber: 'Inspect behavior', red: 'Human attention', gray: 'Insufficient evidence', context: 'Unchanged context' }
const svg = document.getElementById('graph')
const namespace = 'http://www.w3.org/2000/svg'
const byId = new Map(graph.nodes.map(node => [node.id, node]))
const reviewMethods = isInvoice ? graph.nodes.flatMap(module => analysis.nodes
  .filter(node => node.kind === 'method' && node.file === module.file && !['unchanged', 'context'].includes(node.change))
  .map(node => ({ ...node, moduleId: module.id, before: node.before ?? { code: '', line: 0 }, methods: [{ id: node.id, label: node.label, color: node.color }] }))) : []
for (const method of reviewMethods) byId.set(method.id, method)
let reviewSession = null
let overallReview = null
let selected = null
let camera = null
const concernKey = ['earned:green-concerns', analysis.github?.repository ?? 'standalone', analysis.github?.number ?? '', analysis.reviewKey ?? `${analysis.baseHash}:${analysis.headHash}`].join(':')
const accessReview = createAccessReview({ storageKey: `${concernKey}:access-review:1`, revision: analysis.github ?? { base: analysis.baseHash, head: analysis.headHash }, ...(isInvoice ? { scenario: invoiceRetry, source: reviewMethods.find(node => node.label === invoiceRetry.title)?.after, inspectSource } : {}) })
let invoiceReview = null
let concerns = new Map()
const concernDrafts = new Map()
let concernStorageAvailable = true
try {
  const stored = JSON.parse(localStorage.getItem(concernKey) ?? '{}')
  if (stored && typeof stored === 'object' && !Array.isArray(stored)) concerns = new Map(Object.entries(stored).filter(([id, value]) => byId.has(id) && typeof value === 'string' && value.length <= 2000))
} catch { concernStorageAvailable = false }

function isGreenCard(node) {
  return node?.color === 'green' && node.rule === 'whitespace' && ['tokensEquivalent', 'signaturesEquivalent', 'semanticCallsEquivalent', 'compilationComplete'].every(fact => node.facts?.[fact] === true)
}

const approvedPricingReview = {
  id: 'M:HarborOrders.Pricing.Total(HarborOrders.Order)',
  snapshots: [
    ['8ffac34dd4842647fa09ad6e5ebe1a42bd97eeff91c3220e13e4fd1aa12d60fa', 'b4c18dab95f562c42ad0921d0a0de6193aaa33ce466a293c35b81f59e6671ef8'],
    ['047831c68512e569fb8c7dab788bf5ab018250ae2ac61cb431664f0004c8ee16', 'e8fbbcbbf8d7223c9a83c99fc8b22d23e0e4e5351092be9bb08ef5b7393fe49c'],
  ],
  requirement: '# ORD-17: Bulk order pricing\n\nOrders of five or more units receive a ten percent discount on the item subtotal.\nShipping is not discounted. Order submission must still require both an active\nuser and a matching tenant. Receipt formatting is unchanged. Shipping-provider\nintegration is not part of this requirement.\n\nThis is a synthetic evaluation fixture, not a production incident or a benchmark.',
  change: 'Orders of five or more items now receive a 10% discount on the item subtotal. Shipping is not discounted.',
  whyTitle: 'Why inspect',
  reason: 'This changes the amount charged. Check that the discount threshold and calculation match ORD-17.',
}

function isApprovedSnapshot() {
  return analysis.requirement?.trim() === approvedPricingReview.requirement &&
    approvedPricingReview.snapshots.some(([base, head]) => analysis.baseHash === base && analysis.headHash === head)
}

function isShippingReview(node) {
  return node?.id === shippingScenario.methodId && node.color === 'gray' && node.rule === 'unknown' &&
    node.after?.unresolvedCalls?.includes('carrier.PriceFor') && isApprovedSnapshot()
}

function isAccessReview(node) {
  if (isInvoice) return (node?.moduleId ?? node?.id) === 'module:RetryingInvoiceWriter.cs'
  return node?.id === accessScenario.methodId && node.color === 'red' && node.rule === 'boundary' && isApprovedSnapshot()
}

function getCardCopy(node) {
  if (isInvoice) return node ? invoiceCard(node) : null
  if (isGreenCard(node)) return {
    change: (node.after.code.split('\n').length > node.before.code.split('\n').length) ? 'The method was reformatted across more lines.' : 'Only whitespace formatting changed in this method.',
    whyTitle: 'Why light review',
    reason: 'Only whitespace changed; executable tokens, the method signature, and resolved calls are unchanged.',
  }
  if (node?.color === 'amber' && node.rule === 'behavior' && node.id === approvedPricingReview.id && isApprovedSnapshot()) return approvedPricingReview
  if (isShippingReview(node)) return shippingScenario
  if (isAccessReview(node)) return accessScenario
  return null
}

const shippingStorageKey = `${concernKey}:shipping-response:${shippingScenario.version}`
let shippingResponse = null
let shippingStorageAvailable = true
let shippingBusy = false
let shippingPhase = ''
let shippingTimers = []
let shippingRun = 0

function validShippingAnswer(answer) {
  return answer && Object.hasOwn(shippingScenario.answers, answer.choice) &&
    typeof answer.reference === 'string' && answer.reference.length <= 2000 &&
    typeof answer.guarantee === 'string' && answer.guarantee.length <= 1000 &&
    (answer.choice === 'unknown' || answer.reference.trim().length > 0) &&
    (answer.choice !== 'contract' || answer.guarantee.trim().length > 0)
}

try {
  const stored = JSON.parse(localStorage.getItem(shippingStorageKey) ?? 'null')
  if (stored?.mode === shippingScenario.mode && stored.version === shippingScenario.version && validShippingAnswer(stored)) shippingResponse = stored
} catch { shippingStorageAvailable = false }
let shippingDraft = shippingResponse ? { ...shippingResponse } : { choice: '', reference: '', guarantee: '' }
let shippingEditing = !shippingResponse

function updateShippingNodes() {
  if (!isShippingReview(byId.get(shippingScenario.methodId))) return
  const result = shippingResponse ? shippingScenario.answers[shippingResponse.choice] : null
  const color = result?.demoColor ?? 'gray'
  for (const node of document.querySelectorAll('.graph-node')) {
    if (![shippingScenario.methodId, shippingScenario.dependencyId].includes(node.dataset.id)) continue
    node.classList.remove(...Object.keys(labels))
    node.classList.add(color)
    node.dataset.color = color
    node.querySelector('.node-status').textContent = shippingBusy ? 'Recomputing (demo)' : result ? `${result.graphLabel} (demo)` : labels.gray
    node.classList.toggle('recomputing', shippingBusy)
    node.setAttribute('aria-label', `${byId.get(node.dataset.id).label}: ${labels[color]}${result ? ' (demo)' : ''}`)
    node.setAttribute('aria-description', shippingBusy ? 'Scripted demo recompute in progress.' : result ? `${result.title} Demo color only; PA still reports insufficient evidence.` : 'Provider behavior is unverified.')
  }
  if (selected === shippingScenario.methodId) {
    const status = document.getElementById('detail-status')
    status.className = `status ${color}`
    status.textContent = `${labels[color]}${result ? ' (demo)' : ''}`
  }
}

function renderShippingReview() {
  document.getElementById('shipping-form').hidden = shippingBusy || !shippingEditing
  document.getElementById('shipping-progress').hidden = !shippingBusy
  document.getElementById('shipping-result').hidden = shippingBusy || shippingEditing || !shippingResponse
  document.getElementById('shipping-phase').textContent = shippingPhase
  document.getElementById('shipping-continue').disabled = shippingBusy
  document.getElementById('shipping-form').setAttribute('aria-busy', String(shippingBusy))
  for (const input of document.querySelectorAll('input[name="shipping-evidence"]')) input.checked = input.value === shippingDraft.choice
  const needsReference = ['implementation', 'contract'].includes(shippingDraft.choice)
  const needsGuarantee = shippingDraft.choice === 'contract'
  document.getElementById('shipping-reference-field').hidden = !needsReference
  document.getElementById('shipping-guarantee-field').hidden = !needsGuarantee
  document.getElementById('shipping-reference-label').textContent = needsGuarantee ? 'Contract reference' : 'Implementation reference'
  for (const [id, needed, value] of [['shipping-reference', needsReference, shippingDraft.reference], ['shipping-guarantee', needsGuarantee, shippingDraft.guarantee]]) {
    const input = document.getElementById(id)
    input.disabled = !needed
    input.required = needed
    input.value = value
    input.setCustomValidity('')
  }
  if (shippingResponse) {
    const result = shippingScenario.answers[shippingResponse.choice]
    document.getElementById('shipping-result-title').textContent = result.title
    document.getElementById('shipping-result-detail').textContent = result.detail
    document.getElementById('shipping-result-reference').textContent = shippingResponse.reference
    document.getElementById('shipping-result-reference').hidden = !shippingResponse.reference
    document.getElementById('shipping-result-guarantee').textContent = shippingResponse.guarantee ? `Claim: ${shippingResponse.guarantee}` : ''
    document.getElementById('shipping-result-guarantee').hidden = !shippingResponse.guarantee
    document.getElementById('shipping-storage').textContent = (shippingStorageAvailable ? 'Saved locally. ' : 'Kept in this tab only; browser storage is unavailable. ') + 'Demo color only. PA still reports insufficient evidence; no live verification.'
  }
  updateShippingNodes()
}

function submitShippingResponse(event) {
  event.preventDefault()
  if (shippingBusy || !isShippingReview(byId.get(selected))) return
  const answer = {
    choice: shippingDraft.choice,
    reference: shippingDraft.choice === 'unknown' ? '' : shippingDraft.reference.trim(),
    guarantee: shippingDraft.choice === 'contract' ? shippingDraft.guarantee.trim() : '',
  }
  if (!validShippingAnswer(answer)) {
    const input = document.getElementById(!answer.reference ? 'shipping-reference' : 'shipping-guarantee')
    if (!input.disabled) {
      input.setCustomValidity('Add the evidence details before saving.')
      input.reportValidity()
    }
    return
  }
  const run = ++shippingRun
  shippingBusy = true
  shippingPhase = 'Applying response...'
  renderShippingReview()
  shippingTimers = [
    setTimeout(() => {
      if (run !== shippingRun) return
      shippingPhase = 'Recomputing review...'
      renderShippingReview()
    }, 700),
    setTimeout(() => {
      if (run !== shippingRun) return
      shippingResponse = { ...answer, mode: shippingScenario.mode, version: shippingScenario.version, recomputedAt: new Date().toISOString() }
      shippingDraft = { ...answer }
      shippingBusy = false
      shippingEditing = false
      shippingTimers = []
      try {
        localStorage.setItem(shippingStorageKey, JSON.stringify(shippingResponse))
        shippingStorageAvailable = true
      } catch { shippingStorageAvailable = false }
      renderShippingReview()
      if (selected === shippingScenario.methodId && !document.getElementById('diff-dialog').open) document.getElementById('shipping-result').focus({ preventScroll: true })
    }, shippingScenario.recomputeMs),
  ]
}

function renderConcern() {
  const value = concerns.get(selected) ?? ''
  document.getElementById('saved-concern').hidden = !value
  document.getElementById('concern-value').textContent = value
  document.getElementById('concern-status').textContent = concernStorageAvailable ? 'Saved locally; not posted to GitHub.' : 'Kept in this tab only; browser storage is unavailable.'
  document.getElementById('concern-action-label').textContent = value ? 'Edit concern' : 'Add concern'
  document.getElementById('green-concern-text').value = concernDrafts.get(selected) ?? value
  document.getElementById('green-concern-text').setCustomValidity('')
  document.getElementById('green-concern-form').hidden = true
  document.getElementById('green-add-concern').setAttribute('aria-expanded', 'false')
}

function persistConcerns() {
  try {
    localStorage.setItem(concernKey, JSON.stringify(Object.fromEntries(concerns)))
    concernStorageAvailable = true
  } catch { concernStorageAvailable = false }
}

function inspectSource() {
  const node = byId.get(selected)
  if (!getCardCopy(node)) return
  const rows = document.createDocumentFragment()
  const sourceStart = snapshot => snapshot.code ? snapshot.line - snapshot.code.split('\n').findIndex(line => line.trim().length > 0) : 0
  const oldStart = sourceStart(node.before)
  const newStart = sourceStart(node.after)
  let oldLine = oldStart
  let newLine = newStart
  let additions = 0
  let deletions = 0
  for (const part of diffLines(node.before.code, node.after.code)) {
    const lines = part.value.split('\n')
    if (lines.at(-1) === '') lines.pop()
    for (const line of lines) {
      const row = document.createElement('tr')
      row.className = part.added ? 'diff-added' : part.removed ? 'diff-removed' : 'diff-context'
      const cells = [
        ['diff-old-line', part.added ? '' : String(oldLine++)],
        ['diff-new-line', part.removed ? '' : String(newLine++)],
        ['diff-marker', part.added ? '+' : part.removed ? '-' : ' '],
        ['diff-code', line],
      ]
      for (const [className, text] of cells) {
        const cell = document.createElement('td')
        cell.className = className
        cell.textContent = text
        row.append(cell)
      }
      if (part.added) additions += 1
      if (part.removed) deletions += 1
      rows.append(row)
    }
  }
  document.getElementById('diff-lines').replaceChildren(rows)
  document.getElementById('diff-file').textContent = node.file
  document.getElementById('diff-method').textContent = node.label
  document.getElementById('diff-additions').textContent = `+${additions}`
  document.getElementById('diff-deletions').textContent = `-${deletions}`
  document.getElementById('diff-hunk').textContent = `@@ -${oldStart},${oldLine - oldStart} +${newStart},${newLine - newStart} @@`
  document.getElementById('diff-dialog').showModal()
  document.getElementById('diff-scroll').scrollTop = 0
  document.getElementById('diff-scroll').scrollLeft = 0
}

function fitGraph() {
  camera?.resize()
  camera?.fit()
  camera?.center()
  camera?.zoomBy(window.innerWidth < 650 ? 1 : 0.92)
}

function enableReviewResize() {
  const workspace = document.getElementById('workspace')
  const divider = document.getElementById('review-resizer')
  const stage = document.querySelector('.graph-stage')
  const storageKey = 'earned:review-layout:1'
  let share = 1 / 3
  let drag = null
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) ?? 'null')
    if (typeof saved === 'number' && saved > 0 && saved < 1) share = saved
  } catch {}

  function applyShare() {
    workspace.style.setProperty('--graph-share', `${share}fr`)
    workspace.style.setProperty('--review-share', `${1 - share}fr`)
  }
  function persist() {
    try { localStorage.setItem(storageKey, JSON.stringify(share)) } catch {}
  }
  function setWidth(pixels) {
    const available = workspace.clientWidth - divider.offsetWidth
    share = Math.min(available - 320, Math.max(200, pixels)) / available
    applyShare()
  }
  function finishDrag() {
    if (!drag) return
    const pointerId = drag.pointerId
    drag = null
    document.body.classList.remove('resizing-review')
    if (divider.hasPointerCapture(pointerId)) divider.releasePointerCapture(pointerId)
    persist()
  }
  divider.addEventListener('pointerdown', event => {
    if (event.button !== 0 || !event.isPrimary || !divider.offsetWidth) return
    event.preventDefault()
    divider.focus({ preventScroll: true })
    drag = { pointerId: event.pointerId, startX: event.clientX, width: stage.getBoundingClientRect().width }
    divider.setPointerCapture(event.pointerId)
    document.body.classList.add('resizing-review')
  })
  divider.addEventListener('pointermove', event => {
    if (drag?.pointerId === event.pointerId) setWidth(drag.width + event.clientX - drag.startX)
  })
  for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) divider.addEventListener(event, finishDrag)
  divider.addEventListener('dblclick', () => { share = 1 / 3; applyShare(); persist() })
  divider.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Enter'].includes(event.key) || !divider.offsetWidth) return
    event.preventDefault()
    const step = event.shiftKey ? 96 : 32
    if (event.key === 'Enter') { share = 1 / 3; applyShare() }
    else setWidth(event.key === 'Home' ? 200 : event.key === 'End' ? workspace.clientWidth : stage.getBoundingClientRect().width + (event.key === 'ArrowLeft' ? -step : step))
    persist()
  })
  applyShare()
  new ResizeObserver(() => {
    fitGraph()
    if (!divider.offsetWidth) { finishDrag(); return }
    const available = workspace.clientWidth - divider.offsetWidth
    const value = Math.round(stage.getBoundingClientRect().width / available * 100)
    divider.setAttribute('aria-valuemin', String(Math.round(200 / available * 100)))
    divider.setAttribute('aria-valuemax', String(Math.round((available - 320) / available * 100)))
    divider.setAttribute('aria-valuenow', String(value))
    divider.setAttribute('aria-valuetext', `Graph ${value}%, review card ${100 - value}%`)
  }).observe(stage)
}

function element(name, attributes = {}, text) {
  const node = document.createElementNS(namespace, name)
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value)
  if (text !== undefined) node.textContent = text
  return node
}

function inspect(node) {
  if (reviewSession?.active && node.kind === 'module') node = reviewSession.inModule(node.id) ?? node
  if (node.id === shippingScenario.dependencyId && isShippingReview(byId.get(shippingScenario.methodId))) node = byId.get(shippingScenario.methodId)
  selected = node.id
  document.querySelectorAll('.graph-node').forEach(item => item.classList.toggle('selected', item.dataset.id === (node.moduleId ?? selected)))
  document.getElementById('workspace').classList.add('has-detail')
  document.getElementById('detail').hidden = false
  document.getElementById('detail-kind').textContent = node.file ?? 'Unresolved dependency'
  document.getElementById('detail-title').textContent = node.label
  const status = document.getElementById('detail-status')
  status.textContent = labels[node.color]
  status.className = 'status ' + node.color
  const copy = getCardCopy(node)
  const shipping = isShippingReview(node)
  document.getElementById('access-understand').hidden = !isAccessReview(node)
  document.getElementById('green-continue').hidden = isAccessReview(node)
  document.getElementById('green-change').hidden = !copy
  for (const id of ['green-actions', 'green-concern']) document.getElementById(id).hidden = !copy || shipping
  document.getElementById('gray-review').hidden = !shipping
  for (const id of ['standard-rule', 'detail-facts']) document.getElementById(id).hidden = Boolean(copy)
  document.getElementById('green-change-text').textContent = copy?.change ?? ''
  document.getElementById('card-why-title').textContent = copy?.whyTitle ?? ''
  document.getElementById('detail-reason').textContent = copy?.reason ?? node.reason
  document.getElementById('source-change').open = false
  document.getElementById('source-change').hidden = Boolean(copy)
  document.getElementById('detail').scrollTop = 0
  renderConcern()
  renderShippingReview()
  invoiceReview?.render(node)
  document.getElementById('detail-rule').textContent = node.rule
  const facts = [
    ['Change', node.change],
    ['Tokens equivalent', node.facts ? String(node.facts.tokensEquivalent) : 'Not established'],
    ['CFG blocks', `${node.before?.cfg?.length ?? '-'} → ${node.after?.cfg?.length ?? '-'}`],
    ['Conditional blocks', `${node.before?.conditions?.length ?? '-'} → ${node.after?.conditions?.length ?? '-'}`],
    ['Call resolution', node.after?.unresolvedCalls?.length ? 'Incomplete' : node.kind === 'external' ? 'Unresolved' : 'Resolved within scope'],
  ]
  const list = document.getElementById('detail-facts')
  list.replaceChildren()
  for (const [title, value] of facts) {
    const row = document.createElement('div')
    const term = document.createElement('dt')
    const description = document.createElement('dd')
    term.textContent = title
    description.textContent = value
    row.append(term, description)
    list.append(row)
  }
  document.getElementById('before-code').textContent = node.before?.code?.trim() ?? 'Not present'
  document.getElementById('after-code').textContent = node.after?.code?.trim() ?? 'Not present'
  document.getElementById('scope').textContent = isInvoice ? (node.requirements ?? []).map(id => analysis.requirements.items.find(item => item.id === id)?.text ?? id).join(' ') : analysis.contract + '. ' + analysis.policy.green_contract
  document.getElementById('model-signal').textContent = isInvoice ? 'Requirements, program-analysis findings, and verification results inform the assessment.' : node.model ? `Model: ${node.model.choice}. Provider confidence ${node.model.confidence}; not a safety probability.` : 'No model signal used for this block.'
  if (isInvoice) {
    list.replaceChildren()
    for (const [name, value] of [['Compliance confidence', node.model?.assessment === 'unknown' ? 'Needs context' : `${Math.round((node.model?.confidence ?? 0) * 100)}%`]]) {
      const row = document.createElement('div')
      const term = document.createElement('dt')
      const description = document.createElement('dd')
      term.textContent = name
      description.textContent = value
      row.append(term, description)
      list.append(row)
    }
    list.hidden = true
    document.getElementById('detail-confidence').hidden = false
    invoiceReview?.refresh()
  }
  fitGraph()
  reviewSession?.select(node)
}

function draw() {
  const direction = window.innerWidth < 650 ? 'TB' : 'LR'
  const layout = new dagre.graphlib.Graph().setGraph({ rankdir: direction, nodesep: 37, ranksep: 70, marginx: 40, marginy: 40 }).setDefaultEdgeLabel(() => ({}))
  for (const node of graph.nodes) layout.setNode(node.id, { width: 220, height: 86 })
  for (const edge of graph.edges) if (byId.has(edge.source) && byId.has(edge.target)) layout.setEdge(edge.source, edge.target)
  if (direction === 'TB' && dagre.graphlib.alg.isAcyclic(layout)) {
    const order = dagre.graphlib.alg.topsort(layout)
    for (let index = 1; index < order.length; index += 1) {
      if (!layout.hasEdge(order[index - 1], order[index])) layout.setEdge(order[index - 1], order[index], { layoutOnly: true })
    }
  }
  dagre.layout(layout)
  const stage = document.querySelector('.graph-stage')
  stage.style.height = direction === 'TB' ? `${Math.ceil(layout.graph().height * (stage.clientWidth - 20) / layout.graph().width) + 30}px` : ''
  if (camera) { camera.destroy(); camera = null }
  svg.replaceChildren()
  const defs = element('defs')
  const marker = element('marker', { id: 'arrow', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto' })
  marker.append(element('path', { d: 'M0 0L10 5L0 10z', class: 'edge-arrow' }))
  defs.append(marker)
  svg.append(defs)
  const viewport = element('g', { class: 'svg-pan-zoom_viewport' })
  for (const edge of graph.edges) {
    const route = layout.edge(edge.source, edge.target)
    if (!route) continue
    const path = route.points.map((point, index) => `${index ? 'L' : 'M'}${point.x},${point.y}`).join(' ')
    viewport.append(element('path', { d: path, class: 'edge ' + edge.change, 'marker-end': 'url(#arrow)', 'data-source': edge.source, 'data-target': edge.target }))
  }
  for (const node of graph.nodes) {
    const position = layout.node(node.id)
    const group = element('g', { transform: `translate(${position.x - 110},${position.y - 43})`, class: `graph-node ${node.color}${(byId.get(selected)?.moduleId ?? selected) === node.id ? ' selected' : ''}`, role: 'button', tabindex: '0', 'aria-label': `${node.label}: ${labels[node.color]}`, 'data-id': node.id, 'data-color': node.color })
    group.append(element('rect', { width: 220, height: 86, rx: 6, class: 'node-rect' }))
    group.append(element('text', { x: 16, y: 21, class: 'node-kind' }, isInvoice ? node.model?.assessment === 'unknown' ? 'CONTEXT NEEDED' : `${Math.round((node.model?.confidence ?? 0) * 100)}% CONFIDENCE` : node.kind === 'external' ? 'UNRESOLVED TARGET' : node.change.toUpperCase()))
    group.append(element('text', { x: 16, y: 44, class: 'node-title' }, node.label.length > 27 ? node.label.slice(0, 25) + '…' : node.label))
    group.append(element('text', { x: 16, y: 66, class: 'node-status' }, labels[node.color]))
    group.append(element('title', {}, node.label + '\n' + node.reason))
    group.addEventListener('click', () => inspect(node))
    group.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); inspect(node) } })
    viewport.append(group)
  }
  svg.append(viewport)
  camera = svgPanZoom(svg, { viewportSelector: '.svg-pan-zoom_viewport', fit: true, center: true, zoomEnabled: true, panEnabled: true, controlIconsEnabled: false, minZoom: 0.35, maxZoom: 3, dblClickZoomEnabled: false, preventMouseEventsDefault: false })
  fitGraph()
  updateShippingNodes()
  invoiceReview?.refresh()
}

const changed = graph.nodes.filter(node => !['unchanged', 'context'].includes(node.change))
document.getElementById('change-count').textContent = isInvoice ? `${analysis.diff.added.toLocaleString()} added lines / ${analysis.diff.files} files / ${analysis.nodes.filter(node => node.kind === 'method' && !['unchanged', 'context'].includes(node.change)).length} changed methods` : `${changed.length} changed blocks / ${analysis.changedFiles.length} files`
document.getElementById('revision').textContent = `${analysis.baseHash.slice(0, 8)} → ${analysis.headHash.slice(0, 8)}`
const pullRequest = JSON.parse(document.getElementById('pr-metadata').textContent)
if (pullRequest) {
  const [owner, repository] = pullRequest.repository.split('/')
  const repositoryUrl = `https://github.com/${encodeURIComponent(owner)}/${encodeURIComponent(repository)}`
  const pullUrl = `${repositoryUrl}/pull/${pullRequest.number}`
  const setLink = (id, text, url) => {
    const link = document.getElementById(id)
    link.textContent = text
    if (url) link.href = url
  }
  document.body.classList.add('has-pr')
  document.getElementById('fallback-brand').hidden = true
  document.getElementById('fixture-label').hidden = true
  for (const id of ['repo-breadcrumb', 'pr-number', 'pr-meta', 'pr-nav']) document.getElementById(id).hidden = false
  setLink('repo-owner', owner, `https://github.com/${encodeURIComponent(owner)}`)
  setLink('repo-name', repository, repositoryUrl)
  document.getElementById('pr-title').textContent = pullRequest.title
  document.getElementById('pr-number').textContent = `#${pullRequest.number}`
  document.title = `${pullRequest.title} #${pullRequest.number} | ${pullRequest.repository}`
  const states = { open: 'Open', draft: 'Draft', closed: 'Closed', merged: 'Merged' }
  document.getElementById('pr-state').classList.add(pullRequest.state)
  document.getElementById('pr-state').title = 'PR status when this playground was built'
  document.getElementById('pr-state-label').textContent = states[pullRequest.state]
  setLink('pr-author', pullRequest.author, `https://github.com/${encodeURIComponent(pullRequest.author)}`)
  document.getElementById('pr-action').textContent = pullRequest.state === 'merged' ? 'merged' : pullRequest.state === 'closed' ? 'proposed merging' : 'wants to merge'
  setLink('pr-commit-summary', `${pullRequest.commits} ${pullRequest.commits === 1 ? 'commit' : 'commits'}`, `${pullUrl}/commits`)
  const branchUrl = (repositoryName, branch) => repositoryName ? `https://github.com/${repositoryName.split('/').map(encodeURIComponent).join('/')}/tree/${encodeURIComponent(branch)}` : null
  setLink('pr-base', pullRequest.baseBranch, branchUrl(pullRequest.baseRepository, pullRequest.baseBranch))
  setLink('pr-head', pullRequest.headBranch, branchUrl(pullRequest.headRepository, pullRequest.headBranch))
  for (const [id, path] of [['pr-conversation-link', ''], ['pr-commits-link', '/commits'], ['pr-checks-link', '/checks'], ['pr-files-link', '/files']]) document.getElementById(id).href = pullUrl + path
  document.getElementById('pr-commits-count').textContent = pullRequest.commits
  document.getElementById('pr-files-count').textContent = pullRequest.changedFiles
  document.getElementById('revision').textContent = `${pullRequest.base.slice(0, 8)} → ${pullRequest.head.slice(0, 8)}`
  document.getElementById('revision').title = 'Analyzed base and head commits'
  document.getElementById('pr-nav').after(document.getElementById('review-context'))
}
document.getElementById('run-mode').textContent = isInvoice ? 'Review session' : analysis.mode === 'hybrid' ? 'PA + model / prototype' : 'PA + policy / model not run'
document.getElementById('method-mode').textContent = `${analysis.tool.name} ${analysis.tool.version}. Model status: ${analysis.modelRun.status}.`
document.getElementById('green-contract').textContent = isInvoice ? 'Module checks support bounded claims, not exhaustive coverage. Reviewer inputs and scenario outcomes are recorded separately from the original analysis.' : 'Green contract: ' + analysis.policy.green_contract + '.'
if (isInvoice) {
  if (!pullRequest) document.getElementById('pr-title').textContent = analysis.requirements.title
  document.getElementById('amber-legend-label').textContent = labels.amber
  document.getElementById('amber-legend-label').title = 'Unverified assumptions need reviewer input before they can be treated as facts.'
  document.getElementById('fixture-label').textContent = analysis.requirements.id
  document.getElementById('methodology').lastChild.textContent = ' Review details'
  document.getElementById('method-title').textContent = 'Review details'
  document.getElementById('method-dialog').querySelector('ol').hidden = true
  document.getElementById('method-mode').textContent = `${analysis.tool.name} ${analysis.tool.version}. ${analysis.verification.passed} executed checks passed; ${analysis.verification.failed} retry-integrity check failed.`
  document.getElementById('method-dialog').querySelector('.method-warning').remove()
  document.querySelector('footer > span').textContent = analysis.requirements.id
  document.getElementById('scope').parentElement.querySelector('summary').textContent = 'Evidence & requirements'
  document.getElementById('scope').parentElement.hidden = true
}
document.getElementById('zoom-in').addEventListener('click', () => camera.zoomIn())
document.getElementById('zoom-out').addEventListener('click', () => camera.zoomOut())
document.getElementById('fit').addEventListener('click', fitGraph)
function continueReview() {
  if (reviewSession?.active) { reviewSession.next(); return }
  if (!getCardCopy(byId.get(selected))) return
  const index = changed.findIndex(node => node.id === selected)
  const next = changed[(index + 1) % changed.length]
  if (next && next.id !== selected) {
    inspect(next)
    document.getElementById('detail-title').focus({ preventScroll: true })
  } else document.getElementById('close-detail').click()
}
document.getElementById('green-continue').addEventListener('click', continueReview)
document.getElementById('shipping-continue').addEventListener('click', continueReview)
document.getElementById('shipping-inspect').addEventListener('click', inspectSource)
document.getElementById('shipping-question').textContent = shippingScenario.question
document.getElementById('shipping-scope').textContent = shippingScenario.scopeNote
for (const [choice, answer] of Object.entries(shippingScenario.answers)) {
  const label = document.createElement('label')
  const radio = document.createElement('input')
  radio.type = 'radio'
  radio.name = 'shipping-evidence'
  radio.value = choice
  radio.required = true
  const text = document.createElement('span')
  text.textContent = answer.label
  label.append(radio, text)
  document.getElementById('shipping-options').append(label)
}
document.getElementById('shipping-options').addEventListener('change', event => {
  shippingDraft.choice = event.target.value
  renderShippingReview()
})
for (const [id, field] of [['shipping-reference', 'reference'], ['shipping-guarantee', 'guarantee']]) {
  document.getElementById(id).addEventListener('input', event => {
    shippingDraft[field] = event.target.value
    event.target.setCustomValidity('')
  })
}
document.getElementById('shipping-form').addEventListener('submit', submitShippingResponse)
document.getElementById('shipping-cancel').addEventListener('click', () => {
  shippingRun += 1
  shippingTimers.forEach(clearTimeout)
  shippingTimers = []
  shippingBusy = false
  shippingEditing = true
  renderShippingReview()
  document.getElementById('shipping-save').focus()
})
document.getElementById('shipping-edit').addEventListener('click', () => {
  shippingDraft = { ...shippingResponse }
  shippingEditing = true
  renderShippingReview()
  document.querySelector('input[name="shipping-evidence"]:checked')?.focus()
})
document.getElementById('green-inspect').addEventListener('click', inspectSource)
document.getElementById('access-understand').addEventListener('click', () => {
  if (isAccessReview(byId.get(selected))) accessReview.open()
})
document.getElementById('close-diff').addEventListener('click', () => document.getElementById('diff-dialog').close())
document.getElementById('green-add-concern').addEventListener('click', () => {
  document.getElementById('green-concern-form').hidden = false
  document.getElementById('green-add-concern').setAttribute('aria-expanded', 'true')
  document.getElementById('green-concern-text').focus()
})
document.getElementById('green-concern-text').addEventListener('input', event => {
  event.target.setCustomValidity('')
  concernDrafts.set(selected, event.target.value)
})
document.getElementById('green-concern-form').addEventListener('submit', event => {
  event.preventDefault()
  if (!getCardCopy(byId.get(selected))) return
  const input = document.getElementById('green-concern-text')
  const value = input.value.trim()
  if (!value) {
    input.setCustomValidity('Enter a concern before saving.')
    input.reportValidity()
    return
  }
  concerns.set(selected, value)
  concernDrafts.delete(selected)
  persistConcerns()
  renderConcern()
  document.getElementById('green-add-concern').focus()
})
document.getElementById('cancel-concern').addEventListener('click', () => {
  concernDrafts.delete(selected)
  renderConcern()
  document.getElementById('green-add-concern').focus()
})
document.getElementById('remove-concern').addEventListener('click', () => {
  concerns.delete(selected)
  concernDrafts.delete(selected)
  persistConcerns()
  renderConcern()
  document.getElementById('green-add-concern').focus()
})
document.getElementById('close-detail').addEventListener('click', () => {
  if (reviewSession?.active) reviewSession.pause()
  document.getElementById('detail').hidden = true
  document.getElementById('workspace').classList.remove('has-detail')
  selected = null
  document.querySelectorAll('.graph-node').forEach(node => node.classList.remove('selected'))
  fitGraph()
})
const dialog = document.getElementById('method-dialog')
document.getElementById('methodology').addEventListener('click', () => dialog.showModal())
document.getElementById('close-method').addEventListener('click', () => dialog.close())
document.getElementById('export').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' }))
  const anchor = document.createElement('a')
  anchor.href = url; anchor.download = 'order-flow-analysis.json'
  document.body.append(anchor); anchor.click(); anchor.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
})
if (isInvoice) {
  invoiceReview = createInvoiceReview({ analysis, graph, currentId: () => selected, inspectSource, openCard: inspect, next: continueReview, storageKey: `${concernKey}:invoice-answers:1`, onChange: () => overallReview?.refresh() })
  reviewSession = createReviewSession({ methods: reviewMethods, openMethod: inspect, closeDetail: () => document.getElementById('close-detail').click(), storageKey: `${concernKey}:guided-session:1`, onFinish: () => overallReview.open() })
  overallReview = createOverallReview({
    analysis, invoiceReview, getProgress: () => reviewSession.progress,
    getConcerns: () => [...concerns].sort(([left], [right]) => left.localeCompare(right)).map(([id, note]) => ({ id, label: byId.get(id).label, note })),
    openCard: id => { reviewSession.pause(); inspect(byId.get(id)); document.getElementById('detail').scrollIntoView({ block: 'start' }) },
  })
}
let width = window.innerWidth
window.addEventListener('resize', () => { if (width !== window.innerWidth) draw(); else fitGraph(); width = window.innerWidth })
draw()
if (isInvoice) enableReviewResize()