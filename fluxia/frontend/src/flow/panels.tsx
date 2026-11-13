import { useState } from 'react'
import { Plus, Trash2, Sparkles, Loader2, Info } from 'lucide-react'
import { Button, Field, Input, Select, Switch, Textarea, ErrorText } from '@/components/ui'
import HoursEditor from '@/components/HoursEditor'
import { api } from '@/api'
import { cn } from '@/lib/utils'
import type { Flow, FlowConfig, Button as FlowButton } from './types'
import type { NodeId } from './nodes'

type PanelProps = {
  flow: Flow
  cfg: FlowConfig
  set: (patch: Partial<FlowConfig>) => void
  dirty: boolean
  connections: { id: number; label: string; session_id: string }[]
  setConnection: (id: number | null) => void
  onTaught: (cfg: FlowConfig) => void
}

function Toggle({ label, hint, checked, onChange }: { label: string; hint?: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-border/60 px-3 py-2.5">
      <div>
        <p className="text-sm font-medium">{label}</p>
        {hint && <p className="text-xs text-muted-foreground mt-0.5">{hint}</p>}
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  )
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="flex gap-2 rounded-xl bg-muted/50 px-3 py-2 text-xs text-muted-foreground"><Info className="h-3.5 w-3.5 shrink-0 mt-0.5" /><span>{children}</span></p>
}

function Choice({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: { v: string; t: string; d?: string }[] }) {
  return (
    <div className="grid gap-2">
      {options.map(o => (
        <button key={o.v} type="button" onClick={() => onChange(o.v)}
          className={cn('rounded-xl border px-3 py-2 text-left transition', value === o.v ? 'border-primary bg-primary/10' : 'border-border/60 hover:border-border')}>
          <p className="text-sm font-medium">{o.t}</p>
          {o.d && <p className="text-xs text-muted-foreground">{o.d}</p>}
        </button>
      ))}
    </div>
  )
}

const PLACEHOLDERS = '{{loja}} {{endereco}} {{horario}} {{entrega}} {{link_cardapio}} {{cardapio}} {{chave_pix}} {{informacoes}} {{cidade}}'

function Teach({ flow, dirty, onTaught }: Pick<PanelProps, 'flow' | 'dirty' | 'onTaught'>) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<{ reply: string; changes: string[] } | null>(null)
  const [error, setError] = useState('')
  async function send() {
    setBusy(true); setError(''); setResult(null)
    try {
      const r = await api.post(`/flows/${flow.id}/teach`, { instruction: text })
      setResult(r); setText('')
      if (r.changed) onTaught(r.config)
    } catch (e: any) { setError(e.message) } finally { setBusy(false) }
  }
  return (
    <div className="space-y-2 rounded-2xl border border-primary/30 bg-primary/5 p-3">
      <p className="flex items-center gap-2 text-sm font-semibold text-primary"><Sparkles className="h-4 w-4" /> Ensinar o agente</p>
      <p className="text-xs text-muted-foreground">Escreva o que mudar, do mesmo jeito que você faria pelo WhatsApp. Ex.: "quando pedirem desconto, diga que só às terças".</p>
      <Textarea rows={3} value={text} onChange={e => setText(e.target.value)} placeholder="O que o agente deve fazer diferente?" />
      <Button size="sm" onClick={send} disabled={busy || !text.trim() || dirty}>
        {busy ? <Loader2 className="animate-spin" /> : <Sparkles />} {dirty ? 'Salve as alterações antes' : 'Aplicar'}
      </Button>
      {result && (
        <div className="text-xs space-y-1">
          <p>{result.reply}</p>
          {result.changes.map((c, i) => <p key={i} className="text-emerald-400">• {c}</p>)}
        </div>
      )}
      <ErrorText>{error}</ErrorText>
    </div>
  )
}

