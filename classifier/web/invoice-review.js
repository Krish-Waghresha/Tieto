import experience from '../fixtures/invoice-import/experience.json'

export const invoiceRetry = experience.retry

export function invoiceGraph(analysis) {
  const priority = { context: -1, green: 0, amber: 1, gray: 2, red: 3 }
  const sourceNodes = new Map(analysis.nodes.map(node => [node.id, node]))
  const nodes = analysis.changedFiles.map(file => {
    const members = analysis.nodes.filter(node => node.file === file && !['unchanged', 'context'].includes(node.change))
    const strongest = members.reduce((current, node) => priority[node.color] > priority[current.color] ? node : current)
    const fileNode = members.find(node => node.kind === 'file')
    const methods = members.filter(node => node.kind === 'method')
    return {
      ...strongest, id: `module:${file}`, kind: 'module', label: file.replace(/\.cs$/, ''), file,
      before: fileNode?.before ?? { code: '', line: 0 },
      after: fileNode?.after ?? strongest.after,
      methods: methods.map(node => ({ id: node.id, label: node.label, color: node.color })),
      evidence: [...new Map(members.flatMap(node => node.evidence ?? []).map(item => [item.id, item])).values()],
    }
  })
  const files = new Set(nodes.map(node => node.file))
  const pairs = new Map()
  for (const edge of analysis.edges) {
    const source = sourceNodes.get(edge.source)?.file
    const target = sourceNodes.get(edge.target)?.file
    if (source && target && source !== target && files.has(source) && files.has(target)) {
      pairs.set(`${source}:${target}`, { source: `module:${source}`, target: `module:${target}`, change: 'unchanged' })
    }
  }
  return { nodes, edges: [...pairs.values()] }
}

export function invoiceCard(node) {
  if (node.kind !== 'module') return null
  const headings = { green: 'Why light review', amber: 'Why inspect', red: 'Why human attention', gray: 'What needs context' }
  const passed = (node.evidence ?? []).filter(item => item.status === 'passed').length
  return {
    change: node.changeSummary,
    whyTitle: headings[node.color],
    reason: node.color === 'green' ? `${passed} requirement checks support this change. The analyzed flow and dependencies support lighter review.` : node.reason,
  }
}

