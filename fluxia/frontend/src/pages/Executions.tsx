import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { RefreshCw, Loader2, Bot, User, Hand, ArrowRight, X, CheckCircle2, XCircle, StopCircle, MinusCircle } from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Card, PageTitle, Select } from '../components/ui'
import { cn, formatDate, formatPhone } from '../lib/utils'
import type { Execution, Flow, Step } from '../flow/types'

const ICON = { ok: CheckCircle2, error: XCircle, stop: StopCircle, skip: MinusCircle }
const COLOR = { ok: 'text-emerald-400', error: 'text-red-400', stop: 'text-amber-400', skip: 'text-muted-foreground' }
const NODE: Record<string, string> = {
  trigger: 'Mensagem recebida', filter: 'Loja assumiu?', hours: 'Horário', buffer: 'Agrupar', media: 'Tipo de mensagem',
  agent: 'Agente IA', actions: 'Ações', send: 'Enviar', buttons: 'Botões',
}

export default function Executions() {
  const [items, setItems] = useState<Execution[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [flows, setFlows] = useState<Flow[]>([])
  const [flowId, setFlowId] = useState('')
  const [status, setStatus] = useState('')
  const [sel, setSel] = useState<Execution | null>(null)
  const [loading, setLoading] = useState(false)
  const limit = 30

  const load = () => {
    setLoading(true)
    const q = new URLSearchParams({ limit: String(limit), offset: String(page * limit) })
    if (flowId) q.set('flow_id', flowId)
    if (status) q.set('status', status)
    api.get(`/executions?${q}`).then(d => { setItems(d.items); setTotal(d.total) }).finally(() => setLoading(false))
  }
  useEffect(() => { api.get('/flows').then(setFlows) }, [])
  useEffect(() => { load() }, [page, flowId, status])

  return (
    <div>
      <PageTitle title="Execuções" sub="Cada mensagem atendida, com o caminho que percorreu no fluxo">
        <Button variant="ghost" size="sm" onClick={load}>{loading ? <Loader2 className="animate-spin" /> : <RefreshCw />} Atualizar</Button>
      </PageTitle>
      <div className="flex flex-wrap gap-2 mb-4">
        <Select value={flowId} onChange={e => { setPage(0); setFlowId(e.target.value) }} className="w-auto">
          <option value="">Todos os fluxos</option>
          {flows.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
        </Select>
        <Select value={status} onChange={e => { setPage(0); setStatus(e.target.value) }} className="w-auto">
          <option value="">Todos</option>
          <option value="ok">Respondidas</option>
          <option value="error">Com erro</option>
          <option value="skip">Sem resposta</option>
        </Select>
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr_420px]">
        <div className="space-y-2">
          {items.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma execução.</p>}
          {items.map(e => (
            <button key={e.id} onClick={() => setSel(e)} className={cn('w-full text-left rounded-2xl border bg-card/60 p-3 transition', sel?.id === e.id ? 'border-primary' : 'border-border/60 hover:border-primary/60')}>
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span className={cn('h-2 w-2 rounded-full', e.status === 'ok' ? 'bg-emerald-500' : e.status === 'error' ? 'bg-red-500' : 'bg-muted-foreground/50')} />
                <span className="font-medium text-foreground">{e.flow_name}</span>
                {e.direction === 'owner' && <Badge variant="warning"><Hand className="h-3 w-3" /> loja respondeu</Badge>}
                {e.metadata?.mode && e.metadata.mode !== 'live' && <Badge variant="outline">{e.metadata.mode === 'sim' ? 'simulação' : 'teste'}</Badge>}
                <span>{formatPhone(e.phone.replace('sim:', ''))}</span>
                {e.metadata?.response_ms !== undefined && (
                  <span className={cn(e.metadata.response_ms > 30000 && 'text-amber-400')}>respondeu em {Math.round(e.metadata.response_ms / 1000)} s</span>
                )}
                <span className="ml-auto">{formatDate(e.created_at)}</span>
              </div>
              <p className="mt-1.5 text-sm line-clamp-1"><User className="inline h-3.5 w-3.5 mr-1 text-muted-foreground" />{e.content || `[${e.message_type}]`}</p>
              {e.agent_response && <p className="text-sm text-muted-foreground line-clamp-1"><Bot className="inline h-3.5 w-3.5 mr-1 text-primary" />{e.agent_response}</p>}
            </button>
          ))}
          {total > limit && (
            <div className="flex items-center justify-between pt-2 text-sm">
              <Button variant="ghost" size="sm" disabled={page === 0} onClick={() => setPage(p => p - 1)}>Anterior</Button>
              <span className="text-muted-foreground">{page * limit + 1}–{Math.min(total, (page + 1) * limit)} de {total}</span>
              <Button variant="ghost" size="sm" disabled={(page + 1) * limit >= total} onClick={() => setPage(p => p + 1)}>Próxima</Button>
            </div>
          )}
        </div>
        {sel && (
          <Card className="bg-glass border-border/60 p-4 space-y-4 h-fit lg:sticky lg:top-4 fixed inset-x-4 bottom-4 top-20 z-40 overflow-y-auto lg:static lg:inset-auto">
            <div className="flex items-center justify-between">
              <p className="font-semibold">Execução #{sel.id}</p>
              <Button variant="ghost" size="icon" onClick={() => setSel(null)} aria-label="Fechar"><X /></Button>
            </div>
            <p className="rounded-2xl rounded-bl-sm bg-muted px-3 py-2 text-sm whitespace-pre-wrap">{sel.content || `[${sel.message_type}]`}</p>
            {sel.agent_response && <p className="rounded-2xl rounded-br-sm bg-primary/15 px-3 py-2 text-sm whitespace-pre-wrap">{sel.agent_response}</p>}
            <ol className="space-y-1.5">
              {(sel.metadata?.steps || []).map((s: Step, i: number) => {
                const Icon = ICON[s.status]
                return (
                  <li key={i} className="flex gap-2 text-sm">
                    <Icon className={cn('h-4 w-4 shrink-0 mt-0.5', COLOR[s.status])} />
                    <div><span className="font-medium">{NODE[s.node] || s.node}</span>{s.ms !== undefined && <span className="text-xs text-muted-foreground"> · {s.ms} ms</span>}
                      <p className="text-xs text-muted-foreground break-words">{s.info}</p></div>
                  </li>
                )
              })}
            </ol>
            <Link to={`/flows/${sel.flow_id}`}><Button variant="outline" className="w-full">Abrir o fluxo <ArrowRight /></Button></Link>
          </Card>
        )}
      </div>
    </div>
  )
}
