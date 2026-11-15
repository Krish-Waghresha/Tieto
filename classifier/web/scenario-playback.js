export function retryFrames(sample, { reuse = false, acknowledged = false } = {}) {
  const retryId = reuse ? sample.firstId : sample.retryId
  const frames = [
    { stage: 'identity', route: null, attempt: 1, id: sample.firstId, records: [], code: 'identity', title: reuse ? 'Create the identity once.' : 'A new identity for this attempt.', detail: `${sample.number} receives ${sample.firstId}.`, terminal: false },
    { stage: 'store', route: 'save', attempt: 1, id: sample.firstId, records: [sample.firstId], code: 'save', title: 'The invoice is already saved.', detail: `${sample.amount} is stored under ${sample.firstId}. The commit has succeeded.`, terminal: false },
    { stage: 'ack', route: 'ack', attempt: 1, id: sample.firstId, records: [sample.firstId], code: acknowledged ? 'return' : 'catch', title: acknowledged ? 'Confirmation received. No retry.' : 'The confirmation never arrives.', detail: acknowledged ? 'The caller returns successfully with one stored invoice.' : 'The caller sees a timeout. The stored invoice is not rolled back.', terminal: acknowledged },
  ]
  if (!acknowledged) frames.push(
    { stage: 'identity', route: 'retry', attempt: 2, id: retryId, records: [sample.firstId], code: reuse ? 'loop' : 'identity', title: reuse ? 'The retry keeps the same identity.' : 'Same invoice. Different identity.', detail: reuse ? `Attempt two reuses ${sample.firstId}.` : `Attempt two creates ${retryId}, even though ${sample.number} is already stored.`, terminal: false },
    { stage: 'store', route: 'save', attempt: 2, id: retryId, records: reuse ? [sample.firstId] : [sample.firstId, retryId], code: 'save', title: reuse ? 'One identity. One stored record.' : 'One invoice has become two records.', detail: reuse ? 'The store keys invoices by ID, so the retry updates the same entry. Idempotency depends on the store preserving this guarantee.' : 'The store sees two different IDs, not one retried invoice. INV-105 is violated.', terminal: true },
  )
  return frames
}

