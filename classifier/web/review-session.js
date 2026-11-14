export function createReviewSession({ methods, openMethod, closeDetail, storageKey, onFinish = () => {} }) {
  let active = false
  let index = 0
  let finished = false
  const visited = new Set()
  let storageAvailable = true
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) ?? 'null')
    if (saved) {
      const position = methods.findIndex(method => method.id === saved.current)
      if (position >= 0) index = position
      for (const id of Array.isArray(saved.visited) ? saved.visited : []) if (methods.some(method => method.id === id)) visited.add(id)
      finished = saved.finished === true && visited.size === methods.length
    }
  } catch { storageAvailable = false }

  function persist() {
    try { localStorage.setItem(storageKey, JSON.stringify({ current: methods[index]?.id, visited: [...visited], finished })) }
    catch { storageAvailable = false }
  }

  function render() {
    document.getElementById('review-session').hidden = false
    document.getElementById('session-title').textContent = finished ? 'Walkthrough complete' : active ? `Method ${index + 1} of ${methods.length}` : 'Review episode'
    document.getElementById('session-count').textContent = `${methods.length} methods / ${visited.size} visited`
    document.getElementById('session-position').textContent = active ? methods[index].label : ''
    document.getElementById('session-progress').max = methods.length
    document.getElementById('session-progress').value = visited.size
    document.getElementById('session-start').hidden = active
    document.getElementById('session-start-label').textContent = finished ? 'Review again' : visited.size ? 'Resume review' : 'Start review'
    const navigation = document.getElementById('session-navigation')
    const target = document.getElementById(active ? 'session-card-controls' : 'review-session')
    if (navigation.parentElement !== target) target.append(navigation)
    navigation.hidden = !active
    document.getElementById('session-card-controls').hidden = !active
    document.getElementById('session-card-position').textContent = `Method ${index + 1} of ${methods.length}`
    document.getElementById('session-previous').disabled = index === 0
    document.getElementById('session-next-label').textContent = index === methods.length - 1 && visited.size === methods.length ? 'Finish walkthrough' : 'Next method'
    document.getElementById('session-status').textContent = !storageAvailable ? 'Progress stays in this tab.' : finished ? 'Navigation complete. Review decisions remain separate.' : ''
    document.body.classList.toggle('guided-review', active)
  }

  function showCurrent() {
    openMethod(methods[index])
    document.getElementById('detail-title').focus({ preventScroll: true })
    document.getElementById('detail').scrollIntoView({ block: 'start' })
  }

  function pause() {
    active = false
    persist()
    render()
  }

  function next() {
    if (!active) return
    if (index === methods.length - 1) {
      if (visited.size !== methods.length) {
        index = methods.findIndex(method => !visited.has(method.id))
        showCurrent()
        return
      }
      finished = visited.size === methods.length
      pause()
      closeDetail()
      onFinish()
      return
    }
    index++
    showCurrent()
  }

  document.getElementById('session-start').addEventListener('click', () => {
    if (finished) { index = 0; visited.clear(); finished = false }
    active = true
    showCurrent()
  })
  document.getElementById('session-previous').addEventListener('click', () => { if (index > 0) { index--; showCurrent() } })
  document.getElementById('session-next').addEventListener('click', next)
  document.getElementById('session-overview').addEventListener('click', () => { pause(); closeDetail() })
  render()
  return {
    get active() { return active },
    get progress() { return { total: methods.length, visited: [...visited].sort() } },
    next,
    pause,
    inModule(id) { return methods.find(method => method.moduleId === id && !visited.has(method.id)) ?? methods.find(method => method.moduleId === id) },
    select(node) {
      if (!active) return
      const position = methods.findIndex(method => method.id === node.id)
      if (position < 0) return
      index = position
      visited.add(node.id)
      persist()
      render()
    },
  }
}