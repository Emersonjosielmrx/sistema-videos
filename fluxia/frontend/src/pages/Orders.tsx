import { useState, useEffect } from 'react'
import { ShoppingBag, CalendarCheck, MapPin, Phone } from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Card, PageTitle, Tabs } from '../components/ui'
import { formatDate, formatPhone } from '../lib/utils'
import type { Flow } from '../flow/types'

const LABELS: Record<string, string> = {
  pending: 'Aguardando', paid: 'Pago', preparing: 'Preparando', delivering: 'Saiu para entrega',
  done: 'Concluído', confirmed: 'Confirmado', cancelled: 'Cancelado',
}
const NEXT: Record<string, [string, string][]> = {
  pedido: [['pending', 'paid'], ['paid', 'preparing'], ['preparing', 'delivering'], ['delivering', 'done']],
  agendamento: [['pending', 'confirmed'], ['confirmed', 'done']],
}

export default function Orders() {
  const [flows, setFlows] = useState<Flow[]>([])
  const [flowId, setFlowId] = useState<string>('')
  const [orders, setOrders] = useState<any[]>([])

  useEffect(() => {
    api.get('/flows').then((list: Flow[]) => {
      const relevant = list.filter(f => f.config.order_mode === 'pix' || f.config.order_mode === 'agendamento')
      setFlows(relevant)
      if (relevant.length) setFlowId(String(relevant[0].id))
    })
  }, [])
  const load = () => flowId && api.get(`/flows/${flowId}/orders`).then(setOrders)
  useEffect(() => { load() }, [flowId])

  async function changeStatus(id: number, status: string) {
    await api.put(`/orders/${id}/status`, { status }); load()
  }

  return (
    <div>
      <PageTitle title="Pedidos e agendamentos" sub="Registrados pelo agente quando o cliente confirma" />
      {flows.length === 0 && <Card className="bg-glass p-6 text-sm text-muted-foreground">Nenhum fluxo de pedido com Pix ou agendamento. Fluxos com link de cardápio recebem os pedidos no próprio app do cardápio.</Card>}
      {flows.length > 0 && (
        <Tabs value={flowId} onChange={setFlowId} items={flows.map(f => ({ value: String(f.id), label: f.name }))} className="mb-4" />
      )}
      <div className="grid gap-3 lg:grid-cols-2">
        {orders.map(o => (
          <Card key={o.id} className="bg-glass border-border/50 p-4 space-y-2">
            <div className="flex items-center gap-2">
              {o.kind === 'agendamento' ? <CalendarCheck className="h-4 w-4 text-primary" /> : <ShoppingBag className="h-4 w-4 text-primary" />}
              <p className="font-semibold">{o.kind === 'agendamento' ? 'Agendamento' : 'Pedido'} #{o.id}</p>
              <Badge variant={o.status === 'cancelled' ? 'destructive' : o.status === 'pending' ? 'warning' : 'success'}>{LABELS[o.status] || o.status}</Badge>
              <span className="ml-auto text-xs text-muted-foreground">{formatDate(o.created_at)}</span>
            </div>
            <p className="flex items-center gap-1.5 text-sm text-muted-foreground"><Phone className="h-3.5 w-3.5" /> {formatPhone(o.customer_phone)}{o.customer_name && ` · ${o.customer_name}`}</p>
            {o.address && <p className="flex items-center gap-1.5 text-sm text-muted-foreground"><MapPin className="h-3.5 w-3.5" /> {o.address}</p>}
            <p className="text-sm whitespace-pre-wrap">{o.items}</p>
            {o.total > 0 && <p className="font-bold text-primary">R$ {Number(o.total).toFixed(2).replace('.', ',')}</p>}
            {o.pix_code && <code className="block rounded-lg bg-background/60 p-2 text-[11px] text-emerald-300 break-all">{o.pix_code}</code>}
            <div className="flex flex-wrap gap-2 pt-1">
              {(NEXT[o.kind] || NEXT.pedido).filter(([from]) => from === o.status).map(([, to]) => (
                <Button key={to} size="sm" onClick={() => changeStatus(o.id, to)}>{LABELS[to]}</Button>
              ))}
              {o.status !== 'done' && o.status !== 'cancelled' && (
                <Button size="sm" variant="ghost" className="text-destructive" onClick={() => changeStatus(o.id, 'cancelled')}>Cancelar</Button>
              )}
            </div>
          </Card>
        ))}
      </div>
      {flowId && orders.length === 0 && <p className="text-sm text-muted-foreground">Nenhum registro neste fluxo.</p>}
    </div>
  )
}
