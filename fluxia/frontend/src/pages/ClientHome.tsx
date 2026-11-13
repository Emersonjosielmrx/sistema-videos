import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Smartphone, Bot, LogOut, CheckCircle2, WifiOff, Copy, Loader2, MessageSquare, Users, Receipt, Hand,
  Clock, Bell, KeyRound, FileText, Power, QrCode,
} from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { api, clearToken } from '../api'
import { Brand } from '../components/Brand'
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, ErrorText, Field, Input, Switch, Textarea } from '../components/ui'
import HoursEditor from '../components/HoursEditor'
import { cn, formatDate, formatPhone } from '../lib/utils'

type WhatsApp = { status: 'connected' | 'offline' | 'disconnected' | 'unknown'; phone: string }
type Settings = { hours_enabled: boolean; hours: Record<string, string>; store_hours: string; closed_action: string; closed_message: string; notify_phone: string }
type ClientFlow = {
  id: number; name: string; active: boolean; whatsapp: WhatsApp; settings: Settings
  today: { messages: number; clients: number; receipts: number }
}
type Contact = { id: number; phone: string; customer_name: string; paused_until: string; updated_at: string; ai_off: boolean; last: string }
type FileItem = { id: number; phone: string; kind: string; mimetype: string; caption: string; created_at: string }

function SectionIcon({ icon: Icon, className }: { icon: React.ElementType; className?: string }) {
  return (
    <span className={cn('inline-flex rounded-xl bg-primary/15 p-2.5 shadow-glow text-primary', className)}>
      <Icon className="h-5 w-5" />
    </span>
  )
}

function Stat({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: number }) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-border/50 bg-glass p-4">
      <div className="absolute -top-6 -right-6 h-16 w-16 rounded-full bg-primary/10 blur-2xl" />
      <Icon className="h-4 w-4 text-primary" />
      <p className="mt-3 text-2xl font-bold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  )
}

