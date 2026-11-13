import { Handle, Position, type Node, type Edge, type NodeProps } from '@xyflow/react'
import {
  MessageCircle, Hand, Clock, Layers, Split, Type, Mic, Image, FileText, MousePointerClick, Bot, Zap, Send,
  ListChecks, ShieldCheck, CheckCircle2, XCircle, MinusCircle, StopCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FlowConfig, Step } from './types'

export type NodeId =
  | 'trigger' | 'admin' | 'filter' | 'hours' | 'buffer' | 'media'
  | 'm_text' | 'm_audio' | 'm_image' | 'm_doc' | 'm_vote'
  | 'agent' | 'actions' | 'send' | 'buttons'

export type NodeStatus = { status: Step['status']; info: string[] }

type Def = { id: NodeId; title: string; icon: React.ElementType; x: number; y: number; color?: string; summary: (c: FlowConfig, extra: Extra) => string }
type Extra = { whatsapp?: { status: string; phone: string } }

const AUDIO: Record<string, string> = { transcribe: 'Transcreve e responde', reply: 'Resposta fixa', ai: 'IA responde sem ouvir', ignore: 'Ignora' }
const IMAGE: Record<string, string> = { vision: 'A IA olha a imagem', receipt: 'Trata como comprovante', reply: 'Resposta fixa', ignore: 'Ignora' }
const DOC: Record<string, string> = { receipt: 'Trata como comprovante', file: 'Arquivo do cliente (conta páginas)', reply: 'Resposta fixa', ignore: 'Ignora' }
const MODE: Record<string, string> = { link: 'manda o link do cardápio', pix: 'anota pedido e gera Pix', none: 'tira dúvidas', agendamento: 'faz agendamentos' }

// Colunas compactas: a entrada desce pela 2ª coluna, abre por tipo na 4ª e a saída desce pela última.
export const NODE_DEFS: Def[] = [
  { id: 'admin', title: 'Seu número', icon: ShieldCheck, x: 0, y: 0, color: 'text-sky-400',
    summary: () => 'Modo administrador: ensinar, simular e recomeçar' },
  { id: 'trigger', title: 'Mensagem recebida', icon: MessageCircle, x: 0, y: 170, color: 'text-emerald-400',
    summary: (_c, e) => e.whatsapp?.status === 'connected' ? `WhatsApp ${e.whatsapp.phone || 'conectado'}` : e.whatsapp?.status === 'unknown' ? 'WhatsApp sem resposta' : 'WhatsApp desconectado' },
  { id: 'filter', title: 'Loja assumiu?', icon: Hand, x: 290, y: 10,
    summary: c => (c.pause_on_owner_reply ? `Loja respondeu: IA pausa ${c.pause_minutes} min` : 'Não pausa quando a loja responde')
      + (c.owner_off_two_messages ? ' · 2 seguidas: desliga o contato' : '') },
  { id: 'hours', title: 'Horário', icon: Clock, x: 290, y: 170,
    summary: c => !c.hours_enabled ? 'Sem controle de horário' : c.closed_action === 'reply' ? 'Fechado: manda mensagem fixa' : 'Fechado: IA avisa' },
  { id: 'buffer', title: 'Agrupar mensagens', icon: Layers, x: 290, y: 330,
    summary: c => c.buffer_seconds ? `Espera ${c.buffer_seconds}s o cliente terminar` : 'Responde na hora' },
  { id: 'media', title: 'Tipo de mensagem', icon: Split, x: 580, y: 170, summary: () => 'Separa por tipo' },
  { id: 'm_text', title: 'Texto', icon: Type, x: 870, y: -110, summary: c => c.other_action === 'ignore' ? 'Outros tipos: ignora' : 'Vai direto para a IA' },
  { id: 'm_audio', title: 'Áudio', icon: Mic, x: 870, y: 30, summary: c => AUDIO[c.audio_action] || c.audio_action },
  { id: 'm_image', title: 'Imagem', icon: Image, x: 870, y: 170, summary: c => IMAGE[c.image_action] || c.image_action },
  { id: 'm_doc', title: 'Documento / PDF', icon: FileText, x: 870, y: 310, summary: c => DOC[c.document_action] || c.document_action },
  { id: 'm_vote', title: 'Botão tocado', icon: MousePointerClick, x: 870, y: 450,
    summary: c => c.buttons.length ? `${c.buttons.length} botões configurados` : 'Sem botões' },
  { id: 'agent', title: 'Agente IA', icon: Bot, x: 1160, y: 170, color: 'text-emerald-400',
    summary: c => `${MODE[c.order_mode] || ''}${c.learned_rules.length ? ` · ${c.learned_rules.length} regra(s) ensinada(s)` : ''}` },
  { id: 'actions', title: 'Ações', icon: Zap, x: 1450, y: 10,
    summary: c => c.notify_phone ? `Comprovante, pedido, atendente · avisa ${c.notify_phone}` : 'Comprovante, pedido, atendente' },
  { id: 'send', title: 'Enviar resposta', icon: Send, x: 1450, y: 170,
    summary: c => [`resposta ${c.reply_length}`, c.typing && '"digitando..."', c.split_messages && 'divide em partes'].filter(Boolean).join(' · ') },
  { id: 'buttons', title: 'Boas-vindas e botões', icon: ListChecks, x: 1450, y: 330,
    summary: c => !c.buttons_enabled ? (c.greeting_text ? 'Boas-vindas fixa, sem botões' : 'Sem botões') : `${c.buttons.length} botões no primeiro contato` },
]