function ButtonsEditor({ buttons, onChange }: { buttons: FlowButton[]; onChange: (b: FlowButton[]) => void }) {
  const upd = (i: number, patch: Partial<FlowButton>) => onChange(buttons.map((b, j) => (j === i ? { ...b, ...patch } : b)))
  return (
    <div className="space-y-2">
      {buttons.map((b, i) => (
        <div key={i} className="space-y-2 rounded-xl border border-border/60 p-2.5">
          <div className="flex gap-2">
            <Input value={b.label} maxLength={100} onChange={e => upd(i, { label: e.target.value })} placeholder="Texto do botão" />
            <Button variant="ghost" size="icon" onClick={() => onChange(buttons.filter((_, j) => j !== i))} aria-label="Remover botão"><Trash2 /></Button>
          </div>
          <Select value={b.action} onChange={e => upd(i, { action: e.target.value as FlowButton['action'] })}>
            <option value="ai">A IA responde</option>
            <option value="reply">Resposta fixa</option>
            <option value="human">Chamar atendente (pausa a IA)</option>
          </Select>
          {b.action === 'reply' && <Textarea rows={2} value={b.reply} onChange={e => upd(i, { reply: e.target.value })} placeholder="Resposta enviada quando tocar neste botão" />}
        </div>
      ))}
      {buttons.length < 12 && (
        <Button variant="outline" size="sm" onClick={() => onChange([...buttons, { label: '', action: 'ai', reply: '' }])}><Plus /> Adicionar botão</Button>
      )}
    </div>
  )
}

