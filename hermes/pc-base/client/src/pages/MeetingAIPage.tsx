import { useState, useEffect } from "react";
import { Video, Plus, Loader2, AlertTriangle, Link as LinkIcon, Settings2, Ear, Mic, BrainCircuit, Bot, Send, ShieldCheck, Activity, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { apiGet, apiPost } from "@/lib/api";
import { setView } from "@/stores/navigation";

type MeetLine = { who: string; text: string; kind: "system" | "participant" | "ai" };

export function MeetingAIPage() {
  const [meetingUrl, setMeetingUrl] = useState("");
  const [selectedAgent, setSelectedAgent] = useState("");
  const [swarmAgent, setSwarmAgent] = useState("");
  const [agents, setAgents] = useState<any[]>([]);
  const [agentsState, setAgentsState] = useState<"loading" | "ok" | "error">("loading");
  const [meetingContext, setMeetingContext] = useState("");
  const [aiName, setAiName] = useState("Athena");
  const [role, setRole] = useState("participant");
  const [wakeWord, setWakeWord] = useState("Athena,");
  const [listenMode, setListenMode] = useState("continuous");
  const [postAction, setPostAction] = useState("email_summary");
  const [autoMute, setAutoMute] = useState(true);
  const [isJoined, setIsJoined] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [liveLines, setLiveLines] = useState<MeetLine[]>([]);
  const [whisper, setWhisper] = useState("");
  const [sending, setSending] = useState(false);

  // Agentes REAIS da conta. Antes, sem agentes (ou com erro), a tela inventava um agente
  // "Athena (Assistente Padrão)" com id "mock" — que não existe no servidor.
  const loadAgents = () => {
    setAgentsState("loading");
    apiGet<{ profiles: any[] }>("/api/agent-profiles")
      .then((r) => {
        const list = r.profiles ?? [];
        setAgents(list);
        setSelectedAgent((cur) => (cur && list.some((a) => a.id === cur) ? cur : list[0]?.id ?? ""));
        setAgentsState("ok");
      })
      .catch(() => setAgentsState("error"));
  };
  useEffect(() => { loadAgents(); }, []);
  
  const handleJoin = async () => {
    if (!selectedAgent) {
      toast.error("Escolha um agente de IA primeiro.");
      return;
    }
    if (!meetingUrl.includes("meet.google.com") && !meetingUrl.includes("zoom.us")) {
      toast.error("Insira um link válido do Google Meet ou Zoom.");
      return;
    }
    setSending(true);
    // Testa o CÉREBRO ao vivo: manda uma fala com a wake-word pro backend e confirma que
    // o agente responde. O gate wake-word/auto é o mesmo que o worker de áudio usa.
    try {
      const probe = `${wakeWord} apresente-se rapidamente para a reunião.`;
      const r = await apiPost<{ should_respond: boolean; reply?: string }>("/api/meet/turn", {
        profile: selectedAgent, transcript: probe, meeting: meetingUrl,
      });
      setIsJoined(true);
      setShowTranscript(true);
      setLiveLines([
        { who: "Sistema", kind: "system", text: `Cérebro do "${aiName}" ativo e respondendo. Ponte de áudio: rode o worker (meet_agent_worker.py) no host com mic virtual para entrar na sala de verdade.` },
        { who: "Você (teste)", kind: "participant", text: probe },
        ...(r.reply ? [{ who: aiName, kind: "ai" as const, text: r.reply }] : []),
      ]);
      toast.success("Cérebro da reunião validado! Responde à wake-word.");
    } catch (e) {
      toast.error("Falha ao validar o cérebro da reunião", { description: (e as Error).message });
    } finally {
      setSending(false);
    }
  };

  const handleWhisper = async () => {
    const text = whisper.trim();
    if (!text || sending) return;
    setWhisper("");
    setLiveLines(prev => [...prev, { who: "Você (sussurro)", kind: "participant", text }]);
    setSending(true);
    try {
      const r = await apiPost<{ should_respond: boolean; reply?: string; reason?: string }>("/api/meet/turn", {
        profile: selectedAgent, transcript: text, meeting: meetingUrl,
      });
      if (r.should_respond && r.reply) {
        setLiveLines(prev => [...prev, { who: aiName, kind: "ai", text: r.reply! }]);
      } else {
        setLiveLines(prev => [...prev, { who: "Sistema", kind: "system", text: `(${aiName} ficou em silêncio: ${r.reason || "sem gatilho"}). Chame pela wake-word "${wakeWord}" para forçar resposta.` }]);
      }
    } catch (e) {
      toast.error("Falha ao processar", { description: (e as Error).message });
    } finally {
      setSending(false);
    }
  };

  const handleLeave = () => {
    setIsJoined(false);
    setLiveLines([]);
    toast.info("A IA saiu da reunião.");
  };

  if (agentsState !== "ok" || agents.length === 0) {
    return (
      <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Video className="w-6 h-6 text-emerald-500" />
            IA em Reuniões
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Envie sua IA para participar de calls no Google Meet ou Zoom, ouvir a conversa e responder quando for chamada pelo nome.
          </p>
        </div>
        <Card className="p-8 bg-glass border border-border/50 shadow-soft max-w-xl mx-auto text-center space-y-4">
          {agentsState === "loading" && (
            <p className="text-sm text-muted-foreground flex items-center justify-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Carregando seus agentes…</p>
          )}
          {agentsState === "error" && (
            <>
              <p className="text-sm text-destructive flex items-center justify-center gap-2"><AlertTriangle className="w-4 h-4" /> Não consegui carregar seus agentes.</p>
              <Button variant="outline" onClick={loadAgents}>Tentar de novo</Button>
            </>
          )}
          {agentsState === "ok" && agents.length === 0 && (
            <>
              <Bot className="w-12 h-12 mx-auto text-muted-foreground opacity-50" />
              <div>
                <h3 className="font-semibold">Você ainda não tem um agente de IA</h3>
                <p className="text-sm text-muted-foreground mt-1">A IA da reunião usa um dos seus agentes (prompt, voz e base de conhecimento). Crie um para começar.</p>
              </div>
              <Button onClick={() => setView("specialized")} className="gap-2"><Plus className="w-4 h-4" /> Criar agente</Button>
            </>
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Video className="w-6 h-6 text-emerald-500" />
            IA em Reuniões
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Envie sua IA para participar de calls no Google Meet ou Zoom, ouvir a conversa e responder quando for chamada pelo nome.
          </p>
        </div>
        {!isJoined && (
          <Badge className="bg-primary/10 text-primary border-primary/20 shrink-0">
            Bot Disponível
          </Badge>
        )}
        {isJoined && (
          <Badge className="bg-emerald-500/20 text-emerald-500 border-emerald-500/30 shrink-0 animate-pulse">
            <Mic className="w-3 h-3 mr-1" /> Ouvindo Reunião...
          </Badge>
        )}
      </div>

      <div className={`grid grid-cols-1 ${showTranscript ? 'lg:grid-cols-12' : ''} gap-6`}>
        {/* Painel de Controle */}
        <div className={`space-y-6 ${showTranscript ? 'lg:col-span-5' : 'max-w-4xl mx-auto w-full'}`}>
          <Card className="p-5 bg-glass border border-border/50 shadow-soft">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold flex items-center gap-2">
                <LinkIcon className="w-4 h-4 text-primary" /> Entrada na Sala
              </h3>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowTranscript(!showTranscript)}
                className="h-8 text-xs font-medium bg-background/50 border-border/50"
              >
                <Ear className="w-3.5 h-3.5 mr-1.5" />
                {showTranscript ? "Ocultar Transcrição" : "Acompanhar Transcrição"}
              </Button>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Link do Google Meet ou Zoom</Label>
                <Input
                  placeholder="https://meet.google.com/abc-defg-hij"
                  value={meetingUrl}
                  onChange={(e) => setMeetingUrl(e.target.value)}
                  disabled={isJoined}
                  className="bg-background/50 rounded-xl"
                />
              </div>
              <Button
                className="w-full rounded-xl gap-2 bg-emerald-500 hover:bg-emerald-600 text-white"
                onClick={isJoined ? handleLeave : handleJoin}
                disabled={sending}
                variant={isJoined ? "destructive" : "default"}
              >
                {isJoined ? (
                  <>Remover IA da Sala</>
                ) : (
                  <>{sending ? "Validando cérebro..." : <>Ativar IA da Reunião <Send className="w-4 h-4" /></>}</>
                )}
              </Button>
            </div>
          </Card>

          <Card className="p-5 bg-glass border border-border/50 shadow-soft">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Settings2 className="w-4 h-4 text-primary" /> Configurações de Comportamento
            </h3>
            <p className="text-[11px] text-amber-500 -mt-2 mb-4">
              Por enquanto vale só o <strong>agente escolhido</strong>: a IA usa o prompt, a palavra de ativação e a voz configurados nele.
              Os demais ajustes desta caixa ainda não são enviados (em breve).
            </p>
            <div className="space-y-5">
              <div className="space-y-4 bg-muted/20 p-3 rounded-xl border border-border/50">
                <div className="space-y-2">
                  <Label className="flex items-center gap-1.5"><Users className="w-3.5 h-3.5 text-primary"/> Agente IA Principal</Label>
                  <select 
                    className="w-full bg-background border border-border/50 rounded-xl px-3 py-2 text-sm text-foreground outline-none focus:ring-1 focus:ring-primary/50"
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    disabled={isJoined}
                  >
                    {agents.map(a => (
                       <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                     <Label className="flex items-center gap-1.5"><BrainCircuit className="w-3.5 h-3.5 text-amber-500"/> Co-piloto (Modo Swarm)</Label>
                     <Badge variant="outline" className="text-[0.6rem] bg-amber-500/10 text-amber-500 border-amber-500/20">BETA</Badge>
                  </div>
                  <select 
                    className="w-full bg-background border border-border/50 rounded-xl px-3 py-2 text-sm text-foreground outline-none focus:ring-1 focus:ring-primary/50"
                    value={swarmAgent}
                    onChange={(e) => setSwarmAgent(e.target.value)}
                    disabled={isJoined}
                  >
                    <option value="">Nenhum (Apenas 1 agente na call)</option>
                    {agents.filter(a => a.id !== selectedAgent).map(a => (
                       <option key={`swarm-${a.id}`} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                  <p className="text-[0.65rem] text-muted-foreground leading-tight">
                    No modo Swarm (Enxame), o agente principal pode convocar o co-piloto para a mesma reunião caso precise de um especialista secundário.
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Nome pelo qual a IA responde na sala</Label>
                <Input
                  value={aiName}
                  onChange={(e) => setAiName(e.target.value)}
                  className="bg-background/50 rounded-xl font-medium"
                  disabled={isJoined}
                />
                <p className="text-[0.65rem] text-muted-foreground">Ex: Se alguém falar "O que você acha, Athena?", ela abre o microfone.</p>
              </div>

              <div className="space-y-2">
                <Label>Contexto Específico (Somente para esta reunião)</Label>
                <Textarea
                  value={meetingContext}
                  onChange={(e) => setMeetingContext(e.target.value)}
                  placeholder="Ex: Estamos tentando fechar a venda do plano Pro com o cliente João. Fale bastante sobre os benefícios de economia de tempo..."
                  className="bg-background/50 rounded-xl min-h-[80px]"
                  disabled={isJoined}
                />
                <p className="text-[0.65rem] text-muted-foreground">Isso será injetado no prompt do agente temporariamente.</p>
              </div>

              <div className="space-y-2">
                <Label>Papel na Reunião</Label>
                <select 
                  className="w-full bg-background border border-border/50 rounded-xl px-3 py-2 text-sm text-foreground outline-none focus:ring-1 focus:ring-primary/50"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  disabled={isJoined}
                >
                  <option value="participant">Assistente Ativa (Ouve e Responde)</option>
                  <option value="listener">Apenas Ouvinte (Faz a Ata da Reunião)</option>
                  <option value="specialist">Especialista Técnica (Responde só dúvidas técnicas)</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label>Modo de Audição</Label>
                <select 
                  className="w-full bg-background border border-border/50 rounded-xl px-3 py-2 text-sm text-foreground outline-none focus:ring-1 focus:ring-primary/50"
                  value={listenMode}
                  onChange={(e) => setListenMode(e.target.value)}
                  disabled={isJoined}
                >
                  <option value="continuous">Contínuo (Ouve a reunião inteira até o fim)</option>
                  <option value="chunks_15">Blocos de 15 min (Pausa para economizar tokens)</option>
                  <option value="wake_only">Apenas quando chamada (Wake Word stricto)</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label>Palavra-chave de Ativação (Wake Word)</Label>
                <Input
                  value={wakeWord}
                  onChange={(e) => setWakeWord(e.target.value)}
                  className="bg-background/50 rounded-xl font-medium"
                  disabled={isJoined}
                />
                <p className="text-[0.65rem] text-muted-foreground">Ex: "Hey Athena", "Ok IA". O bot só desmuta quando ouvir isso.</p>
              </div>

              <div className="space-y-2">
                <Label>Ação Pós-Reunião</Label>
                <select 
                  className="w-full bg-background border border-border/50 rounded-xl px-3 py-2 text-sm text-foreground outline-none focus:ring-1 focus:ring-primary/50"
                  value={postAction}
                  onChange={(e) => setPostAction(e.target.value)}
                  disabled={isJoined}
                >
                  <option value="email_summary">Enviar Resumo e Ata por Email</option>
                  <option value="crm_log">Criar Log no CRM + Adicionar Tarefas</option>
                  <option value="webhook">Disparar Webhook Customizado</option>
                  <option value="nothing">Apenas Salvar Transcrição</option>
                </select>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input 
                  type="checkbox" 
                  id="autoMute" 
                  checked={autoMute} 
                  onChange={(e) => setAutoMute(e.target.checked)} 
                  disabled={isJoined}
                  className="rounded border-border bg-background/50 text-primary focus:ring-primary/50"
                />
                <Label htmlFor="autoMute" className="text-sm cursor-pointer">
                  Entrar mutada e com câmera desligada
                </Label>
              </div>

              <div className="pt-4 border-t border-border/20 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div className="text-xs text-muted-foreground">
                  A IA usará a <strong className="text-foreground">Base de Conhecimento (RAG)</strong> corporativa para dar respostas fundamentadas.
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-5 bg-glass border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)] relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-3xl rounded-full -mr-16 -mt-16 pointer-events-none"></div>
            <h3 className="font-bold mb-1 flex items-center gap-2 text-emerald-500">
              <BrainCircuit className="w-5 h-5" /> Habilidades Premium
              <Badge variant="outline" className="text-[0.6rem] bg-amber-500/10 text-amber-500 border-amber-500/20 uppercase">Em breve</Badge>
            </h3>
            <p className="text-xs text-muted-foreground mb-5">Estas habilidades ainda estão em desenvolvimento e não podem ser ligadas por enquanto.</p>
            
            <div className="space-y-4">
              {[
                { id: "avatar", icon: Video, label: "Avatar de Vídeo Sintético", desc: "A IA liga a câmera com um rosto fotorrealista / animação (HeyGen)." },
                { id: "crm", icon: Activity, label: "CRM Auto-Update", desc: "Atualiza cards no Kanban em tempo real conforme a conversa." },
                { id: "trans", icon: Ear, label: "Tradução Simultânea Bilingue", desc: "Atua como intérprete (Inglês ↔ Português) para gringos." },
                { id: "screen", icon: Settings2, label: "Leitura de Tela e Slides", desc: "A IA enxerga o que está sendo apresentado e analisa os dados." },
                { id: "emo", icon: Bot, label: "Análise de Sentimento", desc: "Lê a emoção da sala e sugere abordagens no painel." },
                { id: "time", icon: Ear, label: "Guardião da Pauta (Timekeeper)", desc: "Avisa os humanos caso a reunião esteja perdendo o foco ou passando do tempo." },
                { id: "follow", icon: Send, label: "Disparo Autônomo de Follow-up", desc: "Envia o resumo e próximos passos por email para o cliente ao fim da call." },
              ].map(skill => (
                <div key={skill.id} className="flex items-start gap-3 p-3 rounded-xl border border-border/50 bg-background/50 opacity-60" title="Em breve">
                  <div className="pt-1"><Switch checked={false} disabled aria-label={`${skill.label} (em breve)`} /></div>
                  <div className="flex-1">
                    <h4 className="text-sm font-bold flex items-center gap-1.5">
                      <skill.icon className="w-3.5 h-3.5 text-emerald-500" /> {skill.label}
                    </h4>
                    <p className="text-[0.65rem] text-muted-foreground mt-0.5 leading-tight">{skill.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Live Feed / Transcrição */}
        {showTranscript && (
          <div className="lg:col-span-7 flex flex-col animate-in slide-in-from-right-4 fade-in duration-300">
            <Card className="flex-1 p-5 bg-glass border border-border/50 shadow-soft flex flex-col min-h-[500px]">
               <div className="flex items-center justify-between mb-4 border-b border-border/20 pb-4">
                 <h3 className="font-semibold flex items-center gap-2">
                   <Ear className="w-4 h-4 text-primary" /> Transcrição em Tempo Real
                 </h3>
                 {isJoined && (
                   <div className="flex items-center gap-1.5 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-bold border border-primary/20">
                     <Activity className="w-3 h-3 animate-pulse" /> Conectado ao Áudio da Sala
                   </div>
                 )}
               </div>

               <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                 {!isJoined ? (
                   <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50">
                      <Bot className="w-16 h-16 mb-4 opacity-20" />
                      <p>A IA não está conectada a nenhuma sala no momento.</p>
                      <p className="text-sm">Insira o link ao lado para ela entrar e começar a ouvir.</p>
                   </div>
                 ) : (
                   <div className="space-y-4 animate-in fade-in duration-500">
                      {liveLines.map((line, i) => (
                        <div key={i} className={`flex flex-col gap-1 ${line.kind === "ai" ? "items-end mt-6" : "items-start mt-2"}`}>
                          <span className={`text-[0.65rem] uppercase font-bold flex items-center gap-1 ${line.kind === "ai" ? "text-emerald-500" : line.kind === "system" ? "text-muted-foreground" : "text-blue-400"}`}>
                            {line.kind === "ai" && <BrainCircuit className="w-3 h-3" />} {line.who}
                          </span>
                          <div className={`rounded-2xl px-4 py-2 text-sm max-w-[85%] ${
                            line.kind === "ai" ? "bg-primary/20 border border-primary/40 rounded-tr-none text-primary-foreground shadow-[0_0_15px_rgba(16,185,129,0.2)]"
                            : line.kind === "system" ? "bg-muted/40 border border-border/50 rounded-tl-none"
                            : "bg-blue-500/10 border border-blue-500/20 rounded-tl-none text-blue-50"}`}>
                            {line.text}
                          </div>
                        </div>
                      ))}
                      {sending && (
                        <div className="flex items-center gap-2 text-xs text-emerald-500 animate-pulse">
                          <BrainCircuit className="w-3 h-3" /> {aiName} processando...
                        </div>
                      )}
                   </div>
                 )}
               </div>

               <div className="mt-4 pt-4 border-t border-border/20 relative">
                 <Input
                   disabled={!isJoined || sending}
                   value={whisper}
                   onChange={(e) => setWhisper(e.target.value)}
                   onKeyDown={(e) => { if (e.key === "Enter") handleWhisper(); }}
                   placeholder={`Falar com a IA (ex.: "${wakeWord} resuma até agora")...`}
                   className="w-full bg-background/50 rounded-xl pr-10"
                 />
                 <Button onClick={handleWhisper} disabled={!isJoined || sending} size="sm" variant="ghost" className="absolute right-1 top-5 text-primary hover:bg-primary/20">
                   <Send className="w-4 h-4" />
                 </Button>
               </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