// [origem, destino, saída, entrada]: r = direita, b = embaixo, l = esquerda, t = em cima
const EDGES: [NodeId, NodeId, 'r' | 'b', 'l' | 't'][] = [
  ['admin', 'trigger', 'b', 't'], ['trigger', 'filter', 'r', 'l'], ['filter', 'hours', 'b', 't'], ['hours', 'buffer', 'b', 't'],
  ['buffer', 'media', 'r', 'l'],
  ['media', 'm_text', 'r', 'l'], ['media', 'm_audio', 'r', 'l'], ['media', 'm_image', 'r', 'l'], ['media', 'm_doc', 'r', 'l'], ['media', 'm_vote', 'r', 'l'],
  ['m_text', 'agent', 'r', 'l'], ['m_audio', 'agent', 'r', 'l'], ['m_image', 'agent', 'r', 'l'], ['m_doc', 'agent', 'r', 'l'], ['m_vote', 'agent', 'r', 'l'],
  ['agent', 'actions', 'r', 'l'], ['actions', 'send', 'b', 't'], ['send', 'buttons', 'b', 't'],
]

export type StepNodeData = { def: Def; summary: string; run?: NodeStatus; dim: boolean }

const HANDLE = '!w-1.5 !h-1.5 !min-w-0 !min-h-0 !border-0 !bg-muted-foreground/60'
const STATUS_ICON = { ok: CheckCircle2, error: XCircle, stop: StopCircle, skip: MinusCircle }
const STATUS_COLOR = {
  ok: 'border-emerald-500/70 shadow-[0_0_24px_-6px_rgba(16,185,129,0.6)]',
  error: 'border-red-500/80 shadow-[0_0_24px_-6px_rgba(239,68,68,0.6)]',
  stop: 'border-amber-500/80 shadow-[0_0_24px_-6px_rgba(245,158,11,0.5)]',
  skip: 'border-border',
}
const STATUS_TEXT = { ok: 'text-emerald-400', error: 'text-red-400', stop: 'text-amber-400', skip: 'text-muted-foreground' }

