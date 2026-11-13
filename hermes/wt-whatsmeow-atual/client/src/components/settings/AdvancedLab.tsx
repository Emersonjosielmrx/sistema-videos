import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { FlaskConical, Save, Microchip, Brain, Network, Eraser, Send, Bot, Plus, Trash2, Settings2, Database, Volume2, ShieldCheck, MessageSquare, PanelRightClose, Headset, Webhook, Wand2, AlignLeft, Target, Phone, PhoneCall, Upload } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import { apiErrorMessage, apiGet, apiPost } from "@/lib/api";
import { cn } from "@/lib/utils";
import { logError } from "@/lib/log";
import { CredentialSelect } from "@/components/settings/CredentialSelect";
import { fetchAIModels } from "@/services/aimodels";

import { EasyFollowUpWizard } from "./EasyFollowUpWizard";
import { AgentRagPanel } from "./AgentRagPanel";

// Fallback estático só quando NÃO há credencial selecionada (modo legado). Com
// credencial, os modelos vêm dinâmicos via fetchAIModels (GET no provider real).
const MODELS_BY_PROVIDER: Record<string, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini", "o1-mini"],
  groq: ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
  gemini: ["gemini-2.5-flash", "gemini-2.0-flash"],
};

export function AdvancedLab() {
  const [agents, setAgents] = useState<any[]>([]);
  const [instances, setInstances] = useState<any[]>([]);
  const [currentAgentId, setCurrentAgentId] = useState<string>("");
  const [canvasActive, setCanvasActive] = useState(true);
  const [sandboxCollapsed, setSandboxCollapsed] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("core");
  
  // State 
  const [name, setName] = useState("");
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-4o");
  const [instance, setInstance] = useState("");
  const [listenAudio, setListenAudio] = useState(true);
  const [replyAudio, setReplyAudio] = useState(false);
  const [voiceProvider, setVoiceProvider] = useState("openai");
  const [voiceCredential, setVoiceCredential] = useState("");
  const [voiceId, setVoiceId] = useState("alloy");
  const [visionEnabled, setVisionEnabled] = useState(false);
  
  const [fallbackProvider, setFallbackProvider] = useState("groq");
  const [fallbackModel, setFallbackModel] = useState("llama3-8b-8192");
  const [credentialId, setCredentialId] = useState("");
  const [fallbackCredential, setFallbackCredential] = useState("");
  const [mainModels, setMainModels] = useState<string[]>([]);
  const [fbModels, setFbModels] = useState<string[]>([]);

  const [prompt, setPrompt] = useState("");
  const [tone, setTone] = useState("Profissional, acolhedor e direto ao ponto");
  const [dualPersona, setDualPersona] = useState(false);
  const [dualPersonaRules, setDualPersonaRules] = useState("");
  const [steps, setSteps] = useState("");
  const [rag, setRag] = useState("");
  const [guardrails, setGuardrails] = useState("");

  // Criatividade: o servidor lê de extras.temperature (0 a 1; agent_engine_extras.go). Antes este
  // controle abria sempre em 0,70 e ia solto no pedido, onde o servidor descarta (F19).
  // tempDefinida = o agente já tem valor gravado ou a pessoa mexeu no controle.
  const [temperature, setTemperature] = useState([70]);
  const [tempDefinida, setTempDefinida] = useState(false);

  const [tools, setTools] = useState<any[]>([]);
  const [toolName, setToolName] = useState("");
  const [toolCondition, setToolCondition] = useState("");
  const [toolUrl, setToolUrl] = useState("");
  const [toolAction, setToolAction] = useState("Disparar Webhook N8N (Substituir)");

  const [followUp, setFollowUp] = useState<any>({
    enabled: false,
    delayMinutes: 60,
    maxRetries: 1,
    messages: ["Oi, ainda está aí?", "Qualquer dúvida me avise!"]
  });

  // Novos campos: Transbordo, UX e Agenda
  const [handoffKeywords, setHandoffKeywords] = useState("");
  const [handoffDestAgent, setHandoffDestAgent] = useState("");
  const [handoffMessage, setHandoffMessage] = useState("Um momento, vou transferir para um humano.");
  const [simulateTyping, setSimulateTyping] = useState(false);
  const [typingSpeedMs, setTypingSpeedMs] = useState([50]);
  const [excludedDays, setExcludedDays] = useState<string[]>([]);

  // Paridade com Cria Fácil (Passos 1 e 4)
  const [kind, setKind] = useState("both");
  const [kpi, setKpi] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [objections, setObjections] = useState("");
  const [dataToCollect, setDataToCollect] = useState("");
  const [maxLength, setMaxLength] = useState([0]);
  const [extractToForm, setExtractToForm] = useState(false);
  const [mandatoryCollection, setMandatoryCollection] = useState(false);

  // Paridade com Cria Fácil (Passos 5, 6, 7)
  const [hotLeadTagger, setHotLeadTagger] = useState(false);
  const [useProfileName, setUseProfileName] = useState(false);
  const [validateProfileNameWithAI, setValidateProfileNameWithAI] = useState(false);
  const [knowLocalTime, setKnowLocalTime] = useState(false);
  const [empathyThermometer, setEmpathyThermometer] = useState(false);
  const [autoTrain, setAutoTrain] = useState(false);
  const [salesPressure, setSalesPressure] = useState([50]);
  const [maxDiscount, setMaxDiscount] = useState("");
  const [splitMessages, setSplitMessages] = useState(false);
  const [audioCondition, setAudioCondition] = useState("always");

  const [handoffMessageVoice, setHandoffMessageVoice] = useState("");
  const [summaryText, setSummaryText] = useState(true);
  const [summaryVoice, setSummaryVoice] = useState(true);
  const [handoffMethod, setHandoffMethod] = useState("panel");
  const [handoffDestAgent2, setHandoffDestAgent2] = useState("");
  const [handoffNotifyTo, setHandoffNotifyTo] = useState("panel");
  const [adminNumber, setAdminNumber] = useState("");
  const [askForHelp, setAskForHelp] = useState(false);
  const [callTriggers, setCallTriggers] = useState<any[]>([]);

  // RAG: os documentos ficam no servidor (AgentRagPanel, /api/rag/documents). Antes havia
  // aqui um upload de mentira (nome/chunks aleatórios e "Ativo" depois de 2 s).

  // Magic Generator
  const [magicUrl, setMagicUrl] = useState("");
  const [isMagicScraping, setIsMagicScraping] = useState(false);

  // Sandbox state
  const [chatLog, setChatLog] = useState<{role: 'user'|'bot'|'error', text: string}[]>([
    { role: 'bot', text: "**Inicialização do Motor V2.**\nDefina seus parâmetros à esquerda, crie ferramentas e digite aqui para avaliar latência e aderência aos *Guardrails*." }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchBaseData();
  }, []);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatLog, isTyping]);

  const fetchBaseData = async () => {
    try {
      const [instRes, agRes] = await Promise.all([
        apiGet<any>("/api/whatsapp/instances").catch(() => ({ success: false, data: [] })),
        apiGet<any>("/api/agents").catch(() => ({ success: false, data: [] }))
      ]);
      if (instRes.success && instRes.data) setInstances(instRes.data);
      if (agRes.success && agRes.data) setAgents(agRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadAgent = (id: string) => {
    setCurrentAgentId(id);
    if (!id) {
      setName(""); setPrompt(""); setRag(""); setGuardrails(""); setTools([]); setSteps("");
      setTemperature([70]); setTempDefinida(false);
      return;
    }
    const agent = agents.find(a => a.id === id);
    if (agent) {
      setName(agent.name || "");
      setProvider(agent.ai_provider || "openai");
      setModel(agent.ai_model || "gpt-4o");
      setInstance(agent.instance_name || "");
      setPrompt(agent.prompt || "");
      setTone(agent.tone || "Profissional, acolhedor e direto ao ponto");
      setRag(agent.knowledge_base || "");
      setGuardrails(agent.guardrails || "");
      setListenAudio(agent.listen_audio !== false);
      setReplyAudio(agent.reply_audio === true);
      setVoiceProvider(agent.voice_provider || "openai");
      setVoiceCredential(agent.voice_credential || "");
      // A voz salva pode estar em voice (agentes de Funcionários IA/Telegram não têm voice_id).
      // Antes caía em "alloy" e o salvar trocava a voz do agente.
      setVoiceId(agent.voice_id || agent.voice || "");
      setVisionEnabled(agent.vision_enabled === true);
      
      // O motor reserva fica no extras (a lista não tem fallback_provider): antes o Lab sempre
      // regravava groq/llama3-8b-8192 por cima da reserva escolhida no assistente.
      setFallbackProvider(agent.extras?.fallbackProvider || agent.fallback_provider || "groq");
      setFallbackModel(agent.extras?.fallbackModel || agent.fallback_model || "llama3-8b-8192");
      setCredentialId(agent.credential_id || "");
      setFallbackCredential(agent.extras?.fallbackCredentialId || agent.extras?.fallbackCredential || "");
      setDualPersona(agent.dual_persona === true);
      setDualPersonaRules(agent.dual_persona_rules || "");
      setTools(agent.automations || []);
      setFollowUp(agent.follow_up_config || { enabled: false, delayMinutes: 60, maxRetries: 1, messages: ["Oi, ainda está aí?"] });
      
      setHandoffKeywords(agent.escalation_keywords || agent.handoff_keywords || "");
      setHandoffDestAgent(agent.handoff_agent || "");
      setHandoffMessage(agent.handoff_message || "Um momento, vou transferir para a equipe.");
      setSimulateTyping(agent.simulate_typing === true);
      setTypingSpeedMs([agent.typing_speed || 50]);
      setExcludedDays(agent.excluded_days || []);
      
      setKind(agent.kind || "both");
      const ext = agent.extras || {};
      const tempSalva = Number(ext.temperature);
      setTempDefinida(tempSalva > 0);
      setTemperature([tempSalva > 0 ? Math.min(100, Math.round(tempSalva * 100)) : 70]);
      setKpi(ext.kpi || "");
      setTargetAudience(ext.targetAudience || "");
      setObjections(ext.objections || "");
      setDataToCollect(ext.dataToCollect || "");
      setMaxLength([ext.maxLength || 0]);
      setExtractToForm(ext.extractToForm === true);
      setMandatoryCollection(ext.mandatoryCollection === true);
      
      setHotLeadTagger(ext.hotLeadTagger === true);
      setUseProfileName(ext.useProfileName === true);
      setValidateProfileNameWithAI(ext.validateProfileNameWithAI === true);
      setKnowLocalTime(ext.knowLocalTime === true);
      // Gravado como número (0–100) pelo assistente ou true/false por Labs antigos.
      setEmpathyThermometer(ext.empathyThermometer === true || Number(ext.empathyThermometer) >= 60);
      setAutoTrain(ext.autoTrain === true);
      setSalesPressure([ext.salesPressure || 50]);
      setMaxDiscount(ext.maxDiscount ? String(ext.maxDiscount) : "");
      setSplitMessages(ext.splitMessages === true);
      setAudioCondition(ext.audioCondition || "always");

      setHandoffMessageVoice(ext.handoffMessageVoice || "");
      setSummaryText(ext.summaryText !== false);
      setSummaryVoice(ext.summaryVoice !== false);
      setHandoffMethod(ext.handoffMethod || "panel");
      setHandoffDestAgent2(ext.handoffDestAgent2 || "");
      setHandoffNotifyTo(ext.handoffNotifyTo || "panel");
      setAdminNumber(ext.adminNumber || "");
      setAskForHelp(ext.askForHelp === true);
      setCallTriggers(ext.callTriggers || []);

      toast.success("Agente carregado no Laboratório.");
    }
  };

  const handleMagicScrape = async () => {
    if (!magicUrl) return;
    setIsMagicScraping(true);
    try {
      const res: any = await apiPost("/api/agents/generate", {
        url: magicUrl,
        sector: "", goal: "", personality: "", archetype: "custom",
        role_template: "", steps_template: "", provider, model
      });
      if (res?.success && res?.data) {
        const d = res.data;
        if (d.knowledge) setRag(d.knowledge);
        if (d.targetAudience) setTargetAudience(d.targetAudience);
        if (d.objections) setObjections(d.objections);
        if (d.guardrails) setGuardrails(d.guardrails);
        if (d.steps) setSteps(d.steps);
        if (d.tone) setTone(d.tone);
        toast.success("Estratégia extraída da URL e preenchida no RAG!");
      } else {
        throw new Error(res?.error || "A IA não retornou dados.");
      }
    } catch (e: any) {
      toast.error("Erro na leitura mágica: " + (e.message || "desconhecido"));
    } finally {
      setIsMagicScraping(false);
    }
  };

  const addTool = () => {
    if (!toolCondition || !toolAction) {
      toast.error("Condição e Comportamento são obrigatórios."); return;
    }
    const newTool = {
      id: 'fn_' + Math.random().toString(36).substring(2,8),
      trigger: toolName || 'Tool Lógica',
      condition: toolCondition,
      action: toolAction,
      actionUrl: toolUrl,
      isFunctionCalling: true
    };
    setTools([...tools, newTool]);
    setToolName(""); setToolCondition(""); setToolUrl("");
    toast.success("Tool injetada em memória.");
  };

  const removeTool = (id: string) => {
    setTools(tools.filter(t => t.id !== id));
  };

  const sendSandboxMsg = async () => {
    const msg = chatInput.trim();
    if (!msg) return;
    setChatInput("");
    setChatLog(prev => [...prev, { role: 'user', text: msg }]);
    setIsTyping(true);

    try {
      const payload = {
        message: msg,
        tempConfig: { prompt, knowledge_base: rag, guardrails, ai_provider: provider, ai_model: model, temperature: 0.7 }
      };
      if (!currentAgentId) {
        setIsTyping(false);
        setChatLog(prev => [...prev, { role: 'error', text: `Selecione ou grave um agente antes de testar.` }]);
        return;
      }
      const res = await apiPost<{ reply?: string }>(`/api/agents/${currentAgentId}/test`, payload);
      setIsTyping(false);
      if (res.reply) {
        setChatLog(prev => [...prev, { role: 'bot', text: res.reply as string }]);
      } else {
        setChatLog(prev => [...prev, { role: 'error', text: `[Sem resposta do agente]` }]);
      }
    } catch (e: any) {
      setIsTyping(false);
      setChatLog(prev => [...prev, { role: 'error', text: `[Erro] ${e?.message || 'Falha na camada de rede.'}` }]);
    }
  };

  const saveAgent = async () => {
    if (!name) { toast.error("O Nome do Agente é obrigatório."); return; }
    setSaving(true);
    let finalPrompt = prompt;
    if (steps.trim()) finalPrompt += `\n\n[ETAPAS DE ATENDIMENTO / FUNIL]:\n${steps}`;
    if (dualPersona && dualPersonaRules.trim()) finalPrompt += `\n\n[DUPLA PERSONA (MUDANÇA DE TOM DINÂMICA)]:\n${dualPersonaRules}`;

    // Números como números: o servidor lia o extras como número e um texto/booleano fazia o
    // agente perder todas as regras avançadas do prompt.
    const prevExtras = agents.find(a => a.id === currentAgentId)?.extras || {};
    const prevEmpathy = Number(prevExtras.empathyThermometer);
    const empathyNum = empathyThermometer
      ? (prevEmpathy >= 60 ? prevEmpathy : 70)
      : (Number.isFinite(prevEmpathy) && prevEmpathy > 0 && prevEmpathy < 60 ? prevEmpathy : 0);
    const payload = {
      name, instance_name: instance || null, ai_provider: provider, ai_model: model,
      credential_id: credentialId,
      fallback_provider: fallbackProvider, fallback_model: fallbackModel,
      prompt: finalPrompt, knowledge_base: rag, guardrails, tone,
      dual_persona: dualPersona, dual_persona_rules: dualPersonaRules,
      listen_audio: listenAudio, reply_audio: replyAudio, 
      voice_provider: voiceProvider, voice_credential: voiceCredential, voice_id: voiceId, 
      vision_enabled: visionEnabled,
      automations: tools, follow_up_config: followUp,
      handoff_keywords: handoffKeywords, handoff_agent: handoffDestAgent, handoff_message: handoffMessage,
      simulate_typing: simulateTyping, typing_speed: typingSpeedMs[0], excluded_days: excludedDays,
      kind,
      extras: {
        ...prevExtras,
        // Só grava a criatividade se ela já existia ou se a pessoa mexeu: agente sem valor
        // continua no padrão do modelo em vez de ganhar 0,70 só por ter sido aberto e salvo.
        ...(tempDefinida ? { temperature: temperature[0] / 100 } : {}),
        // Fallback lido por applyEngineExtras no runtime (provider+model+credencial).
        fallbackProvider, fallbackModel, fallbackCredentialId: fallbackCredential,
        kpi, targetAudience, objections, dataToCollect, maxLength: maxLength[0], extractToForm, mandatoryCollection,
        hotLeadTagger, useProfileName, validateProfileNameWithAI, knowLocalTime, empathyThermometer: empathyNum, autoTrain,
        salesPressure: salesPressure[0], maxDiscount: Number(String(maxDiscount).replace(",", ".")) || 0, splitMessages, audioCondition,
        handoffMessageVoice, summaryText, summaryVoice, handoffMethod, handoffDestAgent2, handoffNotifyTo,
        adminNumber, askForHelp, callTriggers,
      }
    };

    try {
      const url = currentAgentId ? `/api/agents/${currentAgentId}` : `/api/agents`;
      // We would use apiPut if currentAgentId, but let's use apiPost for simplicity here or check method
      const res = await apiPost<{ success?: boolean; id?: string; error?: string }>(url, payload);
      if (res.success) {
        toast.success(currentAgentId ? "Agente atualizado com sucesso!" : "Novo Agente criado com sucesso!");
        if (!currentAgentId && res.id) setCurrentAgentId(res.id);
      } else {
        throw new Error(res.error);
      }
    } catch (e: any) {
      toast.error(apiErrorMessage(e, e.message || "Erro ao salvar agente."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] -m-4 sm:-m-6 bg-background relative overflow-hidden">
      {/* Neural Bg */}
      {canvasActive && (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-20 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-500/20 via-background to-background" />
      )}
      
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 px-6 border-b border-border/50 bg-background/80 backdrop-blur-md z-10 shrink-0">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2 text-primary">
            <FlaskConical className="h-5 w-5" /> Laboratório Avançado
          </h2>
          <p className="text-sm text-muted-foreground hidden md:block">Configuração de Roteamento, Múltiplos Webhooks e Engenharia de Prompt Extrema.</p>
        </div>
        <div className="flex gap-3 items-center">
          <select 
            className="flex h-9 w-[200px] md:w-[260px] rounded-md border border-emerald-500/30 bg-emerald-500/5 px-3 py-1 text-sm font-medium text-emerald-500 shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-emerald-500" 
            value={currentAgentId} 
            onChange={e => loadAgent(e.target.value)}
          >
            <option value="" className="text-foreground bg-background">-- Criar Novo Agente --</option>
            {agents.map(a => <option key={a.id} value={a.id} className="text-foreground bg-background">{a.name}</option>)}
          </select>

          <div className="flex items-center gap-2 mr-2">
            <Switch checked={canvasActive} onCheckedChange={setCanvasActive} />
            <span className="text-xs text-muted-foreground hidden sm:inline">Animação Neural</span>
          </div>
          <Button onClick={() => setSandboxCollapsed(!sandboxCollapsed)} variant={sandboxCollapsed ? "outline" : "secondary"} className={cn("gap-2 font-bold transition-all", sandboxCollapsed ? "border-emerald-500/50 text-emerald-500 hover:bg-emerald-500/10" : "")}>
            <MessageSquare className="h-4 w-4" />
            {sandboxCollapsed ? "Testar Chat" : "Esconder Chat"}
          </Button>
          <Button onClick={saveAgent} disabled={saving} className="gap-2 font-bold shadow-glow text-white bg-blue-600 hover:bg-blue-500">
            {saving ? <div className="animate-spin h-4 w-4 border-2 border-white/20 border-t-white rounded-full"/> : <Save className="h-4 w-4" />}
            Gravar Agente
          </Button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row flex-1 overflow-hidden z-10 relative">
        {/* Left Sidebar Menu */}
        <div className="w-full lg:w-64 border-r border-border/50 bg-black/40 flex flex-col p-4 overflow-y-auto space-y-1 z-10">
          <div className="text-[0.65rem] font-bold text-muted-foreground uppercase tracking-wider mb-2 px-2">Super Abas de Configuração</div>
          <button onClick={() => setActiveTab('core')} className={cn("text-left px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2", activeTab === 'core' ? "bg-primary/20 text-primary shadow-sm" : "hover:bg-muted/50 text-muted-foreground")}>
            <Microchip className="w-4 h-4 text-emerald-500" /> 1. Identidade & Cérebro
          </button>
          <button onClick={() => setActiveTab('brain')} className={cn("text-left px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2", activeTab === 'brain' ? "bg-primary/20 text-primary shadow-sm" : "hover:bg-muted/50 text-muted-foreground")}>
            <Brain className="w-4 h-4 text-purple-500" /> 2. Personalidade & Prompt
          </button>
          <button onClick={() => setActiveTab('rag')} className={cn("text-left px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2", activeTab === 'rag' ? "bg-primary/20 text-primary shadow-sm" : "hover:bg-muted/50 text-muted-foreground")}>
            <Database className="w-4 h-4 text-sky-500" /> 3. Base de Conhecimento
          </button>
          <button onClick={() => setActiveTab('automation')} className={cn("text-left px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2", activeTab === 'automation' ? "bg-primary/20 text-primary shadow-sm" : "hover:bg-muted/50 text-muted-foreground")}>
            <Network className="w-4 h-4 text-blue-500" /> 4. Automação & Transbordo
          </button>
          <button onClick={() => setActiveTab('voice')} className={cn("text-left px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2", activeTab === 'voice' ? "bg-primary/20 text-primary shadow-sm" : "hover:bg-muted/50 text-muted-foreground")}>
            <Volume2 className="w-4 h-4 text-amber-500" /> 5. Voz, Visão & UX
          </button>
        </div>

        {/* Middle Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-8 custom-scrollbar bg-card/20 space-y-6 z-10">
          
          {/* TAB 1: CORE */}
          {activeTab === 'core' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
              <div>
                <h3 className="text-xl font-bold text-emerald-500 flex items-center gap-2 mb-1"><Microchip className="w-6 h-6"/> Identidade & Cérebro</h3>
                <p className="text-sm text-muted-foreground">O núcleo operacional do agente: nome, conexão e o motor cognitivo principal e de resiliência.</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 border border-border/50 rounded-xl bg-background/50 shadow-sm">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground">Nome da Identidade</label>
                  <Input value={name} onChange={e => setName(e.target.value)} placeholder="Ex: Master Node" className="bg-background focus-visible:ring-primary" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground">Instância Origem (WhatsApp)</label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={instance} onChange={e => setInstance(e.target.value)}>
                      <option value="">Apenas Webhook Externo (Sem WhatsApp)</option>
                      {instances.map(i => {
                        const num = i.jid ? i.jid.replace(/:.*/, "").replace(/@.*/, "") : "";
                        const status = i.connected ? "🟢" : i.paired ? "🟡" : "⚪";
                        const label = num ? `${status} ${i.name} — +${num}` : `${status} ${i.name}`;
                        return <option key={i.name} value={i.name}>{label}</option>;
                      })}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground">Canal de Atendimento</label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={kind} onChange={e => setKind(e.target.value)}>
                      <option value="both">Ambos (Híbrido)</option>
                      <option value="message">Só Mensagens (WhatsApp/Texto)</option>
                      <option value="call">Só Ligação (Voz Latência Zero)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground">Credencial IA Principal</label>
                  <CredentialSelect
                    type="llm"
                    value={credentialId}
                    onChange={(id, cred) => {
                      setCredentialId(id);
                      if (cred?.provider) setProvider(cred.provider);
                      setMainModels([]);
                      if (id && cred) {
                        fetchAIModels(cred.provider, "", cred.base_url, id).then(setMainModels).catch(logError("AdvancedLab/models"));
                      }
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground">Modelo Principal</label>
                  {mainModels.length > 0 ? (
                    <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={model} onChange={e => setModel(e.target.value)}>
                        <option value="">— Escolha o modelo —</option>
                        {mainModels.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  ) : credentialId ? (
                    <Input className="h-10" value={model} onChange={e => setModel(e.target.value)} placeholder="Nome do modelo (ex: gpt-4o)" />
                  ) : (
                    <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={model} onChange={e => setModel(e.target.value)}>
                        {MODELS_BY_PROVIDER[provider]?.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  )}
                </div>

                {/* Fallback Resilience */}
                <div className="space-y-2 pt-4 border-t border-border/50">
                  <label className="text-xs font-semibold text-muted-foreground">Credencial de Resiliência (Fallback)</label>
                  <CredentialSelect
                    type="llm"
                    value={fallbackCredential}
                    onChange={(id, cred) => {
                      setFallbackCredential(id);
                      if (cred?.provider) setFallbackProvider(cred.provider);
                      setFbModels([]);
                      if (id && cred) {
                        fetchAIModels(cred.provider, "", cred.base_url, id).then(setFbModels).catch(logError("AdvancedLab/fbmodels"));
                      }
                    }}
                  />
                </div>
                <div className="space-y-2 pt-4 border-t border-border/50">
                  <label className="text-xs font-semibold text-muted-foreground">Modelo de Resiliência</label>
                  {fbModels.length > 0 ? (
                    <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={fallbackModel} onChange={e => setFallbackModel(e.target.value)}>
                        <option value="">— Escolha o modelo —</option>
                        {fbModels.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  ) : fallbackCredential ? (
                    <Input className="h-10" value={fallbackModel} onChange={e => setFallbackModel(e.target.value)} placeholder="Nome do modelo (ex: llama3-8b-8192)" />
                  ) : (
                    <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={fallbackModel} onChange={e => setFallbackModel(e.target.value)}>
                        {MODELS_BY_PROVIDER[fallbackProvider]?.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  )}
                </div>
              </div>

              {/* Hyperparams moved to Core */}
              <div className="p-6 border border-border/50 rounded-xl bg-background/50 shadow-sm">
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <label className="text-sm font-semibold text-muted-foreground">Temperature (Criatividade)</label>
                      <span className="text-sm font-mono text-primary font-bold">
                        {tempDefinida && temperature[0] > 0 ? (temperature[0]/100).toFixed(2) : "padrão do modelo"}
                      </span>
                    </div>
                    <Slider value={temperature} onValueChange={v => { setTemperature(v); setTempDefinida(true); }} max={100} step={1} className="py-2" />
                    {/* O "Max Tokens" que ficava aqui não era gravado nem lido: o tamanho da resposta
                        é fixo no servidor (curta na ligação, por ser falada). */}
                    <p className="text-[11px] text-muted-foreground">
                      Vale para as ligações e mensagens deste agente. Mais baixo = respostas mais previsíveis; mais alto = mais variadas.
                      Sem mexer (ou em zero), fica o padrão do modelo.
                    </p>
                  </div>
              </div>
            </div>
          )}

          {/* TAB 2: BRAIN */}
          {activeTab === 'brain' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
              <div>
                <h3 className="text-xl font-bold text-purple-500 flex items-center gap-2 mb-1"><Brain className="w-6 h-6"/> Personalidade & Prompt</h3>
                <p className="text-sm text-muted-foreground">Comportamento, scripts de funil e limites de segurança (Guardrails).</p>
              </div>

              {/* Módulo Magic Generator */}
              <div className="p-5 border border-emerald-500/30 rounded-xl bg-emerald-500/5 shadow-sm space-y-4">
                 <h4 className="font-bold flex items-center gap-2 text-emerald-500"><Wand2 className="w-4 h-4"/> Extração Mágica (LLM)</h4>
                 <p className="text-xs text-muted-foreground">O agente extrairá o ICP, dores e objeções diretamente da URL do site para preencher os dados abaixo automaticamente.</p>
                 <div className="flex gap-2">
                   <Input value={magicUrl} onChange={e => setMagicUrl(e.target.value)} placeholder="https://seu-site.com.br" className="bg-background h-10 flex-1 border-emerald-500/30" />
                   <Button onClick={handleMagicScrape} disabled={isMagicScraping || !magicUrl} className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold h-10">
                     {isMagicScraping ? "Lendo Site..." : "Extrair"}
                   </Button>
                 </div>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-muted-foreground">Tom de Voz (Persona)</label>
                      <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={tone} onChange={e => setTone(e.target.value)}>
                          <option value="Profissional, acolhedor e direto ao ponto">Profissional, acolhedor e direto ao ponto</option>
                          <option value="Persuasivo, energético e focado em conversão">Persuasivo, energético e focado em conversão</option>
                          <option value="Técnico, analítico e extremamente preciso">Técnico, analítico e extremamente preciso</option>
                          <option value="Amigável, jovem e cheio de emojis">Amigável, jovem e cheio de emojis</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-muted-foreground">Meta Principal (KPI)</label>
                      <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={kpi} onChange={e => setKpi(e.target.value)}>
                          <option value="">Conversa Livre</option>
                          <option value="Agendar uma reunião/visita">🎯 Agendar Reunião</option>
                          <option value="Emitir segunda via de boleto/PIX">💰 Acordo/PIX</option>
                          <option value="Resolver o chamado no primeiro contato">🛠️ Resolver Ticket</option>
                          <option value="Qualificar perfil (Orçamento e Prazo)">📋 Qualificar Lead</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="p-4 border border-border/50 rounded-lg bg-card/50 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-sm font-semibold flex items-center gap-2">Dupla Persona Dinâmica</span>
                        <p className="text-[0.65rem] text-muted-foreground mt-1">Muda o tom baseado no humor do lead.</p>
                      </div>
                      <Switch checked={dualPersona} onCheckedChange={setDualPersona} />
                    </div>
                    {dualPersona && (
                      <Textarea value={dualPersonaRules} onChange={e => setDualPersonaRules(e.target.value)} rows={2} placeholder="Ex: Se o lead estiver irritado, mude imediatamente para o tom 'Suporte Humanizado'." className="bg-background/80 text-sm" />
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground">System Prompt Mestre (Instruções)</label>
                    <Textarea value={prompt} onChange={e => setPrompt(e.target.value)} rows={5} placeholder="Sua missão é..." className="bg-background/50 font-mono text-sm leading-relaxed" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground">Funil & Etapas de Atendimento</label>
                    <Textarea value={steps} onChange={e => setSteps(e.target.value)} rows={4} placeholder="Ex: 1. Saudação; 2. Qualificação..." className="bg-background/50" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground">Público-Alvo (Quem ele atende?)</label>
                    <Input value={targetAudience} onChange={e => setTargetAudience(e.target.value)} placeholder="Ex: Clientes B2B, Startups..." className="bg-background h-10" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground">Tratamento de Objeções (Contorno)</label>
                    <Textarea value={objections} onChange={e => setObjections(e.target.value)} rows={3} placeholder="Se falarem 'tá caro', diga..." className="bg-background/50" />
                  </div>

                </div>
                
                <div className="space-y-6">
                  {/* Extract to Form / Max Length */}
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 p-5 border border-sky-500/30 rounded-xl bg-sky-500/5 shadow-sm">
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-sky-400 flex items-center gap-1"><Database className="w-4 h-4"/> Formulário Dinâmico</label>
                      <Textarea value={dataToCollect} onChange={e => setDataToCollect(e.target.value)} rows={3} placeholder="Ex: Qual o seu Nome? Empresa?" className="bg-background/80 border-sky-500/30" />
                      <div className="flex flex-col gap-2 pt-2">
                         <div className="flex items-center space-x-2">
                           <Switch checked={extractToForm} onCheckedChange={setExtractToForm} />
                           <label className="text-[10px] text-muted-foreground">Salvar no CRM</label>
                         </div>
                         <div className="flex items-center space-x-2">
                           <Switch checked={mandatoryCollection} onCheckedChange={setMandatoryCollection} disabled={!extractToForm} />
                           <label className={cn("text-[10px] text-muted-foreground", !extractToForm && "opacity-50")}>Travar Funil (Obrigatório)</label>
                         </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-sky-400 flex items-center gap-1"><AlignLeft className="w-4 h-4"/> Tamanho Máx Resposta</label>
                      <div className="flex flex-col items-center gap-4 mt-2 bg-background/50 p-4 rounded-xl border border-border/50">
                        <Slider value={maxLength} min={0} max={1000} step={50} onValueChange={setMaxLength} className="w-full" />
                        <span className="text-xs font-mono bg-background px-3 py-1 rounded border border-border/50">{maxLength[0] ? `${maxLength[0]} chars` : 'Ilimitado'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 p-5 border border-destructive/30 rounded-xl bg-destructive/5 shadow-sm">
                    <label className="text-xs font-bold text-destructive flex items-center gap-2"><ShieldCheck className="w-4 h-4"/> Guardrails & Anti-Jailbreak</label>
                    <Textarea value={guardrails} onChange={e => setGuardrails(e.target.value)} rows={3} placeholder="Ex: Nunca prometa descontos. Não fale sobre política." className="bg-background/80 border-destructive/40 text-destructive-foreground focus-visible:ring-destructive" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: RAG (BASE DE CONHECIMENTO) */}
          {activeTab === 'rag' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2">
              <div>
                <h3 className="text-xl font-bold text-sky-500 flex items-center gap-2 mb-1"><Database className="w-6 h-6"/> Base de Conhecimento (RAG)</h3>
                <p className="text-sm text-muted-foreground">Faça upload de documentos (PDF, TXT, DOCX), adicione links ou defina textos puros para a IA consultar.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Documentos (reais, no servidor) */}
                <div className="lg:col-span-2 space-y-6">
                  {currentAgentId ? (
                    <AgentRagPanel agentId={currentAgentId} />
                  ) : (
                    <div className="p-6 border-2 border-dashed border-sky-500/30 rounded-xl bg-sky-500/5 text-center space-y-2">
                      <Upload className="w-8 h-8 text-sky-500 mx-auto opacity-70" />
                      <h4 className="font-bold text-sky-400">Salve o agente para subir documentos</h4>
                      <p className="text-xs text-muted-foreground">Os arquivos ficam ligados ao agente. Escolha um agente existente no topo ou salve este novo primeiro.</p>
                    </div>
                  )}

                  {/* Static / Pure Text (Fallback) */}
                  <div className="space-y-2 pt-4 border-t border-border/30">
                    <label className="text-xs font-semibold text-sky-400 flex items-center gap-1"><AlignLeft className="w-4 h-4"/> Conhecimento Estático (Texto Puro)</label>
                    <Textarea value={rag} onChange={e => setRag(e.target.value)} rows={6} placeholder="Cole FAQs rápidas, preços, endereços aqui caso não queira subir arquivos..." className="bg-background/80 font-mono text-sm border-sky-500/30 focus-visible:ring-sky-500" />
                  </div>
                </div>

                {/* Como a busca funciona hoje (valores fixos no servidor; antes havia controles que não faziam nada) */}
                <div className="space-y-6">
                  <div className="p-5 border border-border/50 rounded-xl bg-card/30 space-y-3">
                    <h4 className="font-bold flex items-center gap-2 text-primary border-b border-border/50 pb-2"><Settings2 className="w-4 h-4"/> Como a IA usa os documentos</h4>
                    <ul className="text-xs text-muted-foreground space-y-2 list-disc pl-4">
                      <li>Cada arquivo é dividido em trechos de cerca de 1.200 caracteres.</li>
                      <li>Na conversa, a IA busca os trechos mais parecidos com a pergunta (por sentido e por palavra-chave).</li>
                      <li>Se nada for parecido o bastante, ela não usa a base (evita inventar).</li>
                      <li>A Base Global (aba "Base de Conhecimento") vale para todos os agentes.</li>
                    </ul>
                    <p className="text-[11px] text-amber-500">Ajustes finos (tamanho do trecho, quantidade, estratégia) — em breve.</p>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* TAB 3: AUTOMATION */}
          {activeTab === 'automation' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2">
              <div>
                <h3 className="text-xl font-bold text-blue-500 flex items-center gap-2 mb-1"><Network className="w-6 h-6"/> Automação & Transbordo</h3>
                <p className="text-sm text-muted-foreground">Ações de background, webhooks inteligentes e regras para transferência humana.</p>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Handoff */}
                <div className="space-y-4 p-5 border border-border/50 rounded-xl bg-card/30">
                   <h4 className="font-bold flex items-center gap-2 text-primary border-b border-border/50 pb-2"><Headset className="w-4 h-4"/> Transbordo (Handoff)</h4>
                   <div className="space-y-2">
                      <label className="text-xs font-semibold text-muted-foreground">Gatilhos de Escape (Keywords)</label>
                      <Input value={handoffKeywords} onChange={e => setHandoffKeywords(e.target.value)} placeholder="Ex: falar com humano, atendente, suporte" className="bg-background h-10" />
                      <p className="text-[0.65rem] text-muted-foreground">Separado por vírgulas. Pausa a IA imediatamente se detectado.</p>
                   </div>

                   <div className="flex flex-col gap-4 pt-2 border-t border-border/30">
                     <div className="p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl space-y-2">
                        <label className="text-xs font-bold text-emerald-600/80">Mensagem de Transição (Texto/WhatsApp)</label>
                        <Input value={handoffMessage} onChange={e => setHandoffMessage(e.target.value)} placeholder='Ex: "Um momento, vou chamar a equipe..."' className="bg-background/50 h-10 border-emerald-500/20" />
                     </div>
                     <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl space-y-2">
                        <label className="text-xs font-bold text-blue-600/80">Mensagem de Transição (Voz/Telefone)</label>
                        <Input value={handoffMessageVoice} onChange={e => setHandoffMessageVoice(e.target.value)} placeholder='Ex: "Aguarde na linha..."' className="bg-background/50 h-10 border-blue-500/20" />
                     </div>
                   </div>

                   <div className="p-4 bg-background/20 border border-border/50 rounded-xl space-y-2">
                     <h5 className="text-sm font-bold flex items-center gap-2"><Bot className="h-4 w-4"/> Dossiê Instantâneo (Resumo)</h5>
                     <div className="flex flex-wrap gap-6 pt-2">
                       <div className="flex items-center space-x-2">
                         <Switch checked={summaryText} onCheckedChange={setSummaryText} className="data-[state=checked]:bg-emerald-500" />
                         <label className="text-sm font-medium text-emerald-500">No Texto</label>
                       </div>
                       <div className="flex items-center space-x-2">
                         <Switch checked={summaryVoice} onCheckedChange={setSummaryVoice} className="data-[state=checked]:bg-blue-500" />
                         <label className="text-sm font-medium text-blue-500">Na Voz</label>
                       </div>
                     </div>
                   </div>

                   <div className="p-4 bg-violet-500/10 border border-violet-500/20 rounded-xl space-y-3">
                     <div>
                       <h5 className="text-sm font-bold text-violet-500 flex items-center gap-2"><PhoneCall className="h-4 w-4"/> Gatilhos de Conferência na Ligação</h5>
                       <p className="text-xs text-muted-foreground mt-1">Durante uma LIGAÇÃO, a IA pode te chamar automaticamente quando detectar estas situações.</p>
                     </div>
                     {[
                       {key: "human_request", label: "Cliente pede pra falar com humano"},
                       {key: "price", label: "Cliente pergunta preço/valor"},
                       {key: "hot_lead", label: "Cliente demonstra forte intenção de compra"},
                     ].map(g => {
                       const cur = callTriggers.find((t:any) => t.on === g.key);
                       return (
                         <div key={g.key} className="flex items-center justify-between gap-2 pt-2 border-t border-violet-500/10">
                           <div className="flex items-center space-x-2 flex-1">
                             <Switch checked={!!cur} onCheckedChange={(c) => {
                                 const list = callTriggers.filter((t:any) => t.on !== g.key);
                                 if (c) list.push({ on: g.key, action: "bridge", mode: "silent_relay", client: g.key === "human_request" ? "announce" : "silent", channel: "both" });
                                 setCallTriggers(list);
                             }} className="data-[state=checked]:bg-violet-500" />
                             <label className="text-sm">{g.label}</label>
                           </div>
                           {cur && (
                             <select className="h-8 rounded-md border border-input bg-background/50 px-2 text-xs" value={cur.client} onChange={e => {
                               setCallTriggers(callTriggers.map((t:any) => t.on===g.key ? {...t, client: e.target.value} : t));
                             }}>
                               <option value="silent">Sem avisar</option>
                               <option value="announce">Avisar cliente</option>
                             </select>
                           )}
                         </div>
                       );
                     })}
                   </div>

                   <div className="space-y-2">
                      <label className="text-xs font-semibold text-muted-foreground">Método de Transferência</label>
                      <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm" value={handoffMethod} onChange={e => setHandoffMethod(e.target.value)}>
                         <option value="panel">Deixar Humano assumir pelo Painel (Mutar IA)</option>
                         <option value="swarm">Transferir para Outro Agente IA (Swarm)</option>
                      </select>
                   </div>
                   
                   {handoffMethod === 'swarm' ? (
                     <>
                       <div className="space-y-2">
                          <label className="text-xs font-semibold text-muted-foreground">ID da Outra IA (Nível 1)</label>
                          <Input value={handoffDestAgent} onChange={e => setHandoffDestAgent(e.target.value)} className="bg-background/50 h-10 border-primary/50" />
                       </div>
                       <div className="space-y-2">
                          <label className="text-xs font-semibold text-muted-foreground">ID da Outra IA (Nível 2)</label>
                          <Input value={handoffDestAgent2} onChange={e => setHandoffDestAgent2(e.target.value)} className="bg-background/50 h-10" />
                       </div>
                     </>
                   ) : (
                     <div className="space-y-2">
                        <label className="text-xs font-semibold text-muted-foreground">Como avisar o Humano?</label>
                        <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm" value={handoffNotifyTo} onChange={e => setHandoffNotifyTo(e.target.value)}>
                           <option value="panel">Aviso Visual no Painel (Sino de Notificação)</option>
                           <option value="telegram">Mandar mensagem no Telegram</option>
                           <option value="whatsapp">Mandar mensagem no Meu WhatsApp</option>
                        </select>
                     </div>
                   )}

                   <div className="p-4 bg-amber-500/5 border border-amber-500/20 rounded-xl space-y-4">
                      <div className="space-y-2">
                         <label className="text-xs font-semibold text-amber-600/80">Número de WhatsApp do Administrador</label>
                         <Input value={adminNumber} onChange={e => setAdminNumber(e.target.value)} placeholder='Ex: 5511999999999' className="bg-background/50 h-10 border-amber-500/20" />
                      </div>
                      <div className="flex items-center space-x-2 pt-2">
                        <Switch checked={askForHelp} onCheckedChange={setAskForHelp} className="data-[state=checked]:bg-amber-500" />
                        <label className="text-xs font-medium text-amber-500/90">Permitir que a IA pause e peça ajuda ao Admin quando não souber a resposta</label>
                      </div>
                   </div>
                </div>

                {/* Return Mode */}
                <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="text-sm font-bold text-blue-500 flex items-center gap-2"><Phone className="h-4 w-4"/> Modo Retorno de Campanha (Ligar Primeiro)</h5>
                      <p className="text-xs text-muted-foreground mt-1">Se o lead mandar mensagem (ex: respondeu anúncio), a IA tenta LIGAR imediatamente antes de mandar texto.</p>
                    </div>
                    <Switch checked={tools.some(a => a.id === "return_mode")} onCheckedChange={(c) => {
                      if(c) {
                        setTools(prev => [...prev, {id: "return_mode", trigger: "Modo Retorno de Campanha", condition: "Lead inbound_msg", action: "call_first", actionUrl: "", isFunctionCalling: false}]);
                      } else {
                        setTools(prev => prev.filter(a => a.id !== "return_mode"));
                      }
                    }} className="data-[state=checked]:bg-blue-500" />
                  </div>
                  {tools.some(a => a.id === "return_mode") && (
                    <div className="pt-3 animate-in fade-in slide-in-from-top-2 border-t border-blue-500/20">
                       <p className="text-xs text-blue-400/80 font-medium">Fluxo Ativado: Se o cliente enviar mensagem, a IA de Voz liga. Se ele não atender, a IA de Texto manda: <i>"Vi que você me chamou, tentei te ligar rapidinho. Posso te ligar de novo agora?"</i></p>
                    </div>
                  )}
                </div>

                {/* Followup */}
                <div className="p-5 border border-border/50 rounded-xl bg-card/30">
                   <h4 className="font-bold flex items-center gap-2 text-primary border-b border-border/50 pb-2 mb-4"><Bot className="w-4 h-4"/> Follow-up Automático</h4>
                   <EasyFollowUpWizard />
                </div>
              </div>

              {/* Webhooks (Step 7 Parity) */}
              <div className="p-5 border border-blue-500/20 rounded-xl bg-blue-500/5 space-y-4">
                 <h4 className="font-bold flex items-center gap-2 text-blue-500 border-b border-blue-500/20 pb-2"><Webhook className="w-4 h-4"/> Integrações & Webhooks Swarm</h4>
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <div className="space-y-2">
                      <label className="text-xs font-semibold">Nome da Tool (Intenção)</label>
                      <Input value={toolName} onChange={e=>setToolName(e.target.value)} placeholder="Ex: Cancelar Assinatura" className="bg-background" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-semibold">Gatilho (Regex ou Contains)</label>
                      <Input value={toolCondition} onChange={e=>setToolCondition(e.target.value)} placeholder="Ex: cancelar, reembolso" className="bg-background" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-semibold">URL Absoluta do Webhook</label>
                      <Input value={toolUrl} onChange={e=>setToolUrl(e.target.value)} placeholder="https://n8n.seu-dominio.com/webhook/..." className="bg-background" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-semibold">Comportamento</label>
                      <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={toolAction} onChange={e => setToolAction(e.target.value)}>
                          <option value="Disparar Webhook N8N (Substituir)">Substituir (A IA para de responder)</option>
                          <option value="Disparar Webhook N8N (Complemento)">Complementar (Paralelo)</option>
                          <option value="Transferir para Humano">Transferir Fluxo (Pausar IA)</option>
                      </select>
                    </div>
                 </div>
                 <Button variant="outline" className="w-full border-dashed text-blue-500 hover:text-blue-400 hover:bg-blue-500/10 border-blue-500/50" onClick={addTool}>
                    <Plus className="h-4 w-4 mr-2" /> Injetar Tool na Array
                 </Button>

                 {tools.length > 0 && (
                   <div className="flex flex-col gap-2 mt-4 pt-4 border-t border-blue-500/20">
                      {tools.map(t => (
                        <div key={t.id} className="flex justify-between items-center bg-[#1e1e1e] p-3 rounded-lg border-l-4 border-blue-500 shadow-sm font-mono text-xs">
                          <div className="space-y-1">
                            <div><span className="text-blue-400">[{t.id}]</span> <span className="text-white font-bold">{t.trigger}</span></div>
                            <div className="opacity-80">
                              <span className="text-emerald-500">if</span> (msg.includes(<span className="text-amber-500">"{t.condition}"</span>)) {'{'}
                              <br/>&nbsp;&nbsp;<span className="text-purple-400">exec</span>({t.action.includes('Substituir') ? 'OVERRIDE' : 'PARALLEL'}, "{t.actionUrl || 'null'}");
                              <br/>{'}'}
                            </div>
                          </div>
                          <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/20 h-8 w-8" onClick={() => removeTool(t.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                   </div>
                 )}
              </div>
            </div>
          )}

          {/* TAB 4: VOICE, VISION & UX */}
          {activeTab === 'voice' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
              <div>
                <h3 className="text-xl font-bold text-amber-500 flex items-center gap-2 mb-1"><Volume2 className="w-6 h-6"/> Voz, Visão & UX</h3>
                <p className="text-sm text-muted-foreground">Configuração multimodal, simulação humana e agenda de trabalho.</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Voice & Vision */}
                <div className="p-5 border border-border/50 rounded-xl bg-card/30 space-y-6">
                  <h4 className="font-bold flex items-center gap-2 text-amber-500 border-b border-border/50 pb-2"><Volume2 className="w-4 h-4"/> Multimodal (Ouvir e Ver)</h4>
                  <div className="flex flex-col gap-2 p-3 bg-card/50 rounded-lg border border-border/50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold">Ouvir Áudios do Lead (Whisper)</span>
                      <Switch checked={listenAudio} onCheckedChange={setListenAudio} />
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 p-3 bg-card/50 rounded-lg border border-border/50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold">Ler Imagens do Lead (Vision)</span>
                      <Switch checked={visionEnabled} onCheckedChange={setVisionEnabled} />
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 p-3 bg-card/50 rounded-lg border border-border/50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold">Responder em Áudio (TTS)</span>
                      <Switch checked={replyAudio} onCheckedChange={setReplyAudio} />
                    </div>
                  </div>

                  {replyAudio && (
                    <div className="space-y-4 pt-4 border-t border-border/30">
                        <div className="space-y-2">
                          <label className="text-xs font-semibold text-muted-foreground">Provedor TTS & Credencial</label>
                          <div className="flex gap-2">
                            <select className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-1 text-sm" value={voiceProvider} onChange={e => setVoiceProvider(e.target.value)}>
                               <option value="openai">OpenAI TTS</option>
                               <option value="elevenlabs">ElevenLabs</option>
                            </select>
                            <select className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-1 text-sm" value={voiceCredential} onChange={e => setVoiceCredential(e.target.value)}>
                               <option value="">Plataforma Geral</option>
                               <option value="key1">Minha Key 1</option>
                            </select>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <label className="text-xs font-semibold text-muted-foreground flex justify-between">
                             Voz Sintética
                             <button className="text-blue-500 hover:underline" onClick={async () => {
                               try {
                                 const res = await apiPost<{ ok?: boolean; audio_base64?: string; audio_mime?: string; error?: string }>("/api/tts/preview", { text: "Olá, esta é uma amostra da minha voz.", voice: voiceId });
                                 const b64 = res?.audio_base64;
                                 const mime = res?.audio_mime || "audio/ogg";
                                 if (b64) {
                                   new Audio(`data:${mime};base64,${b64}`).play().catch(() => toast.error("Sem permissão de áudio."));
                                 } else {
                                   toast.error("Sem áudio retornado.");
                                 }
                               } catch (err) {
                                 toast.error(`Falhou: ${err instanceof Error ? err.message : String(err)}`);
                               }
                             }}>Ouvir Teste</button>
                          </label>
                          <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={voiceId} onChange={e => setVoiceId(e.target.value)}>
                              {voiceProvider === 'openai' ? (
                                <optgroup label="OpenAI TTS">
                                  <option value="alloy">Alloy (Feminina/Neutra)</option>
                                  <option value="echo">Echo (Masculina)</option>
                                  <option value="nova">Nova (Feminina Dinâmica)</option>
                                </optgroup>
                              ) : (
                                <optgroup label="ElevenLabs">
                                  <option value="rachel">Rachel (Realista Feminina)</option>
                                  <option value="drew">Drew (Realista Masculino)</option>
                                </optgroup>
                              )}
                          </select>
                        </div>
                    </div>
                  )}

                  <div className="space-y-4 pt-4 border-t border-border/30">
                     <div className="space-y-2">
                        <label className="text-xs font-semibold text-muted-foreground">Quando responder em Áudio?</label>
                        <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm" value={audioCondition} onChange={e => setAudioCondition(e.target.value)}>
                           <option value="always">Sempre (Voz 100%)</option>
                           <option value="only_long">Só em respostas longas</option>
                           <option value="only_followup">Só no Retorno/Follow-up</option>
                           <option value="rarely">Raramente (Misto)</option>
                        </select>
                     </div>
                     <div className="flex flex-col gap-2 p-3 bg-card/50 rounded-lg border border-border/50">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold flex items-center gap-2">Dividir Textões (Mensagens Curtas)</span>
                          <Switch checked={splitMessages} onCheckedChange={setSplitMessages} />
                        </div>
                     </div>
                  </div>
                </div>

                {/* UX and Agenda */}
                <div className="space-y-6">
                   {/* UX */}
                   <div className="p-5 border border-border/50 rounded-xl bg-card/30 space-y-4">
                     <h4 className="font-bold flex items-center gap-2 text-primary border-b border-border/50 pb-2"><MessageSquare className="w-4 h-4"/> Experiência do Usuário (UX)</h4>
                     <div className="flex items-center justify-between">
                        <div>
                          <span className="text-sm font-semibold flex items-center gap-2">Simular Digitação Humana</span>
                          <p className="text-[0.65rem] text-muted-foreground">Aparece o "digitando..." no WhatsApp.</p>
                        </div>
                        <Switch checked={simulateTyping} onCheckedChange={setSimulateTyping} />
                     </div>
                     {simulateTyping && (
                       <div className="space-y-2 pt-2">
                         <div className="flex justify-between">
                           <label className="text-xs font-semibold text-muted-foreground">Velocidade (ms por letra)</label>
                           <span className="text-xs font-mono text-primary font-bold">{typingSpeedMs[0]}ms</span>
                         </div>
                         <Slider value={typingSpeedMs} onValueChange={setTypingSpeedMs} min={10} max={200} step={10} />
                       </div>
                     )}
                   </div>

                   {/* Habilidades Mágicas (Step 5 Parity) */}
                   <div className="p-5 border border-purple-500/20 rounded-xl bg-purple-500/5 space-y-4 mt-6">
                     <h4 className="font-bold flex items-center gap-2 text-purple-500 border-b border-purple-500/20 pb-2"><Wand2 className="w-4 h-4"/> Habilidades Especiais & Ajuste Fino</h4>
                     
                     <div className="space-y-3">
                       {[
                         { state: hotLeadTagger, setter: setHotLeadTagger, label: "Etiquetar Leads Automaticamente", desc: "Adiciona tag 'Quente' quando há intenção." },
                         { state: useProfileName, setter: setUseProfileName, label: "Extrair Nome do Perfil", desc: "Saúda pelo nome do WhatsApp." },
                         { state: validateProfileNameWithAI, setter: setValidateProfileNameWithAI, label: "Validar Nome com IA", desc: "Ignora nomes zoados (ex: 'Rei do Gado')." },
                         { state: knowLocalTime, setter: setKnowLocalTime, label: "Acesso a Data e Hora", desc: "Pode dizer 'Bom dia' ou 'Boa tarde' real." },
                         { state: empathyThermometer, setter: setEmpathyThermometer, label: "Termômetro de Empatia", desc: "Desarma o lead se detectar raiva." },
                         { state: autoTrain, setter: setAutoTrain, label: "Auto Treinamento", desc: "Lembra das correções passadas." }
                       ].map(skill => (
                         <div key={skill.label} className="flex items-center justify-between">
                           <div>
                             <span className="text-sm font-semibold">{skill.label}</span>
                             <p className="text-[0.65rem] text-muted-foreground">{skill.desc}</p>
                           </div>
                           <Switch checked={skill.state} onCheckedChange={skill.setter} className="data-[state=checked]:bg-purple-500" />
                         </div>
                       ))}
                     </div>

                     <div className="space-y-4 pt-4 border-t border-purple-500/20">
                       <div className="space-y-2">
                         <div className="flex justify-between">
                           <label className="text-xs font-semibold text-muted-foreground flex items-center gap-1"><Target className="w-3 h-3"/> Pressão de Vendas</label>
                           <span className="text-xs font-mono text-purple-500 font-bold">{salesPressure[0]}%</span>
                         </div>
                         <Slider value={salesPressure} onValueChange={setSalesPressure} min={0} max={100} step={10} className="py-2" />
                       </div>
                       <div className="space-y-2">
                          <label className="text-xs font-semibold text-muted-foreground">Desconto Máximo Permitido (%)</label>
                          <Input value={maxDiscount} onChange={e => setMaxDiscount(e.target.value)} placeholder="Ex: 10, 15 (Deixe em branco para zero)" className="bg-background/50 h-10 border-purple-500/20" />
                       </div>
                     </div>
                   </div>

                   {/* Agenda */}
                   <div className="p-5 border border-border/50 rounded-xl bg-card/30 space-y-4">
                     <h4 className="font-bold flex items-center gap-2 text-primary border-b border-border/50 pb-2"><Database className="w-4 h-4"/> Agenda e Folgas</h4>
                     <div className="space-y-2">
                       <label className="text-xs font-semibold text-muted-foreground">Dias de Folga (Ignorar Mensagens)</label>
                       <div className="flex flex-wrap gap-2">
                         {['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab'].map((d, i) => (
                           <button 
                             key={d} 
                             onClick={() => setExcludedDays(prev => prev.includes(i.toString()) ? prev.filter(x => x !== i.toString()) : [...prev, i.toString()])}
                             className={cn("px-2 py-1 text-xs rounded-md border", excludedDays.includes(i.toString()) ? "bg-destructive/20 border-destructive text-destructive" : "bg-card border-border/50")}
                           >
                             {d}
                           </button>
                         ))}
                       </div>
                     </div>
                   </div>
                </div>

              </div>
            </div>
          )}

        </div>

        {/* Right Side (Sandbox) */}
        {!sandboxCollapsed && (
          <div className="w-full lg:w-[400px] xl:w-[450px] shrink-0 flex flex-col bg-black/60 border-l border-border/50 z-10 shadow-[-10px_0_30px_-15px_rgba(0,0,0,0.5)] animate-in slide-in-from-right-8 duration-300">
            <div className="p-4 border-b border-border/50 bg-card/40 flex justify-between items-center backdrop-blur-md">
              <div className="flex items-center gap-2 overflow-hidden">
                <FlaskConical className="h-5 w-5 text-primary shrink-0" />
                <span className="font-bold whitespace-nowrap">Sandbox (Live Test)</span>
                <span className={cn("text-[0.65rem] px-2 py-0.5 rounded-full ml-2 border whitespace-nowrap", currentAgentId ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30" : "text-muted-foreground bg-muted/40 border-border/50")}>
                  {currentAgentId ? "Conectado" : "Offline"}
                </span>
              </div>
              <div className="flex gap-1">
                <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive transition-colors shrink-0" onClick={() => setChatLog([])} title="Limpar Chat">
                  <Eraser className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary transition-colors shrink-0" onClick={() => setSandboxCollapsed(true)} title="Recolher Sandbox">
                  <PanelRightClose className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar" ref={chatScrollRef}>
              {chatLog.map((c, i) => (
                <div key={i} className={cn(
                  "max-w-[85%] p-3.5 rounded-2xl text-sm animate-in fade-in slide-in-from-bottom-2 whitespace-pre-wrap shadow-sm",
                  c.role === 'user' ? "bg-primary text-primary-foreground self-end rounded-tr-sm ml-auto" :
                  c.role === 'error' ? "bg-destructive/20 border border-destructive/40 text-destructive-foreground self-center mx-auto text-center" :
                  "bg-emerald-500/10 border border-emerald-500/20 text-foreground self-start rounded-tl-sm mr-auto font-medium"
                )}>
                  {c.text}
                </div>
              ))}
              {isTyping && (
                <div className="max-w-[85%] p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 self-start rounded-tl-sm flex gap-1 shadow-sm">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/50 animate-bounce" />
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/50 animate-bounce delay-75" />
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500/50 animate-bounce delay-150" />
                </div>
              )}
            </div>

            <div className="p-4 bg-card/40 border-t border-border/50 backdrop-blur-md flex gap-2">
              <Input
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendSandboxMsg()}
                placeholder="Digite a mensagem para testar..."
                className="bg-background/80 h-10 focus-visible:ring-emerald-500 border-border/50"
              />
              <Button size="icon" onClick={sendSandboxMsg} className="h-10 w-10 shrink-0 bg-emerald-500 hover:bg-emerald-600 text-white shadow-glow">
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