export function NodePanel({ node, ...p }: PanelProps & { node: NodeId }) {
  const { cfg, set } = p
  switch (node) {
    case 'trigger':
      return (
        <div className="space-y-4">
          <Field label="Número de WhatsApp deste fluxo" hint="A loja também conecta o número pela tela dela.">
            <Select value={p.flow.connection_id ?? ''} onChange={e => p.setConnection(e.target.value ? Number(e.target.value) : null)}>
              <option value="">Nenhum (a loja conecta pela tela dela)</option>
              {p.connections.map(c => <option key={c.id} value={c.id}>{c.label || c.session_id}</option>)}
            </Select>
          </Field>
          <Note>Toda mensagem que chega no WhatsApp passa por estes blocos, da esquerda para a direita. Grupos, status e figurinhas são ignorados.</Note>
        </div>
      )
    case 'admin':
      return (
        <div className="space-y-3 text-sm">
          <Note>Quando um número de administrador (Configurações) manda mensagem para este WhatsApp, ele não é atendido como cliente.</Note>
          <ul className="space-y-1.5 text-muted-foreground">
            <li><b className="text-foreground">menu</b>: mostra as opções em botões</li>
            <li><b className="text-foreground">qualquer instrução</b>: ensina o agente (vira regra ou troca de dado)</li>
            <li><b className="text-foreground">simular</b>: você conversa como se fosse um cliente novo</li>
            <li><b className="text-foreground">reiniciar</b>: começa a simulação do zero · <b className="text-foreground">sair</b>: volta ao modo admin</li>
            <li><b className="text-foreground">regras</b>, <b className="text-foreground">apagar regra 2</b>, <b className="text-foreground">desfazer</b></li>
            <li><b className="text-foreground">ligar</b> / <b className="text-foreground">desligar</b>, <b className="text-foreground">status</b>, <b className="text-foreground">prompt</b></li>
            <li><b className="text-foreground">reiniciar 91988887777</b>: zera a conversa de um cliente e devolve para a IA</li>
          </ul>
          <Note>Áudio também vale: mande a instrução falada que ela é transcrita.</Note>
        </div>
      )
    case 'filter':
      return (
        <div className="space-y-4">
          <Toggle label="Pausar a IA quando a loja responder" hint="Se alguém da loja responder o cliente pelo celular, a IA para de responder aquele cliente."
            checked={cfg.pause_on_owner_reply} onChange={v => set({ pause_on_owner_reply: v })} />
          <Field label="Tempo de pausa (minutos)" hint="Também vale quando o cliente pede atendente.">
            <Input type="number" min={0} max={1440} value={cfg.pause_minutes} onChange={e => set({ pause_minutes: Number(e.target.value) })} />
          </Field>
          <Toggle label="Desligar de vez quando a loja mandar 2 mensagens seguidas" hint="Se a loja mandar 2 mensagens para o mesmo contato com menos de 1 minuto entre elas, a IA não responde mais esse contato até alguém religar (tela da loja → Contatos)."
            checked={cfg.owner_off_two_messages} onChange={v => set({ owner_off_two_messages: v })} />
          <Note>Grupos, status e canais nunca são respondidos.</Note>
        </div>
      )
    case 'hours':
      return (
        <div className="space-y-4">
          <Toggle label="Usar horário de funcionamento" checked={cfg.hours_enabled} onChange={v => set({ hours_enabled: v })} />
          <HoursEditor hours={cfg.hours} onChange={hours => set({ hours })} />
          <Field label="Horário escrito para o cliente" hint="Se ficar vazio, usa os horários acima.">
            <Input value={cfg.store_hours} onChange={e => set({ store_hours: e.target.value })} placeholder="Todos os dias das 18h às 23h30" />
          </Field>
          <Field label="Fora do horário">
            <Choice value={cfg.closed_action} onChange={v => set({ closed_action: v })} options={[
              { v: 'ai', t: 'A IA responde avisando que está fechado', d: 'Bom quando o cliente pode adiantar o pedido pelo link.' },
              { v: 'reply', t: 'Manda só a mensagem de fechado', d: 'Enviada no máximo uma vez a cada 3 horas por cliente.' },
            ]} />
          </Field>
          {cfg.closed_action === 'reply' && (
            <Field label="Mensagem de fechado"><Textarea rows={3} value={cfg.closed_message} onChange={e => set({ closed_message: e.target.value })} /></Field>
          )}
          <Field label="Fuso horário">
            <Select value={cfg.timezone} onChange={e => set({ timezone: e.target.value })}>
              {['America/Belem', 'America/Sao_Paulo', 'America/Manaus', 'America/Fortaleza', 'America/Cuiaba', 'America/Rio_Branco', 'America/Noronha'].map(t => <option key={t}>{t}</option>)}
            </Select>
          </Field>
        </div>
      )
    case 'buffer':
      return (
        <div className="space-y-4">
          <Field label={`Esperar ${cfg.buffer_seconds} segundos`} hint="Muita gente manda várias mensagens seguidas. O agente espera e responde tudo de uma vez.">
            <input type="range" min={0} max={30} value={cfg.buffer_seconds} onChange={e => set({ buffer_seconds: Number(e.target.value) })} className="w-full accent-emerald-500" />
          </Field>
        </div>
      )
    case 'media':
      return <Note>Este bloco separa a mensagem pelo tipo. Clique em Texto, Áudio, Imagem, Documento ou Botão tocado para escolher o que fazer em cada caso.</Note>
    case 'm_text':
      return (
        <div className="space-y-4">
          <Note>Texto vai direto para o agente. Abaixo: o que fazer com outros tipos (localização, vídeo, contato).</Note>
          <Field label="Outros tipos de mensagem">
            <Choice value={cfg.other_action} onChange={v => set({ other_action: v })} options={[
              { v: 'ai', t: 'A IA responde' }, { v: 'reply', t: 'Resposta fixa' }, { v: 'ignore', t: 'Ignorar' },
            ]} />
          </Field>
          {cfg.other_action === 'reply' && <Field label="Resposta fixa"><Textarea rows={2} value={cfg.other_reply} onChange={e => set({ other_reply: e.target.value })} /></Field>}
        </div>
      )
    case 'm_audio':
      return (
        <div className="space-y-4">
          <Field label="Quando o cliente mandar áudio">
            <Choice value={cfg.audio_action} onChange={v => set({ audio_action: v })} options={[
              { v: 'transcribe', t: 'Transcrever e responder', d: 'O áudio vira texto e o agente responde normalmente.' },
              { v: 'reply', t: 'Resposta fixa', d: 'Ex.: pedir para escrever.' },
              { v: 'ai', t: 'A IA responde sem ouvir' },
              { v: 'ignore', t: 'Ignorar' },
            ]} />
          </Field>
          <Field label="Resposta fixa" hint="Usada na opção acima e quando a transcrição falhar.">
            <Textarea rows={2} value={cfg.audio_reply} onChange={e => set({ audio_reply: e.target.value })} />
          </Field>
        </div>
      )
    case 'm_image':
      return (
        <div className="space-y-4">
          <Field label="Quando o cliente mandar imagem">
            <Choice value={cfg.image_action} onChange={v => set({ image_action: v })} options={[
              { v: 'vision', t: 'A IA olha a imagem', d: 'Entende comprovantes, fotos de produto, prints.' },
              { v: 'receipt', t: 'Tratar como comprovante', d: 'Agradece e guarda, sem olhar.' },
              { v: 'reply', t: 'Resposta fixa' },
              { v: 'ignore', t: 'Ignorar' },
            ]} />
          </Field>
          {cfg.image_action === 'reply' && <Field label="Resposta fixa"><Textarea rows={2} value={cfg.image_reply} onChange={e => set({ image_reply: e.target.value })} /></Field>}
          <Note>As imagens ficam guardadas; as que a IA reconhecer como comprovante aparecem na tela da loja.</Note>
        </div>
      )
    case 'm_doc':
      return (
        <div className="space-y-4">
          <Field label="Quando o cliente mandar PDF ou documento">
            <Choice value={cfg.document_action} onChange={v => set({ document_action: v })} options={[
              { v: 'receipt', t: 'Tratar como possível comprovante' },
              { v: 'file', t: 'Arquivo do cliente', d: 'Para imprimir/editar: a IA sabe o nome e quantas páginas tem o PDF.' },
              { v: 'reply', t: 'Resposta fixa' }, { v: 'ignore', t: 'Ignorar' },
            ]} />
          </Field>
          {cfg.document_action === 'reply' && <Field label="Resposta fixa"><Textarea rows={2} value={cfg.document_reply} onChange={e => set({ document_reply: e.target.value })} /></Field>}
        </div>
      )
    case 'm_vote':
    case 'buttons':
      return (
        <div className="space-y-4">
          <Toggle label="Menu de opções com perguntas (estilo bot antigo)" hint="Menu → submenu → perguntas do serviço → confirmação, tudo por enquete. A IA só responde o que não for opção. Substitui os botões abaixo."
            checked={cfg.menu_enabled} onChange={v => set({ menu_enabled: v })} />
          <Field label="Como as opções aparecem">
            <Choice value={cfg.button_style} onChange={v => set({ button_style: v as FlowConfig['button_style'] })} options={[
              { v: 'enquete', t: 'Enquete', d: 'Funciona em todo WhatsApp. O cliente marca a opção.' },
              { v: 'botoes', t: 'Botões', d: 'Botões clicáveis do WhatsApp, em grupos de 3 (um menu de 8 opções sai em 3 mensagens). Cada opção com até 20 letras; mais que isso, ou o WhatsApp recusando, vai como enquete.' },
            ]} />
          </Field>
          <Toggle label="Mandar botões" hint="O cliente toca numa opção (no formato escolhido acima). Vai no primeiro contato e quando o cliente pede o menu."
            checked={cfg.buttons_enabled} onChange={v => set({ buttons_enabled: v })} />
          <Field label="Título dos botões"><Input value={cfg.buttons_title} onChange={e => set({ buttons_title: e.target.value })} /></Field>
          <ButtonsEditor buttons={cfg.buttons} onChange={buttons => set({ buttons })} />
          <Field label="Boas-vindas fixa (opcional)" hint="Se preencher, substitui a resposta da IA na primeira mensagem do cliente. Vazio: a IA cumprimenta.">
            <Textarea rows={3} value={cfg.greeting_text} onChange={e => set({ greeting_text: e.target.value })} placeholder="Olá! Bem-vindo ao {{loja}} 😊" />
          </Field>
        </div>
      )
    case 'agent':
      return (
        <div className="space-y-4">
          <Teach flow={p.flow} dirty={p.dirty} onTaught={p.onTaught} />
          <Field label="O que o agente faz">
            <Select value={cfg.order_mode} onChange={e => set({ order_mode: e.target.value as FlowConfig['order_mode'] })}>
              <option value="link">Manda o link do cardápio</option>
              <option value="pix">Anota o pedido e gera Pix</option>
              <option value="none">Tira dúvidas (atendimento geral)</option>
              <option value="agendamento">Faz agendamentos</option>
            </Select>
          </Field>
          {cfg.order_mode === 'link' && <Field label="Link do cardápio"><Input value={cfg.menu_url} onChange={e => set({ menu_url: e.target.value })} placeholder="https://..." /></Field>}
          {cfg.order_mode === 'pix' && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="Chave Pix"><Input value={cfg.pix_key} onChange={e => set({ pix_key: e.target.value })} /></Field>
              <Field label="Cidade (Pix)"><Input value={cfg.store_city} onChange={e => set({ store_city: e.target.value })} /></Field>
            </div>
          )}
          {cfg.order_mode !== 'pix' && cfg.prompt.includes('{{chave_pix}}') && (
            <Field label="Chave Pix (mostrada ao cliente)"><Input value={cfg.pix_key} onChange={e => set({ pix_key: e.target.value })} /></Field>
          )}
          <div className="grid grid-cols-2 gap-3">
            <Field label="Nome da loja"><Input value={cfg.store_name} onChange={e => set({ store_name: e.target.value })} /></Field>
            <Field label="Endereço"><Input value={cfg.store_address} onChange={e => set({ store_address: e.target.value })} /></Field>
          </div>
          <Field label="Entrega"><Input value={cfg.delivery_info} onChange={e => set({ delivery_info: e.target.value })} placeholder="Taxa, bairros atendidos, tempo médio" /></Field>
          <Field label="Informações extras" hint="Serviços, preços, perguntas frequentes. Entra no prompt em {{informacoes}}.">
            <Textarea rows={4} value={cfg.business_info} onChange={e => set({ business_info: e.target.value })} />
          </Field>
          <Field label="Prompt do agente" hint={`Variáveis: ${PLACEHOLDERS}`}>
            <Textarea rows={14} value={cfg.prompt} onChange={e => set({ prompt: e.target.value })} className="font-mono text-xs leading-relaxed" />
          </Field>
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Regras ensinadas ({cfg.learned_rules.length})</p>
            {cfg.learned_rules.length === 0 && <p className="text-xs text-muted-foreground">Nenhuma ainda. Use "Ensinar o agente" acima ou mande pelo WhatsApp do seu número.</p>}
            {cfg.learned_rules.map((r, i) => (
              <div key={i} className="flex gap-2 rounded-xl border border-border/60 px-3 py-2">
                <span className="text-xs font-bold text-primary pt-0.5">{i + 1}</span>
                <p className="flex-1 text-sm">{r.text}<span className="block text-[11px] text-muted-foreground">{r.source} · {r.created_at}</span></p>
                <Button variant="ghost" size="icon" onClick={() => set({ learned_rules: cfg.learned_rules.filter((_, j) => j !== i) })} aria-label="Apagar regra"><Trash2 /></Button>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Modelo">
              <Select value={cfg.model} onChange={e => set({ model: e.target.value })}>
                <option value="cc/claude-haiku-5-5">Haiku (rápido)</option>
                <option value="cc/claude-sonnet-5-5">Sonnet (mais caprichado)</option>
              </Select>
            </Field>
            <Field label="Mensagens de memória"><Input type="number" min={4} max={60} value={cfg.history_limit} onChange={e => set({ history_limit: Number(e.target.value) })} /></Field>
          </div>
        </div>
      )
    case 'actions':
      return (
        <div className="space-y-4">
          <Note>O agente marca na resposta quando recebe comprovante, quando o cliente confirma pedido/agendamento ou pede atendente. O sistema age sozinho: guarda o comprovante, gera o Pix, pausa a IA.</Note>
          <Field label="Número que recebe os avisos" hint="Normalmente o celular pessoal do dono. Vazio: sem avisos.">
            <Input value={cfg.notify_phone} onChange={e => set({ notify_phone: e.target.value })} placeholder="91988887777" />
          </Field>
          <Toggle label="Avisar quando pedirem atendente" checked={cfg.notify_handoff} onChange={v => set({ notify_handoff: v })} />
          <Toggle label="Avisar quando chegar comprovante" checked={cfg.notify_receipt} onChange={v => set({ notify_receipt: v })} />
          <Toggle label="Avisar novo pedido / agendamento" checked={cfg.notify_order} onChange={v => set({ notify_order: v })} />
        </div>
      )
    case 'send':
      return (
        <div className="space-y-4">
          <Field label="Tamanho das respostas">
            <Choice value={cfg.reply_length} onChange={v => set({ reply_length: v as FlowConfig['reply_length'] })} options={[
              { v: 'curta', t: 'Curta', d: 'Até 2 frases, sem repetir saudação. Recomendado para delivery.' },
              { v: 'media', t: 'Média', d: '3 a 4 frases.' },
              { v: 'livre', t: 'Livre', d: 'O agente decide.' },
            ]} />
          </Field>
          <Toggle label='Mostrar "digitando..."' hint="Parece mais humano; adiciona 1 a 3 segundos por mensagem." checked={cfg.typing} onChange={v => set({ typing: v })} />
          <Toggle label="Dividir respostas longas" hint="Separa por parágrafo em até 4 mensagens." checked={cfg.split_messages} onChange={v => set({ split_messages: v })} />
        </div>
      )
  }
}
