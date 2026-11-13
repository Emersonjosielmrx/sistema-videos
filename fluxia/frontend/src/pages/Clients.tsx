import { useState, useEffect } from 'react'
import { UserPlus, Trash2, X, KeyRound, Store } from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Card, Field, Input, PageTitle, Select, ErrorText } from '../components/ui'

export default function Clients() {
  const [clients, setClients] = useState<any[]>([])
  const [flows, setFlows] = useState<any[]>([])
  const [form, setForm] = useState({ name: '', email: '', password: '', flow_id: 0 })
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  const load = () => { api.get('/clients').then(setClients); api.get('/flows').then(setFlows) }
  useEffect(() => { load() }, [])

  async function create(e: React.FormEvent) {
    e.preventDefault()
    setError(''); setInfo('')
    try {
      const c = await api.post('/clients', { name: form.name, email: form.email, password: form.password })
      if (form.flow_id) await api.post(`/clients/${c.id}/flows`, { flow_id: form.flow_id })
      setInfo(`Cliente criado. Login: ${c.email} · senha: ${form.password}`)
      setForm({ name: '', email: '', password: '', flow_id: 0 })
      load()
    } catch (err: any) { setError(err.message) }
  }
  async function resetPassword(c: any) {
    const password = prompt(`Nova senha para ${c.email} (mínimo 6 caracteres):`)
    if (!password) return
    try { await api.put(`/clients/${c.id}`, { password }); setInfo(`Senha de ${c.email} trocada para: ${password}`) } catch (err: any) { setError(err.message) }
  }
  async function rename(c: any) {
    const name = prompt('Nome do cliente:', c.name)
    if (name === null) return
    await api.put(`/clients/${c.id}`, { name }); load()
  }
  async function remove(c: any) {
    if (!confirm(`Apagar ${c.email}? Ele perde o acesso ao painel na hora.`)) return
    await api.delete(`/clients/${c.id}`); load()
  }

  return (
    <div className="space-y-6">
      <PageTitle title="Clientes" sub="O cliente entra no mesmo endereço e vê só a tela da loja: conectar o WhatsApp, ligar/desligar, horário, comprovantes." />
      <Card className="bg-glass border-border/50 p-5">
        <form onSubmit={create} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_1fr_auto] items-end">
          <Field label="Nome"><Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Castanhal Burger" /></Field>
          <Field label="Email de login"><Input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required /></Field>
          <Field label="Senha (mín. 6)"><Input value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required minLength={6} /></Field>
          <Field label="Fluxo">
            <Select value={form.flow_id} onChange={e => setForm({ ...form, flow_id: Number(e.target.value) })}>
              <option value={0}>Escolher depois</option>
              {flows.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
            </Select>
          </Field>
          <Button type="submit"><UserPlus /> Criar</Button>
        </form>
        <div className="mt-3 space-y-2">
          <ErrorText>{error}</ErrorText>
          {info && <p className="text-sm rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-500 px-3 py-2">{info}</p>}
        </div>
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        {clients.length === 0 && <p className="text-sm text-muted-foreground">Nenhum cliente cadastrado.</p>}
        {clients.map(c => (
          <Card key={c.id} className="bg-glass border-border/50 p-5 space-y-3">
            <div className="flex items-start gap-3">
              <span className="inline-flex rounded-xl bg-primary/15 p-2.5"><Store className="h-5 w-5 text-primary" /></span>
              <div className="flex-1 min-w-0">
                <button onClick={() => rename(c)} className="font-semibold truncate hover:text-primary">{c.name || c.email}</button>
                <p className="text-xs text-muted-foreground truncate">{c.email}</p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => resetPassword(c)} aria-label="Trocar senha" title="Trocar senha"><KeyRound /></Button>
              <Button variant="ghost" size="icon" onClick={() => remove(c)} aria-label="Apagar cliente" title="Apagar"><Trash2 /></Button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {c.flows.map((f: any) => (
                <Badge key={f.id} variant="secondary" className="gap-1.5">
                  {f.name}
                  <button onClick={() => api.delete(`/clients/${c.id}/flows/${f.id}`).then(load)} aria-label="Desvincular"><X className="h-3 w-3" /></button>
                </Badge>
              ))}
              <Select value={0} onChange={e => Number(e.target.value) && api.post(`/clients/${c.id}/flows`, { flow_id: Number(e.target.value) }).then(load)} className="h-7 w-auto text-xs">
                <option value={0}>+ vincular fluxo</option>
                {flows.filter(f => !c.flows.some((cf: any) => cf.id === f.id)).map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
              </Select>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
