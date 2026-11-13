import { useEffect, useState, Fragment } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Switch } from "@/components/ui/switch";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import { parseExtras } from "@/lib/agent-extras";
import { logError } from "@/lib/log";
import { getSettings, updateAgentChat } from "@/services/settings";
import { Bot, Trash2, Phone, MessageSquare, ChevronDown, ChevronUp, UploadCloud, PlayCircle, BrainCircuit, Link2, Users, Sparkles, Wand2, Settings2, GraduationCap, Award, Zap, Headphones, History, Copy, Activity, Boxes, Network, ShieldCheck, Play, ArrowRightLeft, List, LayoutGrid, Volume2, Database, AlertTriangle, Filter } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList } from "@/components/ui/tabs";
import { HideableTab } from "@/components/ui/HideableTab";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";
import { KanbanSquare, LayoutPanelLeft } from "lucide-react";
import { AgentChatTest } from "./AgentChatTest";
import { AgentRagPanel } from "./AgentRagPanel";
import { EasyAgentWizard } from "./EasyAgentWizard";
import { EasyManagerWizard } from "./EasyManagerWizard";
import { AdvancedLab } from "./AdvancedLab";
import { ChatMonitor } from "./ChatMonitor";
import { AgentTrainerPanel } from "./AgentTrainerPanel";
import { AgentOrchestratorFlow } from "./AgentOrchestratorFlow";
import { GlobalRagManager } from "./GlobalRagManager";
import { CallAgentsCard } from "./CallAgentsCard";
import type { AgentChatSettings } from "@/types/settings";

type Profile = {
  id: string;
  name: string;
  system_prompt: string;
  voice: string;
  kind: string;    // "call" | "message" | "both"
  trigger: string; // gatilho de uso
  // Campos do builder (backend agent_profiles).
  tone?: string;
  guardrails?: string;
  knowledge_base?: string;
  escalation_keywords?: string;
  handoff_message?: string;
  background_noise?: string;
  background_noise_volume?: number;
  // FLUXO 2 ÁUDIOS (avulsa espelha a campanha): gatilho curto + oferta + flag de enable.
  trigger_audio?: string;
  offer_audio?: string;
  enable_two_audio?: boolean;
  // Metadata for Dify-style UI
  status?: "draft" | "lab" | "production" | "archived";
  llm_model?: string;
  ai_model?: string; // campo REAL do backend (agent_profiles.ai_model). llm_model é legado/mock.
  ai_provider?: string;
  version?: string;
  total_calls?: number;
  logicType?: string;
  // JSON (texto) com as configurações avançadas; o servidor guarda e lê daqui (ex.: temperature).
  extras?: string;
  // Guardados DENTRO de extras (EXTRA_FIELDS). Só a temperatura muda o comportamento hoje.
  temperature?: number;
  webhook_url?: string;
  webhook_events?: string[];
  handoff_notify?: string;
  handoff_notify_msg?: string;
  swarm_mode?: string;
  handoff_agent?: string;
};

// Campos que o servidor não tem como coluna própria: vão dentro de extras (JSON). Antes
// iam soltos e o servidor descartava (04/10: a temperatura nunca valeu, o resto sumia).
// A "API Key Manual" do agente saiu da lista (revisão do PC, 04/10): ia em TEXTO PURO dentro
// de extras e nada no servidor usava. Chave fica no cofre (Credenciais).
const EXTRA_FIELDS = ["temperature", "webhook_url", "webhook_events", "handoff_notify", "handoff_notify_msg", "swarm_mode", "handoff_agent"] as const;
type ExtraField = (typeof EXTRA_FIELDS)[number];
const isExtraField = (f: string): f is ExtraField => (EXTRA_FIELDS as readonly string[]).includes(f);


// A tela usa temperatura de 0 a 100; o servidor (agent_engine_extras.go) lê de 0 a 1.
function extraForScreen(key: ExtraField, v: unknown): unknown {
  if (key === "temperature" && typeof v === "number") return Math.round(v * 100);
  return v;
}
function extraForServer(key: ExtraField, v: unknown): unknown {
  if (key === "temperature") return Number(v) / 100;
  return v;
}

const KINDS = [
  { value: "both", label: "Ligação + Mensagem" },
  { value: "call", label: "Só ligação" },
  { value: "message", label: "Só mensagem" },
];

function kindLabel(k: string): string {
  return KINDS.find((x) => x.value === k)?.label ?? "Ligação + Mensagem";
}

