import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Workflow, Smartphone, Activity, AlertTriangle, ShoppingBag, Hand, ArrowRight, Loader2 } from 'lucide-react'
import { api } from '../api'
import { Badge, Card, PageTitle } from '../components/ui'
import { cn, formatDate, formatPhone } from '../lib/utils'
import type { Execution, Flow } from '../flow/types'

function StatCard({ icon: Icon, label, value, color = '#10b981', warn }: { icon: React.ElementType; label: string; value: number; color?: string; warn?: boolean }) {
  return (
    <Card className={cn('relative overflow-hidden bg-glass border-border/50 p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl group', warn && value > 0 && 'border-red-500/40')}>
      <div className="absolute top-0 right-0 w-24 h-24 bg-primary/10 rounded-full blur-2xl -mr-8 -mt-8 transition-transform group-hover:scale-150" />
      <div className="relative inline-flex rounded-xl bg-primary/15 p-2.5 mb-4 shadow-glow"><Icon className="h-5 w-5" style={{ color }} /></div>
      <p className="relative text-sm font-medium text-muted-foreground">{label}</p>
      <p className="relative text-3xl font-bold tracking-tight mt-1">{value}</p>
    </Card>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null)
  const [flows, setFlows] = useState<Flow[]>([])
  const [recent, setRecent] = useState<Execution[]>([])
  const [events, setEvents] = useState<any[]>([])

  useEffect(() => {
    api.get('/dashboard').then(setStats)
    api.get('/flows').then(setFlows)
    api.get('/executions?limit=8').then(r => setRecent(r.items))
    api.get('/events?limit=10').then(setEvents)
  }, [])

  if (!stats) return <p className="text-muted-foreground flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Carregando...</p>

  return (
    <div className="space-y-6">
      <PageTitle title="Visão geral" sub="Como estão os atendimentos hoje" />
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard icon={Workflow} label="Fluxos ligados" value={stats.flows} />
        <StatCard icon={Smartphone} label="WhatsApps" value={stats.connections} color="#38bdf8" />
        <StatCard icon={Activity} label="Atendimentos hoje" value={stats.today_executions} color="#a78bfa" />
        <StatCard icon={AlertTriangle} label="Erros hoje" value={stats.today_errors} color="#f87171" warn />
        <StatCard icon={Hand} label="Loja atendendo" value={stats.paused_conversations} color="#fbbf24" />
        <StatCard icon={ShoppingBag} label="Pedidos pendentes" value={stats.pending_orders} color="#fb923c" />
      </div>
      {events.length > 0 && (
        <Card className="bg-glass border-border/50 p-5">
          <p className="font-semibold mb-3 flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-amber-400" /> Eventos recentes</p>
          <div className="space-y-1.5">
            {events.map(ev => (
              <div key={ev.id} className="flex gap-3 rounded-xl border border-border/60 px-3 py-2 text-sm">
                <span className="shrink-0 text-xs text-muted-foreground pt-0.5 w-24">{formatDate(ev.created_at)}</span>
                <span className="shrink-0 font-medium">{ev.kind}</span>
                <span className="text-muted-foreground break-words min-w-0">{ev.detail}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="bg-glass border-border/50 p-5">
          <p className="font-semibold mb-3">Fluxos</p>
          <div className="space-y-2">
            {flows.length === 0 && <p className="text-sm text-muted-foreground">Nenhum fluxo. <Link to="/flows" className="text-primary">Criar o primeiro</Link></p>}
            {flows.map(f => (
              <Link key={f.id} to={`/flows/${f.id}`} className="flex items-center gap-3 rounded-xl border border-border/60 px-3 py-2.5 hover:border-primary/60 transition">
                <span className={cn('h-2.5 w-2.5 rounded-full', f.active ? 'bg-emerald-500 animate-pulse-glow' : 'bg-muted-foreground/40')} />
                <span className="flex-1 text-sm font-medium truncate">{f.name}</span>
                <Badge variant={f.active ? 'success' : 'muted'}>{f.active ? 'ligado' : 'desligado'}</Badge>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </Link>
            ))}
          </div>
        </Card>
        <Card className="bg-glass border-border/50 p-5">
          <div className="flex items-center justify-between mb-3">
            <p className="font-semibold">Últimas execuções</p>
            <Link to="/executions" className="text-xs text-primary">ver todas</Link>
          </div>
          <div className="space-y-2">
            {recent.length === 0 && <p className="text-sm text-muted-foreground">Nada ainda.</p>}
            {recent.map(e => (
              <Link key={e.id} to={`/flows/${e.flow_id}`} className="block rounded-xl border border-border/60 px-3 py-2 hover:border-primary/60 transition">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className={cn('h-2 w-2 rounded-full', e.status === 'ok' ? 'bg-emerald-500' : e.status === 'error' ? 'bg-red-500' : 'bg-muted-foreground/50')} />
                  <span className="truncate">{e.flow_name} · {formatPhone(e.phone.replace('sim:', ''))}</span>
                  <span className="ml-auto shrink-0">{formatDate(e.created_at)}</span>
                </div>
                <p className="text-sm mt-1 line-clamp-1">{e.content || `[${e.message_type}]`}</p>
              </Link>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
