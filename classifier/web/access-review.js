import defaultScenario from '../fixtures/order-flow/access-review.json'

export function createAccessReview({ storageKey, revision, scenario = defaultScenario }) {
  const dialog = document.getElementById('understand-dialog')
  const activeInput = document.getElementById('scenario-active')
  const tenantInput = document.getElementById('scenario-tenant')
  const audio = document.getElementById('access-audio')
  const noteForm = document.getElementById('access-note-form')
  const noteStatus = document.getElementById('access-note-status')
  let savedNote = null
  let quizAnswer = null
  if (scenario.kind === 'retry') {
    document.getElementById('understand-title').textContent = scenario.title
    document.querySelector('.understand-provenance').textContent = 'INV-105 / Lost acknowledgement'
    document.getElementById('scenario-active-label').textContent = 'Commit acknowledged'
    document.getElementById('scenario-tenant-label').textContent = 'Reuse ID (proposed fix)'
    activeInput.checked = false
    tenantInput.checked = false
    document.getElementById('before-flow-title').textContent = 'First attempt'
    document.getElementById('after-flow-title').textContent = 'Next attempt'
    document.querySelector('#before-flow-title + code').textContent = 'COMMIT'
    document.querySelector('#after-flow-title + code').textContent = 'RETRY'
    for (const version of ['before', 'after']) {
      document.getElementById(`${version}-active`).previousElementSibling.textContent = 'Invoice ID'
      document.getElementById(`${version}-tenant`).previousElementSibling.textContent = 'Persistence'
    }
    document.getElementById('expected-requirement').textContent = 'INV-105 expected: '
    document.querySelector('.access-limit').hidden = true
  }
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey) ?? 'null')
    if (stored?.version === scenario.version && typeof stored.reviewer === 'string' && stored.reviewer.length <= 100 &&
        typeof stored.note === 'string' && stored.note.length <= 2000 && ['unsure', 'somewhat', 'clear'].includes(stored.confidence)) {
      savedNote = stored
      document.getElementById('access-reviewer').value = stored.reviewer
      document.getElementById('access-note').value = stored.note
      document.getElementById('access-confidence').value = stored.confidence
      quizAnswer = scenario.quiz.options.some(option => option.id === stored.quizAnswer) ? stored.quizAnswer : null
      noteStatus.textContent = 'Saved locally. Red attention is unchanged.'
    }
  } catch { noteStatus.textContent = 'Browser storage is unavailable. Export your note to keep it.' }

  document.getElementById('access-transcript').textContent = scenario.narration
  document.getElementById('access-quiz-question').textContent = scenario.quiz.question
  for (const option of scenario.quiz.options) {
    const label = document.createElement('label')
    const input = document.createElement('input')
    input.type = 'radio'
    input.name = 'access-answer'
    input.value = option.id
    input.required = true
    input.checked = quizAnswer === option.id
    const text = document.createElement('span')
    text.textContent = option.label
    label.append(input, text)
    document.getElementById('access-quiz-options').append(label)
  }
  document.getElementById('access-quiz-form').addEventListener('submit', event => {
    event.preventDefault()
    quizAnswer = new FormData(event.target).get('access-answer')
    const correct = quizAnswer === scenario.quiz.answer
    document.getElementById('access-quiz-feedback').textContent = `${correct ? 'Correct.' : 'Not quite.'} ${scenario.quiz.explanation}`
    document.getElementById('access-quiz-feedback').hidden = false
    if (savedNote) noteStatus.textContent = 'Quiz response changed. Save your note again to include it.'
  })
  document.getElementById('access-quiz-options').addEventListener('change', () => {
    document.getElementById('access-quiz-feedback').hidden = true
  })

  function collectNote() {
    const reviewer = document.getElementById('access-reviewer')
    const note = document.getElementById('access-note')
    for (const input of [reviewer, note]) input.setCustomValidity(input.value.trim() ? '' : 'Enter a value before saving.')
    if (!noteForm.reportValidity()) return null
    return {
      version: scenario.version, mode: scenario.mode, methodId: scenario.methodId, revision,
      reviewer: reviewer.value.trim(), note: note.value.trim(), confidence: document.getElementById('access-confidence').value,
      quizAnswer, quizCorrect: quizAnswer === null ? null : quizAnswer === scenario.quiz.answer,
      attention: 'red', approved: false, savedAt: new Date().toISOString(),
    }
  }

  noteForm.addEventListener('input', event => {
    event.target.setCustomValidity?.('')
    noteStatus.textContent = 'Unsaved changes.'
  })
  noteForm.addEventListener('submit', event => {
    event.preventDefault()
    const note = collectNote()
    if (!note) return
    savedNote = note
    try {
      localStorage.setItem(storageKey, JSON.stringify(note))
      noteStatus.textContent = 'Saved locally. Red attention is unchanged.'
    } catch { noteStatus.textContent = 'Kept in this tab only. Export your note to keep it.' }
  })
  document.getElementById('access-note-export').addEventListener('click', () => {
    const note = collectNote()
    if (!note) return
    const url = URL.createObjectURL(new Blob([JSON.stringify(note, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = scenario.exportName ?? 'access-review-note.json'
    document.body.append(link)
    link.click()
    link.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  })
  if (!audio.getAttribute('src')) {
    audio.removeAttribute('src')
    audio.hidden = true
    document.getElementById('access-audio-status').textContent = 'Narration unavailable; transcript below.'
  }
  audio.addEventListener('error', () => { document.getElementById('access-audio-status').textContent = 'Narration could not play; transcript below.' })
  dialog.addEventListener('close', () => audio.pause())
  document.getElementById('access-audio-section').addEventListener('toggle', event => { if (!event.target.open) audio.pause() })

  function renderScenario() {
    const active = activeInput.checked
    const matches = tenantInput.checked
    if (scenario.kind === 'retry') {
      const duplicated = !active && !matches
      document.getElementById('before-active').textContent = 'A'
      document.getElementById('before-tenant').textContent = 'Committed'
      document.getElementById('before-outcome').textContent = '1 invoice'
      document.getElementById('after-active').textContent = active ? 'No retry' : matches ? 'A' : 'B'
      document.getElementById('after-tenant').textContent = active ? 'Not needed' : matches ? 'Same record' : 'New record'
      document.getElementById('after-tenant-step').classList.toggle('skipped', active)
      document.getElementById('after-outcome').textContent = duplicated ? '2 invoices' : '1 invoice'
      document.getElementById('after-outcome').classList.toggle('unexpected', duplicated)
      document.getElementById('expected-outcome').textContent = '1 invoice'
      document.getElementById('scenario-verdict').textContent = duplicated ? 'Duplicate invoice created' : matches ? 'Proposed repair avoids this duplicate' : 'No retry is needed'
      document.getElementById('scenario-result').classList.toggle('mismatch', duplicated)
      document.getElementById('scenario-consequence').textContent = duplicated ? 'The commit succeeded. Retrying with a new ID saves the invoice a second time.' : matches ? 'A stable identity lets the store recognize the already-committed invoice.' : 'The acknowledgement ends the retry loop after the first write.'
      return
    }
    const before = active && matches
    const after = active || matches
    for (const [version, allowed, tenantReached] of [['before', before, active], ['after', after, !active]]) {
      document.getElementById(`${version}-active`).textContent = active ? 'Yes' : 'No'
      document.getElementById(`${version}-tenant`).textContent = tenantReached ? matches ? 'Yes' : 'No' : 'Not checked'
      document.getElementById(`${version}-tenant-step`).classList.toggle('skipped', !tenantReached)
      document.getElementById(`${version}-outcome`).textContent = allowed ? 'Allowed' : 'Denied'
    }
    document.getElementById('after-outcome').classList.toggle('unexpected', after !== before)
    document.getElementById('expected-outcome').textContent = before ? 'Allowed' : 'Denied'
    document.getElementById('scenario-verdict').textContent = after !== before ? 'Conflicts with ORD-17' : 'Matches ORD-17 for this input'
    document.getElementById('scenario-result').classList.toggle('mismatch', after !== before)
    document.getElementById('scenario-consequence').textContent = after !== before
      ? active ? 'An active user can submit another tenant\'s order.' : 'An inactive user can submit an order for their tenant.'
      : before ? 'Both conditions pass, so both versions allow this request.' : 'Both conditions fail, so both versions deny this request.'
  }

  activeInput.addEventListener('change', renderScenario)
  tenantInput.addEventListener('change', renderScenario)
  document.getElementById('reset-scenario').addEventListener('click', () => {
    activeInput.checked = scenario.kind !== 'retry'
    tenantInput.checked = false
    renderScenario()
  })
  document.getElementById('close-understand').addEventListener('click', () => dialog.close())

  return {
    open() {
      renderScenario()
      dialog.showModal()
    },
  }
}