export function createInvoiceReview({ graph, currentId, inspectSource, next, storageKey }) {
  const section = document.getElementById('invoice-question')
  const form = document.getElementById('invoice-answer-form')
  const reference = document.getElementById('invoice-reference')
  const records = new Map()
  const drafts = new Map()
  const byId = new Map(graph.nodes.map(node => [node.id, node]))
  let busy = null
  let timers = []
  let selectedNode = null
  const editing = new Set()
  let phase = ''
  let storageAvailable = true
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey) ?? '{}')
    for (const [id, value] of Object.entries(stored ?? {})) {
      const spec = experience.questions[byId.get(id)?.file]
      if (spec && Object.hasOwn(spec.answers, value?.choice) && typeof value.reference === 'string' && value.reference.length <= 2000) records.set(id, value)
    }
  } catch { storageAvailable = false }

  function refresh() {
    const labels = { green: 'Light review', amber: 'Inspect behavior', red: 'Human attention', gray: 'Insufficient evidence' }
    for (const element of document.querySelectorAll('.graph-node')) {
      const node = byId.get(element.dataset.id)
      const record = records.get(node.id)
      const result = experience.questions[node.file]?.answers[record?.choice]
      const color = result?.color ?? node.color
      element.classList.remove('green', 'amber', 'red', 'gray')
      element.classList.add(color)
      element.dataset.color = color
      element.classList.toggle('recomputing', busy === node.id)
      element.querySelector('.node-status').textContent = busy === node.id ? 'Recomputing review' : result?.title ?? labels[node.color]
      element.setAttribute('aria-label', `${node.label}: ${labels[color]}`)
      if (result) element.querySelector('.node-kind').textContent = `${Math.round(result.confidence * 100)}% CONFIDENCE`
      if (result && currentId() === node.id) {
        const badge = document.getElementById('detail-status')
        badge.className = `status ${color}`
        badge.textContent = labels[color]
        const confidence = document.querySelector('#detail-facts dd')
        if (confidence) confidence.textContent = `${Math.round(result.confidence * 100)}%`
      }
    }
  }

  function render(node = selectedNode) {
    selectedNode = node
    const spec = experience.questions[node?.file]
    section.hidden = !spec
    refresh()
    if (!spec) return
    const record = records.get(node.id)
    const draft = drafts.get(node.id) ?? record ?? { choice: '', reference: '' }
    const running = busy === node.id
    const edit = editing.has(node.id) || !record
    form.hidden = running || !edit
    document.getElementById('invoice-processing').hidden = !running
    document.getElementById('invoice-processing-text').textContent = phase
    document.getElementById('invoice-answer-result').hidden = running || !record || edit
    document.getElementById('invoice-question-title').textContent = node.question ?? spec.question
    document.getElementById('invoice-next').disabled = running
    const options = document.getElementById('invoice-answer-options')
    options.replaceChildren()
    for (const [choice, answer] of Object.entries(spec.answers)) {
      const label = document.createElement('label')
      const radio = document.createElement('input')
      radio.type = 'radio'; radio.name = 'invoice-choice'; radio.value = choice; radio.required = true; radio.checked = draft.choice === choice
      const text = document.createElement('span')
      text.textContent = answer.label
      label.append(radio, text)
      options.append(label)
    }
    const needsReference = Boolean(spec.answers[draft.choice]?.reference)
    document.getElementById('invoice-reference-field').hidden = !needsReference
    reference.disabled = !needsReference
    reference.required = needsReference
    reference.value = draft.reference
    reference.setCustomValidity('')
    if (record) {
      const result = spec.answers[record.choice]
      document.getElementById('invoice-result-title').textContent = result.title
      document.getElementById('invoice-result-detail').textContent = result.detail
      document.getElementById('invoice-result-reference').textContent = record.reference
      document.getElementById('invoice-result-reference').hidden = !record.reference
      document.getElementById('invoice-save-status').textContent = storageAvailable ? 'Response saved' : 'Response kept in this tab only'
    }
  }

  form.addEventListener('change', event => {
    if (event.target.name !== 'invoice-choice') return
    drafts.set(selectedNode.id, { choice: event.target.value, reference: reference.value })
    render()
  })
  reference.addEventListener('input', () => {
    drafts.set(selectedNode.id, { ...(drafts.get(selectedNode.id) ?? records.get(selectedNode.id)), reference: reference.value })
    reference.setCustomValidity('')
  })
  form.addEventListener('submit', event => {
    event.preventDefault()
    if (busy) return
    const node = selectedNode
    const answer = drafts.get(node.id) ?? records.get(node.id)
    const spec = experience.questions[node.file].answers[answer?.choice]
    if (!spec) return
    if (spec.reference && !reference.value.trim()) {
      reference.setCustomValidity('Add a provider contract reference.')
      reference.reportValidity()
      return
    }
    const result = { choice: answer.choice, reference: spec.reference ? reference.value.trim() : '', origin: 'authored-outcome', updatedAt: new Date().toISOString() }
    busy = node.id; phase = 'Applying your answer...'; render()
    timers = [setTimeout(() => { phase = 'Recomputing review...'; render() }, 700), setTimeout(() => {
      records.set(node.id, result)
      drafts.delete(node.id)
      busy = null; editing.delete(node.id); timers = []
      try { localStorage.setItem(storageKey, JSON.stringify(Object.fromEntries(records))) } catch { storageAvailable = false }
      render()
    }, 2000)]
  })
  document.getElementById('invoice-cancel').addEventListener('click', () => {
    timers.forEach(clearTimeout); timers = []; busy = null; editing.add(selectedNode.id); render()
  })
  document.getElementById('invoice-edit-answer').addEventListener('click', () => { editing.add(selectedNode.id); render() })
  document.getElementById('invoice-inspect').addEventListener('click', inspectSource)
  document.getElementById('invoice-next').addEventListener('click', next)
  return { render(node) { render(node) }, refresh }
}