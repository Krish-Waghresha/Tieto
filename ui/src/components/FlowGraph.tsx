import { useMemo } from 'react'
import { ReactFlow, Handle, Position, MarkerType, type Node, type Edge, type NodeProps } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from '@dagrejs/dagre'
import { X, Layers, GitBranch, ShieldQuestion, MessageSquareWarning } from 'lucide-react'
import type { Ledger } from '../lib/ledger'

export type GraphMode = 'before' | 'after'
type Kind = 'callers' | 'plain' | 'new' | 'question' | 'ok' | 'risk'
type ND = { label: string; sub?: string; kind: Kind; badge?: string; hidden?: boolean; selected?: boolean; target?: string }

const W = 190, H = 58

function FlowNode({ data }: NodeProps<Node<ND>>) {
  const k = data.kind
  const cls = {
    callers: 'border-ink/60 bg-card shadow-[4px_4px_0_-1px_var(--color-card),4px_4px_0_0_var(--color-line),8px_8px_0_-1px_var(--color-card),8px_8px_0_0_var(--color-line)]',
    plain: 'border-ink/50 bg-card',
    new: 'border-argued border-dashed bg-[#fbf3f8]',
    question: 'border-argued border-dashed bg-[#fbf3f8] rounded-[28px]',
    ok: 'border-measured bg-[#eef8f4]',
    risk: 'border-risk bg-risk-soft',
  }[k]
  const Icon = { callers: Layers, plain: GitBranch, new: GitBranch, question: ShieldQuestion, ok: MessageSquareWarning, risk: X }[k]
  return (
    <div className={`relative flex h-[58px] w-[190px] cursor-pointer items-center gap-2 rounded-xl border-2 px-3 text-left transition-all duration-500
      ${cls} ${data.hidden ? 'pointer-events-none scale-95 opacity-0' : 'opacity-100'} ${data.selected ? 'ring-4 ring-accent/30' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <Icon size={16} className={k === 'risk' ? 'text-risk' : k === 'ok' ? 'text-measured' : 'text-muted'} aria-hidden />
      <div className="min-w-0">
        <div className={`truncate text-[13px] font-semibold ${k === 'risk' ? 'text-risk' : ''}`}>{data.label}</div>
        {data.sub && <div className="truncate font-mono text-[10.5px] text-muted">{data.sub}</div>}
      </div>
      {data.badge && <span className="absolute -right-2 -top-2.5 rounded-full bg-ink px-2 py-0.5 text-[11px] font-bold text-paper">{data.badge}</span>}
      <Handle type="source" position={Position.Right} />
    </div>
  )
}
const nodeTypes = { flow: FlowNode }

function layout(nodes: Node<ND>[], edges: Edge[]) {
  const g = new dagre.graphlib.Graph().setGraph({ rankdir: 'LR', nodesep: 70, ranksep: 92 }).setDefaultEdgeLabel(() => ({}))
  nodes.forEach(n => g.setNode(n.id, { width: W, height: H }))
  edges.forEach(e => g.setEdge(e.source, e.target))
  dagre.layout(g)
  return nodes.map(n => { const p = g.node(n.id); return { ...n, position: { x: p.x - W / 2, y: p.y - H / 2 } } })
}

/** Builds the graph only from deterministic tool facts (fan-out + branch shape). */
export function useFlow(L: Ledger) {
  return useMemo(() => {
    const fan = L.facts.find(f => f.kind === 'fanout')
    const br = L.facts.find(f => f.kind === 'branch')
    if (!fan) return null
    const fanHunk = fan.claims?.[0]
    const brHunk = br ? L.coverage.hunks.find(h => h.path.endsWith('.cs') && br.lines && h.new_start <= br.lines[0] && br.lines[0] <= h.new_start + h.added)?.id : undefined
    const nodes: Node<ND>[] = [
      { id: 'callers', type: 'flow', position: { x: 0, y: 0 }, data: { kind: 'callers', label: `${fan.count} call sites`, sub: `${fan.methods?.length} methods`, badge: `×${fan.count}`, target: 'callers' } },
      { id: 'field', type: 'flow', position: { x: 0, y: 0 }, data: { kind: 'plain', label: fan.field ?? 'delegate', sub: 'report delegate', target: fanHunk } },
      ...(br ? [
        { id: 'filter', type: 'flow', position: { x: 0, y: 0 }, data: { kind: 'new' as Kind, label: br.method ?? 'filter', sub: 'NEW filter', target: `method:${br.method}` } },
        { id: 'q', type: 'flow', position: { x: 0, y: 0 }, data: { kind: 'question' as Kind, label: 'In this project?', sub: 'location in source', target: `method:${br.method}` } },
      ] : []),
      { id: 'shown', type: 'flow', position: { x: 0, y: 0 }, data: { kind: 'ok', label: 'Warning shown', sub: 'user sees diagnostic' } },
      ...(br && !br.has_else ? [{ id: 'dropped', type: 'flow', position: { x: 0, y: 0 }, data: { kind: 'risk' as Kind, label: 'DROPPED', sub: 'no warning, no signal', target: `method:${br.method}` } }] : []),
    ]
    const edgeAfter: Edge[] = [
      { id: 'e1', source: 'callers', target: 'field' },
      ...(br ? [{ id: 'e2', source: 'field', target: 'filter' }, { id: 'e3', source: 'filter', target: 'q' }, { id: 'e4', source: 'q', target: 'shown', label: 'yes' }] : [{ id: 'e2b', source: 'field', target: 'shown' }]),
      ...(br && !br.has_else ? [{ id: 'e5', source: 'q', target: 'dropped', label: 'no → dropped' }] : []),
    ]
    return { nodes: layout(nodes, edgeAfter), edgeAfter, fan, br, fanHunk, brHunk }
  }, [L])
}

const grey = '#8f897f'
export function FlowGraph({ L, mode, selected, onSelect }: { L: Ledger; mode: GraphMode; selected?: string | null; onSelect?: (target: string) => void }) {
  const flow = useFlow(L)
  if (!flow) return <p className="text-muted">No cross-cutting change detected — no flow graph.</p>
  const afterOnly = new Set(['filter', 'q', 'dropped'])
  const nodes = flow.nodes.map(n => ({
    ...n, draggable: false, selectable: false,
    data: { ...n.data, hidden: mode === 'before' && afterOnly.has(n.id), selected: !!selected && n.data.target === selected },
  }))
  const style = (id: string): Edge => {
    if (id === 'e5') return { id, source: 'q', target: 'dropped', animated: true, label: 'no → DROPPED',
      style: { stroke: '#D55E00', strokeWidth: 3, strokeDasharray: '7 5' }, labelStyle: { fill: '#D55E00', fontWeight: 700, fontSize: 12 },
      labelBgStyle: { fill: '#fbeee6' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#D55E00' } }
    const e = flow.edgeAfter.find(x => x.id === id)!
    const isNew = ['e2', 'e3', 'e4'].includes(id)
    return { ...e, style: { stroke: isNew ? '#CC79A7' : grey, strokeWidth: isNew ? 2.5 : 1.8 }, labelStyle: { fontSize: 12, fill: '#6b665e' },
      markerEnd: { type: MarkerType.ArrowClosed, color: isNew ? '#CC79A7' : grey } }
  }
  const edges: Edge[] = mode === 'before'
    ? [style('e1'), { id: 'eb', source: 'field', target: 'shown', style: { stroke: grey, strokeWidth: 1.8 }, markerEnd: { type: MarkerType.ArrowClosed, color: grey }, label: 'always', labelStyle: { fontSize: 12, fill: '#6b665e' } }]
    : flow.edgeAfter.map(e => style(e.id))
  return (
    <div className="h-[340px] w-full rounded-2xl border border-line bg-[radial-gradient(#e4ded3_1px,transparent_1px)] [background-size:18px_18px]">
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.15 }}
        nodesDraggable={false} nodesConnectable={false} elementsSelectable={false} zoomOnScroll={false} panOnScroll={false}
        panOnDrag={false} zoomOnPinch={false} zoomOnDoubleClick={false} preventScrolling={false}
        onNodeClick={(_, n) => n.data.target && onSelect?.(n.data.target as string)} proOptions={{ hideAttribution: true }} />
    </div>
  )
}
