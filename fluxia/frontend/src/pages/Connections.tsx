import { useState, useEffect } from 'react'
import { Plus, Smartphone, Trash2, Info } from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Card, Field, Input, PageTitle, ErrorText } from '../components/ui'

export default function Connections() {
  const [connections, setConnections] = useState<any[]>([])
  const [status, setStatus] = useState<Record<number, any>>({})
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ session_id: '', hermes_url: '', api_key: '', label: '' })
  const [error, setError] = useState('')

  const load = () => api.get('/connections').then((list: any[]) => {
    setConnections(list)
    list.forEach(c => api.get(`/connections/${c.id}/status`).then(s => setStatus(st => ({ ...st, [c.id]: s }))))
  })
  useEffect(() => { load() }, [])

  async function create(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try { await api.post('/connections', form) } catch (err: any) { setError(err.message); return }
    setShowForm(false)
    setForm({ session_id: '', hermes_url: form.hermes_url, api_key: '', label: '' })
    load()
  }

  return (
    <div className="space-y-4">
      <PageTitle title="WhatsApp" sub="Sessões do Hermes ligadas ao FluxIA">
        <Button onClick={() => setShowForm(!showForm)}><Plus /> Ligar sessão existente</Button>
      </PageTitle>
      <p className="flex gap-2 rounded-xl bg-muted/50 px-3 py-2 text-sm text-muted-foreground max-w-3xl">
        <Info className="h-4 w-4 shrink-0 mt-0.5" />
        Normalmente você não precisa desta tela: quando a loja conecta o número pela tela dela, a sessão é criada sozinha. Use aqui só para ligar uma sessão que já existe no Hermes.
      </p>
      {showForm && (
        <Card className="bg-glass border-border/50 p-5">
          <form onSubmit={create} className="grid gap-3 sm:grid-cols-2">
            <Field label="ID da sessão no Hermes"><Input value={form.session_id} onChange={e => setForm({ ...form, session_id: e.target.value })} required placeholder="sess-..." /></Field>
            <Field label="Apelido"><Input value={form.label} onChange={e => setForm({ ...form, label: e.target.value })} /></Field>
            <Field label="URL do Hermes (vazio = Configurações)"><Input value={form.hermes_url} onChange={e => setForm({ ...form, hermes_url: e.target.value })} /></Field>
            <Field label="Chave de API (vazio = Configurações)"><Input type="password" value={form.api_key} onChange={e => setForm({ ...form, api_key: e.target.value })} /></Field>
            <div className="sm:col-span-2 space-y-2">
              <Button type="submit">Ligar</Button>
              <ErrorText>{error}</ErrorText>
            </div>
          </form>
        </Card>
      )}
      <div className="grid gap-3 md:grid-cols-2">
        {connections.length === 0 && <p className="text-sm text-muted-foreground">Nenhuma sessão ligada.</p>}
        {connections.map(c => {
          const s = status[c.id]
          return (
            <Card key={c.id} className="bg-glass border-border/50 p-4 flex items-center gap-3">
              <span className="inline-flex rounded-xl bg-primary/15 p-2.5"><Smartphone className="h-5 w-5 text-primary" /></span>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{c.label || c.session_id}</p>
                <p className="text-xs text-muted-foreground truncate">{c.session_id}</p>
              </div>
              {s && <Badge variant={s.status === 'connected' ? 'success' : s.status === 'offline' ? 'warning' : 'muted'}>{s.status === 'connected' ? 'conectado' : s.status === 'offline' ? 'sem sinal' : s.status === 'unknown' ? '?' : 'desconectado'}</Badge>}
              <Button variant="ghost" size="icon" onClick={() => confirm('Remover esta sessão do FluxIA? (não apaga no Hermes)') && api.delete(`/connections/${c.id}`).then(load)} aria-label="Remover"><Trash2 /></Button>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
