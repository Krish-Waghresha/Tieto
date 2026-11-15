import experience from '../fixtures/invoice-import/experience.json'

export const invoiceRetry = experience.retry
export const invoiceAttention = { green: 'Light review', amber: 'Hallucination risk', red: 'Human attention', gray: 'Insufficient evidence', context: 'Unchanged context' }

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

export function engineDecision(node, outcome = null) {
  const color = outcome?.color ?? node.color
  const openings = {
    green: `The engine recommends light review for this ${node.kind === 'method' ? 'method' : 'module'}.`,
    amber: node.file === 'TaxGateway.cs' ? 'The engine recommends reviewing the provider integration against its supplied contract.' : node.rule === 'dependency' ? 'The engine recommends targeted review of the dependencies before acceptance.' : 'The engine needs a policy clarification before completing this assessment.',
    red: node.file === 'TaxGateway.cs' ? 'The engine requires human review before this integration can be accepted.' : 'The engine recommends a correction before acceptance.',
    gray: 'The engine cannot complete this assessment without the provider implementation and its contract.',
  }
  const reasoning = outcome?.detail ?? (node.kind === 'method' ? experience.engineReasoning.methods[node.label] : experience.engineReasoning.modules[node.file]) ?? 'The available analysis does not establish the complete behavior of this change.'
  return `${openings[color]} ${reasoning}`
}

export function invoiceCard(node) {
  if (!['module', 'method'].includes(node.kind)) return null
  return {
    change: node.kind === 'method' ? experience.methodChanges[node.label] ?? `This ${node.change} method is reviewed against ${(node.requirements ?? []).join(', ')}.` : experience.moduleChanges[node.file] ?? node.changeSummary,
    whyTitle: 'Engine decision',
    reason: engineDecision(node),
  }
}

export function engineStory(analysis, node, outcome = null) {
  const methods = node.kind === 'method' ? [node] : analysis.nodes.filter(item => item.file === node.file && item.kind === 'method')
  const calls = methods.flatMap(item => item.after?.callSignatures ?? [])
  const conditions = methods.flatMap(item => item.after?.conditions ?? [])
  const unknownCalls = [...new Set(methods.flatMap(item => item.after?.unresolvedCalls ?? []))]
  const color = outcome?.color ?? node.color
  const requirements = (node.requirements ?? []).join(', ')
  let observed = 'PA resolved the types and direct calls in this scope.'
  let interpretation = color === 'green' ? `AI interprets the analyzed paths as consistent with ${requirements}.` : invoiceCard(node).reason
  let unknown = 'The engine cannot establish behavior outside the analyzed paths.'
  if (unknownCalls.length) {
    observed = `PA found a runtime call to ${unknownCalls.join(', ')} whose implementation it could not identify.`
    interpretation = 'The result depends on provider behavior that is not available in the source analysis.'
    unknown = 'The engine cannot establish the provider\'s rate and failure guarantees.'
  } else if (calls.includes('NewGuid:System.Guid') && calls.includes('Save:void')) {
    observed = 'PA found invoice ID creation and a store write in the retry method.'
    interpretation = 'A retry may save a second invoice if the first write committed before the timeout.'
    unknown = 'The engine cannot establish the production store\'s duplicate-prevention or rollback guarantees.'
  } else if (conditions.some(condition => condition.includes('InvoiceStatus.Cancelled'))) {
    observed = 'PA found a cancelled-status check alongside the stored-invoice lookup.'
    interpretation = outcome?.detail ?? 'AI interprets this as blocking re-import even when the earlier invoice was cancelled.'
    unknown = color === 'green' ? 'Your clarification settles the cancellation rule. Concurrent imports remain outside this analysis.' : 'The engine cannot determine the intended rule for cancelled invoices without an owner\'s decision.'
  } else if (conditions.includes('net < 0m') && conditions.includes('parsedTax < 0m')) {
    observed = 'PA found negative-amount checks and calls that parse and round monetary values.'
    interpretation = 'AI interprets these guards as protecting the amount-normalization rules.'
  } else if (node.rule === 'dependency') {
    const methodIds = new Set(methods.map(item => item.id))
    const byId = new Map(analysis.nodes.map(item => [item.id, item]))
    const pending = [...new Set(analysis.edges.filter(edge => methodIds.has(edge.source)).map(edge => byId.get(edge.target)).filter(item => item && !['green', 'context'].includes(item.color)).map(item => item.label))]
    observed = pending.length ? `PA found calls to code that still needs review: ${pending.slice(0, 3).join(', ')}${pending.length > 3 ? ', and other methods' : ''}.` : 'PA found calls to code that still needs review.'
    interpretation = 'AI cannot judge the complete behavior from this method alone.'
    unknown = 'The engine needs more context about those dependencies.'
  } else if (node.question && color !== 'green') {
    unknown = 'The engine still needs the requirement owner to settle the open policy question.'
  }
  if (Object.values(analysis.errors).some(items => items.length)) observed = 'PA could not fully resolve the types in these source snapshots.'
  return { observed, interpretation: outcome?.detail ?? interpretation, unknown }
}