function AgentsList({ onNavigate }: { onNavigate?: (tab: string) => void }) {
  const [list, setList] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"list" | "kanban" | "flow">("list");
  const [activeRoutingLevel, setActiveRoutingLevel] = useState<"level_1" | "level_2" | "level_3">("level_1");
  // Roteamento Nível 1: salvo no servidor (agent_chat.default_profile_id / voice_profile_id).
  // Antes eram valores fixos "mock-1"/"mock-3" que não salvavam nem eram usados.
  const [level1VoiceAgent, setLevel1VoiceAgent] = useState<string>("");
  const [level1TextAgent, setLevel1TextAgent] = useState<string>("");
  useEffect(() => {
    getSettings()
      .then((st) => {
        setLevel1TextAgent(st.agent_chat?.default_profile_id ?? "");
        setLevel1VoiceAgent(st.agent_chat?.voice_profile_id ?? "");
      })
      .catch(() => {});
  }, []);
  const saveLevel1 = async (campo: "default_profile_id" | "voice_profile_id", valor: string) => {
    try {
      const st = await getSettings();
      await updateAgentChat({ ...st.agent_chat, [campo]: valor });
      toast.success(campo === "default_profile_id" ? "Atendente de mensagens salvo." : "Quem atende ligações recebidas: salvo.");
    } catch (e) {
      toast.error("Não consegui salvar o roteamento", { description: (e as Error).message });
    }
  };
  const [activeInnerTabs, setActiveInnerTabs] = useState<Record<string, string>>({});
  const [kanbanCategory, setKanbanCategory] = useState<"general" | "tags" | "stages" | "time" | "exact" | "contains" | "similar">("general");
  const [listSearch, setListSearch] = useState("");
  const [listFilter, setListFilter] = useState("all");
  const [listFormat, setListFormat] = useState<"grid" | "table">("grid");
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);

  const [hierarchy, setHierarchy] = useState([
    { id: 'time', label: 'Horário', color: 'orange' },
    { id: 'stage', label: 'Etapas', color: 'indigo' },
    { id: 'tag', label: 'Tags', color: 'amber' },
    { id: 'words', label: 'Palavras', color: 'pink' }
  ]);

  const handleHierarchyDragStart = (e: React.DragEvent, index: number) => {
    e.dataTransfer.setData("hierarchyIndex", index.toString());
  };

  const handleHierarchyDrop = (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    const sourceIndex = parseInt(e.dataTransfer.getData("hierarchyIndex"));
    if (isNaN(sourceIndex) || sourceIndex === targetIndex) return;

    const newHierarchy = [...hierarchy];
    const [draggedItem] = newHierarchy.splice(sourceIndex, 1);
    newHierarchy.splice(targetIndex, 0, draggedItem);
    setHierarchy(newHierarchy);
    toast.success("Prioridade de roteamento atualizada!");
  };

  const handleDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.setData("agentId", id);
  };

  // Persiste o trigger de um agente no backend (upsert por nome em /api/agent-profiles).
  // O roteamento por gatilho é lido daí no runtime (autoreply/broadcast).
  // FIX P0-007 (2026-07-25): antes mandava só ~11 campos (name, system_prompt,
  // kind, trigger, voice, tone, guardrails, knowledge_base, escalation_keywords,
  // handoff_message). O UPSERT do backend (cmd/server/agentprofiles.go) faz
  // ON CONFLICT DO UPDATE SET <todas as 35 colunas> = EXCLUDED.*, então
  // QUALQUER campo omitido é ZERADO — voice_id, trigger_audio, offer_audio,
  // background_noise, ai_model, ai_provider, listen_audio, reply_audio,
  // vision_enabled, extras, tts_default, etc. Agora espelhamos ...agent
  // (igual a persistModel/persistProvider já fazem) para preservar tudo.
  const persistTrigger = async (agent: Profile, newTrigger: string) => {
    try {
      await apiPost("/api/agent-profiles", {
        ...agent,
        ...(edits[agent.id] ?? {}),
        trigger: newTrigger,
      });
      return true;
    } catch (e) {
      toast.error("Falha ao salvar o roteamento", { description: (e as Error).message });
      return false;
    }
  };

  // Persiste o modelo de IA de um agente. Antes o onChange só mudava o estado local e
  // mostrava "Modelo atualizado!" — falso sucesso, nada era gravado. Manda o profile
  // completo (o upsert por nome sobrescreve com EXCLUDED, então campos omitidos seriam
  // zerados).
  const persistModel = async (agent: Profile, newModel: string) => {
    try {
      // FIX (QA IA): POST /api/agent-profiles faz UPSERT de TODAS as colunas com EXCLUDED,
      // então QUALQUER campo omitido é ZERADO no banco. O corpo antigo mandava só ~11 campos
      // → trocar o modelo apagava tts_default, wake_word, voice_id, background_noise, os 2
      // áudios (trigger/offer), custom_tags/alerts e os ~30 campos avançados (extras). Como o
      // GET /api/agent-profiles já devolve o perfil COMPLETO (inclusive extras como string
      // JSON), reenviamos o objeto inteiro + só o modelo trocado, preservando tudo.
      await apiPost("/api/agent-profiles", {
        ...agent,
        ...(edits[agent.id] ?? {}),
        ai_provider: agent.ai_provider ?? "openai",
        ai_model: newModel,
      });
      return true;
    } catch (e) {
      toast.error("Falha ao salvar o modelo", { description: (e as Error).message });
      return false;
    }
  };

  // Persiste o PROVEDOR de IA (ai_provider) do agente. Mesmo cuidado do persistModel:
  // reenvia o perfil completo pra não zerar as colunas que o UPSERT sobrescreve.
  const persistProvider = async (agent: Profile, newProvider: string) => {
    try {
      await apiPost("/api/agent-profiles", {
        ...agent,
        ...(edits[agent.id] ?? {}),
        ai_provider: newProvider,
      });
      return true;
    } catch (e) {
      toast.error("Falha ao salvar o provedor", { description: (e as Error).message });
      return false;
    }
  };

  const handleDrop = async (e: React.DragEvent, newTrigger: string) => {
    e.preventDefault();
    const id = e.dataTransfer.getData("agentId");
    if (!id) return;
    const agent = list.find(a => a.id === id);
    if (!agent) return;

    // Check if dragging to "unassigned/inactive"
    if (newTrigger === "unassigned") {
      if (!(await persistTrigger(agent, ""))) return;
      setList(prev => prev.map(a => a.id === id ? { ...a, logicType: 'none', trigger: '' } : a));
      toast.success("Agente desvinculado das regras condicionais!");
      return;
    }

    // Determine Logic Type based on category
    let newLogicType = 'none';
    if (kanbanCategory === 'tags') newLogicType = 'tag';
    else if (kanbanCategory === 'stages') newLogicType = 'stage';
    else if (kanbanCategory === 'time') newLogicType = 'time';
    else if (kanbanCategory === 'exact') newLogicType = 'exact';
    else if (kanbanCategory === 'contains') newLogicType = 'contains';
    else if (kanbanCategory === 'similar') newLogicType = 'similar';

    if (!(await persistTrigger(agent, newTrigger))) return;
    setList(prev => prev.map(a => a.id === id ? { ...a, logicType: newLogicType, trigger: newTrigger } : a));
    toast.success(`Agente mapeado para a regra: ${newTrigger}`);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const duplicateAgent = async (p: Profile) => {
    // Cópia COMPLETA (voz, áudios, extras, automações, modelo/provedor). Antes mandava só 11
    // campos, forçava provider "openai" e, se já existisse "<nome> - Cópia", SOBRESCREVIA esse
    // agente (o POST faz upsert por nome). Agora o nome é sempre único.
    const nomes = new Set(list.map((a) => a.name));
    let nome = `${p.name} - Cópia`;
    for (let i = 2; nomes.has(nome); i++) nome = `${p.name} - Cópia ${i}`;
    try {
      toast.info("Criando cópia do agente...");
      const { id: _id, ...resto } = { ...p, ...(edits[p.id] ?? {}) } as any;
      await apiPost("/api/agent-profiles", { ...resto, name: nome });
      toast.success(`Agente duplicado: ${nome}`);
      reload();
    } catch (err) {
      toast.error("Erro ao duplicar agente", { description: (err as Error).message });
      reload();
    }
  };


  // form variables removed

  const reload = () => {
    // FIX (QA IA): antes, quando /api/agent-profiles vinha vazio OU dava erro, a tela
    // caía num FALLBACK de 3 agentes MOCK ("Closer", "Suporte", "Recrutador RH"). Isso
    // era a causa REAL do sintoma "Meus Funcionários mostra só 3 / algo sumiu": não é que
    // agentes sumiram — é que a lista real estava vazia/erro e a UI exibia 3 fakes fixos
    // (que também não existem no runtime nem no Chat/Teste). Agora refletimos SEMPRE a
    // fonte única (agent_profiles). Vazio = vazio (empty-state honesto).
    apiGet<{ profiles: Profile[] }>("/api/agent-profiles")
      .then((r) => setList(r.profiles ?? []))
      .catch((e) => {
         toast.error("Falha ao carregar funcionários: " + (e as Error).message);
         setList([]);
      })
      .finally(() => setLoading(false));
  };
  useEffect(() => { reload(); }, []);

  

  // Inline creation logic removed - replaced by EasyAgentWizard and Lab Avançado

  // Edições por-agente (aba IA & Modelo / Integrações). Chave = id do agente.
  const [edits, setEdits] = useState<Record<string, Partial<Profile>>>({});
  // editVal devolve o valor da tela (edição local ou o salvo); `any` porque os campos são
  // de tipos diferentes (texto, número, lista). Campos de extras vêm de dentro do JSON.
  const editVal = (p: Profile, field: keyof Profile): any => {
    const local = edits[p.id]?.[field];
    if (local !== undefined) return local;
    if (isExtraField(field)) return extraForScreen(field, parseExtras(p.extras)[field]) ?? "";
    return p[field] ?? "";
  };
  const setEdit = (id: string, field: keyof Profile, value: unknown) =>
    setEdits((prev) => ({ ...prev, [id]: { ...prev[id], [field]: value } }));

  // Salva o agente (upsert por nome no backend): reenvia o perfil com as edições.
  const saveAgent = async (p: Profile) => {
    const merged: Profile = { ...p, ...edits[p.id] };
    const extras = parseExtras(p.extras);
    for (const key of EXTRA_FIELDS) {
      const v = edits[p.id]?.[key];
      if (v !== undefined) extras[key] = extraForServer(key, v);
      delete merged[key];
    }
    // Chave manual gravada antes (texto puro, sem uso): sai na primeira vez que o agente é salvo.
    delete extras.api_key;
    merged.extras = JSON.stringify(extras);
    try {
      // FIX (QA IA): o UPSERT do backend sobrescreve TODAS as colunas com EXCLUDED, logo
      // campo omitido = campo ZERADO. O corpo antigo listava só ~13 campos, então Salvar
      // apagava ai_provider/ai_model, voice_id, wake_word, tts_default, custom_tags/alerts,
      // vision_enabled e os ~30 avançados (extras). Como `merged` já é o perfil COMPLETO
      // vindo do GET (todas as 36 colunas, extras como string JSON) + as edições locais,
      // reenviamos ele inteiro pra preservar tudo o que a tela não conhece.
      await apiPost("/api/agent-profiles", {
        ...merged,
        kind: merged.kind ?? "both",
        // Som de ambiente: o slider da tela mexe aqui, mas o saveAgent ORIGINAL não
        // enviava — era a causa do "ontem funcionava / hoje sumiu": a dona clicava
        // Salvar e o backend nunca recebia background_noise/volume. Agora persiste.
        background_noise: merged.background_noise ?? "",
        background_noise_volume: merged.background_noise_volume ?? 0,
        // FLUXO 2 ÁUDIOS (avulsa espelha campanha): gatilho curto + oferta completa +
        // enable_two_audio habilita o pipeline isca→oferta→IA. Vazio = 1 áudio só.
        trigger_audio: merged.trigger_audio ?? "",
        offer_audio: merged.offer_audio ?? "",
        enable_two_audio: merged.enable_two_audio ?? false,
      });
      toast.success("Configurações salvas");
      setEdits((prev) => { const n = { ...prev }; delete n[p.id]; return n; });
      reload();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const remove = async (id: string, nm: string) => {
    if (!confirm(`Apagar o funcionário "${nm}"?`)) return;
    try {
      await apiDelete(`/api/agent-profiles/${id}`);
      toast.success("Funcionário apagado");
      reload();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  return (
    <div className="mt-4 space-y-6">
      {/* Os dois papéis de ligação ficam juntos e com nomes claros (são coisas diferentes):
          quem ATENDE as recebidas (agent_chat.voice_profile_id) e quem FAZ as que o dono pede. */}
      <CallAgentsCard
        agents={list}
        loadingAgents={loading}
        inboundValue={level1VoiceAgent}
        onInboundChange={(v) => { setLevel1VoiceAgent(v); saveLevel1("voice_profile_id", v); }}
      />

      {/* Global Routing Mode Selector */}
      <div className="bg-background/40 border border-border/50 rounded-xl p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h4 className="text-sm font-bold text-foreground">Sistema de Orquestração Ativo</h4>
          <p className="text-[10px] text-muted-foreground mt-0.5">Apenas um nível de inteligência de roteamento pode operar por vez para evitar conflitos no webhook.</p>
        </div>
        <div className="flex bg-muted/30 p-1 rounded-lg border border-border/50">
          <button 
            onClick={() => setActiveRoutingLevel("level_1")}
            className={cn("px-4 py-1.5 text-xs font-medium rounded-md transition-colors", activeRoutingLevel === "level_1" ? "bg-emerald-500/20 text-emerald-500 shadow-sm" : "text-muted-foreground hover:text-foreground")}
          >
            Nível 1 (Básico)
          </button>
          <button 
            onClick={() => setActiveRoutingLevel("level_2")}
            className={cn("px-4 py-1.5 text-xs font-medium rounded-md transition-colors", activeRoutingLevel === "level_2" ? "bg-sky-500/20 text-sky-500 shadow-sm" : "text-muted-foreground hover:text-foreground")}
          >
            Nível 2 (Kanban CRM)
          </button>
          <button 
            onClick={() => setActiveRoutingLevel("level_3")}
            className={cn("px-4 py-1.5 text-xs font-medium rounded-md transition-colors", activeRoutingLevel === "level_3" ? "bg-indigo-500/20 text-indigo-500 shadow-sm" : "text-muted-foreground hover:text-foreground")}
          >
            Nível 3 (Orquestrador IA)
          </button>
        </div>
      </div>

      <div className="flex justify-between items-end mb-2 border-b border-border/50 pb-4">
        <div>
           <h3 className="text-lg font-bold">
             {viewMode === "flow" ? "Hierarquia (Orquestrador IA)" : 
              viewMode === "kanban" ? "Agentes por Etapa (Condicional)" : 
              "Quadro de Funcionários (Gerenciamento)"}
           </h3>
           <p className="text-xs text-muted-foreground mt-1">
             {viewMode === "flow" ? "Múltiplos agentes conversam entre si e transferem o contato dinamicamente." :
              viewMode === "kanban" ? "O agente que atende depende da etapa do funil CRM ou tag do contato." :
              "Gerencie todos os agentes. Aqui você pode definir o roteamento básico (1 para voz, 1 para texto)."}
           </p>
        </div>
        
        <div className="flex flex-col items-end gap-3">
          <div className="flex items-center bg-muted/50 rounded-lg p-1 border border-border/50 shrink-0 hidden md:flex">
            <button 
              onClick={() => setViewMode("list")} 
              className={cn("flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors", viewMode === "list" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground")}
            >
              <LayoutPanelLeft className="h-4 w-4" /> Quadro Geral
            </button>
            <button 
              onClick={() => setViewMode("kanban")} 
              className={cn("flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors", viewMode === "kanban" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground")}
            >
              <KanbanSquare className="h-4 w-4" /> Kanban
            </button>
            <button 
              onClick={() => setViewMode("flow")} 
              className={cn("flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors", viewMode === "flow" ? "bg-indigo-500 text-white shadow-sm" : "text-muted-foreground hover:text-foreground")}
            >
              <Network className="h-4 w-4" /> Hierarquia
            </button>
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-2 w-full md:w-auto mb-6">
        <div className="flex gap-2 w-full md:w-auto">
           <Button variant="default" onClick={() => onNavigate?.("facil")} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 flex-1 md:flex-none shadow-[0_0_15px_rgba(16,185,129,0.3)]">
              <Boxes className="h-4 w-4" /> Criar Novo Funcionário Fácil
           </Button>
           <Button variant="outline" onClick={() => onNavigate?.("lab")} className="gap-2 flex-1 md:flex-none border-dashed bg-muted/20">
              <Bot className="h-4 w-4" /> Criar Funcionário Avançado
           </Button>
        </div>
      </div>

      {/* Roteamento Nível 1 UI */}
      {activeRoutingLevel === "level_1" && viewMode === "list" && (
        <div className="bg-primary/10 border border-primary/20 rounded-xl p-5 mb-8">
          <h4 className="text-sm font-bold text-primary flex items-center gap-2 mb-4">
            <Bot className="w-4 h-4" /> Roteamento Nível 1 Ativo
          </h4>
          <p className="text-xs text-muted-foreground mb-4">
            Selecione qual funcionário atenderá as mensagens de texto por padrão.
            Quem atende e quem faz as ligações fica no quadro "Ligações", no topo desta tela.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-background/50 border border-border/50 rounded-lg p-4">
              <label className="text-xs font-bold text-foreground mb-2 block flex items-center gap-2">
                💬 Atendente de Mensagens (Texto)
              </label>
              <select 
                value={level1TextAgent} 
                onChange={(e) => { setLevel1TextAgent(e.target.value); saveLevel1("default_profile_id", e.target.value); }}
                className="w-full bg-black border border-border/50 rounded-md text-sm p-2 text-white focus:ring-1 focus:ring-primary focus:border-primary outline-none"
              >
                <option value="">— Atendente padrão —</option>
                {list.map(a => (
                  <option key={a.id} value={a.id}>{a.name} ({kindLabel(a.kind)})</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Lista de agentes */}
      {loading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : viewMode === "kanban" ? (
        <div className="flex flex-col gap-4 min-h-[500px]">
          <div className="flex flex-wrap items-center justify-between gap-4 bg-black/40 p-2 rounded-lg border border-border/50">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-muted-foreground ml-2">Visão Kanban:</span>
              <select 
                value={kanbanCategory}
                onChange={(e) => setKanbanCategory(e.target.value as any)}
                className="bg-[#111] border border-border/50 rounded-md text-xs p-1.5 text-white outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="general">Visão Geral (Todas as Regras)</option>
                <option disabled>──────────</option>
                <option value="tags">Tags do Lead</option>
                <option value="stages">Etapas do Funil</option>
                <option value="time">Horário de Atendimento</option>
                <option value="exact">Palavra (Exata)</option>
                <option value="contains">Palavra (Contém)</option>
                <option value="similar">Palavra (Aproximada/Parecida)</option>
              </select>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-background/50 rounded-md border border-border/50 text-[0.65rem] text-muted-foreground overflow-x-auto custom-scrollbar">
              <span className="font-bold text-primary mr-1 whitespace-nowrap">Hierarquia de Roteamento (Arraste):</span>
              {hierarchy.map((item, index) => (
                <Fragment key={item.id}>
                  <Badge 
                    variant="outline" 
                    draggable
                    onDragStart={(e) => handleHierarchyDragStart(e, index)}
                    onDrop={(e) => handleHierarchyDrop(e, index)}
                    onDragOver={handleDragOver}
                    className={`text-[0.6rem] bg-${item.color}-500/10 border-${item.color}-500/20 text-${item.color}-400 cursor-grab active:cursor-grabbing hover:bg-${item.color}-500/20 transition-colors whitespace-nowrap`}
                  >
                    {index + 1}º {item.label}
                  </Badge>
                  {index < hierarchy.length - 1 && <span className="text-border mx-1">❯</span>}
                </Fragment>
              ))}
            </div>
          </div>

          <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar flex-1">
             {/* Coluna Unassigned (Sem Regra) */}
             <div 
               className="flex w-72 shrink-0 flex-col rounded-2xl border border-border/50 bg-glass shadow-soft overflow-hidden opacity-75 hover:opacity-100 transition-opacity"
               onDrop={(e) => handleDrop(e, 'unassigned')}
               onDragOver={handleDragOver}
             >
                <div className="p-3 border-b border-muted/30 flex justify-between items-center bg-muted/5">
                   <h5 className="text-[0.65rem] font-bold text-muted-foreground uppercase tracking-wider">Agentes Fallback / Sem Regra</h5>
                   <Badge variant="secondary" className="bg-muted/10 text-muted-foreground h-5 px-1.5 text-[0.6rem]">{list.filter(p => !p.logicType || p.logicType === 'none').length}</Badge>
                </div>
                <div className="p-3 flex-1 flex flex-col gap-3 min-h-[100px]">
                   {list.filter(p => !p.logicType || p.logicType === 'none').length === 0 && <p className="text-xs text-muted-foreground m-auto text-center">Nenhum agente fallback.<br/>A IA central lidará com casos soltos.</p>}
                   {list.filter(p => !p.logicType || p.logicType === 'none').map((p) => (
                      <div key={p.id} draggable onDragStart={(e) => handleDragStart(e, p.id)} className="p-3 bg-background border border-border/50 rounded-xl cursor-grab active:cursor-grabbing hover:-translate-y-1 transition-all shadow-sm">
                         <div className="flex items-center gap-2 font-bold text-sm mb-2">
                           {p.kind === "call" ? <Phone className="h-3 w-3 text-sky-500" /> : p.kind === "message" ? <MessageSquare className="h-3 w-3 text-emerald-500" /> : <Bot className="h-3 w-3 text-amber-500" />}
                           <span className="truncate">{p.name}</span>
                         </div>
                         <Badge variant="outline" className="text-[0.6rem]">{kindLabel(p.kind)}</Badge>
                      </div>
                   ))}
                </div>
             </div>

             {/* Colunas Dinâmicas baseadas na Categoria */}
             {(
                kanbanCategory === 'general' ? [
                  { id: '08:00-18:00', label: 'Comercial (08h-18h)', color: 'orange', logicType: 'time' },
                  { id: '1', label: '1. Qualificação', color: 'indigo', logicType: 'stage' },
                  { id: 'vip', label: '⭐ Cliente VIP', color: 'amber', logicType: 'tag' },
                  { id: 'comprar', label: 'Contém: "comprar"', color: 'emerald', logicType: 'contains' }
                ] :
                kanbanCategory === 'tags' ? [
                  { id: 'vip', label: '⭐ Cliente VIP', color: 'amber', logicType: 'tag' },
                  { id: 'devedor', label: '⚠️ Inadimplente', color: 'red', logicType: 'tag' },
                  { id: 'novo', label: '👋 Lead Novo', color: 'blue', logicType: 'tag' }
                ] :
                kanbanCategory === 'stages' ? [
                  { id: '1', label: '1. Qualificação', color: 'indigo', logicType: 'stage' },
                  { id: '2', label: '2. Apresentação', color: 'purple', logicType: 'stage' },
                  { id: '3', label: '3. Fechamento', color: 'emerald', logicType: 'stage' }
                ] :
                kanbanCategory === 'time' ? [
                  { id: '08:00-18:00', label: 'Comercial (08h-18h)', color: 'orange', logicType: 'time' },
                  { id: '18:00-08:00', label: 'Noturno / Madrugada', color: 'slate', logicType: 'time' }
                ] :
                kanbanCategory === 'exact' ? [
                  { id: 'comprar', label: 'Exato: "comprar"', color: 'pink', logicType: 'exact' },
                  { id: 'falar com humano', label: 'Exato: "falar com humano"', color: 'pink', logicType: 'exact' }
                ] :
                kanbanCategory === 'contains' ? [
                  { id: 'preço', label: 'Contém: "preço"', color: 'emerald', logicType: 'contains' },
                  { id: 'cancelar', label: 'Contém: "cancelar"', color: 'emerald', logicType: 'contains' }
                ] :
                kanbanCategory === 'similar' ? [
                  { id: 'suporte', label: 'Aprox: "suporte"', color: 'sky', logicType: 'similar' },
                  { id: 'vendas', label: 'Aprox: "vendas"', color: 'sky', logicType: 'similar' }
                ] : []
             ).map(col => {
                const colAgents = list.filter(p => p.logicType === col.logicType && p.trigger === col.id);
                const hasConflict = colAgents.length > 1;
                
                return (
                  <div 
                    key={`${col.logicType}-${col.id}`}
                    className={`flex w-72 shrink-0 flex-col rounded-2xl border bg-glass shadow-soft overflow-hidden ${hasConflict ? 'border-yellow-500/50' : 'border-border/50'}`}
                    onDrop={(e) => handleDrop(e, col.id)}
                    onDragOver={handleDragOver}
                  >
                     <div className={`p-3 border-b flex justify-between items-center ${hasConflict ? 'border-yellow-500/30 bg-yellow-500/10' : `border-${col.color}-500/30 bg-${col.color}-500/5`}`}>
                        <div className="flex flex-col">
                          <h5 className={`text-[0.65rem] font-bold uppercase tracking-wider ${hasConflict ? 'text-yellow-500' : `text-${col.color}-500`}`}>{col.label}</h5>
                          {hasConflict && <span className="text-[0.55rem] text-yellow-500/80 mt-0.5">⚠️ Conflito IA Desempata</span>}
                        </div>
                        <Badge variant="secondary" className={`${hasConflict ? 'bg-yellow-500/20 text-yellow-500' : `bg-${col.color}-500/10 text-${col.color}-500`} h-5 px-1.5 text-[0.6rem]`}>{colAgents.length}</Badge>
                     </div>
                     <div className="p-3 flex-1 flex flex-col gap-3 min-h-[100px]">
                        {colAgents.length === 0 && <p className="text-xs text-muted-foreground m-auto">Arraste para alocar</p>}
                        {colAgents.map((p) => (
                           <div key={p.id} draggable onDragStart={(e) => handleDragStart(e, p.id)} className={`p-3 bg-background border rounded-xl cursor-grab active:cursor-grabbing hover:-translate-y-1 transition-all shadow-md ${hasConflict ? 'border-yellow-500/30' : `border-${col.color}-500/30`}`}>
                              <div className="flex items-center gap-2 font-bold text-sm mb-2">
                                {p.kind === "call" ? <Phone className="h-3 w-3 text-sky-500" /> : p.kind === "message" ? <MessageSquare className="h-3 w-3 text-emerald-500" /> : <Bot className="h-3 w-3 text-amber-500" />}
                                <span className="truncate">{p.name}</span>
                              </div>
                              <div className="flex flex-wrap gap-1 mt-1">
                                <Badge variant="outline" className={`text-[0.55rem] ${hasConflict ? 'border-yellow-500/20 text-yellow-400' : `border-${col.color}-500/20 text-${col.color}-400`}`}>Regra Ativa</Badge>
                                {/* Cross-category badge simulation */}
                                {p.status === 'production' && <Badge variant="outline" className="text-[0.55rem] border-primary/20 text-primary">⚙️ Triador IA</Badge>}
                              </div>
                           </div>
                        ))}
                     </div>
                  </div>
                );
             })}
          </div>
        </div>
      ) : viewMode === "flow" ? (
         <div className="mt-2 h-[600px] border border-border/50 rounded-2xl overflow-hidden shadow-inner bg-[#0a0a0a]">
            <AgentOrchestratorFlow 
              agents={list} 
              onUpdateAgent={(id, updates) => {
                setList(prev => prev.map(a => a.id === id ? { ...a, ...updates } : a));
                // We'd also send to API here
                toast.success("Gatilho atualizado com sucesso!");
              }} 
            />
         </div>
      ) : (
        <div className="space-y-4 mt-4">
          <div className="flex flex-col sm:flex-row gap-3 items-center bg-black/20 p-3 rounded-xl border border-border/50">
            <div className="relative w-full sm:w-64">
              <Activity className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input 
                name="agent_search_box"
                autoComplete="off"
                placeholder="Buscar agente por nome..." 
                className="pl-9 bg-background/50 border-border/50 h-9"
                value={listSearch}
                onChange={(e) => setListSearch(e.target.value)}
              />
            </div>
            <div className="flex-1 flex gap-2">
              {selectedAgents.length > 0 && (
                <Button variant="secondary" size="sm" className="h-9 bg-primary/20 text-primary border border-primary/30 hover:bg-primary/30">
                  <Settings2 className="w-4 h-4 mr-2" />
                  Editar {selectedAgents.length} agentes
                </Button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground font-medium hidden sm:inline-block">Habilidade:</span>
              <select 
                className="bg-background/50 border border-border/50 rounded-md text-xs p-1.5 text-white outline-none focus:ring-1 focus:ring-primary min-w-[120px]"
                value={listFilter}
                onChange={(e) => setListFilter(e.target.value)}
              >
                <option value="all">Todos os Agentes</option>
                <option value="call">Apenas Ligação (Voz)</option>
                <option value="message">Apenas Texto (WhatsApp)</option>
                <option value="both">Híbridos (Voz + Texto)</option>
              </select>
            </div>
            <div className="flex bg-background/50 rounded-lg p-1 border border-border/50 shrink-0">
               <button onClick={() => setListFormat("grid")} className={`p-1.5 rounded-md transition-colors ${listFormat === 'grid' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted/50'}`} title="Modo Grid">
                  <LayoutGrid className="w-4 h-4" />
               </button>
               <button onClick={() => setListFormat("table")} className={`p-1.5 rounded-md transition-colors ${listFormat === 'table' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted/50'}`} title="Modo Lista (Compacto)">
                  <List className="w-4 h-4" />
               </button>
            </div>
          </div>
          
          {listFormat === 'table' ? (
             <div className="col-span-1 xl:col-span-2 overflow-x-auto border border-border/50 rounded-2xl bg-black/20">
                <table className="w-full text-left text-sm whitespace-nowrap">
                   <thead className="bg-muted/10 text-muted-foreground text-xs uppercase border-b border-border/50">
                      <tr>
                         <th className="p-3 w-10">
                            <input 
                              type="checkbox" 
                              className="w-4 h-4 rounded border-border/50 accent-primary" 
                              checked={selectedAgents.length > 0 && selectedAgents.length === list.length}
                              onChange={(e) => {
                                 if (e.target.checked) setSelectedAgents(list.map(a => a.id));
                                 else setSelectedAgents([]);
                              }}
                            />
                         </th>
                         <th className="p-3">Agente</th>
                         <th className="p-3">Habilidade</th>
                         <th className="p-3">LLM</th>
                         <th className="p-3">Voz/Credencial</th>
                         <th className="p-3">Conversas</th>
                         <th className="p-3 text-right">Ações</th>
                      </tr>
                   </thead>
                   <tbody className="divide-y divide-border/30">
                      {list.filter(p => {
                         const matchSearch = p.name.toLowerCase().includes(listSearch.toLowerCase());
                         const matchFilter = listFilter === 'all' ? true : p.kind === listFilter;
                         return matchSearch && matchFilter;
                      }).map(p => (
                         <tr key={p.id} className="hover:bg-muted/5 transition-colors">
                            <td className="p-3">
                               <input 
                                 type="checkbox" 
                                 className="w-4 h-4 rounded border-border/50 accent-primary"
                                 checked={selectedAgents.includes(p.id)}
                                 onChange={(e) => {
                                    if (e.target.checked) setSelectedAgents(prev => [...prev, p.id]);
                                    else setSelectedAgents(prev => prev.filter(id => id !== p.id));
                                 }}
                               />
                            </td>
                            <td className="p-3 font-medium flex items-center gap-2">
                               {p.status === "production" ? <span className="flex h-2 w-2 rounded-full bg-emerald-500"></span> : <span className="flex h-2 w-2 rounded-full bg-muted"></span>}
                               {p.name}
                               {p.id.includes('draft') && <Badge variant="outline" className="text-[0.55rem] border-yellow-500/30 text-yellow-500 bg-yellow-500/10">Draft</Badge>}
                            </td>
                            <td className="p-3">
                               <Badge variant="outline" className="text-[0.6rem]">{p.kind}</Badge>
                            </td>
                            <td className="p-3 text-xs text-muted-foreground">{p.ai_model || p.llm_model || 'Padrão do sistema'}</td>
                            <td className="p-3 text-xs text-muted-foreground flex items-center gap-2">
                               {p.kind === 'call' ? <><Volume2 className="w-3 h-3 text-pink-400" /> ElevenLabs</> : <><ShieldCheck className="w-3 h-3 text-indigo-400" /> API Padrão</>}
                            </td>
                            <td className="p-3 text-xs font-mono">{p.total_calls ?? 0}</td>
                            <td className="p-3 text-right">
                               <Button variant="ghost" size="sm" onClick={() => { setListFormat('grid'); setExpandedId(p.id); }} className="h-7 text-xs bg-primary/10 text-primary">Setup</Button>
                            </td>
                         </tr>
                      ))}
                   </tbody>
                </table>
             </div>
          ) : (
             <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
             {list.filter(p => {
                const matchSearch = p.name.toLowerCase().includes(listSearch.toLowerCase());
                const matchFilter = listFilter === 'all' ? true : p.kind === listFilter;
                return matchSearch && matchFilter;
             }).map((p) => (
            <Card key={p.id} className={`p-0 overflow-hidden bg-background/50 border-primary/20 shadow-glow transition-all duration-300 ${expandedId === p.id ? 'ring-2 ring-primary/30 xl:col-span-2' : 'hover:border-primary/50'}`}>
              <div className="p-5 flex flex-col">
                
                {/* HEADER (Esquerda: Título | Direita: Botões) */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  {/* Título e Ícones */}
                  <div className="min-w-0 flex-1 flex items-center gap-3 font-bold text-lg">
                    <input 
                       type="checkbox" 
                       className="w-4 h-4 rounded border-border/50 accent-primary" 
                       checked={selectedAgents.includes(p.id)}
                       onChange={(e) => {
                          if (e.target.checked) setSelectedAgents(prev => [...prev, p.id]);
                          else setSelectedAgents(prev => prev.filter(id => id !== p.id));
                       }}
                    />
                    <div className="p-2 rounded-lg bg-background border border-border/50 shadow-sm shrink-0">
                      {p.kind === "call" ? <Phone className="h-4 w-4 text-sky-500" /> :
                       p.kind === "message" ? <MessageSquare className="h-4 w-4 text-emerald-500" /> :
                       <Bot className="h-4 w-4 text-amber-500" />}
                    </div>
                    <span className="truncate group/name relative cursor-default" title={p.system_prompt || "Prompt do sistema não configurado..."}>
                       {p.name}
                    </span>
                    {p.status === "production" && <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse ml-2 shrink-0" title="Em Produção"></span>}
                    {p.id.includes('draft') && (
                       <Badge variant="outline" className="ml-2 text-[0.55rem] border-yellow-500/30 text-yellow-500 bg-yellow-500/10 shrink-0">📝 Rascunho</Badge>
                    )}
                  </div>
                  
                  {/* Botões de Ação */}
                  <div className="flex flex-col gap-2 shrink-0">
                    <div className="flex gap-1 justify-end">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => setExpandedId(expandedId === p.id ? null : p.id)}
                        className="h-8 rounded-lg font-semibold bg-primary/10 text-primary hover:bg-primary/20"
                      >
                        <Settings2 className="h-3.5 w-3.5 mr-1.5" /> Setup {expandedId === p.id ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />}
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => duplicateAgent(p)} className="h-8 w-8 rounded-lg hover:bg-muted/50" title="Duplicar">
                        <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                      </Button>
                      <Button variant="ghost" size="icon" onClick={() => remove(p.id, p.name)} className="h-8 w-8 rounded-lg hover:bg-destructive/10 hover:text-destructive">
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                    
                    <div className="flex gap-1 justify-end mt-auto items-center">
                      <Badge variant="muted" className="h-5 text-[0.6rem] px-1.5">Em breve</Badge>
                      <Button variant="outline" size="sm" disabled className="h-7 text-[0.65rem] border-dashed opacity-50 cursor-not-allowed" title="Histórico de versões ainda não disponível">
                        <History className="w-3 h-3 mr-1" /> Reverter Versão
                      </Button>
                      <Button 
                        size="sm" 
                        onClick={() => {
                          setExpandedId(p.id);
                          setActiveInnerTabs(prev => ({...prev, [p.id]: "test"}));
                          setTimeout(() => document.querySelector(`[data-agent="${p.id}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100);
                        }}
                        className="h-7 text-[0.65rem] bg-emerald-500 hover:bg-emerald-600 text-white"
                      >
                        <PlayCircle className="w-3 h-3 mr-1" /> Run/Test
                      </Button>
                    </div>
                  </div>
                </div>
                  
                {/* Meta tags (Distribuição Orgânica) - Agora ocupa 100% da largura do card */}
                  <div className="flex flex-wrap gap-3 mb-4 mt-4">
                    
                    {/* Bloco 1: LLM */}
                    <div className="flex-1 min-w-[220px] flex flex-col gap-2 p-2.5 rounded-xl bg-card/40 border border-border/40 shadow-sm">
                      <span className="text-[0.6rem] uppercase font-bold text-muted-foreground flex items-center gap-1"><BrainCircuit className="w-3 h-3"/> Motor (LLM)</span>
                      <div className="flex flex-wrap items-center gap-2">
                        {/* Provedor */}
                        <div className="relative inline-flex items-center group">
                          <Zap className="w-3 h-3 text-amber-500 absolute left-2 pointer-events-none" />
                          <select 
                            className="pl-6 pr-6 py-1 text-[0.65rem] font-medium bg-muted/50 border border-border/50 rounded-full appearance-none hover:bg-muted/80 hover:border-border transition-colors outline-none cursor-pointer"
                            defaultValue={p.ai_provider || "openai"}
                            onChange={async (e) => {
                              // FIX (QA IA): antes gravava no campo LOCAL `provider` (que o
                              // backend NÃO lê — ele usa `ai_provider`) e mostrava sucesso sem
                              // fazer POST nenhum. Falso sucesso: recarregava e voltava tudo.
                              // Agora persiste em ai_provider reenviando o perfil completo.
                              const newProvider = e.target.value;
                              setList(prev => prev.map(a => a.id === p.id ? { ...a, ai_provider: newProvider } : a));
                              if (await persistProvider(p, newProvider)) toast.success("Provedor atualizado!");
                            }}
                          >
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="groq">Groq</option>
                            <option value="google">Google</option>
                          </select>
                          <ChevronDown className="w-3 h-3 text-muted-foreground absolute right-2 pointer-events-none group-hover:text-foreground transition-colors" />
                        </div>

                        {/* Modelo */}
                        <div className="relative inline-flex items-center group">
                          <select 
                            className="pl-3 pr-6 py-1 text-[0.65rem] font-medium bg-muted/50 border border-border/50 rounded-full appearance-none hover:bg-muted/80 hover:border-border transition-colors outline-none cursor-pointer max-w-[130px] truncate"
                            defaultValue={p.ai_model || p.llm_model || "gpt-4o"}
                            onChange={async (e) => {
                              const newModel = e.target.value;
                              setList(prev => prev.map(a => a.id === p.id ? { ...a, ai_model: newModel } : a));
                              if (await persistModel(p, newModel)) toast.success("Modelo atualizado!");
                            }}
                          >
                            <optgroup label="OpenAI">
                              <option value="gpt-4o">GPT-4o</option>
                              <option value="gpt-4o-mini">GPT-4o Mini</option>
                            </optgroup>
                            <optgroup label="Anthropic">
                              <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                              <option value="claude-3-haiku">Claude 3 Haiku</option>
                            </optgroup>
                            <optgroup label="Groq">
                              <option value="llama-3-70b">Llama 3 70B</option>
                              <option value="mixtral-8x7b">Mixtral 8x7b</option>
                            </optgroup>
                          </select>
                          <ChevronDown className="w-3 h-3 text-muted-foreground absolute right-2 pointer-events-none group-hover:text-foreground transition-colors" />
                        </div>

                        {/* Credencial Texto */}
                        <div className="relative inline-flex items-center group">
                          <ShieldCheck className="w-3 h-3 text-indigo-400 absolute left-2 pointer-events-none" />
                          <select 
                            className="pl-6 pr-6 py-1 text-[0.65rem] font-medium bg-muted/50 border border-border/50 rounded-full appearance-none hover:bg-muted/80 hover:border-border transition-colors outline-none cursor-pointer"
                            defaultValue="default"
                            onChange={(e) => {
                              // FIX (QA IA): "Conta Vendas"/"Conta Suporte" eram valores MOCK e
                              // não existe coluna de credencial-por-agente no backend — o toast
                              // "alterada com sucesso" era FALSO (nada persistia; o agente usa a
                              // credencial global de IA). Enquanto não há suporte real, avisamos
                              // com honestidade e voltamos pro padrão em vez de mentir.
                              e.target.value = "default";
                              toast.info("Por agora todos os agentes usam a credencial de IA global. Credencial por agente ainda não está disponível.");
                            }}
                          >
                            <option value="default">API Padrão (global)</option>
                          </select>
                          <ChevronDown className="w-3 h-3 text-muted-foreground absolute right-2 pointer-events-none group-hover:text-foreground transition-colors" />
                        </div>
                      </div>
                    </div>

                    {/* Bloco 2: Voz */}
                    {p.kind === 'call' && (
                      <div className="flex-1 min-w-[220px] flex flex-col gap-2 p-2.5 rounded-xl bg-pink-500/5 border border-pink-500/10 shadow-sm">
                        <span className="text-[0.6rem] uppercase font-bold text-pink-500/70 flex items-center gap-1"><Volume2 className="w-3 h-3"/> Voz (TTS)</span>
                        <div className="flex flex-wrap items-center gap-2">
                          
                          {/* Credencial Voz */}
                          <div className="relative inline-flex items-center group">
                            <ShieldCheck className="w-3 h-3 text-pink-400 absolute left-2 pointer-events-none" />
                            <select 
                              className="pl-6 pr-6 py-1 text-[0.65rem] font-medium bg-pink-500/10 border border-pink-500/20 rounded-full appearance-none hover:bg-pink-500/20 hover:border-pink-500/30 transition-colors outline-none cursor-pointer text-pink-500"
                              defaultValue="default"
                              onChange={(e) => {
                                // FIX (QA IA): "ElevenLabs (1)/(2)" eram MOCK e não persistiam —
                                // não há coluna de credencial-de-voz por agente. O toast de
                                // sucesso era falso. As chaves ElevenLabs são geridas globalmente
                                // (Cofre de Credenciais / eleven keys manager), não por agente.
                                e.target.value = "default";
                                toast.info("As chaves de voz (ElevenLabs) são geridas no Cofre de Credenciais, não por agente.");
                              }}
                            >
                              <option value="default">API Padrão (global)</option>
                            </select>
                            <ChevronDown className="w-3 h-3 text-pink-400/70 absolute right-2 pointer-events-none group-hover:text-pink-400 transition-colors" />
                          </div>

                          {/* Configuração de Voz e Play */}
                          <div className="flex items-center gap-1">
                            <div className="relative inline-flex items-center group">
                              <select 
                                className="pl-3 pr-6 py-1 text-[0.65rem] font-medium bg-muted/50 border border-border/50 rounded-full appearance-none hover:bg-muted/80 hover:border-border transition-colors outline-none cursor-pointer"
                              >
                                <optgroup label="ElevenLabs">
                                  <option>Voz: Antony (Suave)</option>
                                  <option>Voz: Rachel (Empolgada)</option>
                                </optgroup>
                                <optgroup label="Google TTS">
                                  <option>Voz: pt-BR-Standard-A</option>
                                </optgroup>
                              </select>
                              <ChevronDown className="w-3 h-3 text-muted-foreground absolute right-2 pointer-events-none group-hover:text-foreground transition-colors" />
                            </div>
                            <button onClick={() => toast("Testando áudio via WS...")} className="p-1 rounded-full bg-pink-500/10 text-pink-500 hover:bg-pink-500/20 transition-colors" title="Testar Áudio">
                               <Play className="w-3 h-3" fill="currentColor" />
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Bloco 3: Status / Métricas */}
                    <div className="flex-1 min-w-[150px] flex flex-col gap-2 p-2.5 rounded-xl bg-card/40 border border-border/40 shadow-sm">
                      <span className="text-[0.6rem] uppercase font-bold text-muted-foreground flex items-center gap-1"><Activity className="w-3 h-3"/> Status & Uso</span>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="outline" className="text-[0.65rem] bg-muted/50 font-medium h-6">
                          {/* FIX (QA IA): total_calls não existe no backend (só nos mocks) →
                              perfis reais mostravam "undefined conversas". Fallback pra 0. */}
                          {p.total_calls ?? 0} conversas
                        </Badge>
                        
                        <div className="relative inline-flex items-center group opacity-50">
                          <History className="w-3 h-3 text-emerald-500 absolute left-2 pointer-events-none" />
                          <select
                            disabled
                            className="pl-6 pr-6 py-1 text-[0.65rem] font-medium bg-muted/50 border border-emerald-500/20 text-emerald-500 rounded-full appearance-none outline-none cursor-not-allowed"
                            defaultValue={p.version || "v1.0"}
                            title="Histórico de versões ainda não disponível"
                          >
                            <option value={p.version || "v1.0"}>{p.version || "v1.0"} (Atual)</option>
                          </select>
                          <ChevronDown className="w-3 h-3 text-emerald-500 absolute right-2 pointer-events-none" />
                        </div>
                        <Badge variant="muted" className="h-5 text-[0.6rem] px-1.5">Versões: Em breve</Badge>
                      </div>
                    </div>

                  </div>
                  <div className="mt-2 flex items-center justify-end opacity-50 text-[0.6rem] font-medium border-t border-border/30 pt-2 w-full">
                     {/* "Última edição por Joãozinho" era 100% hardcoded (nome fixo + new Date()).
                         Não há dado real de editor nem data de criação no Profile → linha omitida. */}
                     {p.logicType !== 'none' && p.logicType && <span className="flex items-center gap-1"><Network className="w-3 h-3" /> Integrado</span>}
                  </div>
              </div>
              
              {/* Área de Configuração Avançada Expandida (O Treinador) */}
              {expandedId === p.id && (
                <div className="border-t border-border/50 bg-background/50 p-0 animate-in slide-in-from-top-2" data-agent={p.id}>
                  <Tabs value={activeInnerTabs[p.id] || "facil"} onValueChange={(val) => setActiveInnerTabs(prev => ({...prev, [p.id]: val}))} className="w-full">
                    <div className="border-b border-border/50 px-4 pt-2 bg-muted/10">
                      <TabsList className="bg-muted/50 p-1 rounded-xl flex flex-wrap w-full h-auto justify-start gap-1 my-2">
                        <HideableTab value="facil" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 text-sm flex-1 sm:flex-none"><Wand2 className="h-4 w-4 mr-2 shrink-0" /> Configuração Fácil</HideableTab>
                        <HideableTab value="ai" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 text-sm flex-1 sm:flex-none"><BrainCircuit className="h-4 w-4 mr-2 shrink-0" /> IA & Modelo</HideableTab>
                        <HideableTab value="rag" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 text-sm flex-1 sm:flex-none"><UploadCloud className="h-4 w-4 mr-2 shrink-0" /> RAG & Base</HideableTab>
                        <HideableTab value="integrations" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 text-sm flex-1 sm:flex-none"><Link2 className="h-4 w-4 mr-2 shrink-0" /> Webhook & Integrações</HideableTab>
                        <HideableTab value="swarm" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 text-sm flex-1 sm:flex-none"><Network className="h-4 w-4 mr-2 shrink-0" /> Roteamento (Swarm)</HideableTab>
                        <HideableTab value="qa" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 text-sm flex-1 sm:flex-none"><ShieldCheck className="h-4 w-4 mr-2 shrink-0" /> QA / Auditoria</HideableTab>
                        <HideableTab value="trainer" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 text-sm flex-1 sm:flex-none"><GraduationCap className="h-4 w-4 mr-2 shrink-0" /> O Treinador</HideableTab>
                        <HideableTab value="test" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 text-sm flex-1 sm:flex-none"><PlayCircle className="h-4 w-4 mr-2 shrink-0" /> Testar Chat</HideableTab>
                      </TabsList>
                    </div>

                    {/* TAB: FÁCIL */}
                    <TabsContent value="facil" className="p-0 mt-0">
                      <div className="bg-background border-t border-border/50 p-6">
                        <EasyAgentWizard initialProfile={p} editMode={true} onSaved={() => {
                           toast.success("Edições aplicadas.");
                           reload();
                        }} />
                      </div>
                    </TabsContent>

                    {/* TAB: IA & MODELO */}
                    <TabsContent value="ai" className="p-5 space-y-5 mt-0">
                      <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
                        <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <BrainCircuit className="w-5 h-5 text-primary" />
                            <h3 className="font-bold text-sm">Cérebro da IA (LLM)</h3>
                          </div>
                        </div>
                        <div className="p-6 space-y-6">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-1">
                              <label className="text-sm font-semibold">Provedor</label>
                              {/* FIX (QA IA): lia/gravava "provider" (campo inexistente no
                                  backend) → "Salvar Motor da IA" mostrava sucesso mas ai_provider
                                  nunca mudava. Agora usa ai_provider, que o backend persiste. */}
                              <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={editVal(p, "ai_provider") || "anthropic"} onChange={(e) => setEdit(p.id, "ai_provider", e.target.value)}>
                                <option value="anthropic">Anthropic (Claude)</option>
                                <option value="openai">OpenAI</option>
                                <option value="gemini">Google Gemini</option>
                                <option value="groq">Groq</option>
                                <option value="custom">Custom / Proxy</option>
                              </select>
                            </div>
                            {/* "API Key Manual" saiu (revisão do PC, 04/10): gravava a chave em texto puro
                                e o agente não usava. A chave de cada motor fica em Credenciais (cofre). */}
                          </div>
                          <div className="space-y-1">
                            <label className="text-sm font-semibold">Modelo Específico</label>
                            {/* FIX (QA IA): lia/gravava "llm_model" (campo legado/mock que o
                                backend não persiste) → o modelo digitado aqui não ia pra lugar
                                nenhum. Agora usa ai_model, a coluna real de agent_profiles. */}
                            <Input className="flex-1 bg-background" value={editVal(p, "ai_model") || ""} onChange={(e) => setEdit(p.id, "ai_model", e.target.value)} placeholder="Ex: claude-3-5-sonnet-20240620" />
                          </div>
                          <div className="space-y-1 mt-4">
                            <label className="text-sm font-semibold">Manual do Cargo {/* System Prompt */}</label>
                            <Textarea rows={8} value={editVal(p, "system_prompt") || ""} onChange={(e) => setEdit(p.id, "system_prompt", e.target.value)} placeholder="Você é um assistente..." className="bg-[#0D1117] text-[#C9D1D9] border-border/50 font-mono text-sm resize-none focus:ring-primary/50 mt-2" />
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                            <Field label="Tom de Voz" hint="Ex.: formal, amigável, direto ao ponto.">
                               <Input value={editVal(p, "tone") || ""} onChange={(e) => setEdit(p.id, "tone", e.target.value)} placeholder="Ex.: cordial e objetivo" className="bg-background" />
                            </Field>
                            <Field label="Grau de Criatividade {/* Temperatura */}" hint="Valores baixos são precisos, altos são criativos.">
                              <div className="flex items-center gap-4 py-2">
                                <Slider value={[Number(editVal(p, "temperature") ?? 30)]} max={100} step={1} className="flex-1" onValueChange={(v) => setEdit(p.id, "temperature", v[0])} />
                                <span className="text-sm font-mono text-muted-foreground w-8">{Number(editVal(p, "temperature") ?? 30) / 100}</span>
                              </div>
                            </Field>
                          </div>
                          <Field label="Limites de Alçada {/* Guardrails */}" hint="Regras que o agente nunca deve quebrar.">
                             <Textarea value={editVal(p, "guardrails") || ""} onChange={(e) => setEdit(p.id, "guardrails", e.target.value)} rows={3} className="bg-background resize-y" placeholder="Ex.: Nunca prometa desconto sem aprovação." />
                          </Field>
                        </div>
                      </Card>

                      <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
                        <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Headphones className="w-5 h-5 text-pink-500" />
                            <h3 className="font-bold text-sm">Estúdio de Voz (TTS) & Acústica</h3>
                          </div>
                        </div>
                        <div className="p-6 space-y-6">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <Field label="Sintetizador e Voz" hint="Escolha quem vai falar por este agente.">
                              <div className="flex gap-2">
                                <select className="flex-1 rounded-md border bg-background px-3 py-2 text-sm" value={editVal(p, "voice") || "alloy"} onChange={(e) => setEdit(p.id, "voice", e.target.value)}>
                                  <option value="alloy">Alloy (Neutro/Profissional)</option>
                                  <option value="echo">Echo (Grave/Masculino)</option>
                                  <option value="fable">Fable (Expressivo)</option>
                                  <option value="onyx">Onyx (Forte/Profundo)</option>
                                  <option value="nova">Nova (Feminino/Dinâmico)</option>
                                  <option value="shimmer">Shimmer (Suave/Calmo)</option>
                                </select>
                                <Button variant="secondary" onClick={async () => {
                                  const voice = editVal(p, "voice") || "alloy";
                                  const text = "Olá! Eu sou o assistente virtual desta conta. Esta é uma amostra da minha voz.";
                                  try {
                                    const res = await apiPost<{ ok?: boolean; audio_base64?: string; audio_mime?: string; error?: string }>("/api/tts/preview", { text, voice });
                                    if (res?.ok && res.audio_base64) {
                                      const bytes = Uint8Array.from(atob(res.audio_base64), (c) => c.charCodeAt(0));
                                      const blob = new Blob([bytes], { type: res.audio_mime || "audio/ogg" });
                                      const url = URL.createObjectURL(blob);
                                      const audio = new Audio(url);
                                      audio.onended = () => URL.revokeObjectURL(url);
                                      await audio.play();
                                    } else {
                                      toast.error("Amostra indisponível: " + (res?.error || "TTS falhou"));
                                    }
                                  } catch (err) {
                                    toast.error("Erro ao tocar amostra: " + (err instanceof Error ? err.message : String(err)));
                                  }
                                }} className="shadow-sm">
                                  <Play className="w-4 h-4 mr-1"/> Ouvir
                                </Button>
                              </div>
                            </Field>
                            
                            <Field label="Ambientação Acústica" hint="Fundo sonoro durante a ligação.">
                              <div className="flex gap-2 items-center">
                                <select className="flex-1 rounded-md border bg-background px-3 py-2 text-sm" value={editVal(p, "background_noise") || "none"} onChange={(e) => setEdit(p.id, "background_noise", e.target.value)}>
                                  <option value="none">Usar Padrão Global</option>
                                  <option value="clean">Nenhum (Voz Limpa - Forçar zero som)</option>
                                  <option value="office">🏢 Escritório (Teclados, vozes distantes)</option>
                                  <option value="call_center">🎧 Call Center (Telemarketing movimentado)</option>
                                  <option value="street">🚗 Rua / Trânsito Leve</option>
                                  <option value="coffee_shop">☕ Cafeteria</option>
                                </select>
                              </div>
                            </Field>
                          </div>

                          <div className="flex gap-6 items-center border-t border-border/50 pt-4">
                             <div className="flex-1 space-y-3">
                               <span className="text-xs text-muted-foreground flex items-center justify-between font-bold">Tom (Pitch)</span>
                               <Slider value={[50]} max={100} step={1} className="w-full" />
                             </div>
                             <div className="flex-1 space-y-3">
                               <span className="text-xs text-muted-foreground flex items-center justify-between font-bold">Velocidade (Speed)</span>
                               <Slider value={[50]} max={100} step={1} className="w-full" />
                             </div>
                             {(editVal(p, "background_noise") && editVal(p, "background_noise") !== "none" && editVal(p, "background_noise") !== "clean") && (
                             <div className="flex-1 space-y-3">
                               <span className="text-xs text-muted-foreground flex items-center justify-between font-bold">Volume Acústico</span>
                               <Slider value={[Number(editVal(p, "background_noise_volume") ? Number(editVal(p, "background_noise_volume")) * 100 : 10)]} max={30} step={1} className="w-full" onValueChange={(v) => setEdit(p.id, "background_noise_volume", v[0]/100)} />
                             </div>
                             )}
                          </div>
                        </div>
                      </Card>
                      
                      <div className="flex justify-end pt-2">
                        <Button onClick={() => saveAgent(p)} className="rounded-xl shadow-glow gap-2 px-6"><Zap className="w-4 h-4"/> Salvar Motor da IA</Button>
                      </div>
                    </TabsContent>

                    {/* TAB: RAG & BASE */}
                    <TabsContent value="rag" className="p-5 space-y-5 mt-0">
                       {(p.kind === "call") ? (
                        <div className="text-center py-8">
                          <BrainCircuit className="h-8 w-8 text-muted-foreground mx-auto mb-2 opacity-50" />
                          <p className="text-muted-foreground">Funcionários exclusivos de voz não utilizam base RAG para manter a latência da ligação ultrabaixa (&lt; 500ms).</p>
                        </div>
                       ) : (
                        <AgentRagPanel agentId={p.id} />
                       )}
                    </TabsContent>

                    {/* TAB: INTEGRAÇÕES */}
                    <TabsContent value="integrations" className="p-5 space-y-5 mt-0">
                      <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
                        <div className="border-b border-border/50 bg-muted/20 px-6 py-4 flex items-center justify-between">
                          <div>
                            <h4 className="font-bold flex items-center gap-2 text-primary">
                              <Link2 className="w-5 h-5" /> Webhook Específico (Event-Driven)
                            </h4>
                            <p className="text-xs text-muted-foreground mt-1">
                              Sobrescreve o webhook global. A IA envia requisições POST para cá sempre que este agente atuar.
                            </p>
                          </div>
                        </div>
                        
                        <div className="p-6 space-y-6">
                          <p className="text-[11px] font-semibold text-amber-600">Em breve: fica salvo, mas ainda não muda o comportamento do agente.</p>
                          <Field label="URL do Webhook do Agente" hint="Endpoint que receberá JSONs de chamadas, resumos e transbordos.">
                            <Input name={`webhook_url_${p.id}`} autoComplete="off" value={editVal(p, "webhook_url") || ""} onChange={(e) => setEdit(p.id, "webhook_url", e.target.value)} placeholder="https://seu-n8n.com/webhook/agente-vendedor" className="rounded-xl bg-background" />
                          </Field>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-1">
                              <label className="text-sm font-semibold">Tópicos de Inscrição (Events)</label>
                              <div className="flex flex-wrap gap-2 mt-2">
                                 {["call.started", "call.ended", "ai_field_detected", "call_summary"].map(ev => {
                                   const active = (editVal(p, "webhook_events") || []).includes(ev);
                                   return (
                                     <button
                                       key={ev}
                                       onClick={() => {
                                         const curr = editVal(p, "webhook_events") || [];
                                         setEdit(p.id, "webhook_events", active ? curr.filter((x: string) => x !== ev) : [...curr, ev]);
                                       }}
                                       className={cn("rounded-lg border px-3 py-1.5 text-[10px] font-semibold transition-all shadow-sm", active ? "border-primary bg-primary text-primary-foreground shadow-glow" : "border-border/50 bg-background text-muted-foreground hover:bg-muted")}
                                     >
                                       {ev}
                                     </button>
                                   )
                                 })}
                              </div>
                            </div>

                            <div className="space-y-4">
                              {/* Espaço reservado ou outras configurações podem entrar aqui */}
                            </div>
                          </div>
                        </div>
                      </Card>

                      <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
                        <div className="border-b border-border/50 bg-muted/20 px-6 py-4 flex items-center justify-between">
                          <div>
                            <h4 className="font-bold flex items-center gap-2 text-rose-500">
                              <AlertTriangle className="w-5 h-5" /> Passar para a Equipe Humana {/* Handoff */}
                            </h4>
                            <p className="text-xs text-muted-foreground mt-1">
                              Para onde a plataforma deve gritar quando o agente pausar a chamada e pedir ajuda?
                            </p>
                          </div>
                        </div>
                        <div className="p-6 space-y-6">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div className="md:col-span-2"><p className="text-[11px] font-semibold text-amber-600">Em breve: fica salvo, mas ainda não muda o comportamento do agente.</p></div>
                            <Field label="Canal de Notificação" hint="Como você quer ser notificado?">
                              <select className="w-full rounded-xl border bg-background px-3 py-2.5 text-sm" value={editVal(p, "handoff_notify") || "panel"} onChange={(e) => setEdit(p.id, "handoff_notify", e.target.value)}>
                                 <option value="panel">Aviso Visual no Painel (Notificações)</option>
                                 <option value="telegram">Mandar mensagem no Telegram</option>
                                 <option value="whatsapp">Mandar mensagem no Meu WhatsApp</option>
                              </select>
                            </Field>
                            <Field label="Mensagem para o Humano" hint="O que mandar para sua equipe?">
                              <Input value={editVal(p, "handoff_notify_msg") || ""} onChange={(e) => setEdit(p.id, "handoff_notify_msg", e.target.value)} placeholder='Ex.: "Agente pausado, lead querendo falar com humano!"' className="rounded-xl bg-background" />
                            </Field>
                          </div>
                        </div>
                      </Card>

                      <div className="flex justify-end pt-2">
                        <Button onClick={() => saveAgent(p)} className="rounded-xl shadow-glow gap-2 px-6"><Link2 className="w-4 h-4"/> Salvar Integrações</Button>
                      </div>
                    </TabsContent>

                    {/* TAB: TESTAR CHAT */}
                    <TabsContent value="test" className="p-0 mt-0">
                      <AgentChatTest agentId={p.id} />
                    </TabsContent>

                    {/* TAB: ROTEAMENTO / SWARM */}
                    <TabsContent value="swarm" className="p-5 mt-0 space-y-6">
                      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                        {/* Modo de Transferência */}
                        <div className="border border-border/50 bg-background/50 p-5 rounded-2xl shadow-sm space-y-4">
                           <h4 className="font-bold text-sm flex items-center gap-2"><Network className="w-4 h-4 text-primary"/> Comportamento do Multi-Agente</h4>
                           <p className="text-[11px] font-semibold text-amber-600">Em breve: fica salvo, mas ainda não muda o comportamento do agente.</p>
                           
                           <div className="space-y-3">
                             <label className={cn("flex flex-col gap-2 p-3 border rounded-xl cursor-pointer transition-all", editVal(p, "swarm_mode") === "silent" ? "border-muted/50 bg-muted/10 opacity-70" : "border-primary bg-primary/5 ring-1 ring-primary/20")}>
                               <div className="flex items-center gap-2">
                                 <input type="radio" name={`swarm_mode_${p.id}`} value="announced" checked={editVal(p, "swarm_mode") !== "silent"} onChange={() => setEdit(p.id, "swarm_mode", "announced")} className="accent-primary" />
                                 <span className="font-bold text-sm">Transferência Anunciada (Clássica)</span>
                               </div>
                               <p className="text-xs text-muted-foreground pl-5">
                                 A IA avisa o cliente ("<i>Um momento, vou transferir você para o setor de suporte</i>") e a próxima IA assume se apresentando com um <strong>novo nome e voz</strong>. O cliente sabe que está falando com outra pessoa da equipe.
                               </p>
                             </label>
                             
                             <label className={cn("flex flex-col gap-2 p-3 border rounded-xl cursor-pointer transition-all", editVal(p, "swarm_mode") === "silent" ? "border-primary bg-primary/5 ring-1 ring-primary/20" : "border-muted/50 bg-muted/10 opacity-70")}>
                               <div className="flex items-center gap-2">
                                 <input type="radio" name={`swarm_mode_${p.id}`} value="silent" checked={editVal(p, "swarm_mode") === "silent"} onChange={() => setEdit(p.id, "swarm_mode", "silent")} className="accent-primary" />
                                 <span className="font-bold text-sm flex items-center gap-2">Transferência Silenciosa <Badge variant="secondary" className="text-[9px] bg-primary/20 text-primary border-primary/30">Troca de Cérebro</Badge></span>
                               </div>
                               <p className="text-xs text-muted-foreground pl-5">
                                 O cliente <strong>não percebe a mudança</strong>. A IA mantém o mesmo nome e voz, mas seu <i>Prompt (cérebro)</i> é trocado silenciosamente no meio da chamada, ganhando novas regras e habilidades instantaneamente.
                               </p>
                             </label>
                           </div>
                        </div>

                        {/* Regras de Gatilho */}
                        <div className="border border-border/50 bg-background/50 p-5 rounded-2xl shadow-sm flex flex-col justify-center space-y-4">
                           <Field label="Gatilhos de Escalonamento {/* Handoff */}" hint="Palavras que, se o cliente disser, disparam a transferência.">
                              <Input value={editVal(p, "escalation_keywords")} onChange={(e) => setEdit(p.id, "escalation_keywords", e.target.value)} placeholder='Ex: "falar com humano", "cancelar", "financeiro"' className="rounded-xl" />
                           </Field>
                           <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                             <Field label="Transferir para qual Agente?" hint="A quem entregar a chamada?">
                                <select className="w-full rounded-xl border bg-background px-3 py-2.5 text-sm" value={editVal(p, "handoff_agent") || ""} onChange={(e) => setEdit(p.id, "handoff_agent", e.target.value)}>
                                   <option value="">Nenhum (Transferir p/ Humano)</option>
                                   <option value="suporte">IA: Suporte Técnico L2</option>
                                   <option value="vendas">IA: Closer de Vendas</option>
                                </select>
                             </Field>
                             <Field label="Mensagem de Despedida" hint="Só usada na Anunciada.">
                                <Input value={editVal(p, "handoff_message")} disabled={editVal(p, "swarm_mode") === "silent"} onChange={(e) => setEdit(p.id, "handoff_message", e.target.value)} placeholder='"Vou transferir, aguarde..."' className="rounded-xl disabled:opacity-50" />
                             </Field>
                           </div>
                           <Button onClick={() => saveAgent(p)} className="rounded-xl shadow-glow w-full mt-2">Salvar Regras Swarm</Button>
                        </div>
                      </div>

                      {/* Visual Mapa */}
                      <div className="bg-background/80 border border-border/50 p-6 rounded-2xl relative overflow-hidden flex flex-col items-center justify-center min-h-[220px]">
                        <div className="absolute inset-0 opacity-[0.03] bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
                        
                        <div className="flex items-center justify-center gap-4 relative z-10 w-full max-w-2xl">
                          <div className="bg-emerald-500/10 border border-emerald-500/30 p-4 rounded-2xl flex-1 text-center shadow-soft">
                            <Phone className="w-6 h-6 text-emerald-500 mx-auto mb-2"/>
                            <h4 className="font-bold text-sm">Cliente</h4>
                          </div>
                          
                          <ArrowRightLeft className="w-8 h-8 text-muted-foreground animate-pulse"/>
                          
                          <div className="bg-primary/10 border border-primary/30 p-5 rounded-2xl flex-[2] text-center shadow-[0_0_30px_rgba(16,185,129,0.15)] ring-2 ring-primary/20 ring-offset-4 ring-offset-background relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-1.5 opacity-20"><Bot className="w-12 h-12"/></div>
                            <Bot className="w-8 h-8 text-primary mx-auto mb-2 relative z-10"/>
                            <h4 className="font-bold text-base relative z-10">{p.name}</h4>
                            <p className="text-[11px] text-primary/70 font-semibold uppercase tracking-wider relative z-10">Ocupado agora</p>
                          </div>

                          <div className="flex flex-col gap-2 relative">
                             {editVal(p, "swarm_mode") === "silent" ? (
                                <Zap className="w-6 h-6 text-amber-500 mx-auto animate-pulse"/>
                             ) : (
                                <ArrowRightLeft className="w-6 h-6 text-muted-foreground mx-auto"/>
                             )}
                          </div>
                          
                          <div className="flex flex-col gap-3 flex-1">
                            <div className="bg-amber-500/10 border border-amber-500/30 p-3 rounded-xl text-center shadow-soft ring-1 ring-amber-500/20 bg-amber-500/5">
                              {editVal(p, "swarm_mode") === "silent" ? <BrainCircuit className="w-4 h-4 text-amber-500 mx-auto mb-1"/> : <Bot className="w-4 h-4 text-amber-500 mx-auto mb-1"/>}
                              <h4 className="font-bold text-[10px]">{editVal(p, "swarm_mode") === "silent" ? "Novo Cérebro" : "Novo Agente"}</h4>
                            </div>
                            <div className="bg-sky-500/10 border border-sky-500/30 p-3 rounded-xl text-center opacity-70 shadow-soft">
                              <Users className="w-4 h-4 text-sky-500 mx-auto mb-1"/>
                              <h4 className="font-bold text-[10px]">Humano</h4>
                            </div>
                          </div>
                        </div>
                      </div>
                    </TabsContent>

                    {/* TAB: QA & AUDITORIA */}
                    <TabsContent value="qa" className="p-5 mt-0 space-y-5">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-emerald-500/10 border border-emerald-500/20 p-5 rounded-2xl text-center flex flex-col justify-center shadow-soft">
                          <h3 className="text-4xl font-extrabold text-emerald-500 mb-1 drop-shadow-sm">94<span className="text-lg opacity-50">/100</span></h3>
                          <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mt-1">Score Médio</p>
                        </div>
                        <div className="bg-background/80 border border-border/50 p-5 rounded-2xl text-left md:col-span-2 flex flex-col justify-center relative overflow-hidden shadow-soft">
                           <div className="absolute top-2 right-2 p-2"><ShieldCheck className="w-6 h-6 text-primary/20"/></div>
                           <h4 className="text-xs font-bold uppercase tracking-wider text-primary mb-2">Relatório do IA Supervisor</h4>
                           <p className="text-sm text-foreground/80 leading-relaxed">
                             O agente responde com excelente latência e ótimo engajamento. Porém, nas últimas 24h, encontrou dificuldades em 2 chamadas quando o lead exigiu tabelas de preços detalhadas antes de confirmar o email. Recomenda-se adicionar um gatilho rápido na Base RAG para essa objeção.
                           </p>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-emerald-500/5 border border-emerald-500/10 p-5 rounded-2xl shadow-sm">
                          <h4 className="text-sm font-bold text-emerald-500 flex items-center gap-2 mb-4"><Zap className="w-4 h-4"/> Maiores Forças</h4>
                          <ul className="text-sm text-muted-foreground space-y-2 list-none">
                            <li className="flex items-start gap-2"><span className="text-emerald-500 mt-0.5">•</span> Capta os dados rapidamente (email/telefone).</li>
                            <li className="flex items-start gap-2"><span className="text-emerald-500 mt-0.5">•</span> Mantém tom altamente empático, sem parecer robótico.</li>
                          </ul>
                        </div>
                        <div className="bg-destructive/5 border border-destructive/10 p-5 rounded-2xl shadow-sm">
                          <h4 className="text-sm font-bold text-destructive flex items-center gap-2 mb-4"><ShieldCheck className="w-4 h-4"/> Pontos de Falha Recentes</h4>
                          <ul className="text-sm text-muted-foreground space-y-2 list-none">
                            <li className="flex items-start gap-2"><span className="text-destructive mt-0.5">•</span> Desistiu 3x ao sofrer pressão agressiva por desconto.</li>
                            <li className="flex items-start gap-2"><span className="text-destructive mt-0.5">•</span> Ficou em loop pedindo o nome do cliente 1x na terça.</li>
                          </ul>
                        </div>
                      </div>
                      <div className="flex justify-end">
                        <Button variant="outline" className="rounded-xl bg-background border-dashed"><Bot className="w-4 h-4 mr-2"/> Ver Transcrições Completas</Button>
                      </div>
                    </TabsContent>

                    {/* TAB: O TREINADOR */}
                    <TabsContent value="trainer" className="p-4 mt-0 bg-muted/10 border-t border-border/50">
                      <AgentTrainerPanel agentId={p.id} />
                    </TabsContent>

                  </Tabs>
                </div>
              )}
            </Card>
          ))}
          </div>
          )}
          
          <div className="border-t border-border/50 pt-8 mt-4">
            <GamificationPanel />
          </div>
        </div>
      )}

      {/* Form removed - creation happens exclusively via Facil or Lab Avançado */}
    </div>
  );
}

// Desempenho por agente. Antes era um painel de "gamificação" 100% inventado: receita
// "estimada" calculada a partir do ID do agente, gráfico com valores fixos e "MVP da
// Semana". Não há métrica real por agente no servidor ainda, então fica "em breve".
function GamificationPanel() {
  return (
    <Card className="p-5 bg-glass border-border/50 shadow-soft">
      <h3 className="font-bold text-sm flex items-center gap-2">
        <Award className="w-4 h-4 text-primary" /> Desempenho por agente
        <Badge variant="outline" className="text-[10px] bg-amber-500/10 text-amber-500 border-amber-500/20 uppercase">Em breve</Badge>
      </h3>
      <p className="text-xs text-muted-foreground mt-2">
        Aqui vão aparecer as ligações, conversas e resultados reais de cada agente. Por enquanto, veja os números gerais no Painel e em Análises.
      </p>
    </Card>
  );
}

export function SpecializedAgents() {
  const [activeTab, setActiveTab] = useState("facil");
  const [agentChat, setAgentChat] = useState<AgentChatSettings | null>(null);
  const [savingOutbound, setSavingOutbound] = useState(false);

  useEffect(() => {
    apiGet("/api/settings")
      .then((data: any) => setAgentChat(data.agent_chat))
      .catch(logError("SpecializedAgents.fetchAgentChat"));
  }, []);

  const toggleOutboundOnly = async (checked: boolean) => {
    if (!agentChat) return;
    setSavingOutbound(true);
    try {
      // Relê o agent_chat na hora: o guardado na tela podia ser velho (de antes do Roteamento
      // Nível 1 ou do Gestor Fácil) e desfazia essas escolhas (auditoria do mês 2, F25).
      const st = await getSettings();
      const updated = { ...(st.agent_chat || agentChat), outbound_only: checked };
      await updateAgentChat(updated);
      setAgentChat(updated);
      toast.success(updated.outbound_only ? "Modo ativado: só responde quem você já ligou" : "Modo desativado: responde qualquer pessoa");
    } catch (e) {
      toast.error("Erro ao salvar", { description: (e as Error).message });
    } finally {
      setSavingOutbound(false);
    }
  };

  const getTabTitle = () => {
    switch(activeTab) {
      case "facil": return "Funcionário Fácil";
      case "gestor_facil": return "Gestor Fácil";
      case "agentes": return "Meus Funcionários";
      case "lab": return "Lab Avançado";
      case "monitor": return "Chat / Teste";
      case "treinador": return "O Treinador";
      default: return "Funcionários IA";
    }
  };

  const getTabDesc = () => {
    switch(activeTab) {
      case "facil": return "Crie agentes com personalidades únicas passo a passo.";
      case "gestor_facil": return "Configure o agente roteador (Gestor Mestre) de forma simplificada.";
      case "agentes": return "Gerencie e acompanhe sua equipe autônoma.";
      case "lab": return "Configure modelos, RAG e webhooks avançados.";
      case "monitor": return "Faça um Test Drive conversando com seus agentes.";
      case "treinador": return "Treine IAs usando suas conversas reais do WhatsApp.";
      default: return "";
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Cabeçalho Compacto Funcionários IA */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-violet-500/10 via-background to-background border border-violet-500/20 p-4 shadow-glow mb-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
          <Users className="w-16 h-16 text-violet-500" />
        </div>
        <div className="relative z-10 flex items-center gap-3">
          <div className="hidden sm:flex items-center justify-center p-2 bg-violet-500/10 rounded-xl border border-violet-500/20 shadow-glow shrink-0">
            <img src="/inovareLogo.png" alt="Inovare Logo" className="w-8 h-8 object-contain drop-shadow-[0_0_8px_rgba(16,185,129,0.3)] rounded-full" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-violet-500 to-violet-400 drop-shadow-sm">
                {getTabTitle()}
              </h2>
              <Badge className="bg-violet-500/10 text-violet-500 border-violet-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Hermes Call Inovare
              </Badge>
              <Badge className="bg-violet-500/10 text-violet-500 border-violet-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Equipe Autônoma
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {getTabDesc()}
            </p>
          </div>
        </div>
      </div>

      {/* Banner de Configuração Global de Atendimento */}
      {agentChat && (
        <Card className="bg-amber-500/5 border-amber-500/20 shadow-soft">
          <div className="p-4 flex items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <Filter className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold">Filtro de Atendimento: Responder só quem eu já liguei</p>
                <p className="text-xs text-muted-foreground mt-1">
                  <strong>Ligado:</strong> Seus funcionários IA só respondem mensagens de números pra quem o Hermes já ligou antes (campanha ou ligação manual).
                  <strong className="ml-1">Desligado (padrão):</strong> Respondem qualquer pessoa que mandar mensagem.
                </p>
                <p className="text-xs text-amber-600 dark:text-amber-500 mt-1.5">
                  ⚠️ Esta é uma configuração <strong>global</strong> que afeta <strong>todos</strong> os seus funcionários IA de atendimento.
                </p>
              </div>
            </div>
            <Switch
              checked={agentChat.outbound_only}
              onCheckedChange={toggleOutboundOnly}
              disabled={savingOutbound}
              className="shrink-0"
            />
          </div>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col md:flex-row gap-6 w-full">
        <div className="w-full md:w-56 shrink-0">
          <TabsList className="flex flex-col h-auto bg-transparent items-stretch p-0 space-y-1">
            <HideableTab value="facil" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Wand2 className="h-4 w-4 mr-2" /> Criar Funcionário Fácil
            </HideableTab>
            <HideableTab value="gestor_facil" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Sparkles className="h-4 w-4 mr-2" /> Criar Gestor Fácil
            </HideableTab>
            <HideableTab value="agentes" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Users className="h-4 w-4 mr-2" /> Meus Funcionários
            </HideableTab>
            <HideableTab value="lab" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Settings2 className="h-4 w-4 mr-2" /> Lab Avançado
            </HideableTab>
            <HideableTab value="rag" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=primary] data-[state=active]:bg-sky-500 data-[state=active]:text-white data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-sky-500/20">
              <Database className="h-4 w-4 mr-2" /> Base de Conhecimento
            </HideableTab>
            <HideableTab value="monitor" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <MessageSquare className="h-4 w-4 mr-2" /> Chat / Teste
            </HideableTab>
            <HideableTab value="treinador" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <GraduationCap className="h-4 w-4 mr-2" /> O Treinador
            </HideableTab>
          </TabsList>
        </div>
        
        <div className="flex-1 min-w-0">
          <TabsContent value="facil" className="m-0 focus-visible:outline-none">
            <EasyAgentWizard onComplete={() => { toast.success("Funcionário criado! Agora configure o Gestor."); setActiveTab("gestor_facil"); }} />
          </TabsContent>
          <TabsContent value="gestor_facil" className="m-0 focus-visible:outline-none">
            <EasyManagerWizard />
          </TabsContent>
          <TabsContent value="agentes" className="m-0 focus-visible:outline-none">
            <AgentsList onNavigate={setActiveTab} />
          </TabsContent>
          <TabsContent value="lab" className="m-0 focus-visible:outline-none">
            <AdvancedLab />
          </TabsContent>
          <TabsContent value="rag" className="m-0 focus-visible:outline-none">
            <GlobalRagManager />
          </TabsContent>
          <TabsContent value="monitor" className="m-0 focus-visible:outline-none">
            <ChatMonitor />
          </TabsContent>
          <TabsContent value="treinador" className="m-0 focus-visible:outline-none">
            <div className="bg-background/50 border border-primary/20 shadow-glow rounded-2xl p-6">
              <AgentTrainerPanel />
            </div>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