export function StepNode({ data, selected }: NodeProps<Node<StepNodeData>>) {
  const { def, summary, run, dim } = data
  const Icon = def.icon
  const StatusIcon = run ? STATUS_ICON[run.status] : null
  return (
    <div className={cn(
      'w-[240px] cursor-pointer rounded-2xl border bg-card/95 px-4 py-3 transition-all hover:border-primary/60',
      run ? STATUS_COLOR[run.status] : 'border-border/70',
      selected && 'ring-2 ring-primary ring-offset-2 ring-offset-background',
      dim && !run && 'opacity-40',
    )}>
      <Handle id="l" type="target" position={Position.Left} className={HANDLE} />
      <Handle id="t" type="target" position={Position.Top} className={HANDLE} />
      <div className="flex items-center gap-2.5">
        <span className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/15', def.color || 'text-primary')}>
          <Icon className="h-5 w-5" />
        </span>
        <p className="text-[15px] font-semibold leading-tight flex-1">{def.title}</p>
        {StatusIcon && <StatusIcon className={cn('h-5 w-5', STATUS_TEXT[run!.status])} />}
      </div>
      <p className="mt-2 text-[13px] text-muted-foreground leading-snug line-clamp-2">{summary}</p>
      {run && run.info.length > 0 && (
        <p className={cn('mt-2 rounded-lg bg-background/60 px-2 py-1 text-xs leading-snug line-clamp-2', STATUS_TEXT[run.status])} title={run.info.join('\n')}>
          {run.info.join(' · ')}
        </p>
      )}
      <Handle id="r" type="source" position={Position.Right} className={HANDLE} />
      <Handle id="b" type="source" position={Position.Bottom} className={HANDLE} />
    </div>
  )
}

function mediaBranch(info: string): NodeId {
  if (info.startsWith('Botão')) return 'm_vote'
  if (info.startsWith('Áudio')) return 'm_audio'
  if (info.startsWith('Imagem')) return 'm_image'
  if (info.startsWith('Documento')) return 'm_doc'
  return 'm_text'
}

const RANK = { error: 3, stop: 2, ok: 1, skip: 0 }

export function stepsToStatus(steps: Step[] | undefined): Partial<Record<NodeId, NodeStatus>> {
  const out: Partial<Record<NodeId, NodeStatus>> = {}
  const add = (id: NodeId, s: Step) => {
    const cur = out[id]
    if (!cur) out[id] = { status: s.status, info: [s.info] }
    else {
      cur.info.push(s.info)
      if (RANK[s.status] > RANK[cur.status]) cur.status = s.status
    }
  }
  for (const s of steps || []) {
    if (s.node === 'media') {
      add('media', { ...s, info: '' })
      add(mediaBranch(s.info), s)
    } else if ((NODE_DEFS as { id: string }[]).some(d => d.id === s.node)) {
      add(s.node as NodeId, s)
    }
  }
  if (out.media) out.media.info = out.media.info.filter(Boolean)
  return out
}

export function buildGraph(cfg: FlowConfig, extra: Extra, status: Partial<Record<NodeId, NodeStatus>>, selected: NodeId | null) {
  const hasRun = Object.keys(status).length > 0
  const nodes: Node<StepNodeData>[] = NODE_DEFS.map(def => ({
    id: def.id,
    type: 'step',
    position: { x: def.x, y: def.y },
    selected: selected === def.id,
    data: { def, summary: def.summary(cfg, extra), run: status[def.id], dim: hasRun },
  }))
  const reached = (id: NodeId) => !!status[id] && status[id]!.status !== 'skip'
  const edges: Edge[] = EDGES.map(([a, b, out, inp]) => ({
    id: `${a}-${b}`,
    source: a,
    target: b,
    sourceHandle: out,
    targetHandle: inp,
    type: out === 'b' ? 'straight' : 'default',
    animated: reached(a) && reached(b),
    className: reached(a) && reached(b) ? 'done' : undefined,
    style: a === 'admin' ? { strokeDasharray: '5 5' } : undefined,
  }))
  return { nodes, edges }
}