export function greenReviewBasis(analysis, node, outcome = null) {
  const methods = analysis.nodes.filter(item => item.file === node.file && item.kind === 'method' && !['unchanged', 'context'].includes(item.change) && (node.kind !== 'method' || item.id === node.id))
  const methodIds = new Set(methods.map(item => item.id))
  const byId = new Map(analysis.nodes.map(item => [item.id, item]))
  const dependencies = [...new Set(analysis.edges.filter(edge => methodIds.has(edge.source)).map(edge => edge.target))]
    .map(id => byId.get(id)).filter(item => item && (node.kind === 'method' || item.file !== node.file))
  const facts = methods.map(item => item.facts ?? {})
  const snapshots = methods.map(item => item.after).filter(Boolean)
  const blocks = snapshots.flatMap(item => item.cfg ?? [])
  const conditions = snapshots.flatMap(item => item.conditions ?? [])
  const unresolved = snapshots.flatMap(item => item.unresolvedCalls ?? [])
  const callSignatures = new Set(snapshots.flatMap(item => item.callSignatures ?? []))
  const dataFlows = snapshots.filter(item => item.dataFlow?.succeeded)
  const diagnostics = Object.values(analysis.errors).reduce((total, items) => total + items.length, 0)
  const boundaryCount = facts.filter(item => item.protectedBefore || item.protectedAfter).length
  const sensitive = facts.some(item => item.hasDirectives || item.sourceSensitive)
  const requirements = (node.requirements ?? []).join(', ')
  const confidence = Math.round((outcome?.confidence ?? node.model?.confidence ?? 0) * 100)
  const pending = dependencies.filter(item => !['green', 'context'].includes(outcome && item.file === node.file ? outcome.color : item.color))
  const summarize = (values, limit = 6) => {
    const unique = [...new Set(values)]
    return unique.length ? `${unique.slice(0, limit).join(', ')}${unique.length > limit ? `, and ${unique.length - limit} more` : ''}` : 'none'
  }
  const reads = summarize(dataFlows.flatMap(item => item.dataFlow.reads ?? []))
  const writes = summarize(dataFlows.flatMap(item => item.dataFlow.writes ?? []))
  return {
    confidence,
    techniques: [
      ['Inspect source', `Roslyn mapped ${methods.length} changed ${methods.length === 1 ? 'method' : 'methods'} in ${node.file}. ${diagnostics ? `Source-only compilation reported ${diagnostics} errors.` : 'Source-only compilation reported no errors.'}`, `Selected ${summarize(methods.map(item => item.label), 4)} for review against ${requirements}.`],
      ['Trace control flow', `The control-flow extraction returned ${blocks.length} blocks and ${conditions.length} condition entries.`, conditions.length ? `Inspected conditions including ${summarize(conditions, 3)} to locate guards, exits, and repeated operations relevant to the requirement.` : 'Inspected the straight-line body; no condition entries were returned for this scope.'],
      ['Inspect data flow', `Region data-flow analysis succeeded for ${dataFlows.length} of ${snapshots.length} ${snapshots.length === 1 ? 'method' : 'methods'}. Read set: ${reads}. Write set: ${writes}.`, dataFlows.length ? 'Used the read/write sets to identify which inputs and local values need review. These sets alone do not prove value correctness.' : 'Kept data-flow behavior unresolved because no successful region result is available.'],
      ['Resolve calls', `Call resolution returned ${callSignatures.size} distinct resolved signatures and ${unresolved.length} unresolved runtime calls. Resolved operations: ${summarize([...callSignatures].map(signature => `${signature.split(':')[0]}()`))}.`, unresolved.length ? `Could not resolve ${summarize(unresolved)}. Left the external implementation and its contract as required context.` : pending.length ? `Carried forward source-assessment findings from ${summarize(pending.map(item => item.label))}; the caller cannot settle those findings locally.` : `Reviewed ${dependencies.length} ${node.kind === 'method' ? 'source' : 'cross-module'} ${dependencies.length === 1 ? 'callee' : 'callees'} with no outstanding dependency finding in this scope. Resolved symbols do not establish external runtime guarantees.`],
      ['Check review boundaries', `The extraction flagged ${boundaryCount} marked review boundaries. ${sensitive ? 'Directive or caller-source sensitivity flags require attention.' : 'No directive or caller-source sensitivity flags were found.'}`, 'Limited the assessment to the supplied source and requirements. Unavailable production contracts remain outside the conclusion.'],
    ],
    steps: [
      `Compared the inspected behavior with ${requirements} and retained the findings relevant to ${node.label}.`,
      ...(outcome ? ['Included the reviewer\'s policy clarification or provider response in the updated assessment. The source-analysis results are unchanged.'] : []),
      node.model?.assessment === 'unknown' && !outcome ? 'The engine needs more context before it can assign a supported compliance confidence.' : `Recorded ${confidence}% compliance confidence. ${outcome ? 'The recorded response determines the updated attention level.' : node.color === 'green' ? `It meets the ${Math.round(analysis.policy.greenThreshold * 100)}% threshold, with no blocking analysis guard.` : 'The unresolved finding determines the attention level.'}`,
    ],
    conclusion: engineDecision(node, outcome),
  }
}

