import { useState, useEffect } from 'react'
import { Smartphone, ShieldCheck, Globe, Loader2 } from 'lucide-react'
import { api } from '../api'
import { Button, Card, Field, Input, PageTitle } from '../components/ui'
import { cn } from '../lib/utils'

type Msg = { type: 'ok' | 'warn' | 'error'; text: string } | null
const COLORS = { ok: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500', warn: 'border-amber-500/30 bg-amber-500/10 text-amber-500', error: 'border-destructive/30 bg-destructive/10 text-destructive' }

function MsgBox({ msg }: { msg: Msg }) {
  return msg ? <p className={cn('text-sm rounded-lg border px-3 py-2', COLORS[msg.type])}>{msg.text}</p> : null
}

export default function Settings() {
  const [hermesUrl, setHermesUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [keySet, setKeySet] = useState(false)
  const [publicUrl, setPublicUrl] = useState('')
  const [phones, setPhones] = useState('')
  const [lids, setLids] = useState('')
  const [msg, setMsg] = useState<Msg>(null)
  const [phonesMsg, setPhonesMsg] = useState<Msg>(null)
  const [saving, setSaving] = useState(false)

  const load = () => api.get('/settings').then(s => {
    setHermesUrl(s.hermes_url); setKeySet(s.hermes_api_key_set); setPublicUrl(s.public_url); setPhones(s.admin_phones); setLids(s.admin_lids || '')
  })
  useEffect(() => { load() }, [])

  async function save(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true); setMsg(null)
    try {
      const r = await api.put('/settings', { hermes_url: hermesUrl, hermes_api_key: apiKey })
      setApiKey(''); await load()
      setMsg(r.hermes_agent_enabled
        ? { type: 'warn', text: 'Salvo. Atenção: o Agente de IA do Hermes está LIGADO nessa conta, os clientes vão receber duas respostas. Desligue o agente no Hermes ou use outra conta.' }
        : { type: 'ok', text: 'Salvo e testado: o Hermes aceitou a chave.' })
    } catch (err: any) { setMsg({ type: 'error', text: err.message }) } finally { setSaving(false) }
  }
  async function savePhones(e: React.FormEvent) {
    e.preventDefault()
    try { await api.put('/settings', { admin_phones: phones, admin_lids: lids }); await load(); setPhonesMsg({ type: 'ok', text: 'Salvo.' }) } catch (err: any) { setPhonesMsg({ type: 'error', text: err.message }) }
  }

  return (
    <div className="max-w-2xl space-y-4">
      <PageTitle title="Configurações" />
      <Card className="bg-glass border-border/50 p-5">
        <form onSubmit={save} className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="inline-flex rounded-xl bg-primary/15 p-2.5 shadow-glow"><Smartphone className="h-5 w-5 text-primary" /></span>
            <div>
              <p className="font-semibold">WhatsApp (Hermes Call)</p>
              <p className="text-sm text-muted-foreground">Crie uma chave no Hermes (Configurações → API) numa conta com o Agente de IA desligado.</p>
            </div>
          </div>
          <Field label="URL do Hermes"><Input value={hermesUrl} onChange={e => setHermesUrl(e.target.value)} required /></Field>
          <Field label={<>Chave de API {keySet ? <span className="text-emerald-500">(configurada; vazio mantém)</span> : <span className="text-amber-500">(não configurada)</span>}</>}>
            <Input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} autoComplete="off" placeholder="hk_..." />
          </Field>
          <Button type="submit" disabled={saving}>{saving && <Loader2 className="animate-spin" />} {saving ? 'Testando...' : 'Salvar e testar'}</Button>
          <MsgBox msg={msg} />
        </form>
      </Card>
      <Card className="bg-glass border-border/50 p-5">
        <form onSubmit={savePhones} className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="inline-flex rounded-xl bg-sky-500/15 p-2.5"><ShieldCheck className="h-5 w-5 text-sky-400" /></span>
            <div>
              <p className="font-semibold">Números de administrador</p>
              <p className="text-sm text-muted-foreground">Quem manda mensagem destes números para o WhatsApp de um fluxo entra no modo administrador: ensina o agente, simula cliente, reinicia. Também recebem aviso quando a IA falha.</p>
            </div>
          </div>
          <Field label="Números (com DDD, separados por vírgula)"><Input value={phones} onChange={e => setPhones(e.target.value)} placeholder="5591984698653" /></Field>
          <Field label="IDs internos do WhatsApp (LID) desses números" hint="O WhatsApp às vezes manda a mensagem com um ID interno no lugar do número. É fixo por conta; aparece nas Conversas quando o número não aparece.">
            <Input value={lids} onChange={e => setLids(e.target.value)} placeholder="132250784018630" />
          </Field>
          <Button type="submit" variant="outline">Salvar números</Button>
          <MsgBox msg={phonesMsg} />
        </form>
      </Card>
      <Card className="bg-glass border-border/50 p-5 text-sm flex items-center gap-3">
        <Globe className="h-5 w-5 text-muted-foreground shrink-0" />
        <div className="min-w-0">
          <p className="text-muted-foreground">Endereço público (usado no webhook do WhatsApp)</p>
          <code className="text-primary break-all">{publicUrl}</code>
        </div>
      </Card>
    </div>
  )
}