export function createScenarioPlayback({ dialog, scenario, source, inspectSource }) {
  const sample = scenario.sample
  const root = document.getElementById('retry-experience')
  const packet = document.getElementById('retry-packet')
  const audio = document.getElementById('access-audio')
  const loss = document.getElementById('retry-lose-confirmation')
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)')
  const tabs = [...root.querySelectorAll('[role=tab]')]
  let index = 0
  let playing = false
  let animation = null
  let elapsed = 0
  let previousTime = null
  const duration = 1250
  const sourceLines = (source?.code ?? '').split('\n')
  const sourceStart = (source?.line ?? 1) - Math.max(0, sourceLines.findIndex(line => line.trim()))
  const codePatterns = [['loop', 'for (int attempt'], ['identity', 'Guid.NewGuid()'], ['save', 'store.Save(invoice)'], ['return', 'return new WriteResult(true'], ['catch', 'catch (TransientStoreException)']]

  for (const child of [...dialog.children]) if (child.tagName !== 'HEADER' && child !== root) child.hidden = true
  root.hidden = false
  dialog.classList.add('retry-dialog')
  document.getElementById('understand-title').textContent = 'One invoice. Two records.'
  document.querySelector('.understand-provenance').textContent = 'RetryingInvoiceWriter.Write / INV-105'
  document.getElementById('retry-invoice-number').textContent = sample.number
  document.getElementById('retry-invoice-meta').textContent = `${sample.supplier} / ${sample.amount}`
  document.getElementById('retry-audio-host').append(audio)
  document.getElementById('retry-transcript').textContent = scenario.narration
  if (!audio.getAttribute('src')) {
    audio.removeAttribute('src')
    audio.hidden = true
    document.getElementById('retry-audio-status').textContent = 'Audio unavailable. Transcript below.'
  }
  audio.addEventListener('error', () => { document.getElementById('retry-audio-status').textContent = 'Audio unavailable. Transcript below.' })
  audio.addEventListener('play', () => {
    pause()
    if (document.getElementById('retry-listen-panel').hidden) audio.pause()
  })

  function selectTab(tab) {
    pause()
    if (tab.id !== 'retry-listen-tab') audio.pause()
    for (const candidate of tabs) {
      const active = candidate === tab
      candidate.setAttribute('aria-selected', String(active))
      candidate.tabIndex = active ? 0 : -1
      document.getElementById(candidate.getAttribute('aria-controls')).hidden = !active
    }
    dialog.scrollTop = 0
  }
  for (const tab of tabs) {
    tab.addEventListener('click', () => { if (tab.getAttribute('aria-selected') !== 'true') selectTab(tab) })
    tab.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
      event.preventDefault()
      const position = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (tabs.indexOf(tab) + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length
      selectTab(tabs[position])
      tabs[position].focus({ preventScroll: true })
    })
  }

  function frames() {
    return retryFrames(sample, { reuse: document.getElementById('retry-fixed').checked, acknowledged: !loss.checked })
  }

  function controls() {
    const play = document.getElementById('retry-play')
    const label = playing ? 'Pause import' : frames()[index].terminal ? 'Replay import' : 'Run import'
    play.setAttribute('aria-label', label)
    play.title = label
    document.getElementById('retry-play-label').textContent = label
    document.getElementById('retry-play-icon').hidden = playing
    document.getElementById('retry-pause-icon').hidden = !playing
    document.getElementById('retry-back').disabled = index === 0
    document.getElementById('retry-next').disabled = index === frames().length - 1
    root.classList.toggle('is-playing', playing)
  }

  function renderCode(frame) {
    const list = document.getElementById('retry-code')
    list.replaceChildren()
    const fixed = document.getElementById('retry-fixed').checked
    const rows = codePatterns.map(([kind, match]) => {
      const position = sourceLines.findIndex(line => line.includes(match))
      return { kind, line: position < 0 ? '' : sourceStart + position, text: position < 0 ? match : sourceLines[position].trim() }
    })
    if (fixed) {
      rows.splice(1, 1)
      rows.unshift({ kind: 'identity', line: '+', text: 'var invoiceId = Guid.NewGuid();' })
      rows.splice(2, 0, { kind: 'argument', line: '+', text: 'invoiceId,' })
    }
    for (const row of rows) {
      const item = document.createElement('li')
      const number = document.createElement('span')
      const code = document.createElement('code')
      number.textContent = row.line
      code.textContent = row.text
      item.dataset.kind = row.kind
      if (row.kind === frame.code) item.setAttribute('aria-current', 'step')
      item.append(number, code)
      list.append(item)
    }
    document.getElementById('retry-code-label').textContent = fixed ? 'Proposed edit / relevant lines' : 'Current PR / relevant lines'
  }

  function render() {
    const flow = frames()
    const frame = flow[index]
    root.dataset.step = String(index)
    root.classList.toggle('has-duplicate', frame.records.length > 1)
    root.classList.toggle('has-finished', frame.terminal)
    document.getElementById('retry-step-title').textContent = frame.title
    document.getElementById('retry-step-detail').textContent = frame.detail
    document.getElementById('retry-attempt').textContent = `Attempt ${frame.attempt}`
    document.getElementById('retry-identity-value').textContent = frame.id
    document.getElementById('retry-record-count').textContent = String(frame.records.length)
    document.getElementById('retry-count-label').textContent = frame.records.length === 1 ? 'record stored' : 'records stored'
    document.getElementById('retry-confirmation-label').textContent = loss.checked ? 'Confirmation lost' : 'Confirmation delivered'
    document.getElementById('retry-position').textContent = `${index + 1} / ${flow.length}`
    const scrubber = document.getElementById('retry-scrubber')
    scrubber.max = flow.length - 1
    scrubber.value = index
    scrubber.setAttribute('aria-valuetext', frame.title)
    for (const node of document.querySelectorAll('[data-retry-stage]')) {
      if (node.dataset.retryStage === frame.stage) node.setAttribute('aria-current', 'step')
      else node.removeAttribute('aria-current')
    }
    for (const path of document.querySelectorAll('.retry-route')) path.classList.toggle('active', path.dataset.route === frame.route)
    const ledger = document.getElementById('retry-ledger')
    ledger.replaceChildren()
    for (let position = 0; position < 2; position++) {
      const row = document.createElement('li')
      const id = document.createElement('code')
      const description = document.createElement('span')
      const occupied = position < frame.records.length
      row.className = occupied ? position ? 'duplicate-record' : 'stored-record' : 'empty-record'
      id.textContent = occupied ? frame.records[position] : position ? 'No second record' : 'No records yet'
      description.textContent = occupied ? `${sample.number} / ${sample.amount}` : position ? 'Expected to stay empty' : 'Waiting for the write'
      row.append(id, description)
      ledger.append(row)
    }
    renderCode(frame)
    controls()
  }

  function pause() {
    cancelAnimationFrame(animation)
    animation = null
    playing = false
    previousTime = null
    controls()
  }

  function seek(position) {
    index = Math.max(0, Math.min(position, frames().length - 1))
    pause()
    elapsed = 0
    packet.hidden = true
    render()
  }

  function tick(time) {
    if (!playing) return
    if (previousTime !== null) elapsed += time - previousTime
    previousTime = time
    const progress = Math.min(1, elapsed / duration)
    const flow = frames()
    const next = flow[index + 1]
    if (!next) { pause(); return }
    const path = document.querySelector(`.retry-route[data-route="${next.route}"]`)
    const point = path.getPointAtLength(path.getTotalLength() * progress)
    packet.hidden = reducedMotion.matches
    const scene = packet.parentElement
    const margin = (packet.offsetWidth / 2 + 4) / scene.clientWidth
    packet.style.left = `${Math.max(margin, Math.min(1 - margin, point.x / 640)) * 100}%`
    packet.style.top = `${point.y / 440 * 100}%`
    document.getElementById('retry-packet-id').textContent = flow[index].id
    if (progress === 1) {
      index++
      elapsed = 0
      packet.hidden = true
      render()
      if (frames()[index].terminal) { pause(); return }
    }
    animation = requestAnimationFrame(tick)
  }

  function play() {
    if (document.getElementById('retry-simulation-panel').hidden) return
    if (frames()[index].terminal) seek(0)
    audio.pause()
    playing = true
    previousTime = null
    controls()
    animation = requestAnimationFrame(tick)
  }

  for (const input of document.querySelectorAll('input[name="retry-version"], #retry-lose-confirmation')) input.addEventListener('change', () => {
    seek(0)
    if (!reducedMotion.matches) play()
  })
  document.getElementById('retry-play').addEventListener('click', () => playing ? pause() : play())
  document.getElementById('retry-back').addEventListener('click', () => seek(index - 1))
  document.getElementById('retry-next').addEventListener('click', () => seek(index + 1))
  document.getElementById('retry-reset').addEventListener('click', () => seek(0))
  document.getElementById('retry-scrubber').addEventListener('input', event => seek(Number(event.target.value)))
  for (const button of document.querySelectorAll('[data-retry-stage]')) button.addEventListener('click', () => seek(button.dataset.retryStage === 'identity' ? index >= 3 ? 3 : 0 : button.dataset.retryStage === 'store' ? index >= 3 ? frames().length - 1 : 1 : 2))
  document.getElementById('retry-inspect').addEventListener('click', () => { pause(); audio.pause(); inspectSource?.() })
  const answers = document.getElementById('retry-answers')
  const questions = scenario.quiz.questions
  const quizResponses = new Map()
  let questionIndex = 0

  function renderQuiz(moveFocus = false) {
    const question = questions[questionIndex]
    const selected = quizResponses.get(question.id)
    const correctCount = questions.filter(item => quizResponses.get(item.id) === item.answer).length
    document.getElementById('retry-quiz-position').textContent = `Question ${questionIndex + 1} of ${questions.length}`
    document.getElementById('retry-quiz-progress').textContent = `${quizResponses.size} of ${questions.length} answered${quizResponses.size ? ` / ${correctCount} correct` : ''}`
    document.getElementById('retry-quiz-title').textContent = question.title
    document.getElementById('retry-quiz-question').textContent = question.question
    if (answers.dataset.question !== question.id) {
      answers.replaceChildren()
      for (const option of question.options) {
        const label = document.createElement('label')
        const radio = document.createElement('input')
        const text = document.createElement('span')
        radio.type = 'radio'
        radio.name = 'retry-answer'
        radio.value = option.id
        radio.checked = selected === option.id
        text.textContent = option.label
        label.append(radio, text)
        answers.append(label)
      }
      answers.dataset.question = question.id
    }
    const feedback = document.getElementById('retry-quiz-feedback')
    feedback.hidden = selected === undefined
    feedback.dataset.correct = String(selected === question.answer)
    feedback.textContent = selected === undefined ? '' : `${selected === question.answer ? 'Exactly.' : 'Not quite.'} ${question.explanation}`
    document.getElementById('retry-quiz-back').disabled = questionIndex === 0
    document.getElementById('retry-quiz-next-label').textContent = questionIndex === questions.length - 1 ? 'Review answers' : 'Next question'
    if (moveFocus) {
      document.getElementById('retry-quiz-title').focus({ preventScroll: true })
      dialog.scrollTop = 0
    }
  }
  answers.addEventListener('change', event => {
    const question = questions[questionIndex]
    if (!question.options.some(option => option.id === event.target.value)) return
    quizResponses.set(question.id, event.target.value)
    renderQuiz()
  })
  document.getElementById('retry-quiz-back').addEventListener('click', () => { questionIndex = Math.max(0, questionIndex - 1); renderQuiz(true) })
  document.getElementById('retry-quiz-next').addEventListener('click', () => { questionIndex = (questionIndex + 1) % questions.length; renderQuiz(true) })
  renderQuiz()
  document.getElementById('close-understand').addEventListener('click', () => dialog.close())
  dialog.addEventListener('close', () => { pause(); audio.pause() })
  document.addEventListener('visibilitychange', () => { if (document.hidden) { pause(); audio.pause() } })
  reducedMotion.addEventListener('change', () => { pause(); packet.hidden = true })
  return { open() { seek(0); selectTab(tabs[0]); dialog.showModal(); dialog.scrollTop = 0 } }
}