export function createInvoiceReview({ analysis, graph, currentId, inspectSource, openCard, next, storageKey, onChange = () => {} }) {
  const section = document.getElementById('invoice-question')
  const engineBasis = document.getElementById('green-engine-basis')
  engineBasis.addEventListener('toggle', () => {
    if (!engineBasis.open || engineBasis.hidden) return
    const panel = document.getElementById('detail')
    if (getComputedStyle(panel).overflowY === 'visible') {
      engineBasis.scrollIntoView({ block: 'start' })
      return
    }
    const navigationHeight = panel.querySelector('#session-card-controls:not([hidden])')?.offsetHeight ?? 0
    panel.scrollTop += engineBasis.getBoundingClientRect().top - panel.getBoundingClientRect().top - navigationHeight - 16
  })
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

  function renderCardEvidence(node, outcome) {
    const section = document.getElementById('invoice-card-evidence')
    section.hidden = !node
    const warning = document.getElementById('hallucination-warning')
    warning.hidden = !node || (outcome?.color ?? node.color) !== 'amber'
    if (!warning.hidden) {
      const messages = {
        'DuplicatePolicy.cs': 'The cancellation policy needs your confirmation. Without it, an AI explanation could invent a business rule instead of following the intended requirement.',
        'ImportPreview.cs': 'The preview depends on the duplicate-policy rule. Confirm that rule so the review does not rely on an unsupported assumption.',
        'BatchImporter.cs': 'The import depends on policy and provider guarantees. Confirm those facts rather than letting an AI explanation fill in the gaps.',
        'TaxGateway.cs': 'A contract reference alone does not establish the provider\'s rate and failure guarantees. Confirm the relevant contract rather than assuming how the provider behaves.',
      }
      document.getElementById('hallucination-message').textContent = messages[node.file] ?? 'This assessment depends on unconfirmed assumptions. Supply the missing requirement or context before relying on the conclusion.'
      const targets = node.file === 'BatchImporter.cs' ? ['DuplicatePolicy.cs', 'TaxGateway.cs'] : node.file === 'ImportPreview.cs' ? ['DuplicatePolicy.cs'] : [node.file]
      const actions = document.getElementById('hallucination-actions')
      actions.replaceChildren()
      for (const file of targets.filter(file => experience.questions[file])) {
        const button = document.createElement('button')
        button.type = 'button'
        button.className = 'evidence-source'
        button.textContent = file === 'DuplicatePolicy.cs' ? 'Clarify duplicate policy' : 'Review provider contract'
        button.disabled = Boolean(busy)
        button.addEventListener('click', () => {
          const target = byId.get(`module:${file}`)
          openCard(target)
          editing.add(target.id)
          render(target)
          form.scrollIntoView({ block: 'center' })
          form.querySelector('input[type=radio]:checked, input[type=radio]')?.focus({ preventScroll: true })
        })
        actions.append(button)
      }
    }
    if (!node) return
    const requirements = (node.requirements ?? []).map(id => analysis.requirements.items.find(item => item.id === id)).filter(Boolean)
    document.getElementById('card-requirements-summary').textContent = `Requirements: ${requirements.map(item => item.id).join(', ')}`
    document.getElementById('card-requirements-text').textContent = requirements.map(item => item.text).join(' ')
    const confidence = outcome?.confidence ?? node.model?.confidence
    document.getElementById('detail-confidence').textContent = node.model?.assessment === 'unknown' && !outcome ? 'Needs context' : `${Math.round((confidence ?? 0) * 100)}% confidence`
    if (section.dataset.node !== node.id) {
      section.querySelectorAll('details').forEach(item => { item.open = false })
      section.dataset.node = node.id
    }
  }

  function refresh() {
    onChange()
    const labels = invoiceAttention
    const selectedId = byId.has(currentId()) ? currentId() : graph.nodes.find(node => node.methods.some(method => method.id === currentId()))?.id
    for (const element of document.querySelectorAll('.graph-node')) {
      const node = byId.get(element.dataset.id)
      const record = records.get(node.id)
      const result = experience.questions[node.file]?.answers[record?.choice]
      const color = result?.color ?? node.color
      element.classList.remove('green', 'amber', 'red', 'gray')
      element.classList.add(color)
      element.dataset.color = color
      element.classList.toggle('recomputing', busy === node.id)
      element.querySelector('.node-status').textContent = busy === node.id ? 'Recomputing review' : color === 'amber' ? labels.amber : result?.title ?? labels[node.color]
      element.setAttribute('aria-label', `${node.label}: ${labels[color]}`)
      if (result) element.querySelector('.node-kind').textContent = `${Math.round(result.confidence * 100)}% CONFIDENCE`
      if (result && selectedId === node.id) {
        const badge = document.getElementById('detail-status')
        badge.className = `status ${color}`
        badge.textContent = labels[color]
        const confidence = document.querySelector('#detail-facts dd')
        if (confidence) confidence.textContent = `${Math.round(result.confidence * 100)}%`
      }
    }
    const selected = analysis.nodes.find(node => node.id === currentId() && node.kind === 'method') ?? byId.get(selectedId)
    const outcome = experience.questions[selected?.file]?.answers[records.get(selectedId)?.choice]
    renderCardEvidence(selected, outcome)
    if (selected && outcome) {
      document.getElementById('card-why-title').textContent = 'Engine decision'
      document.getElementById('detail-reason').textContent = engineDecision(selected, outcome)
    }
    const basis = document.getElementById('green-engine-basis')
    const visible = Boolean(selected)
    basis.hidden = !visible
    if (!visible) { basis.open = false; return }
    if (basis.dataset.node !== selected.id) basis.open = false
    basis.dataset.node = selected.id
    const evidence = greenReviewBasis(analysis, selected, outcome)
    const techniques = document.getElementById('engine-techniques')
    techniques.replaceChildren()
    for (const [name, observed, aiUse] of evidence.techniques) {
      const row = document.createElement('li')
      const title = document.createElement('h4')
      const fact = document.createElement('p')
      const use = document.createElement('p')
      title.textContent = name
      fact.textContent = observed
      use.textContent = aiUse
      use.className = 'engine-ai-use'
      row.append(title, fact, use)
      techniques.append(row)
    }
    const steps = document.getElementById('engine-ai-path')
    steps.replaceChildren()
    for (const text of evidence.steps) {
      const step = document.createElement('li')
      step.textContent = text
      steps.append(step)
    }
    document.getElementById('engine-green-conclusion').textContent = evidence.conclusion
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
  return {
    render(node) { render(byId.get(node.moduleId) ?? node) },
    refresh,
    get busy() { return Boolean(busy) },
    snapshot() {
      return graph.nodes.map(node => {
        const response = records.get(node.id)
        const outcome = experience.questions[node.file]?.answers[response?.choice]
        return { id: node.id, label: node.label, color: outcome?.color ?? node.color, sourceColor: node.color, reason: engineDecision(node, outcome), response: outcome ? { choice: response.choice, label: outcome.label, reference: response.reference } : null }
      })
    },
  }
}

export function reviewHandoff(snapshot, acknowledged = false) {
  const text = value => String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/([\\`*_[\]{}()#!|])/g, '\\$1')
  const { revision, modules, concerns, progress } = snapshot
  const repository = revision.repository
  const url = typeof repository === 'string' && /^[A-Za-z0-9-]+\/[\w.-]+$/.test(repository) && !['.', '..'].includes(repository.split('/')[1]) && Number.isSafeInteger(revision.number) && revision.number > 0
    ? new URL(`/${repository}/pull/${revision.number}/files`, 'https://github.com').href : null
  const findings = modules.filter(item => item.color !== 'green')
  const answers = modules.filter(item => item.response)
  const lines = [
    '## Review summary',
    '',
    ...(url ? [`**Pull request:** ${text(repository)}#${revision.number}`] : []),
    `**Analyzed head:** ${text(revision.head)}`,
    `**Analyzed base:** ${text(revision.base)}`,
    `**Walkthrough:** ${progress.visited.length} of ${progress.total} methods visited.`,
    '', '### Outstanding findings',
    ...(findings.length ? findings.map(item => `- **${text(item.label)}** (${invoiceAttention[item.color]}): ${text(item.reason)}`) : ['No outstanding findings in this assessment.']),
    ...(answers.length ? ['', '### Clarifications', ...answers.map(item => `- **${text(item.label)}:** ${text(item.response.label)}${item.response.reference ? `; reference: ${text(item.response.reference)}` : ''}`)] : []),
    ...(concerns.length ? ['', '### Recorded concerns', ...concerns.map(item => `- **${text(item.label)}:** ${text(item.note)}`)] : []),
    ...(acknowledged ? ['', "**Review acknowledgment:** I've reviewed the findings and understand the remaining risks."] : []),
    '', 'This review summary applies to the analyzed revision above. Confirm the PR head has not changed before submitting the review.',
  ]
  return { url, body: lines.join('\n') }
}

export function createOverallReview({ analysis, invoiceReview, getProgress, getConcerns, openCard }) {
  const dialog = document.getElementById('overall-review-dialog')
  const form = document.getElementById('overall-review-form')
  const risk = document.getElementById('overall-risk')
  const trigger = document.getElementById('overall-review-open')
  const status = document.getElementById('overall-review-status')
  const comment = document.getElementById('overall-comment')
  const commentSection = document.getElementById('overall-comment-section')
  const githubLink = document.getElementById('overall-github')
  const labels = invoiceAttention
  let lastContext = null
  let preparedContext = null
  let generation = 0
  let copying = false
  let handoffStatus = ''

  function snapshot() {
    return {
      revision: { repository: analysis.github?.repository ?? null, number: analysis.github?.number ?? null, reviewKey: analysis.reviewKey, base: analysis.github?.base ?? analysis.baseHash, head: analysis.github?.head ?? analysis.headHash },
      modules: invoiceReview.snapshot(),
      concerns: getConcerns(),
      progress: getProgress(),
    }
  }

  function cardLink(item) {
    const link = document.createElement('a')
    link.href = '#detail'
    link.textContent = item.label
    link.title = item.reason ?? 'Open review card'
    link.addEventListener('click', event => { event.preventDefault(); dialog.close(); openCard(item.id) })
    return link
  }

  function render() {
    const current = snapshot()
    const context = JSON.stringify(current)
    if (lastContext !== null && lastContext !== context) {
      risk.checked = false
      preparedContext = null
      generation++
      handoffStatus = 'Review context changed. Acknowledge the updated findings.'
    }
    if (invoiceReview.busy && risk.checked) { risk.checked = false; preparedContext = null; generation++ }
    lastContext = context
    const findings = current.modules.filter(item => item.color !== 'green')
    const remaining = current.progress.total - current.progress.visited.length
    document.getElementById('overall-progress').textContent = `${current.progress.visited.length} of ${current.progress.total} methods visited.${remaining ? ` ${remaining} unvisited.` : ''}`
    document.getElementById('overall-commit').textContent = current.revision.head.slice(0, 12)
    document.getElementById('overall-commit').title = current.revision.head
    document.getElementById('overall-findings-title').textContent = `${findings.length} unresolved ${findings.length === 1 ? 'finding' : 'findings'}`
    const findingList = document.getElementById('overall-findings-list')
    findingList.replaceChildren()
    for (const item of findings) {
      const row = document.createElement('li')
      const badge = document.createElement('span')
      badge.className = `status ${item.color}`
      badge.textContent = labels[item.color]
      row.append(cardLink(item), badge)
      findingList.append(row)
    }
    const handoff = reviewHandoff(current, risk.checked)
    comment.value = handoff.body
    githubLink.hidden = !handoff.url || preparedContext !== context || !risk.checked || invoiceReview.busy || copying
    if (handoff.url) githubLink.href = handoff.url
    else githubLink.removeAttribute('href')
    document.getElementById('overall-handoff-label').textContent = copying ? 'Copying review...' : handoff.url ? 'Continue to GitHub' : 'Copy review'
    document.getElementById('overall-save').disabled = invoiceReview.busy || copying || !risk.checked
    status.textContent = invoiceReview.busy ? 'A clarification is being recomputed. Handoff is paused.' : copying ? 'Preparing your review comment...' : handoffStatus
    return { current, context }
  }

  function open() {
    risk.checked = false
    preparedContext = null
    handoffStatus = ''
    generation++
    document.getElementById('overall-findings').open = false
    commentSection.open = false
    render()
    if (!dialog.open) dialog.showModal()
    dialog.scrollTop = 0
    document.getElementById('overall-review-title').focus({ preventScroll: true })
  }
  form.addEventListener('input', () => {
    generation++
    preparedContext = null
    handoffStatus = ''
    render()
  })
  form.addEventListener('submit', async event => {
    event.preventDefault()
    const { current, context } = render()
    if (invoiceReview.busy || copying) return
    if (!risk.checked || !form.reportValidity()) return
    const handoff = reviewHandoff(current, true)
    const version = generation
    copying = true
    render()
    let manualCopy = false
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable')
      await navigator.clipboard.writeText(handoff.body)
      if (generation !== version || !dialog.open || !risk.checked || invoiceReview.busy || context !== JSON.stringify(snapshot())) return
      preparedContext = context
      handoffStatus = handoff.url ? 'Review copied. Paste it into Review changes on GitHub and submit with your account.' : 'Review copied.'
      if (handoff.url) window.open(handoff.url, '_blank', 'noopener,noreferrer')
    } catch {
      if (generation !== version || !dialog.open || !risk.checked || invoiceReview.busy || context !== JSON.stringify(snapshot())) return
      preparedContext = context
      handoffStatus = 'Clipboard unavailable. The review comment is ready to copy below.'
      manualCopy = true
    } finally {
      copying = false
      render()
      if (manualCopy) { commentSection.open = true; comment.focus(); comment.select() }
    }
  })
  trigger.hidden = false
  document.getElementById('review-session').append(trigger)
  trigger.addEventListener('click', open)
  dialog.addEventListener('close', () => { risk.checked = false; preparedContext = null; generation++ })
  document.getElementById('overall-review-close').addEventListener('click', () => dialog.close())
  return { open, refresh() { if (dialog.open) render() } }
}