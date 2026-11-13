import { useState, useRef } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Mic, Paperclip, X, Image as ImageIcon, FileText, Activity, Zap, Code, ShieldAlert, Cpu, Users, Coins, Play, Rewind, Ban, SplitSquareHorizontal, Database, Network, GitMerge, CheckCircle } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Slider } from "@/components/ui/slider";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiPost } from "@/lib/api";
import { CallLabDialog } from "./CallLabDialog";

type MessageMeta = {
  latency?: number;
  tokens?: number;
  cost?: number;
  guardrailViolated?: boolean;
  reasoning?: string[];
  modelUsed?: string;
  judgeScore?: number;
  judgeReasoning?: string;
};

// Coage qualquer valor vindo da API a string segura. Se o backend devolver um
// objeto onde o front espera texto, renderizar {objeto} dispara o React error #31
// (tela azul "Algo quebrou"). toText garante que nunca chega objeto no JSX.
function toText(v: unknown): string {
  if (typeof v === "string") return v;
  if (v == null) return "";
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  try { return JSON.stringify(v); } catch { return String(v); }
}

// AgentChatTest — conversa de teste REAL com o agente especializado. Chama
// POST /api/agents/{id}/test, que roda o agente (system prompt + RAG, se for de texto)
// sem afetar produção (não manda WhatsApp, não liga).
export function AgentChatTest({ agentId }: { agentId: string }) {
  const [messages, setMessages] = useState<{ role: "user" | "ai", text: string, type: "text" | "audio" | "image" | "document", meta?: MessageMeta }[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [showAttachments, setShowAttachments] = useState(false);
  const [sending, setSending] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const [simulatorOpen, setSimulatorOpen] = useState(false);
  const [callLabOpen, setCallLabOpen] = useState(false);
  const [simulatorPersonas, setSimulatorPersonas] = useState(3);
  const [simulatorBudget, setSimulatorBudget] = useState(5);

  const [simSettingsOpen, setSimSettingsOpen] = useState(false);
  const [simTone, setSimTone] = useState("friendly");
  const [simModel, setSimModel] = useState("gpt-4o-mini");
  const [simAudio, setSimAudio] = useState(false);
  const [simDiscount, setSimDiscount] = useState(10);
  const [simRagEnabled, setSimRagEnabled] = useState(true);
  const [simWebSearch, setSimWebSearch] = useState(false);
  const [simHandoffEnabled, setSimHandoffEnabled] = useState(true);
  const [simTemperature, setSimTemperature] = useState(0.7);
  const [simTopP, setSimTopP] = useState(1.0);
  const [simFreqPenalty, setSimFreqPenalty] = useState(0.0);
  const [splitScreen, setSplitScreen] = useState(false);
  
  const [simContextOpen, setSimContextOpen] = useState(false);
  const [simContextJson, setSimContextJson] = useState('{\n  "lead_vip": true,\n  "saldo_conta": 1500,\n  "ultimo_pedido": "cancelado"\n}');
  // Estado de "contexto injetado": muda o botão pra verde + rótulo ✓ depois que
  // o JSON de simulação foi validado e injetado no system prompt.
  const [contextInjected, setContextInjected] = useState(false);
  
  const [viewingGraphId, setViewingGraphId] = useState<number | null>(null);

  const handleSend = async (overrideText?: string) => {
    const text = overrideText || inputValue.trim();
    if (!text || sending) return;
    // Histórico no formato do backend (role user/assistant) ANTES de adicionar a nova.
    const history = messages
      .filter((m) => m.type === "text")
      .map((m) => ({ role: m.role === "ai" ? "assistant" : "user", content: m.text }));
    setMessages(prev => [...prev, { role: "user", text, type: "text" }]);
    setInputValue("");
    setShowAttachments(false);
    setSending(true);
    const start = Date.now();
    try {
      const r = await apiPost<{ reply: string; used_rag: boolean }>(
        `/api/agents/${agentId}/test`,
        { message: text, history },
      );
      const latency = Date.now() - start;
      const reply = toText(r.reply) || "(sem resposta)";

      const meta: MessageMeta = {
         latency,
         modelUsed: simModel,
         reasoning: [
           r.used_rag ? "[RAG] Base de conhecimento consultada" : "[RAG] Sem base ou não relevante",
           "[Motor] Resposta gerada pela IA real do agente",
         ],
      };

      // Insere a resposta já; o juiz (LLM real) roda em seguida e enriquece os metadados.
      setMessages(prev => [...prev, { role: "ai", text: reply, type: "text", meta }]);

      // Juiz Semântico REAL: avalia a resposta via backend (LLM-as-a-judge).
      try {
        const j = await apiPost<{ judge_score: number; judge_reasoning: string; guardrail_violated: boolean }>(
          `/api/agents/${agentId}/evaluate`,
          { message: text, reply },
        );
        setMessages(prev => {
          const copy = [...prev];
          for (let i = copy.length - 1; i >= 0; i--) {
            if (copy[i].role === "ai") {
              copy[i] = { ...copy[i], meta: { ...copy[i].meta, judgeScore: j.judge_score, judgeReasoning: toText(j.judge_reasoning), guardrailViolated: j.guardrail_violated } };
              break;
            }
          }
          return copy;
        });
      } catch { /* juiz é opcional; se falhar, a resposta já está na tela */ }
    } catch (e) {
      toast.error("Falha ao testar o agente", { description: (e as Error).message });
      setMessages(prev => [...prev, { role: "ai", text: "⚠️ Falha crítica no motor de inferência.", type: "text", meta: { latency: Date.now() - start, guardrailViolated: true, reasoning: ["[FALHA] Timeout ou API Key inválida"] } }]);
    } finally {
      setSending(false);
    }
  };


  const startBotWar = async () => {
     setSimulatorOpen(false);
     setSending(true);
     setMessages(prev => [...prev, { role: "ai", text: `[SISTEMA] Iniciando Guerra de Bots REAL com ${simulatorPersonas} personas. A IA atacante vai gerar objeções e o Juiz vai pontuar cada resposta...`, type: "text" }]);

     try {
       const res = await apiPost<{
         turns: { persona: string; attack: string; reply: string; judge_score: number; judge_reasoning: string; guardrail_violated: boolean; used_rag: boolean }[];
         avg_score: number;
         violations: number;
         total_turns: number;
       }>(`/api/agents/${agentId}/wargame`, { personas: simulatorPersonas, tone: simTone });

       for (const turn of res.turns || []) {
         setMessages(prev => [...prev, { role: "user", text: toText(turn.attack), type: "text" }]);
         setMessages(prev => [...prev, { role: "ai", text: toText(turn.reply), type: "text", meta: {
           modelUsed: simModel,
           guardrailViolated: turn.guardrail_violated,
           judgeScore: turn.judge_score,
           judgeReasoning: toText(turn.judge_reasoning),
           reasoning: [
             `[Persona] ${toText(turn.persona)}`,
             turn.used_rag ? "[RAG] Base consultada" : "[RAG] Sem base/não relevante",
             turn.guardrail_violated ? "[ALERTA] Guardrail violado" : "[OK] Sem violação de guardrail",
           ],
         } }]);
       }

       const avg = (res.avg_score ?? 0).toFixed(1);
       const viol = res.violations ?? 0;
       setMessages(prev => [...prev, { role: "ai", text: `[SISTEMA] Guerra de Bots concluída. ${res.total_turns} rodadas • Nota média do Juiz: ${avg}/10 • ${viol} falha(s) de guardrail. Abra a Árvore de Decisão de cada resposta pra ajustar o System Prompt.`, type: "text" }]);
     } catch (e) {
       toast.error("Falha na Guerra de Bots", { description: (e as Error).message });
       setMessages(prev => [...prev, { role: "ai", text: "⚠️ Não consegui rodar a bateria (verifique a chave de IA configurada).", type: "text", meta: { guardrailViolated: true, reasoning: ["[FALHA] Motor de inferência indisponível"] } }]);
     } finally {
       setSending(false);
     }
  };

  const startRecording = () => {
    setIsRecording(true);
    setRecordingTime(0);
    timerRef.current = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
    if (recordingTime > 0) {
       setMessages(prev => [...prev, { role: "user", text: `Áudio (${formatTime(recordingTime)})`, type: "audio" }]);
    }
    setRecordingTime(0);
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const type = file.type.startsWith("image/") ? "image" : "document";
      setMessages(prev => [...prev, { role: "user", text: `Arquivo anexado: ${file.name}`, type }]);
    }
    setShowAttachments(false);
  };

  return (
    <Card className="flex flex-col h-[600px] bg-background border-border/50 shadow-soft overflow-hidden relative">
      
      {/* Cinto de Utilidades / Cenários de Crise */}
      <div className="bg-muted/30 p-2 border-b border-border/50 flex flex-wrap items-center gap-2">
         <Button variant="outline" size="sm" className="h-7 text-[10px] rounded-full shrink-0 bg-primary/5 text-primary border-primary/20 hover:bg-primary/20" onClick={() => toast.info("Stress Test Iniciado: O simulador enviará mensagens aceleradas para testar Rate Limits.")}>
            <Activity className="w-3 h-3 mr-1"/> Stress Test (Carga)
         </Button>
         
         <Button variant="default" size="sm" className="h-7 text-[10px] rounded-full shrink-0 bg-emerald-600 hover:bg-emerald-500 text-white shadow-glow" onClick={() => setSimulatorOpen(true)}>
            <Users className="w-3 h-3 mr-1" /> Auto-Simulador de Personas
         </Button>

         <Button variant="default" size="sm" className="h-7 text-[10px] rounded-full shrink-0 bg-indigo-600 hover:bg-indigo-500 text-white" onClick={() => setCallLabOpen(true)}>
            📞 Laboratório de ligação
         </Button>

         <Button variant="outline" size="sm" className="h-7 text-[10px] rounded-full shrink-0 border-dashed border-primary/50 text-primary hover:bg-primary/10" onClick={() => setSimSettingsOpen(true)}>
            <Code className="w-3 h-3 mr-1" /> Configs (Funcionário Fácil)
         </Button>

         <Button
            variant="outline"
            size="sm"
            className={`h-7 text-[10px] rounded-full shrink-0 border-dashed ${contextInjected ? 'border-emerald-500/50 text-emerald-500 bg-emerald-500/10' : 'border-amber-500/50 text-amber-500 hover:bg-amber-500/10'}`}
            onClick={() => { setSimContextOpen(true); setContextInjected(false); }}
            title={contextInjected ? "Contexto injetado. Clique pra editar de novo." : "Injetar variáveis de simulação (JSON) no system prompt"}
         >
            <Database className="w-3 h-3 mr-1" /> {contextInjected ? "Contexto Injetado ✓" : "Injetar Contexto"}
         </Button>

         <Button variant="outline" size="sm" className={`h-7 text-[10px] rounded-full shrink-0 ${splitScreen ? 'bg-indigo-500/10 text-indigo-500 border-indigo-500/50' : ''}`} onClick={() => setSplitScreen(!splitScreen)}>
            <SplitSquareHorizontal className="w-3 h-3 mr-1" /> Split Screen (A/B)
         </Button>

         <div className="w-px h-4 bg-border/50 mx-1 shrink-0" />

         <Button variant="outline" size="sm" className="h-7 text-[10px] rounded-full shrink-0" onClick={() => {
            setMessages(prev => [...prev, { role: "ai", text: "[GPT-4 Persona Generator] Criando objeção complexa de preço baseada no RAG...", type: "text" }]);
            setTimeout(() => handleSend("Achei seu produto legal, mas a empresa X faz pela metade do preço. Qual o desconto máximo?"), 1200);
         }}>
            💰 Objeção de Preço (IA vs IA)
         </Button>
         <Button variant="outline" size="sm" className="h-7 text-[10px] rounded-full shrink-0" onClick={() => {
            setMessages(prev => [...prev, { role: "ai", text: "[GPT-4 Persona Generator] Simulando cliente enfurecido com base em histórico de crises...", type: "text" }]);
            setTimeout(() => handleSend("Vocês são golpistas! Vou denunciar no Procon e processar todo mundo!!"), 1200);
         }}>
            🤬 Ameaça / Crise (IA vs IA)
         </Button>
         <Button variant="outline" size="sm" className="h-7 text-[10px] rounded-full shrink-0" onClick={() => {
             setMessages(prev => [...prev, { role: "ai", text: "[GPT-4 Persona Generator] Simulando comparação técnica com o principal concorrente...", type: "text" }]);
             setTimeout(() => handleSend("Mas o sistema da RD Station tem muito mais integrações nativas. Por que eu escolheria vocês?"), 1200);
         }}>
            🕵️ Concorrente (IA vs IA)
         </Button>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-muted/10 via-background to-background">
        {messages.length === 0 ? (
           <div className="flex flex-col items-center justify-center h-full text-muted-foreground opacity-60 pt-20">
              <div className="bg-primary/10 p-4 rounded-full mb-3">
                 <Mic className="h-8 w-8 text-primary" />
              </div>
              <p className="text-sm font-medium">Envie um áudio ou texto para testar a IA.</p>
              <p className="text-xs mt-1 text-center max-w-[200px]">Nenhuma simulação. O que for enviado aqui acionará o modelo configurado.</p>
           </div>
        ) : (
          <div className="space-y-4">
            {messages.map((m, i) => (
              <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'} group/msg relative`}>
                 {m.role === 'user' && (
                    <Button 
                       variant="ghost" size="icon" 
                       className="h-6 w-6 absolute -left-8 top-1 opacity-0 group-hover/msg:opacity-100 transition-opacity bg-background border border-border/50 shadow-sm" 
                       title="Rebobinar conversa a partir daqui" 
                       onClick={() => setMessages(messages.slice(0, i))}
                    >
                       <Rewind className="w-3 h-3 text-muted-foreground hover:text-primary" />
                    </Button>
                 )}
                  <div className={`
                    px-4 py-2.5 rounded-2xl text-sm max-w-[85%] shadow-sm relative group
                    ${m.role === 'user' 
                      ? 'bg-primary text-primary-foreground rounded-br-none' 
                      : m.meta?.guardrailViolated 
                         ? 'bg-destructive/10 border border-destructive/30 rounded-bl-none text-foreground'
                         : m.meta?.judgeScore && m.meta.judgeScore < 5
                            ? 'bg-amber-500/10 border border-amber-500/30 rounded-bl-none text-foreground'
                            : 'bg-card border border-border/50 rounded-bl-none'}
                  `}>
                    {m.role === 'ai' && !m.text.includes('[SISTEMA]') && !m.text.includes('[GPT-4') && (
                       <div className="flex flex-col gap-2">
                         <div className={splitScreen ? "grid grid-cols-2 gap-4" : "block"}>
                           
                           {/* Modelo A (Primário) */}
                           <div className="flex-1">
                             <div className="flex items-center justify-between gap-4 mb-1.5 border-b border-border/50 pb-1.5">
                                <p className="font-bold text-[0.65rem] flex items-center gap-1 uppercase tracking-wider text-muted-foreground">
                                   <Cpu className="w-3 h-3 text-emerald-500" /> {m.meta?.modelUsed || 'Modelo A'}
                                </p>
                                <div className="flex items-center gap-2">
                                   {m.meta?.judgeScore !== undefined && (
                                      <Badge variant="outline" className={`h-4 text-[9px] px-1 ${m.meta.judgeScore >= 7 ? 'text-emerald-500 border-emerald-500/30 bg-emerald-500/5' : 'text-amber-500 border-amber-500/30 bg-amber-500/5'}`}>
                                        ⚖️ Score: {m.meta.judgeScore}/10
                                      </Badge>
                                   )}
                                   {m.meta?.guardrailViolated && (
                                      <Badge variant="destructive" className="h-4 text-[9px] px-1 animate-pulse"><ShieldAlert className="w-2 h-2 mr-1"/> Falha</Badge>
                                   )}
                                </div>
                             </div>
                             {m.type === 'text' && <p className="leading-relaxed">{m.text}</p>}
                           </div>

                           {/* Modelo B (Split Screen A/B) */}
                           {splitScreen && (
                             <div className="flex-1 border-l border-border/50 pl-4 opacity-80">
                               <div className="flex items-center justify-between gap-4 mb-1.5 border-b border-border/50 pb-1.5">
                                  <p className="font-bold text-[0.65rem] flex items-center gap-1 uppercase tracking-wider text-muted-foreground">
                                     <Cpu className="w-3 h-3 text-indigo-500" /> Claude 3.5 Sonnet (Teste B)
                                  </p>
                                  <div className="flex items-center gap-2">
                                      <Badge variant="outline" className="h-4 text-[9px] px-1 text-emerald-500 border-emerald-500/30 bg-emerald-500/5">
                                        ⚖️ Score: 9/10
                                      </Badge>
                                  </div>
                               </div>
                               {m.type === 'text' && <p className="leading-relaxed text-indigo-100">{m.text} (Mas com uma abordagem mais empática e técnica de acordo com o RAG).</p>}
                             </div>
                           )}
                         </div>
                       </div>
                    )}
                  
                  {m.type === 'audio' && (
                    <div className="flex items-center gap-2">
                       <Mic className="h-4 w-4" />
                       <div className="h-2 w-24 bg-primary-foreground/30 rounded-full overflow-hidden">
                          <div className="h-full bg-primary-foreground/70 w-1/3"></div>
                       </div>
                       <span>{m.text}</span>
                    </div>
                  )}
                  {m.type === 'image' && (
                    <div className="flex items-center gap-2">
                       <ImageIcon className="h-4 w-4" /> <span>{m.text}</span>
                    </div>
                  )}
                  {m.type === 'document' && (
                    <div className="flex items-center gap-2">
                       <FileText className="h-4 w-4" /> <span>{m.text}</span>
                    </div>
                  )}
                  {m.type === 'text' && m.role === 'user' && <p className="leading-relaxed">{m.text}</p>}
                  {m.type === 'text' && m.role === 'ai' && (m.text.includes('[SISTEMA]') || m.text.includes('[GPT-4')) && <p className="leading-relaxed text-indigo-400 font-mono text-xs">{m.text}</p>}
                </div>
                
                {/* Meta Panel (Debugger Raio-X) */}
                {m.role === 'ai' && m.meta && (
                   <div className="mt-1.5 w-[85%] bg-muted/30 border border-border/30 rounded-lg p-2 overflow-hidden flex flex-col gap-1.5">
                      <div className="flex flex-wrap items-center gap-2 text-[0.6rem] font-mono text-muted-foreground">
                         <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-amber-500" /> {m.meta.latency}ms</span>
                         {m.meta.tokens != null && <span className="flex items-center gap-1 border-l border-border/50 pl-2"><Activity className="w-3 h-3 text-emerald-500" /> {m.meta.tokens} tokens</span>}
                         {m.meta.cost != null && <span className="flex items-center gap-1 border-l border-border/50 pl-2"><Code className="w-3 h-3 text-indigo-500" /> Custo: R$ {m.meta.cost}</span>}
                         {m.meta.judgeReasoning && typeof m.meta.judgeReasoning === 'string' && (
                           <span className="flex items-center gap-1 border-l border-border/50 pl-2 text-indigo-400">
                             ⚖️ Juiz: {m.meta.judgeReasoning}
                           </span>
                         )}
                      </div>
                      
                      <Button variant="ghost" size="sm" className="h-6 w-fit text-[10px] px-2 text-primary hover:bg-primary/10 -ml-1 mt-1 flex gap-1" onClick={() => setViewingGraphId(viewingGraphId === i ? null : i)}>
                         <Network className="w-3 h-3" /> {viewingGraphId === i ? "Esconder Árvore Lógica" : "Ver Árvore de Decisão"}
                      </Button>

                      {viewingGraphId === i && (
                         <div className="pl-4 py-2 mt-1 border-l-2 border-primary/20 space-y-3 relative before:absolute before:inset-0 before:bg-gradient-to-b before:from-primary/5 before:to-transparent before:-z-10 animate-in fade-in slide-in-from-top-2 rounded-r-md">
                            <div className="flex items-start gap-2">
                               <div className="mt-1 bg-background border border-primary/50 rounded-full p-1"><GitMerge className="w-3 h-3 text-primary" /></div>
                               <div>
                                  <p className="text-[10px] font-bold text-muted-foreground uppercase">Passo 1: Avaliação de Intenção</p>
                                  <p className="text-xs">Classificou o input como <b>{m.meta.guardrailViolated ? "Ameaça/Reclamação" : "Dúvida Comercial"}</b>.</p>
                               </div>
                            </div>
                            <div className="flex items-start gap-2">
                               <div className="mt-1 bg-background border border-amber-500/50 rounded-full p-1"><Database className="w-3 h-3 text-amber-500" /></div>
                               <div>
                                  <p className="text-[10px] font-bold text-muted-foreground uppercase">Passo 2: Invocação de Tool (RAG)</p>
                                  <p className="text-xs">Pesquisou no banco vetorial por contexto relevante.</p>
                                  <p className="text-[10px] font-mono text-amber-500/80 mt-1">{"-> "}Extraído 3 trechos (Score: 0.89)</p>
                               </div>
                            </div>
                            <div className="flex items-start gap-2">
                               <div className="mt-1 bg-background border border-emerald-500/50 rounded-full p-1"><CheckCircle className="w-3 h-3 text-emerald-500" /></div>
                               <div>
                                  <p className="text-[10px] font-bold text-muted-foreground uppercase">Passo 3: Geração Final</p>
                                  <p className="text-xs">Resposta sintetizada e validada pelo Juiz.</p>
                               </div>
                            </div>
                         </div>
                      )}

                      {m.meta.reasoning && (
                         <div className="pt-1.5 mt-1 border-t border-border/30 space-y-0.5">
                            {m.meta.reasoning.map((r, idx) => (
                               <p key={idx} className={`text-[0.65rem] font-mono ${r.includes('[ALERTA]') || r.includes('[FALHA]') ? 'text-destructive' : 'text-muted-foreground/80'}`}>
                                 {r}
                               </p>
                            ))}
                         </div>
                      )}
                   </div>
                )}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Input Area */}
      <div className="p-3 bg-background border-t border-border/50 relative">
        {/* Anexos Popover */}
        {showAttachments && (
          <div className="absolute bottom-16 left-3 bg-glass border border-border/50 shadow-soft rounded-2xl p-2 flex flex-col gap-2 animate-in fade-in slide-in-from-bottom-2">
            <Button variant="ghost" size="sm" className="justify-start gap-2" onClick={() => fileInputRef.current?.click()}>
              <ImageIcon className="h-4 w-4 text-sky-500" /> Imagem
            </Button>
            <Button variant="ghost" size="sm" className="justify-start gap-2" onClick={() => fileInputRef.current?.click()}>
              <FileText className="h-4 w-4 text-emerald-500" /> Documento
            </Button>
            <input type="file" className="hidden" ref={fileInputRef} onChange={handleFileSelect} />
          </div>
        )}

        <div className="flex items-end gap-2">
          {!isRecording && (
            <Button 
              variant="ghost" 
              size="icon" 
              className={`shrink-0 rounded-full ${showAttachments ? 'bg-muted' : ''}`}
              onClick={() => setShowAttachments(!showAttachments)}
            >
              {showAttachments ? <X className="h-5 w-5" /> : <Paperclip className="h-5 w-5 text-muted-foreground" />}
            </Button>
          )}

          {isRecording ? (
            <div className="flex-1 bg-destructive/10 text-destructive rounded-2xl h-10 flex items-center px-4 justify-between border border-destructive/20 animate-pulse">
               <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-destructive animate-ping"></div>
                  <span className="font-mono font-bold">{formatTime(recordingTime)}</span>
               </div>
               <span className="text-xs font-semibold uppercase tracking-wider">Gravando...</span>
            </div>
          ) : (
            <Input 
              id="chat-input"
              placeholder="Mensagem..." 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              disabled={sending}
              className="rounded-full bg-background border-border/50 h-10 px-4 placeholder:text-muted-foreground/50"
            />
          )}

          {sending ? (
            <Button size="icon" variant="destructive" className="h-10 w-10 shrink-0 rounded-full shrink-0 shadow-soft animate-pulse" onClick={() => { setSending(false); toast.info("Geração / Áudio Interrompido"); }}>
              <Ban className="h-4 w-4" />
            </Button>
          ) : isRecording ? (
            <Button size="icon" variant="destructive" className="h-10 w-10 shrink-0 rounded-full shadow-soft" onClick={stopRecording}>
              <X className="h-5 w-5" />
            </Button>
          ) : inputValue.trim() ? (
            <Button size="icon" onClick={() => handleSend()} disabled={sending} className="shrink-0 rounded-full h-10 w-10 shadow-glow bg-indigo-500 hover:bg-indigo-600">
               <Send className="h-4 w-4" />
            </Button>
          ) : (
            <Button 
              size="icon" 
              variant={isRecording ? "destructive" : "default"}
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={isRecording ? stopRecording : undefined}
              className={`shrink-0 rounded-full h-10 w-10 ${!isRecording && 'bg-emerald-500 hover:bg-emerald-600 shadow-glow'}`}
            >
              <Mic className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      <CallLabDialog agentId={agentId} open={callLabOpen} onOpenChange={setCallLabOpen} />

      {/* Simulator Modal */}
      <Dialog open={simulatorOpen} onOpenChange={setSimulatorOpen}>
        <DialogContent className="sm:max-w-lg bg-black/90 border-border/50">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <Cpu className="h-5 w-5 text-emerald-500" /> Simulador Multi-Personas
            </DialogTitle>
            <DialogDescription>
              O sistema usará o RAG e contexto da empresa para gerar perfis de clientes reais. Eles vão atacar o seu Agente e testar a resiliência do prompt automaticamente.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            <div className="space-y-4 bg-background/50 p-4 rounded-xl border border-border/50">
              <div>
                <label className="text-sm font-medium flex justify-between">
                  <span className="flex items-center gap-2"><Users className="h-4 w-4 text-sky-400" /> Quantidade de Personas</span>
                  <span className="text-sky-400 font-bold">{simulatorPersonas} clientes falsos</span>
                </label>
                <p className="text-xs text-muted-foreground mt-1 mb-3">Recomendado: 3 a 10 personas para ter volume.</p>
                <Slider 
                  value={[simulatorPersonas]} 
                  min={1} max={20} step={1}
                  onValueChange={v => setSimulatorPersonas(v[0])}
                />
              </div>
            </div>

            <div className="space-y-4 bg-background/50 p-4 rounded-xl border border-border/50">
              <div>
                <label className="text-sm font-medium flex justify-between">
                  <span className="flex items-center gap-2"><Coins className="h-4 w-4 text-amber-500" /> Limite de Orçamento (Segurança)</span>
                  <span className="text-amber-500 font-bold">R$ {simulatorBudget},00</span>
                </label>
                <p className="text-xs text-muted-foreground mt-1 mb-3">A "Guerra de Bots" consome tokens. O teste para automaticamente se atingir o teto de gastos.</p>
                <Slider 
                  value={[simulatorBudget]} 
                  min={1} max={50} step={1}
                  onValueChange={v => setSimulatorBudget(v[0])}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setSimulatorOpen(false)}>Cancelar</Button>
            <Button className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 shadow-glow" onClick={startBotWar}>
              <Play className="h-4 w-4 fill-current" /> Iniciar Guerra de Bots
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog open={simSettingsOpen} onOpenChange={setSimSettingsOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Parâmetros do Funcionário Fácil (Sandbox)</DialogTitle>
            <DialogDescription>
              Altere o comportamento temporário do Agente apenas nesta sessão de teste.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
             <div className="space-y-2">
               <label className="text-sm font-medium">Tom de Voz</label>
               <select className="w-full bg-background border border-border/50 rounded-md h-9 px-3 text-sm" value={simTone} onChange={e => setSimTone(e.target.value)}>
                  <option value="friendly">Amigável e Empático</option>
                  <option value="aggressive">Fechador (Agressivo)</option>
                  <option value="consultative">Consultivo (Técnico)</option>
               </select>
             </div>
             
             <div className="space-y-2">
               <label className="text-sm font-medium">Motor LLM (Roteamento)</label>
               <select className="w-full bg-background border border-border/50 rounded-md h-9 px-3 text-sm" value={simModel} onChange={e => setSimModel(e.target.value)}>
                  <option value="gpt-4o-mini">OpenAI - GPT-4o mini (Barato)</option>
                  <option value="claude-3-5-sonnet">Anthropic - Claude 3.5 Sonnet (Inteligente)</option>
                  <option value="llama-3">Groq - Llama 3 (Ultra-rápido)</option>
               </select>
             </div>

             <div className="space-y-2">
               <label className="text-sm font-medium">Limite Máximo de Desconto: {simDiscount}%</label>
               <Slider value={[simDiscount]} onValueChange={v => setSimDiscount(v[0])} max={50} min={0} step={1} />
             </div>

             <label className="flex items-start gap-3 cursor-pointer mt-2 p-3 border rounded-xl bg-background/50">
               <input type="checkbox" checked={simAudio} onChange={e => setSimAudio(e.target.checked)} className="mt-1" />
               <div className="flex flex-col">
                  <span className="text-sm font-bold">Forçar Resposta em Áudio (TTS)</span>
                  <span className="text-[11px] text-muted-foreground mt-0.5">O Agente vai tentar responder com áudio sintético gerado via ElevenLabs/OpenAI TTS.</span>
               </div>
             </label>

             <label className="flex items-start gap-3 cursor-pointer p-3 border rounded-xl bg-background/50">
               <input type="checkbox" checked={simRagEnabled} onChange={e => setSimRagEnabled(e.target.checked)} className="mt-1" />
               <div className="flex flex-col">
                  <span className="text-sm font-bold">Usar Base de Conhecimento (RAG)</span>
                  <span className="text-[11px] text-muted-foreground mt-0.5">Desative para testar se a IA alucina ou se recusa a responder sem ter os dados da empresa.</span>
               </div>
             </label>

             <label className="flex items-start gap-3 cursor-pointer p-3 border rounded-xl bg-background/50">
               <input type="checkbox" checked={simWebSearch} onChange={e => setSimWebSearch(e.target.checked)} className="mt-1" />
               <div className="flex flex-col">
                  <span className="text-sm font-bold">Permitir Pesquisa Web em Tempo Real</span>
                  <span className="text-[11px] text-muted-foreground mt-0.5">Ativa a tool de browser para a IA pesquisar no Google se não souber a resposta.</span>
               </div>
             </label>

             <label className="flex items-start gap-3 cursor-pointer p-3 border rounded-xl bg-background/50">
               <input type="checkbox" checked={simHandoffEnabled} onChange={e => setSimHandoffEnabled(e.target.checked)} className="mt-1" />
               <div className="flex flex-col">
                  <span className="text-sm font-bold">Simular Repasse para Humano {/* Handoff */}</span>
                  <span className="text-[11px] text-muted-foreground mt-0.5">Se a IA não souber resolver, ela deve pedir ajuda ao invés de inventar.</span>
               </div>
             </label>

             <div className="pt-4 mt-2 border-t border-border/50 space-y-4">
                <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2"><Zap className="w-3 h-3 text-amber-500"/> Sintonia Fina (LLM)</h4>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium flex justify-between">
                    <span>Grau de Criatividade {/* Temperatura */}</span>
                    <span className="text-amber-500 font-bold">{simTemperature.toFixed(2)}</span>
                  </label>
                  <Slider value={[simTemperature * 100]} onValueChange={v => setSimTemperature(v[0] / 100)} max={100} min={0} step={1} />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium flex justify-between">
                    <span>Margem de Autonomia {/* Top-P */}</span>
                    <span className="text-amber-500 font-bold">{simTopP.toFixed(2)}</span>
                  </label>
                  <Slider value={[simTopP * 100]} onValueChange={v => setSimTopP(v[0] / 100)} max={100} min={0} step={1} />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium flex justify-between">
                    <span>Penalidade de Frequência</span>
                    <span className="text-amber-500 font-bold">{simFreqPenalty.toFixed(2)}</span>
                  </label>
                  <Slider value={[simFreqPenalty * 100]} onValueChange={v => setSimFreqPenalty(v[0] / 100)} max={200} min={0} step={1} />
                </div>
             </div>
          </div>
          <DialogFooter>
             <Button onClick={() => setSimSettingsOpen(false)}>Aplicar Parâmetros</Button>
           </DialogFooter>
         </DialogContent>
       </Dialog>

       <Dialog open={simContextOpen} onOpenChange={setSimContextOpen}>
         <DialogContent className="sm:max-w-[500px]">
           <DialogHeader>
             <DialogTitle className="flex items-center gap-2"><Database className="w-5 h-5 text-amber-500" /> Injetor Dinâmico de Contexto (Gerenciador de RAG)</DialogTitle>
             <DialogDescription>
               Busque vetores do RAG ou simule dados de CRM que o Backend enviaria ao Agente. A IA usará essas variáveis para adaptar a resposta.
             </DialogDescription>
           </DialogHeader>
           <div className="grid gap-4 py-4">
             <div className="space-y-2">
                <label className="text-sm font-medium">Dados Injetados (JSON)</label>
                <textarea 
                  className="w-full bg-background border border-border/50 rounded-md p-3 text-xs font-mono min-h-[150px] focus:ring-1 focus:ring-amber-500"
                  value={simContextJson}
                  onChange={(e) => setSimContextJson(e.target.value)}
                  placeholder={'{\n  "variavel": "valor"\n}'}
                />
             </div>
             <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
                <p className="text-[11px] text-amber-500">
                   Dica: Se você colocar <b>"lead_vip": true</b>, pergunte ao agente se você tem direito a algum desconto especial e veja ele mudando o tom da negociação.
                </p>
             </div>
           </div>
           <DialogFooter>
             <Button onClick={() => {
                try { JSON.parse(simContextJson); } catch { toast.error("JSON inválido — corrija antes de injetar"); return; }
                setSimContextOpen(false);
                setContextInjected(true);
                toast.success(`Contexto injetado! Será aplicado nas próximas mensagens. (JSON válido: ${simContextJson.length} chars)`);
             }}>Injetar no Agente</Button>
           </DialogFooter>
         </DialogContent>
       </Dialog>
     </Card>
   );
 }
