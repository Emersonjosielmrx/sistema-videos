import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Link2, QrCode, MessageCircleQuestion, CalendarCheck, Printer, ListChecks, Workflow, ArrowRight, Trash2, X, Loader2 } from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Card, Field, Input, PageTitle, Select, Switch, Textarea, ErrorText } from '../components/ui'
import { cn } from '../lib/utils'
import type { Flow } from '../flow/types'

type Template = { key: string; label: string; description: string; order_mode: string }
const ICONS: Record<string, React.ElementType> = { delivery_link: Link2, delivery_pix: QrCode, atendimento: MessageCircleQuestion, agendamento: CalendarCheck, servicos: Printer, servicos_menu: ListChecks }
const MODE_LABEL: Record<string, string> = { link: 'Link do cardápio', pix: 'Pedido + Pix', none: 'Atendimento', agendamento: 'Agendamento' }

function NewFlow({ onClose, connections }: { onClose: () => void; connections: any[] }) {
  const navigate = useNavigate()
  const [templates, setTemplates] = useState<Template[]>([])
  const [template, setTemplate] = useState('delivery_link')
  const [name, setName] = useState('')
  const [fields, setFields] = useState<Record<string, string>>({})
  const [connection, setConnection] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { api.get('/templates').then(setTemplates) }, [])
  const f = (k: string) => fields[k] || ''
  const setF = (k: string, v: string) => setFields({ ...fields, [k]: v })

  async function create(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const r = await api.post('/flows', { name, template, connection_id: connection ? Number(connection) : null, fields })
      navigate(`/flows/${r.id}`)
    } catch (err: any) { setError(err.message); setBusy(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/70 p-4">
      <Card className="relative w-full max-w-2xl my-8 p-6 bg-card">
        <button onClick={onClose} className="absolute right-4 top-4 p-2 rounded-xl hover:bg-muted" aria-label="Fechar"><X className="h-5 w-5" /></button>
        <h2 className="text-xl font-bold">Novo fluxo</h2>
        <p className="text-sm text-muted-foreground mt-1">Escolha o tipo. Prompt, botões, regras de áudio/imagem e o resto já vêm prontos e você ajusta depois.</p>
        <form onSubmit={create} className="mt-5 space-y-5">
          <div className="grid gap-3 sm:grid-cols-2">
            {templates.map(t => {
              const Icon = ICONS[t.key] || Workflow
              return (
                <button type="button" key={t.key} onClick={() => setTemplate(t.key)}
                  className={cn('rounded-2xl border p-4 text-left transition', template === t.key ? 'border-primary bg-primary/10 shadow-glow' : 'border-border/60 hover:border-border')}>
                  <Icon className="h-5 w-5 text-primary" />
                  <p className="mt-2 font-semibold text-sm">{t.label}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{t.description}</p>
                </button>
              )
            })}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Nome da loja / empresa"><Input value={name} onChange={e => setName(e.target.value)} required placeholder="Castanhal Burger" /></Field>
            <Field label="WhatsApp (opcional)" hint="A loja também pode conectar pela tela dela.">
              <Select value={connection} onChange={e => setConnection(e.target.value)}>
                <option value="">Conectar depois</option>
                {connections.map(c => <option key={c.id} value={c.id}>{c.label || c.session_id}</option>)}
              </Select>
            </Field>
            {template === 'delivery_link' && (
              <Field label="Link do cardápio" className="sm:col-span-2"><Input value={f('menu_url')} onChange={e => setF('menu_url', e.target.value)} placeholder="https://pedido.anota.ai/loja/..." required /></Field>
            )}
            {template === 'delivery_pix' && (<>
              <Field label="Chave Pix"><Input value={f('pix_key')} onChange={e => setF('pix_key', e.target.value)} required /></Field>
              <Field label="Cidade"><Input value={f('store_city')} onChange={e => setF('store_city', e.target.value)} required /></Field>
            </>)}
            {(template === 'servicos' || template === 'servicos_menu') && (
              <Field label="Chave Pix (opcional)" className="sm:col-span-2" hint="Com o nome do titular, do jeito que o cliente deve ver.">
                <Input value={f('pix_key')} onChange={e => setF('pix_key', e.target.value)} placeholder="91 98888-7777 (celular), titular Fulano" />
              </Field>
            )}
            {(template === 'atendimento' || template === 'agendamento' || template.startsWith('servicos')) && (
              <Field label={template.startsWith('servicos') ? 'Tabela de serviços e valores' : 'O que o agente precisa saber'} className="sm:col-span-2"
                hint={template.startsWith('servicos') ? 'Um serviço por linha, com o preço. O botão "Tabela de preços" manda este texto.' : 'Serviços, preços, perguntas frequentes. Dá para completar depois.'}>
                <Textarea rows={template.startsWith('servicos') ? 8 : 4} value={f('business_info')} onChange={e => setF('business_info', e.target.value)} />
              </Field>
            )}
            <Field label="Endereço (opcional)"><Input value={f('store_address')} onChange={e => setF('store_address', e.target.value)} /></Field>
            <Field label="Horário (opcional)"><Input value={f('store_hours')} onChange={e => setF('store_hours', e.target.value)} placeholder="Todos os dias das 18h às 23h30" /></Field>
          </div>
          <ErrorText>{error}</ErrorText>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={busy}>{busy ? <Loader2 className="animate-spin" /> : <Plus />} Criar e abrir o editor</Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

export default function Flows() {
  const [flows, setFlows] = useState<Flow[] | null>(null)
  const [connections, setConnections] = useState<any[]>([])
  const [creating, setCreating] = useState(false)
  const load = () => { api.get('/flows').then(setFlows); api.get('/connections').then(setConnections) }
  useEffect(() => { load() }, [])

  async function remove(f: Flow) {
    if (!confirm(`Apagar o fluxo "${f.name}"? Execuções, conversas e pedidos dele também são apagados.`)) return
    await api.delete(`/flows/${f.id}`); load()
  }

  return (
    <div>
      <PageTitle title="Fluxos" sub="Cada fluxo é o atendimento de um WhatsApp.">
        <Button onClick={() => setCreating(true)}><Plus /> Novo fluxo</Button>
      </PageTitle>
      {creating && <NewFlow onClose={() => setCreating(false)} connections={connections} />}
      {flows?.length === 0 && (
        <Card className="bg-glass p-8 text-center">
          <Workflow className="mx-auto h-8 w-8 text-primary" />
          <p className="mt-3 font-semibold">Nenhum fluxo ainda</p>
          <p className="text-sm text-muted-foreground">Crie o primeiro a partir de um modelo.</p>
        </Card>
      )}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {flows?.map(f => {
          const Icon = ICONS[f.template] || Workflow
          return (
            <Card key={f.id} className="group relative overflow-hidden bg-glass border-border/50 p-5 transition-all hover:-translate-y-1 hover:shadow-xl">
              <div className="absolute -top-8 -right-8 h-24 w-24 rounded-full bg-primary/10 blur-2xl transition-transform group-hover:scale-150" />
              <div className="relative flex items-start gap-3">
                <span className="inline-flex rounded-xl bg-primary/15 p-2.5 shadow-glow"><Icon className="h-5 w-5 text-primary" /></span>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold truncate">{f.name}</p>
                  <p className="text-xs text-muted-foreground">{MODE_LABEL[f.config.order_mode]}</p>
                </div>
                <Switch checked={f.active} onCheckedChange={() => api.put(`/flows/${f.id}/toggle`).then(load)} aria-label="Ligar ou desligar" />
              </div>
              <div className="relative mt-4 flex flex-wrap gap-1.5">
                <Badge variant={f.active ? 'success' : 'muted'}>{f.active ? 'Ligado' : 'Desligado'}</Badge>
                {f.config.buttons_enabled && <Badge variant="outline">{f.config.buttons.length} botões</Badge>}
                {f.config.learned_rules.length > 0 && <Badge variant="outline">{f.config.learned_rules.length} regras</Badge>}
                {f.config.hours_enabled && <Badge variant="outline">horário</Badge>}
              </div>
              <div className="relative mt-4 flex items-center gap-2">
                <Link to={`/flows/${f.id}`} className="flex-1"><Button className="w-full">Abrir editor <ArrowRight /></Button></Link>
                <Button variant="ghost" size="icon" onClick={() => remove(f)} aria-label="Apagar fluxo"><Trash2 /></Button>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