function Connection({ flow, reload }: { flow: ClientFlow; reload: () => Promise<ClientFlow[]> }) {
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [qr, setQr] = useState('')
  const [qrBusy, setQrBusy] = useState(false)
  const wa = flow.whatsapp

  useEffect(() => {
    if (!code && !qr) return
    const timer = setInterval(async () => {
      const flows = await reload()
      if (flows.find(f => f.id === flow.id)?.whatsapp.status === 'connected') { setCode(''); setQr('') }
    }, 3000)
    return () => clearInterval(timer)
  }, [code, qr])

  // O QR do WhatsApp vence em ~60 s: pede outro enquanto a loja não escaneia.
  useEffect(() => {
    if (!qr) return
    const timer = setTimeout(() => loadQr(), 50000)
    return () => clearTimeout(timer)
  }, [qr])

  async function loadQr() {
    setQrBusy(true); setError('')
    try {
      const data = await api.post(`/client/flows/${flow.id}/qr`)
      setQr(data.qr); setCode('')
    } catch (err: any) {
      setError(err.message); setQr(''); reload()
    } finally { setQrBusy(false) }
  }

  async function pair(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const data = await api.post(`/client/flows/${flow.id}/pair`, { phone })
      setCode(data.code); setCopied(false)
    } catch (err: any) {
      setError(err.message); reload()
    } finally { setBusy(false) }
  }

  async function disconnect() {
    if (!confirm('Desconectar este WhatsApp? O atendimento automático para de responder até você conectar de novo.')) return
    setBusy(true); setError('')
    try { await api.post(`/client/flows/${flow.id}/disconnect`); await reload() } catch (err: any) { setError(err.message) } finally { setBusy(false) }
  }

  async function copyCode() {
    try { await navigator.clipboard.writeText(code.replace(/-/g, '')); setCopied(true) } catch { setCopied(false) }
  }

  return (
    <Card className="bg-glass border-border/50">
      <CardHeader className="flex-row items-center gap-3 space-y-0">
        <SectionIcon icon={Smartphone} />
        <div className="flex-1">
          <CardTitle>WhatsApp da loja</CardTitle>
          <CardDescription>O número que atende seus clientes</CardDescription>
        </div>
        {wa.status === 'connected' && <Badge variant="success"><CheckCircle2 className="h-3 w-3" /> Conectado</Badge>}
        {wa.status === 'offline' && <Badge variant="warning"><WifiOff className="h-3 w-3" /> Sem sinal</Badge>}
        {wa.status === 'disconnected' && <Badge variant="muted">Desconectado</Badge>}
      </CardHeader>
      <CardContent className="space-y-4">
        {wa.status === 'connected' && (
          <div className="flex items-center justify-between gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3">
            <p className="font-medium text-emerald-500">{wa.phone ? formatPhone(wa.phone) : 'Conectado'}</p>
            <Button variant="ghost" size="sm" onClick={disconnect} disabled={busy} className="text-destructive hover:bg-destructive/10 hover:text-destructive">Desconectar</Button>
          </div>
        )}
        {wa.status === 'offline' && (
          <div className="flex items-center justify-between gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
            <p className="text-sm text-amber-500">Deixe o celular ligado e com internet. Ele reconecta sozinho.</p>
            <Button variant="ghost" size="sm" onClick={disconnect} disabled={busy} className="text-destructive">Desconectar</Button>
          </div>
        )}
        {wa.status === 'unknown' && <p className="text-sm text-muted-foreground">Não consegui verificar a conexão agora. Atualize a página em instantes.</p>}
        {wa.status === 'disconnected' && !code && !qr && (
          <div className="space-y-4">
            <form onSubmit={pair} className="space-y-3">
              <Field label="Número do WhatsApp da loja (com DDD)">
                <Input type="tel" inputMode="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="(91) 98888-7777" required className="h-11 text-base" />
              </Field>
              <Button type="submit" size="lg" disabled={busy || qrBusy} className="w-full">
                {busy ? <Loader2 className="animate-spin" /> : <Smartphone />} {busy ? 'Gerando código...' : 'Conectar com código'}
              </Button>
            </form>
            <div className="flex items-center gap-3 text-xs text-muted-foreground"><span className="h-px flex-1 bg-border" />ou<span className="h-px flex-1 bg-border" /></div>
            <Button variant="outline" size="lg" className="w-full" onClick={loadQr} disabled={busy || qrBusy}>
              {qrBusy ? <Loader2 className="animate-spin" /> : <QrCode />} {qrBusy ? 'Gerando QR code...' : 'Conectar com QR code'}
            </Button>
            <p className="text-xs text-muted-foreground text-center">QR code: abra esta tela num computador ou em outro celular e escaneie com o celular da loja.</p>
          </div>
        )}
        {qr && wa.status !== 'connected' && (
          <div className="space-y-4">
            <div className="mx-auto w-fit rounded-2xl bg-white p-4 shadow-glow">
              <QRCodeSVG value={qr} size={232} />
            </div>
            <ol className="text-sm space-y-2">
              {['Abra o WhatsApp no celular da loja.',
                'Toque em ⋮ (Android) ou em Configurações (iPhone) e depois em Aparelhos conectados.',
                'Toque em Conectar aparelho e aponte a câmera para este QR code.'].map((s, i) => (
                <li key={i} className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary">{i + 1}</span>
                  <span className="text-muted-foreground pt-0.5">{s}</span>
                </li>
              ))}
            </ol>
            <p className="flex items-center justify-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Esperando a conexão... o QR se renova sozinho.</p>
            <Button variant="ghost" className="w-full" onClick={() => setQr('')}>Voltar</Button>
          </div>
        )}
        {code && wa.status !== 'connected' && (
          <div className="space-y-4">
            <div className="text-center rounded-2xl border border-primary/30 bg-primary/10 py-5">
              <p className="text-xs text-muted-foreground mb-1">Seu código</p>
              <p className="text-3xl font-mono font-bold tracking-widest text-primary">{code}</p>
              <Button variant="link" size="sm" onClick={copyCode} className="mt-1"><Copy /> {copied ? 'Copiado' : 'Copiar código'}</Button>
            </div>
            <ol className="text-sm space-y-2">
              {['Abra o WhatsApp no celular da loja.',
                'Toque em ⋮ (Android) ou em Configurações (iPhone) e depois em Aparelhos conectados.',
                'Toque em Conectar aparelho e depois em Conectar com número de telefone.',
                'Digite o código acima.'].map((s, i) => (
                <li key={i} className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary">{i + 1}</span>
                  <span className="text-muted-foreground pt-0.5">{s}</span>
                </li>
              ))}
            </ol>
            <p className="flex items-center justify-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Esperando a conexão... esta tela atualiza sozinha.</p>
            <Button variant="ghost" className="w-full" onClick={() => setCode('')}>Gerar outro código</Button>
          </div>
        )}
        <ErrorText>{error}</ErrorText>
      </CardContent>
    </Card>
  )
}

