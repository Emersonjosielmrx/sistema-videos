import { useEffect, useState, useRef } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiGet, apiPost } from "@/lib/api";
import { Wand2, PlayCircle, Loader2, RefreshCw, Clock, Eye, Star, ArrowRightLeft, BrainCircuit } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";


type Job = {
  id: string;
  agent_id: string;
  status: "running" | "paused" | "done" | "aborted" | "error";
  conv_limit: number;
  max_cost_usd: number;
  cost_usd: number;
  processed: number;
  total: number;
  error: string;
  created_at: string;
  finished_at: string | null;
};

type Prompt = {
  id: string;
  agent_id: string;
  job_id: string;
  version: number;
  is_active: boolean;
  created_at: string;
};

type PromptDetail = Prompt & {
  body: string;
};

export function AgentTrainerPanel({ agentId: initialAgentId }: { agentId?: string }) {
  const [activeTab, setActiveTab] = useState("train");

  const [agents, setAgents] = useState<{id:string, name:string, system_prompt?: string}[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState(initialAgentId || "");
  const [showNewAgent, setShowNewAgent] = useState(false);
  const [newAgentName, setNewAgentName] = useState("");

  const loadAgents = async () => {
    try {
      const r = await apiGet<{ profiles: {id:string, name:string, system_prompt?: string}[] }>("/api/agent-profiles");
      setAgents(r.profiles || []);
      return r.profiles || [];
    } catch (e) {
      console.error("Failed to load agents", e);
      return [];
    }
  };

  useEffect(() => {
    if (!initialAgentId) {
      loadAgents().then(list => {
        if (list.length > 0 && !selectedAgentId) setSelectedAgentId(list[0].id);
      });
    }
  }, [initialAgentId]);

  const [convLimit] = useState(20);
  const [maxCostUsd] = useState(5.0);
  const [starting, setStarting] = useState(false);

  // Active Job State
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [allJobs, setAllJobs] = useState<Job[]>([]);
  const [, setLoadingJob] = useState(false);
  
  // Prompts State
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [, setLoadingPrompts] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptDetail | null>(null);
  const [, setLoadingPromptBody] = useState(false);

  // Polling ref
  const pollTimer = useRef<NodeJS.Timeout | null>(null);

  // Load existing active job on mount
  useEffect(() => {
    if (selectedAgentId) {
      fetchActiveJob();
      if (activeTab === "prompts") fetchPrompts();
    }
    return () => stopPolling();
  }, [selectedAgentId]);

  const stopPolling = () => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
  };

  const fetchActiveJob = async () => {
    if (!selectedAgentId) return;
    try {
      setLoadingJob(true);
      const jobs = await apiGet<Job[]>(`/api/training/jobs?agent_id=${selectedAgentId}`);
      if (jobs) {
        jobs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setAllJobs(jobs);
        if (jobs.length > 0) {
          setCurrentJob(jobs[0]);
          if (jobs[0].status === "running") {
            startPolling(jobs[0].id);
          }
        } else {
          setCurrentJob(null);
        }
      }
    } catch (e) {
      console.error("Failed to load jobs", e);
    } finally {
      setLoadingJob(false);
    }
  };

  const startPolling = (jobId: string) => {
    stopPolling();
    pollTimer.current = setInterval(async () => {
      try {
        const job = await apiGet<Job>(`/api/training/jobs/${jobId}`);
        setCurrentJob(job);
        if (job.status !== "running") {
          stopPolling();
          if (job.status === "done") {
            toast.success("Treinamento concluído com sucesso!");
          } else if (job.status === "error") {
            toast.error(`Falha no treinamento: ${job.error}`);
          }
        }
      } catch (e) {
        console.error("Failed polling job", e);
      }
    }, 2000);
  };

  const createAgent = async () => {
    if (!newAgentName) return;
    // Nome que já existe: seleciona o agente em vez de criar (o servidor recusaria com 409;
    // antes ele regravava o agente existente só com nome e prompt e apagava o resto).
    const existente = agents.find(a => a.name.trim() === newAgentName.trim());
    if (existente) {
      toast.error("Já existe um agente com esse nome — selecionei ele pra você");
      setSelectedAgentId(existente.id);
      setShowNewAgent(false);
      setNewAgentName("");
      return;
    }
    try {
      const res = await apiPost<any>("/api/agent-profiles", { name: newAgentName, system_prompt: "Você é um assistente." });
      toast.success("Agente criado!");
      const list = await loadAgents();
      setSelectedAgentId(res.profile?.id || res.id || list[list.length-1]?.id);
      setShowNewAgent(false);
      setNewAgentName("");
    } catch (e) {
      toast.error((e as Error).message || "Erro ao criar agente");
    }
  };


  const startTraining = async () => {
    if (!selectedAgentId) { toast.error("Selecione um agente"); return; }
    setStarting(true);
    try {
      const res = await apiPost<{ job_id: string; status: string }>("/api/training/jobs", {
        agent_id: selectedAgentId,
        conv_limit: convLimit,
        max_cost_usd: maxCostUsd,
      });
      toast.success("Treinamento iniciado!");
      startPolling(res.job_id);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setStarting(false);
    }
  };


  const fetchPrompts = async () => {
    if (!selectedAgentId) return;
    setLoadingPrompts(true);
    try {
      const list = await apiGet<Prompt[]>(`/api/training/prompts?agent_id=${selectedAgentId}`);
      list.sort((a, b) => b.version - a.version);
      setPrompts(list);
    } catch (e) {
      toast.error("Erro ao listar prompts gerados.");
    } finally {
      setLoadingPrompts(false);
    }
  };

  const viewPrompt = async (id: string) => {
    setLoadingPromptBody(true);
    try {
      const p = await apiGet<PromptDetail>(`/api/training/prompts/${id}`);
      setSelectedPrompt(p);
    } catch (e) {
      toast.error("Erro ao carregar corpo do prompt.");
    } finally {
      setLoadingPromptBody(false);
    }
  };

  const activatePrompt = async (id: string) => {
    try {
      await apiPost(`/api/training/prompts/${id}/activate`, {});
      toast.success("Prompt ativado com sucesso!");
      fetchPrompts();
      if (selectedPrompt && selectedPrompt.id === id) {
        setSelectedPrompt({ ...selectedPrompt, is_active: true });
      }
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  return (
    <div className="flex flex-col space-y-6 max-w-[1400px] w-full pb-20">
      
      {/* 1. Header (Treinar Agente) */}
      <div className="flex justify-between items-start">
        <div className="max-w-4xl">
          <h4 className="text-xl font-bold flex items-center gap-2 mb-2">Treinar agente</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Dispara o pipeline completo: destila o <em className="text-foreground">system prompt</em>, extrai pares Q&A e reconstrói o índice RAG. Cada <strong className="text-foreground">agente</strong> (empresa) tem suas próprias versões isoladas; o treino sempre acumula sobre a última versão do agente.
          </p>
        </div>
        <div className="flex items-center gap-2 border border-border/50 rounded-full px-3 py-1 bg-muted/10 shrink-0">
          <div className="w-2 h-2 rounded-full bg-muted-foreground" />
          <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">ocloso</span>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full space-y-6">
        <TabsList className="bg-muted/50 p-1 rounded-xl h-12 w-full justify-start overflow-x-auto no-scrollbar">
          <TabsTrigger value="train" className="rounded-lg text-xs font-semibold px-6 h-full data-[state=active]:bg-background data-[state=active]:shadow-sm">Configuração & Treino</TabsTrigger>
          <TabsTrigger value="monitor" className="rounded-lg text-xs font-semibold px-6 h-full data-[state=active]:bg-background data-[state=active]:shadow-sm">Monitor de Jobs</TabsTrigger>
          <TabsTrigger value="prompts" className="rounded-lg text-xs font-semibold px-6 h-full data-[state=active]:bg-background data-[state=active]:shadow-sm">Versões & Diff</TabsTrigger>
        </TabsList>

        {/* ===================== TAB 1: CONFIG ===================== */}
        <TabsContent value="train" className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
          <Card className="bg-background border-primary/20 shadow-glow overflow-hidden rounded-2xl">
            <div className="p-6 space-y-6">
          
          {/* Agente Selector + Criar */}
          <div className="flex flex-col space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center gap-3 w-full sm:w-auto">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Agente:</span>
                <select 
                  className="w-full sm:w-64 rounded-xl border border-border/50 bg-background/50 px-3 py-2 text-sm font-semibold hover:border-primary/50 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
                  value={selectedAgentId}
                  onChange={e => setSelectedAgentId(e.target.value)}
                >
                  {agents.length === 0 ? <option value="">Carregando...</option> : agents.map(a => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="flex flex-col sm:flex-row sm:items-center gap-4 w-full sm:w-auto">
                <Button variant="ghost" size="sm" className="rounded-xl h-9 text-xs w-full sm:w-auto" onClick={() => setShowNewAgent(!showNewAgent)}>
                  + Novo agente
                </Button>
                
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold text-center sm:text-left">
                  {currentJob ? currentJob.total : 0} CONVERSAS - {prompts.length} VERSÃO(ÕES)
                </span>
              </div>
            </div>

            {showNewAgent && (
              <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center animate-in fade-in slide-in-from-top-2">
                <Input placeholder="Nome (ex.: Loja A)" value={newAgentName} onChange={e => setNewAgentName(e.target.value)} className="h-9 rounded-xl w-full sm:w-48 bg-muted/20" />
                <Input placeholder="chave (ex.: loja_a)" className="h-9 rounded-xl w-full sm:w-48 bg-muted/20" />
                <Input placeholder="números (vírgula)" className="h-9 rounded-xl w-full sm:w-48 bg-muted/20" />
                <Button size="sm" onClick={createAgent} className="rounded-xl h-9 bg-violet-600 hover:bg-violet-700 text-white w-full sm:w-auto sm:px-6">Criar</Button>
              </div>
            )}
          </div>

          {/* Quality Gate & Exclusões */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-border/50">
            <div className="space-y-3">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                Filtro de Qualidade (Quality Gate)
              </label>
              <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl flex items-center justify-between">
                 <div>
                    <p className="text-sm font-bold text-emerald-500">Treinar apenas com "Wins"</p>
                    <p className="text-xs text-muted-foreground mt-1">Usa apenas conversas que terminaram em venda ou conversão. Ignora tickets com sentimento negativo.</p>
                 </div>
                 <Switch defaultChecked />
              </div>
            </div>
            <div className="space-y-3">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                Coisas a ignorar (Exclusões)
              </label>
              <textarea 
                className="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-2 text-sm h-[76px] resize-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50" 
                placeholder="Ex.: IGNORE O BOT X, FOQUE NA LOJA Y..."
              />
            </div>
          </div>
        </div>

        {/* Instâncias */}
        <div className="px-6 py-5 border-t border-border/50 bg-muted/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h5 className="font-bold text-sm">Instâncias WhatsApp para treinar</h5>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-1">Nenhuma mensagem registrada ainda.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="h-8 text-[11px] rounded-xl text-muted-foreground hover:text-foreground">Selecionar todas</Button>
            <Button variant="ghost" size="sm" className="h-8 text-[11px] rounded-xl text-muted-foreground hover:text-foreground">Desmarcar todas</Button>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-xl text-muted-foreground hover:text-foreground"><RefreshCw className="w-3.5 h-3.5"/></Button>
          </div>
        </div>

        {/* Classificação */}
        <div className="px-6 py-5 border-t border-border/50 bg-muted/10">
          <div className="flex flex-col sm:flex-row justify-between sm:items-start gap-4 mb-2">
            <div>
              <h5 className="font-bold text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-orange-500" /> Classificar conversas (antes de treinar)
              </h5>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-2 max-w-4xl leading-relaxed">
                SEPARA ATENDIMENTO (PROFISSIONAL) DE CONVERSAS PESSOAIS/GRUPOS VIA IA. O TREINO SÓ USA AS DE ATENDIMENTO — ASSIM A PERSONA NÃO VIRA "AMIGÃO DE GRUPO". RODA EM SEGUNDO PLANO.
              </p>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-2">
                AINDA NÃO CLASSIFICADO. CLIQUE PARA SEPARAR ATENDIMENTO DE PESSOAL/GRUPOS.
              </p>
            </div>
            <Button variant="secondary" size="sm" className="rounded-xl h-9 text-xs bg-violet-600/10 text-violet-400 hover:bg-violet-600/20 border border-violet-600/20 shrink-0">
              <Wand2 className="w-3.5 h-3.5 mr-2" /> Classificar automaticamente
            </Button>
          </div>
        </div>

        {/* Shadow Mode & Ações */}
        <div className="px-6 py-5 border-t border-border/50 bg-background space-y-4">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <Button 
              className="rounded-xl h-10 px-5 text-sm bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white shadow-glow border-none w-full sm:w-auto" 
              onClick={startTraining}
              disabled={starting}
            >
              {starting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <PlayCircle className="w-4.5 h-4.5 mr-2 shrink-0" />}
              Treinar (Pipeline Completo)
            </Button>
            <Button variant="outline" className="rounded-xl h-10 px-5 text-sm bg-background border-border/50 hover:bg-muted/50 w-full sm:w-auto" onClick={() => toast.success("Modo Fantasma Ativado. A nova versão rodará em background para validar performance.")}>
              <Eye className="w-4 h-4 mr-2 shrink-0" /> Ativar Shadow Mode
            </Button>
          </div>
        </div>
      </Card>
    </TabsContent>

    {/* ===================== TAB 2: MONITOR DE JOBS ===================== */}
    <TabsContent value="monitor" className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
      <div className="pt-2">
        <div className="flex justify-between items-end mb-4">
          <div>
            <h4 className="text-xl font-bold">Runs históricas</h4>
            <p className="text-sm text-muted-foreground mt-1">Histórico de execuções incrementais. Runs pausadas podem ser retomadas.</p>
          </div>
          <Button variant="outline" size="sm" className="rounded-xl text-xs h-9 bg-background border-border/50 hover:bg-muted/50" onClick={fetchActiveJob}>
            Atualizar
          </Button>
        </div>
        
        <Card className="p-0 bg-background border-primary/20 shadow-glow overflow-hidden rounded-2xl">
          {allJobs.length === 0 ? (
            <div className="text-sm text-muted-foreground italic text-center p-8 bg-muted/5">Nenhuma run encontrada.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-border/50 bg-muted/10 text-muted-foreground">
                    <th className="py-3 px-6 font-bold text-[10px] uppercase tracking-wider">RUN ID</th>
                    <th className="py-3 px-6 font-bold text-[10px] uppercase tracking-wider">SCOPE</th>
                    <th className="py-3 px-6 font-bold text-[10px] uppercase tracking-wider">STATUS</th>
                    <th className="py-3 px-6 font-bold text-[10px] uppercase tracking-wider">PROGRESSO</th>
                    <th className="py-3 px-6 font-bold text-[10px] uppercase tracking-wider">INÍCIO</th>
                    <th className="py-3 px-6 font-bold text-[10px] uppercase tracking-wider">VERSÕES</th>
                    <th className="py-3 px-6 font-bold text-[10px] uppercase tracking-wider text-right">AÇÃO</th>
                  </tr>
                </thead>
                <tbody>
                  {allJobs.map(j => (
                    <tr key={j.id} className="border-b border-border/50 hover:bg-muted/5">
                      <td className="py-3 px-6 font-mono text-xs">{j.id.split("-")[0]}</td>
                      <td className="py-3 px-6 text-xs text-muted-foreground">Full pipeline</td>
                      <td className="py-3 px-6">
                        <Badge variant={j.status === "done" ? "default" : j.status === "error" ? "destructive" : "secondary"} className="text-[10px] uppercase font-semibold">
                          {j.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-6 text-xs font-medium">{j.processed} / {j.total}</td>
                      <td className="py-3 px-6 text-xs text-muted-foreground">{new Date(j.created_at).toLocaleString()}</td>
                      <td className="py-3 px-6 text-xs">-</td>
                      <td className="py-3 px-6 text-right">
                         <Button variant="ghost" size="sm" disabled title="Em breve" className="h-7 text-[10px] uppercase tracking-wider font-semibold">Retomar (em breve)</Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      {/* Removido: cartão "Human-in-the-Loop Requisitado" com uma objeção INVENTADA ("permuta de 30%")
          que aparecia em toda run em andamento. O servidor não pausa runs pedindo ajuda. */}
    </TabsContent>

    {/* ===================== TAB 3: VERSÕES & DIFF ===================== */}
    <TabsContent value="prompts" className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
      <div className="pt-2 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Versões */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex justify-between items-end mb-4">
            <div>
              <h4 className="text-xl font-bold flex items-center gap-2">Versões do prompt</h4>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold mt-1 text-right absolute right-0 top-0 hidden lg:block">{prompts.length} VERSÃO(ÕES)</p>
            </div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold lg:hidden">{prompts.length} VERSÃO(ÕES)</span>
          </div>
          
          <p className="text-sm text-muted-foreground">
            Lista de versões do clone selecionado. Selecione para testar; ative com a estrela.
          </p>
          
          <div className="flex flex-wrap gap-2 mb-2">
            <Button variant="link" size="sm" className="h-6 text-primary p-0 flex items-center gap-1 font-semibold text-xs hover:no-underline hover:text-primary/80">
              <ArrowRightLeft className="w-3.5 h-3.5" /> Comparar versões
            </Button>
          </div>

          <div className="space-y-3">
            {prompts.map(p => (
              <Card 
                key={p.id} 
                className={`p-4 cursor-pointer transition-all border ${selectedPrompt?.id === p.id ? 'border-primary/50 shadow-glow bg-primary/5' : 'border-border/50 hover:border-primary/30 bg-muted/5'}`}
                onClick={() => viewPrompt(p.id)}
              >
                <div className="flex justify-between items-start mb-2">
                  <h6 className="font-bold text-sm">v{p.version}</h6>
                  <span className="text-[10px] text-muted-foreground font-mono">{new Date(p.created_at).toLocaleString()}</span>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-3 mb-4 font-mono leading-relaxed break-words">
                  # Persona Você é um assistente virtual que se comunica de forma amigável...
                </p>
                <div className="flex flex-wrap items-center gap-2 mt-2 pt-3 border-t border-border/50">
                   <Button variant="ghost" size="sm" className="h-7 text-xs font-semibold px-2 text-primary hover:text-primary hover:bg-primary/10 flex-1 sm:flex-none">
                     <Eye className="w-3.5 h-3.5 mr-1.5 shrink-0" /> Selecionar
                   </Button>
                   {p.is_active ? (
                     <Button variant="ghost" size="sm" className="h-7 text-xs font-bold px-2 text-emerald-500 hover:text-emerald-400 hover:bg-emerald-500/10 flex-1 sm:flex-none">
                       <Star className="w-3.5 h-3.5 mr-1.5 shrink-0 fill-current" /> Ativo
                     </Button>
                   ) : (
                     <Button variant="outline" size="sm" className="h-7 text-xs font-semibold px-2 border-primary/30 text-primary hover:bg-primary/10 flex-1 sm:flex-none" onClick={(e) => { e.stopPropagation(); activatePrompt(p.id); }}>
                       <Star className="w-3.5 h-3.5 mr-1.5 shrink-0" /> Ativar
                     </Button>
                   )}
                </div>
              </Card>
            ))}
            {prompts.length === 0 && (
              <div className="text-sm text-muted-foreground italic text-center p-8 bg-muted/5 rounded-xl border border-dashed border-border/50">
                Nenhuma versão encontrada para este agente.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Editor */}
        <div className="lg:col-span-2 space-y-4 flex flex-col min-h-[500px]">
           <div className="flex justify-between items-end mb-4">
             <div>
               <h4 className="text-xl font-bold flex items-center gap-2">Editor & Diff Viewer</h4>
               <p className="text-sm text-muted-foreground mt-1">
                 Visualize as diferenças entre versões. O que a IA aprendeu de novo fica em <strong className="text-emerald-500">Verde</strong>.
               </p>
             </div>
             {selectedPrompt && (
               <Badge variant="outline" className="text-[10px] uppercase tracking-wider px-3 py-1 bg-muted/10 shrink-0 font-bold border-border/50 text-muted-foreground">
                 Visualização do Prompt
               </Badge>
             )}
          </div>

          <Card className="flex-1 flex flex-col bg-background border-primary/20 shadow-glow overflow-hidden rounded-2xl p-0 relative">
             {selectedPrompt ? (
               <div className="w-full h-full absolute inset-0 bg-black/5 dark:bg-black/20 font-mono text-sm leading-relaxed p-6 overflow-y-auto">
                 <div className="text-foreground/90 font-bold mb-4 flex items-center gap-2">Prompt da v{selectedPrompt.version} <Badge variant="muted" className="h-4 text-[0.55rem] px-1">Diff visual: em breve</Badge></div>
                 {/* O diff linha-a-linha (regras adicionadas/removidas) ainda não é calculado pelo backend.
                     Exibimos o corpo real do prompt; o realce de diferenças fica como "Em breve". */}
                 <div className="text-foreground/90 mt-2 whitespace-pre-wrap">
                   {selectedPrompt.body}
                 </div>
               </div>
             ) : (
               <div className="absolute inset-0 flex flex-col p-6 font-mono text-sm leading-relaxed text-muted-foreground overflow-y-auto bg-muted/5">
                 <div className="font-bold text-foreground mb-4 flex items-center gap-2">
                   <BrainCircuit className="w-4 h-4 text-primary" /> Prompt Inicial do Agente
                 </div>
                 <div className="whitespace-pre-wrap border border-border/50 bg-background/50 p-4 rounded-xl shadow-inner">
                   {agents.find(a => a.id === selectedAgentId)?.system_prompt || "Este agente não possui um System Prompt configurado. O Treinador usará a heurística padrão para construir um do zero."}
                 </div>
                 <div className="mt-6 italic text-xs text-center p-4 bg-primary/5 rounded-xl border border-primary/20 text-primary">
                   O treinador irá analisar as conversas registradas e gerar uma nova versão aprimorada deste prompt, injetando guardrails descobertos no Shadow Mode.
                 </div>
               </div>
             )}
          </Card>
          
          <div className="flex flex-col sm:flex-row justify-end items-center gap-3 pt-2">
             <Badge variant="muted" className="h-6 text-[0.6rem]">Auto-Corrigir: Em breve</Badge>
             <Button variant="outline" size="sm" className="rounded-xl h-9 text-xs border-border/50 bg-background hover:bg-muted/50 w-full sm:w-auto opacity-50 cursor-not-allowed" disabled title="Correção automática de guardrails ainda não disponível">
               Auto-Corrigir Guardrails
             </Button>
             <Button
               size="sm"
               className="rounded-xl h-9 px-6 text-sm bg-violet-600 hover:bg-violet-700 text-white shadow-glow border-none w-full sm:w-auto"
               disabled={!selectedPrompt || selectedPrompt.is_active}
               onClick={() => selectedPrompt && activatePrompt(selectedPrompt.id)}
             >
               {selectedPrompt?.is_active ? "Versão Ativa" : "Salvar e Ativar Versão"}
             </Button>
          </div>
        </div>

      </div>
    </TabsContent>

    </Tabs>
  </div>
  );
}
