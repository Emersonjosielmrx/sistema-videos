import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ReactFlow, Background, Controls, BackgroundVariant, useReactFlow } from '@xyflow/react'
import {
  ArrowLeft, Save, Undo2, FlaskConical, X, Send, RotateCcw, Loader2, Workflow, ListChecks, MessagesSquare,
  UtensilsCrossed, History, Bot, User, Hand, Trash2, Plus, CheckCircle2, XCircle, StopCircle, MinusCircle, RefreshCw,
} from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Card, Input, Switch, Tabs, ErrorText } from '../components/ui'
import { cn, formatDate, formatPhone } from '../lib/utils'
import { NODE_DEFS, StepNode, buildGraph, stepsToStatus, type NodeId } from '../flow/nodes'
import { NodePanel } from '../flow/panels'
import type { Execution, Flow, FlowConfig, Step } from '../flow/types'

const nodeTypes = { step: StepNode }
type Tab = 'fluxo' | 'execucoes' | 'conversas' | 'cardapio' | 'versoes'
type ChatMsg = { from: 'client' | 'bot'; text?: string; poll?: { title: string; options: string[] } }

const STEP_ICON = { ok: CheckCircle2, error: XCircle, stop: StopCircle, skip: MinusCircle }
const STEP_COLOR = { ok: 'text-emerald-400', error: 'text-red-400', stop: 'text-amber-400', skip: 'text-muted-foreground' }
const NODE_TITLE: Record<string, string> = Object.fromEntries(NODE_DEFS.map(d => [d.id, d.title]))

const PANEL_PX = 216 // metade da largura do painel lateral (420px + margem)