function Automation({ flow, reload }: { flow: ClientFlow; reload: () => Promise<ClientFlow[]> }) {
  const [busy, setBusy] = useState(false)
  async function toggle() {
    setBusy(true)
    try { await api.put(`/client/flows/${flow.id}/toggle`); await reload() } finally { setBusy(false) }
  }
  return (
    <Card className={cn('bg-glass border-border/50 relative overflow-hidden', flow.active && 'shadow-glow')}>
      <div className="absolute -top-10 -right-10 h-32 w-32 rounded-full bg-primary/10 blur-3xl" />
      <CardContent className="p-5 flex items-center gap-4">
        <SectionIcon icon={Bot} className={flow.active ? 'animate-pulse-glow' : 'bg-muted text-muted-foreground shadow-none'} />
        <div className="flex-1">
          <p className="font-semibold">Atendimento automático</p>
          <p className={cn('text-sm', flow.active ? 'text-emerald-500' : 'text-muted-foreground')}>
            {flow.active ? 'Ligado: respondendo seus clientes' : 'Desligado: ninguém recebe resposta automática'}
          </p>
        </div>
        <button onClick={toggle} disabled={busy} aria-pressed={flow.active}
          className={cn('relative h-8 w-14 shrink-0 rounded-full transition disabled:opacity-50', flow.active ? 'bg-primary' : 'bg-input')}>
          <span className={cn('absolute top-1 h-6 w-6 rounded-full bg-white shadow transition-all', flow.active ? 'left-7' : 'left-1')} />
          <span className="sr-only">{flow.active ? 'Desligar' : 'Ligar'}</span>
        </button>
      </CardContent>
    </Card>
  )
}

function Contacts({ flow }: { flow: ClientFlow }) {
  const [items, setItems] = useState<Contact[]>([])
  const [q, setQ] = useState('')
  const load = (query = q) => api.get(`/client/flows/${flow.id}/contacts?q=${encodeURIComponent(query)}`).then(setItems)
  useEffect(() => { load('') }, [flow.id])
  useEffect(() => { const t = setTimeout(() => load(q), 300); return () => clearTimeout(t) }, [q])
  async function setAi(c: Contact, on: boolean) {
    setItems(list => list.map(x => (x.id === c.id ? { ...x, ai_off: !on, paused_until: on ? '' : x.paused_until } : x)))
    await api.post(`/client/flows/${flow.id}/conversations/${c.id}/ai`, { on })
    load()
  }
  const paused = (c: Contact) => !c.ai_off && c.paused_until && new Date(c.paused_until.replace(' ', 'T') + 'Z') > new Date()
  return (
    <Card className="bg-glass border-border/50">
      <CardHeader className="flex-row items-center gap-3 space-y-0">
        <SectionIcon icon={Users} />
        <div>
          <CardTitle>Contatos</CardTitle>
          <CardDescription>Desligue a IA para quem não é cliente (equipe, fornecedor, família). Ela não responde mais essa pessoa até você ligar de novo.</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <Input value={q} onChange={e => setQ(e.target.value)} placeholder="Buscar por nome ou número" className="h-10" />
        {items.length === 0 && <p className="text-sm text-muted-foreground">Nenhum contato ainda.</p>}
        {items.map(c => (
          <div key={c.id} className="flex items-center gap-3 rounded-xl border border-border/60 px-3 py-2.5">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium truncate">{c.customer_name || (c.phone.length <= 13 ? formatPhone(c.phone) : 'Contato sem nome')}</p>
              {c.last && <p className="text-xs text-muted-foreground truncate">{c.last}</p>}
              {c.ai_off && <p className="text-xs text-amber-500">IA desligada para este contato</p>}
              {paused(c) && (
                <p className="text-xs text-amber-500">Loja atendendo, IA volta às {formatDate(c.paused_until)} · <button className="underline" onClick={() => setAi(c, true)}>devolver agora</button></p>
              )}
            </div>
            <div className="flex flex-col items-center gap-1">
              <Switch checked={!c.ai_off} onCheckedChange={on => setAi(c, on)} aria-label={`IA para ${c.customer_name || c.phone}`} />
              <span className="text-[10px] text-muted-foreground">IA</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function Receipts({ flow }: { flow: ClientFlow }) {
  const [items, setItems] = useState<FileItem[]>([])
  const [thumbs, setThumbs] = useState<Record<number, string>>({})
  useEffect(() => {
    api.get(`/client/flows/${flow.id}/files`).then(async (list: FileItem[]) => {
      setItems(list)
      const urls: Record<number, string> = {}
      for (const f of list.slice(0, 12)) {
        if (f.mimetype.startsWith('image/')) {
          try { urls[f.id] = await api.blobUrl(`/client/files/${f.id}`) } catch { /* sem miniatura */ }
        }
      }
      setThumbs(urls)
    })
  }, [flow.id])
  async function open(f: FileItem) {
    const url = thumbs[f.id] || await api.blobUrl(`/client/files/${f.id}`)
    window.open(url, '_blank')
  }
  return (
    <Card className="bg-glass border-border/50">
      <CardHeader className="flex-row items-center gap-3 space-y-0">
        <SectionIcon icon={Receipt} />
        <div>
          <CardTitle>Comprovantes recebidos</CardTitle>
          <CardDescription>Imagens e PDFs que os clientes mandaram como pagamento</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {items.length === 0 && <p className="text-sm text-muted-foreground">Nenhum comprovante ainda.</p>}
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
          {items.slice(0, 12).map(f => (
            <button key={f.id} onClick={() => open(f)} className="group relative aspect-square overflow-hidden rounded-xl border border-border/60 bg-muted/40 text-left">
              {thumbs[f.id]
                ? <img src={thumbs[f.id]} alt="Comprovante" className="h-full w-full object-cover transition group-hover:scale-105" />
                : <FileText className="absolute inset-0 m-auto h-8 w-8 text-muted-foreground" />}
              <span className="absolute inset-x-0 bottom-0 bg-black/60 px-1.5 py-1 text-[10px] text-white truncate">{formatDate(f.created_at)} · {f.phone.slice(-4)}</span>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function Options({ flow, reload }: { flow: ClientFlow; reload: () => Promise<ClientFlow[]> }) {
  const [s, setS] = useState<Settings>(flow.settings)
  const [saved, setSaved] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => setS(flow.settings), [flow.id])
  async function save() {
    setBusy(true); setError(''); setSaved('')
    try {
      await api.put(`/client/flows/${flow.id}/settings`, s)
      await reload()
      setSaved('Salvo!')
    } catch (err: any) { setError(err.message) } finally { setBusy(false) }
  }
  return (
    <>
      <Card className="bg-glass border-border/50">
        <CardHeader className="flex-row items-center gap-3 space-y-0">
          <SectionIcon icon={Clock} />
          <div className="flex-1">
            <CardTitle>Horário de funcionamento</CardTitle>
            <CardDescription>Fora do horário o cliente fica sabendo que a loja está fechada</CardDescription>
          </div>
          <Switch checked={s.hours_enabled} onCheckedChange={v => setS({ ...s, hours_enabled: v })} aria-label="Usar horário" />
        </CardHeader>
        {s.hours_enabled && (
          <CardContent className="space-y-4">
            <HoursEditor hours={s.hours} onChange={hours => setS({ ...s, hours })} />
            <Field label="Fora do horário">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {[{ v: 'ai', t: 'A IA responde e avisa que está fechado' }, { v: 'reply', t: 'Mandar só a mensagem abaixo' }].map(o => (
                  <button key={o.v} type="button" onClick={() => setS({ ...s, closed_action: o.v })}
                    className={cn('rounded-xl border px-3 py-2 text-left text-sm transition', s.closed_action === o.v ? 'border-primary bg-primary/10 text-foreground' : 'border-border/60 text-muted-foreground hover:border-border')}>
                    {o.t}
                  </button>
                ))}
              </div>
            </Field>
            {s.closed_action === 'reply' && (
              <Field label="Mensagem de loja fechada" hint="{{horario}} vira o horário da loja.">
                <Textarea rows={3} value={s.closed_message} onChange={e => setS({ ...s, closed_message: e.target.value })} />
              </Field>
            )}
          </CardContent>
        )}
      </Card>
      <Card className="bg-glass border-border/50">
        <CardHeader className="flex-row items-center gap-3 space-y-0">
          <SectionIcon icon={Bell} />
          <div>
            <CardTitle>Avisos no seu WhatsApp</CardTitle>
            <CardDescription>Receba um aviso quando chegar comprovante, pedido ou um cliente pedir atendente</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <Field label="Seu número pessoal (com DDD)" hint="Deixe vazio para não receber avisos.">
            <Input type="tel" inputMode="tel" value={s.notify_phone} onChange={e => setS({ ...s, notify_phone: e.target.value })} placeholder="(91) 98888-7777" className="h-11 text-base" />
          </Field>
        </CardContent>
      </Card>
      <div className="flex items-center gap-3">
        <Button size="lg" onClick={save} disabled={busy} className="flex-1 sm:flex-none">{busy ? <Loader2 className="animate-spin" /> : null} Salvar opções</Button>
        {saved && <span className="text-sm text-emerald-500">{saved}</span>}
      </div>
      <ErrorText>{error}</ErrorText>
    </>
  )
}

function PasswordCard() {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')
  async function save(e: React.FormEvent) {
    e.preventDefault()
    setMsg(''); setError('')
    try { await api.post('/auth/password', { current, new: next }); setMsg('Senha trocada!'); setCurrent(''); setNext('') } catch (err: any) { setError(err.message) }
  }
  return (
    <Card className="bg-glass border-border/50">
      <CardHeader className="flex-row items-center gap-3 space-y-0">
        <SectionIcon icon={KeyRound} />
        <CardTitle>Trocar senha</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={save} className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
          <Field label="Senha atual"><Input type="password" autoComplete="current-password" value={current} onChange={e => setCurrent(e.target.value)} required /></Field>
          <Field label="Nova senha"><Input type="password" autoComplete="new-password" value={next} onChange={e => setNext(e.target.value)} required minLength={6} /></Field>
          <Button type="submit" variant="outline">Trocar</Button>
        </form>
        {msg && <p className="mt-3 text-sm text-emerald-500">{msg}</p>}
        <div className="mt-3"><ErrorText>{error}</ErrorText></div>
      </CardContent>
    </Card>
  )
}

export default function ClientHome() {
  const [flows, setFlows] = useState<ClientFlow[] | null>(null)
  const navigate = useNavigate()

  async function load() {
    const data: ClientFlow[] = await api.get('/client/flows')
    setFlows(data)
    return data
  }
  useEffect(() => { load() }, [])

  return (
    <div className="min-h-screen bg-background relative">
      <div className="pointer-events-none fixed top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary/10 rounded-full blur-[120px]" />
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-border/60 bg-background/80 backdrop-blur-xl px-4 h-14">
        <Brand small />
        <Button variant="ghost" size="sm" onClick={() => { clearToken(); navigate('/login') }}><LogOut /> Sair</Button>
      </header>
      <main className="relative max-w-2xl mx-auto p-4 pb-16 space-y-4">
        {flows === null && <p className="text-muted-foreground text-sm flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Carregando...</p>}
        {flows?.length === 0 && (
          <Card className="bg-glass"><CardContent className="p-6 text-sm text-muted-foreground">Sua conta ainda não tem atendimento configurado. Fale com o suporte.</CardContent></Card>
        )}
        {flows?.map(f => (
          <section key={f.id} className="space-y-4">
            <div className="pt-2">
              <p className="text-sm text-muted-foreground">Painel da loja</p>
              <h1 className="text-3xl font-black tracking-tight text-gradient">{f.name}</h1>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <Stat icon={MessageSquare} label="Mensagens hoje" value={f.today.messages} />
              <Stat icon={Users} label="Clientes hoje" value={f.today.clients} />
              <Stat icon={Receipt} label="Comprovantes hoje" value={f.today.receipts} />
            </div>
            <Automation flow={f} reload={load} />
            <Connection flow={f} reload={load} />
            <Contacts flow={f} />
            <Receipts flow={f} />
            <Options flow={f} reload={load} />
          </section>
        ))}
        {flows && flows.length > 0 && <PasswordCard />}
        {flows && flows.length > 0 && (
          <p className="flex items-center justify-center gap-1.5 pt-4 text-xs text-muted-foreground"><Power className="h-3 w-3" /> Atendimento feito pela FluxIA</p>
        )}
      </main>
    </div>
  )
}