function useIsDesktop() {
  const query = '(min-width: 768px)'
  const [desktop, setDesktop] = useState(() => window.matchMedia(query).matches)
  useEffect(() => {
    const mq = window.matchMedia(query)
    const on = () => setDesktop(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return desktop
}

function ViewportControl({ panel, selected }: { panel: string | null; selected: NodeId | null }) {
  const rf = useReactFlow()
  useEffect(() => {
    const t = setTimeout(() => {
      if (panel === 'node' && selected) {
        const d = NODE_DEFS.find(n => n.id === selected)!
        const zoom = 0.9
        rf.setCenter(d.x + 120 + PANEL_PX / zoom, d.y + 55, { zoom, duration: 300 })
      } else if (panel) {
        rf.fitView({ padding: { top: '30px', bottom: '30px', left: '30px', right: '450px' }, maxZoom: 1, duration: 300 })
      } else {
        rf.fitView({ padding: 0.08, maxZoom: 1, duration: 300 })
      }
    }, 60)
    return () => clearTimeout(t)
  }, [panel, selected])
  return null
}

function StepList({ steps }: { steps: Step[] }) {
  return (
    <ol className="space-y-1.5">
      {steps.map((s, i) => {
        const Icon = STEP_ICON[s.status]
        return (
          <li key={i} className="flex gap-2 text-sm">
            <Icon className={cn('h-4 w-4 shrink-0 mt-0.5', STEP_COLOR[s.status])} />
            <div className="min-w-0">
              <span className="font-medium">{NODE_TITLE[s.node] || s.node}</span>
              {s.ms !== undefined && <span className="text-xs text-muted-foreground"> · {s.ms} ms</span>}
              <p className="text-xs text-muted-foreground break-words">{s.info}</p>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'ok') return <Badge variant="success">ok</Badge>
  if (status === 'error') return <Badge variant="destructive">erro</Badge>
  return <Badge variant="muted">{status === 'skip' ? 'sem resposta' : status}</Badge>
}

function TestPanel({ flow, dirty, onSteps }: { flow: Flow; dirty: boolean; onSteps: (s: Step[]) => void }) {
  const [msgs, setMsgs] = useState<ChatMsg[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs, busy])

  async function send(body: { message?: string; vote?: string }, shown: string) {
    setBusy(true); setError('')
    setMsgs(m => [...m, { from: 'client', text: shown }])
    try {
      const r = await api.post('/test/message', { flow_id: flow.id, ...body })
      setMsgs(m => [...m, ...r.messages.map((x: any) => x.type === 'poll'
        ? { from: 'bot' as const, poll: { title: x.title, options: x.options } }
        : { from: 'bot' as const, text: x.text })])
      onSteps(r.steps)
    } catch (e: any) { setError(e.message) } finally { setBusy(false) }
  }
  async function reset() {
    await api.post(`/test/reset/${flow.id}`)
    setMsgs([]); onSteps([])
  }
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between gap-2 pb-3">
        <p className="text-sm text-muted-foreground">Converse como um cliente. O caminho acende no fluxo.</p>
        <Button variant="ghost" size="sm" onClick={reset}><RotateCcw /> Reiniciar</Button>
      </div>
      {dirty && <p className="mb-2 rounded-lg bg-amber-500/10 px-3 py-2 text-xs text-amber-500">O teste usa a versão salva. Salve para testar suas alterações.</p>}
      <div className="flex-1 min-h-0 overflow-y-auto space-y-2 rounded-2xl bg-background/60 p-3">
        {msgs.length === 0 && <p className="text-center text-xs text-muted-foreground pt-6">Mande "oi" para começar.</p>}
        {msgs.map((m, i) => (
          <div key={i} className={cn('flex', m.from === 'client' ? 'justify-end' : 'justify-start')}>
            {m.poll ? (
              <div className="max-w-[85%] rounded-2xl rounded-bl-sm bg-card border border-border/60 p-3 space-y-2">
                <p className="text-sm font-medium">{m.poll.title}</p>
                {m.poll.options.map(o => (
                  <button key={o} disabled={busy} onClick={() => send({ vote: o }, `[tocou] ${o}`)}
                    className="flex w-full items-center gap-2 rounded-xl border border-border/60 px-3 py-2 text-left text-sm hover:border-primary hover:bg-primary/10 transition">
                    <span className="h-3.5 w-3.5 rounded-full border border-muted-foreground" /> {o}
                  </button>
                ))}
              </div>
            ) : (
              <p className={cn('max-w-[85%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm break-words',
                m.from === 'client' ? 'rounded-br-sm bg-primary text-primary-foreground' : 'rounded-bl-sm bg-card border border-border/60')}>
                {m.text}
              </p>
            )}
          </div>
        ))}
        {busy && <p className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> respondendo...</p>}
        <div ref={end} />
      </div>
      <ErrorText>{error}</ErrorText>
      <form onSubmit={e => { e.preventDefault(); if (text.trim()) { send({ message: text }, text); setText('') } }} className="flex gap-2 pt-3">
        <Input value={text} onChange={e => setText(e.target.value)} placeholder="Mensagem do cliente" disabled={busy} className="h-10" />
        <Button type="submit" size="icon" className="h-10 w-10 shrink-0" disabled={busy || !text.trim()} aria-label="Enviar"><Send /></Button>
      </form>
    </div>
  )
}

function ExecutionsTab({ flowId, onOpen }: { flowId: number; onOpen: (e: Execution) => void }) {
  const [items, setItems] = useState<Execution[]>([])
  const [loading, setLoading] = useState(false)
  const load = () => { setLoading(true); api.get(`/executions?flow_id=${flowId}&limit=100`).then(r => setItems(r.items)).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [flowId])
  return (
    <div className="space-y-2">
      <div className="flex justify-end"><Button variant="ghost" size="sm" onClick={load}>{loading ? <Loader2 className="animate-spin" /> : <RefreshCw />} Atualizar</Button></div>
      {items.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma execução ainda.</p>}
      {items.map(e => (
        <button key={e.id} onClick={() => onOpen(e)} className="w-full text-left rounded-2xl border border-border/60 bg-card/60 p-3 hover:border-primary/60 transition">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <StatusBadge status={e.status} />
            {e.direction === 'owner' && <Badge variant="warning"><Hand className="h-3 w-3" /> loja respondeu</Badge>}
            {e.metadata?.mode && e.metadata.mode !== 'live' && <Badge variant="outline">{e.metadata.mode === 'sim' ? 'simulação' : 'teste'}</Badge>}
            <span>{formatPhone(e.phone.replace('sim:', ''))}</span>
            <span className="ml-auto">{formatDate(e.created_at)}</span>
          </div>
          <p className="mt-1.5 text-sm line-clamp-1"><User className="inline h-3.5 w-3.5 mr-1 text-muted-foreground" />{e.content || `[${e.message_type}]`}</p>
          {e.agent_response && <p className="text-sm text-muted-foreground line-clamp-1"><Bot className="inline h-3.5 w-3.5 mr-1 text-primary" />{e.agent_response}</p>}
        </button>
      ))}
    </div>
  )
}

function ConversationsTab({ flowId }: { flowId: number }) {
  const [items, setItems] = useState<any[]>([])
  const [sel, setSel] = useState<any>(null)
  const load = () => api.get(`/flows/${flowId}/conversations`).then((list: any[]) => { setItems(list); setSel((s: any) => s && list.find(c => c.id === s.id)) })
  useEffect(() => { load() }, [flowId])
  const aiOff = (c: any) => (c.paused_until || '') >= '9999'
  const paused = (c: any) => !aiOff(c) && c.paused_until && new Date(c.paused_until.replace(' ', 'T') + 'Z') > new Date()
  const setAi = (c: any, on: boolean) => api.post(`/flows/${flowId}/conversations/${c.id}/ai`, { on }).then(load)
  return (
    <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
      <div className="space-y-2 max-h-[70vh] overflow-y-auto">
        {items.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma conversa ainda.</p>}
        {items.map(c => (
          <button key={c.id} onClick={() => setSel(c)} className={cn('w-full text-left rounded-2xl border p-3 transition', sel?.id === c.id ? 'border-primary bg-primary/5' : 'border-border/60 hover:border-border')}>
            <div className="flex items-center gap-2">
              <p className="text-sm font-medium truncate flex-1">{c.customer_name || formatPhone(c.phone.replace(/^(sim|teste):/, ''))}</p>
              {paused(c) && <Badge variant="warning">loja atendendo</Badge>}
              {aiOff(c) && <Badge variant="muted">IA desligada</Badge>}
              {c.phone.startsWith('sim:') && <Badge variant="outline">simulação</Badge>}
            </div>
            <p className="text-xs text-muted-foreground mt-1">{c.history.length} mensagens · {formatDate(c.updated_at)}</p>
          </button>
        ))}
      </div>
      <Card className="p-4 min-h-[300px] max-h-[70vh] overflow-y-auto">
        {!sel && <p className="text-sm text-muted-foreground">Selecione uma conversa.</p>}
        {sel && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-border/60">
              <p className="font-semibold flex-1">{sel.customer_name || formatPhone(sel.phone)}</p>
              {paused(sel) && <Button size="sm" variant="outline" onClick={() => api.post(`/flows/${flowId}/conversations/${sel.id}/resume`).then(load)}><Bot /> Devolver para a IA</Button>}
              {aiOff(sel)
                ? <Button size="sm" variant="outline" onClick={() => setAi(sel, true)}><Bot /> Ligar a IA neste contato</Button>
                : <Button size="sm" variant="ghost" onClick={() => setAi(sel, false)}><Hand /> Desligar a IA neste contato</Button>}
              <Button size="sm" variant="ghost" onClick={() => confirm('Apagar o histórico desta conversa? O cliente volta a ser tratado como novo.') && api.delete(`/flows/${flowId}/conversations/${sel.id}`).then(() => { setSel(null); load() })}><Trash2 /> Reiniciar</Button>
            </div>
            {sel.history.map((m: any, i: number) => (
              <div key={i} className={cn('flex', m.role === 'user' ? 'justify-start' : 'justify-end')}>
                <p className={cn('max-w-[80%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm break-words',
                  m.role === 'user' ? 'rounded-bl-sm bg-muted' : m.content.startsWith('[Resposta da equipe') ? 'rounded-br-sm bg-amber-500/15 text-amber-200' : 'rounded-br-sm bg-primary/15')}>
                  {m.content}
                </p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

function MenuTab({ flowId }: { flowId: number }) {
  const [menu, setMenu] = useState<any[]>([])
  const [item, setItem] = useState({ category: '', name: '', description: '', price: '' })
  const load = () => api.get(`/flows/${flowId}/menu`).then(setMenu)
  useEffect(() => { load() }, [flowId])
  async function add(e: React.FormEvent) {
    e.preventDefault()
    await api.post(`/flows/${flowId}/menu`, { ...item, price: Number(item.price.replace(',', '.')) })
    setItem({ ...item, name: '', description: '', price: '' }); load()
  }
  return (
    <div className="space-y-4 max-w-3xl">
      <form onSubmit={add} className="grid gap-2 sm:grid-cols-[1fr_1.4fr_1.6fr_100px_auto] items-end rounded-2xl border border-border/60 bg-card/60 p-3">
        <Input value={item.category} onChange={e => setItem({ ...item, category: e.target.value })} placeholder="Categoria" />
        <Input value={item.name} onChange={e => setItem({ ...item, name: e.target.value })} placeholder="Nome" required />
        <Input value={item.description} onChange={e => setItem({ ...item, description: e.target.value })} placeholder="Descrição" />
        <Input value={item.price} onChange={e => setItem({ ...item, price: e.target.value })} placeholder="Preço" inputMode="decimal" required />
        <Button type="submit"><Plus /> Adicionar</Button>
      </form>
      {menu.length === 0 && <p className="text-sm text-muted-foreground">Cardápio vazio. O agente usa estes itens para anotar pedidos e calcular o Pix.</p>}
      {menu.map(cat => (
        <div key={cat.name} className="space-y-1.5">
          <p className="text-sm font-semibold text-muted-foreground">{cat.name}</p>
          {cat.items.map((it: any) => (
            <div key={it.id} className="flex items-center gap-3 rounded-xl border border-border/60 px-3 py-2 text-sm">
              <span className="flex-1">{it.name}{it.description && <span className="text-muted-foreground"> — {it.description}</span>}</span>
              <span className="font-medium text-primary">R$ {it.price.toFixed(2).replace('.', ',')}</span>
              <Button variant="ghost" size="icon" onClick={() => api.delete(`/menu/${it.id}`).then(load)} aria-label="Remover item"><Trash2 /></Button>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

const SOURCE_LABEL: Record<string, string> = {
  painel: 'painel', whatsapp: 'WhatsApp do admin', criacao: 'criação', desfazer: 'desfazer', restaurado: 'restaurado', cliente: 'tela da loja', original: 'original',
}

function VersionsTab({ flowId, onRestored }: { flowId: number; onRestored: (cfg: FlowConfig) => void }) {
  const [items, setItems] = useState<any[]>([])
  const load = () => api.get(`/flows/${flowId}/versions`).then(setItems)
  useEffect(() => { load() }, [flowId])
  async function restore(id: number) {
    if (!confirm('Voltar o fluxo para esta versão?')) return
    const r = await api.post(`/flows/${flowId}/versions/${id}/restore`)
    onRestored(r.config); load()
  }
  return (
    <div className="space-y-2 max-w-3xl">
      {items.map((v, i) => (
        <div key={v.id} className="flex items-center gap-3 rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{v.note || SOURCE_LABEL[v.source] || v.source}</p>
            <p className="text-xs text-muted-foreground">{formatDate(v.created_at)} · {SOURCE_LABEL[v.source] || v.source}</p>
          </div>
          {i === 0 ? <Badge variant="success">atual</Badge> : <Button size="sm" variant="outline" onClick={() => restore(v.id)}><History /> Voltar para esta</Button>}
        </div>
      ))}
    </div>
  )
}

export default function FlowEditor() {
  const { id } = useParams()
  const flowId = Number(id)
  const [flow, setFlow] = useState<Flow | null>(null)
  const [cfg, setCfg] = useState<FlowConfig | null>(null)
  const [tab, setTab] = useState<Tab>('fluxo')
  const [selected, setSelected] = useState<NodeId | null>(null)
  const [panel, setPanel] = useState<'node' | 'test' | 'exec' | null>(null)
  const [steps, setSteps] = useState<Step[]>([])
  const [execution, setExecution] = useState<Execution | null>(null)
  const [connections, setConnections] = useState<any[]>([])
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const desktop = useIsDesktop()

  const load = () => api.get(`/flows/${flowId}`).then((f: Flow) => { setFlow(f); setCfg(f.config) })
  useEffect(() => { load(); api.get('/connections').then(setConnections) }, [flowId])

  const dirty = !!flow && !!cfg && JSON.stringify(cfg) !== JSON.stringify(flow.config)
  const status = useMemo(() => stepsToStatus(steps), [steps])
  const graph = useMemo(() => cfg ? buildGraph(cfg, { whatsapp: flow?.whatsapp }, status, panel === 'node' ? selected : null) : null, [cfg, flow, status, selected, panel])

  function flash(text: string) { setMessage(text); setTimeout(() => setMessage(''), 3000) }

  async function save() {
    if (!cfg) return
    setSaving(true); setError('')
    try {
      const r = await api.put(`/flows/${flowId}`, { config: cfg })
      setFlow(f => f && { ...f, config: r.config }); setCfg(r.config); flash('Salvo')
    } catch (e: any) { setError(e.message) } finally { setSaving(false) }
  }
  async function undo() {
    try { const r = await api.post(`/flows/${flowId}/undo`); await load(); flash(r.message) } catch (e: any) { setError(e.message) }
  }
  async function toggle() {
    await api.put(`/flows/${flowId}/toggle`); load()
  }
  async function setConnection(connection_id: number | null) {
    await api.put(`/flows/${flowId}`, { connection_id }); load()
  }
  function applyServerConfig(c: FlowConfig) { setFlow(f => f && { ...f, config: c }); setCfg(c) }

  if (!flow || !cfg || !graph) return <p className="text-muted-foreground flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Carregando...</p>

  const panelTitle = panel === 'test' ? 'Testar' : panel === 'exec' ? 'Execução' : selected ? NODE_TITLE[selected] : ''

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/flows" className="p-2 rounded-xl hover:bg-muted" aria-label="Voltar"><ArrowLeft className="h-5 w-5" /></Link>
        <div className="min-w-0">
          <h1 className="text-xl md:text-2xl font-bold tracking-tight truncate">{flow.name}</h1>
          <div className="flex flex-wrap items-center gap-2 mt-1">
            <Badge variant={flow.whatsapp?.status === 'connected' ? 'success' : 'muted'}>WhatsApp {flow.whatsapp?.status === 'connected' ? formatPhone(flow.whatsapp.phone) : 'desconectado'}</Badge>
            <label className="flex items-center gap-2 text-xs text-muted-foreground"><Switch checked={flow.active} onCheckedChange={toggle} /> {flow.active ? 'Ligado' : 'Desligado'}</label>
          </div>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          {message && <span className="text-sm text-emerald-500">{message}</span>}
          <Button variant="outline" size="sm" onClick={() => { setTab('fluxo'); setPanel('test') }}><FlaskConical /> Testar</Button>
          <Button variant="ghost" size="sm" onClick={undo}><Undo2 /> Desfazer</Button>
          <Button size="sm" onClick={save} disabled={!dirty || saving}>{saving ? <Loader2 className="animate-spin" /> : <Save />} {dirty ? 'Salvar' : 'Salvo'}</Button>
        </div>
      </div>
      <ErrorText>{error}</ErrorText>

      <Tabs value={tab} onChange={setTab} items={[
        { value: 'fluxo', label: <><Workflow /> Fluxo</> },
        { value: 'execucoes', label: <><ListChecks /> Execuções</> },
        { value: 'conversas', label: <><MessagesSquare /> Conversas</> },
        ...(cfg.order_mode === 'pix' ? [{ value: 'cardapio' as Tab, label: <><UtensilsCrossed /> Cardápio</> }] : []),
        { value: 'versoes', label: <><History /> Versões</> },
      ]} />

      {tab === 'fluxo' && (
        <div className="relative">
          <div className="space-y-2 md:hidden">
            {NODE_DEFS.map(d => {
              const run = status[d.id]
              const Icon = d.icon
              const RunIcon = run ? STEP_ICON[run.status] : null
              return (
                <button key={d.id} onClick={() => { setSelected(d.id); setPanel('node') }}
                  className={cn('flex w-full items-start gap-3 rounded-2xl border bg-card/80 p-3 text-left', d.id.startsWith('m_') && 'ml-6 w-[calc(100%-1.5rem)]',
                    run ? (run.status === 'ok' ? 'border-emerald-500/60' : run.status === 'error' ? 'border-red-500/60' : run.status === 'stop' ? 'border-amber-500/60' : 'border-border') : 'border-border/60',
                    steps.length > 0 && !run && 'opacity-40')}>
                  <span className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/15', d.color || 'text-primary')}><Icon className="h-5 w-5" /></span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold">{d.title}</p>
                    <p className="text-xs text-muted-foreground">{d.summary(cfg, { whatsapp: flow.whatsapp })}</p>
                    {run && run.info.length > 0 && <p className={cn('mt-1 text-xs', STEP_COLOR[run.status])}>{run.info.join(' · ')}</p>}
                  </div>
                  {RunIcon && <RunIcon className={cn('h-4 w-4 shrink-0', STEP_COLOR[run!.status])} />}
                </button>
              )
            })}
          </div>
          {desktop && <div className="relative hidden md:block h-[calc(100vh-230px)] min-h-[520px] rounded-2xl border border-border/60 bg-card/30 overflow-hidden">
            <ReactFlow
              nodes={graph.nodes}
              edges={graph.edges}
              nodeTypes={nodeTypes}
              onNodeClick={(_, n) => { setSelected(n.id as NodeId); setPanel('node') }}
              onPaneClick={() => panel === 'node' && setPanel(null)}
              nodesDraggable={false}
              nodesConnectable={false}
              fitView
              fitViewOptions={{ padding: 0.08, maxZoom: 1 }}
              minZoom={0.2}
              proOptions={{ hideAttribution: true }}
            >
              <Background variant={BackgroundVariant.Dots} gap={22} size={1.2} color="hsl(220 13% 28%)" />
              <Controls showInteractive={false} />
              <ViewportControl panel={panel} selected={selected} />
            </ReactFlow>
            {steps.length > 0 && (
              <button onClick={() => { setSteps([]); setExecution(null); if (panel === 'exec') setPanel(null) }}
                className="absolute left-3 top-3 rounded-full border border-border/60 bg-card/90 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground">
                Limpar caminho destacado
              </button>
            )}
            {!panel && steps.length === 0 && (
              <p className="absolute left-3 top-3 rounded-full border border-border/60 bg-card/90 px-3 py-1.5 text-xs text-muted-foreground">Clique num bloco para configurar</p>
            )}
          </div>}
          {panel && (
            <aside className="fixed inset-0 z-40 bg-background p-4 md:absolute md:inset-auto md:right-3 md:top-3 md:bottom-3 md:z-10 md:w-[420px] md:max-w-[calc(100%-1.5rem)] md:bg-transparent md:p-0">
              <Card className="flex h-full flex-col bg-card/95 backdrop-blur-xl border-border/60 p-4 shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-border/60 mb-3">
                  <p className="font-semibold">{panelTitle}</p>
                  <Button variant="ghost" size="icon" onClick={() => setPanel(null)} aria-label="Fechar"><X /></Button>
                </div>
                <div className="flex-1 min-h-0 overflow-y-auto pr-1">
                  {panel === 'node' && selected && (
                    <NodePanel node={selected} flow={flow} cfg={cfg} set={patch => setCfg(c => c && { ...c, ...patch })} dirty={dirty}
                      connections={connections} setConnection={setConnection} onTaught={applyServerConfig} />
                  )}
                  {panel === 'test' && <TestPanel flow={flow} dirty={dirty} onSteps={setSteps} />}
                  {panel === 'exec' && execution && (
                    <div className="space-y-4">
                      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground items-center">
                        <StatusBadge status={execution.status} /> {formatPhone(execution.phone)} · {formatDate(execution.created_at)}
                      </div>
                      <div className="space-y-2">
                        <p className="rounded-2xl rounded-bl-sm bg-muted px-3 py-2 text-sm whitespace-pre-wrap">{execution.content || `[${execution.message_type}]`}</p>
                        {execution.agent_response && <p className="rounded-2xl rounded-br-sm bg-primary/15 px-3 py-2 text-sm whitespace-pre-wrap">{execution.agent_response}</p>}
                      </div>
                      <StepList steps={execution.metadata?.steps || []} />
                      {execution.metadata?.error && <ErrorText>{execution.metadata.error}</ErrorText>}
                    </div>
                  )}
                </div>
                {panel === 'node' && dirty && (
                  <div className="pt-3 border-t border-border/60 mt-3 flex gap-2">
                    <Button className="flex-1" onClick={save} disabled={saving}><Save /> Salvar alterações</Button>
                    <Button variant="ghost" onClick={() => setCfg(flow.config)}>Descartar</Button>
                  </div>
                )}
              </Card>
            </aside>
          )}
        </div>
      )}
      {tab === 'execucoes' && <ExecutionsTab flowId={flowId} onOpen={e => { setExecution(e); setSteps(e.metadata?.steps || []); setPanel('exec'); setTab('fluxo') }} />}
      {tab === 'conversas' && <ConversationsTab flowId={flowId} />}
      {tab === 'cardapio' && <MenuTab flowId={flowId} />}
      {tab === 'versoes' && <VersionsTab flowId={flowId} onRestored={applyServerConfig} />}
    </div>
  )
}
