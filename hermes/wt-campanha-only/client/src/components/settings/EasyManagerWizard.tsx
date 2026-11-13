import { useState, useEffect } from "react";
import { toast } from "sonner";
import { apiGet, apiPut, apiPost, apiErrorMessage } from "@/lib/api";
import { fetchAIModels } from "@/services/aimodels";
import { logError } from "@/lib/log";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { RotateCcw, Save, ShieldCheck, MonitorSmartphone, CheckCircle2, ArrowRight, ArrowLeft, Brain, Volume2, Globe, User, Users, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Field } from "@/components/ui/field";
import { CredentialSelect } from "./CredentialSelect";
import { LLM_PROVIDERS } from "@/constants/ai-providers";
import { getAgentGroups, type WhatsAppGroup } from "@/services/settings";

export const EasyManagerWizard = () => {
  const [step, setStep] = useState(1);
  const [state, setState] = useState({
    enabled: true,
    name: "Hermes Gestor",
    systemPrompt: "Você é o Hermes, assistente que opera o WhatsApp a pedido do DONO da conta...",
    cognitiveIndependence: true,
    managerApiKey: "",
    credentialId: "",
    model: "",
    treeViewMode: "canvas", // 'list' | 'canvas'

    // Comunicacao
    whatsappMode: "private", // private or group
    welcomeMessage: "",
    groupJid: "",
    groupName: "",
    notifyTelegram: false,
    selfChat: false,
    audioCondition: "text_and_audio",
    chunkMessages: true,

    // OpenClaw & Ferramentas
    tools: ["web_search", "weather", "crm", "agenda", "company_consultant", "vision_analysis"],
    openclawEnabled: true,
    openclawUrl: "",
    openclawKey: "",
    
    // Superpoderes do Gestor
    haltOverride: true,
    billingAlerts: true,
    scheduledReports: false,
    promisesAccountability: true,
    criticalAlerts: true,
    handoffAlerts: true,
    shadowingMode: false,
    
    // Deep Tech
    memoryClustering: true,
    swarmCollaboration: false,
    
    // Personal Agent OS Features
    osControl: false,
    perpetualMemory: true,
    taskDelegation: true,
    deepResearch: false,
    
    provider: "openai",
    fallbackProvider: "groq",
  });

  const [saving, setSaving] = useState(false);
  const [groups, setGroups] = useState<WhatsAppGroup[]>([]);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [creatingGroup, setCreatingGroup] = useState(false);
  const [testingTg, setTestingTg] = useState(false);
  const [savedBaseURL, setSavedBaseURL] = useState("");
  const [savedModel, setSavedModel] = useState("");
  const [telegramToken, setTelegramToken] = useState("");
  const [telegramChatId, setTelegramChatId] = useState("");
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);

  const updateState = (key: keyof typeof state, value: any) => {
    setState((prev) => ({ ...prev, [key]: value }));
  };

  const fetchModelsForCredential = async (provider: string, credentialId: string) => {
    if (!credentialId) return;
    setLoadingModels(true);
    try {
      // A rota certa é /api/ai/models (antes chamava /api/models, que não existe → 404).
      setAvailableModels(await fetchAIModels(provider, "", undefined, credentialId));
    } catch (e) {
      toast.error("Erro ao buscar modelos", { description: apiErrorMessage(e, "Não consegui listar os modelos desta credencial.") });
      setAvailableModels([]);
    } finally {
      setLoadingModels(false);
    }
  };

  // FIX (QA IA): antes o wizard era 100% cosmético — handleSave só dava um toast e nada
  // era persistido, então NUNCA dava pra saber se editava/substituía o gestor atual (ele
  // sempre abria do zero com os defaults). Agora carregamos o gestor REAL de /api/settings
  // (bloco `manager`, o MESMO AgentConfig que o "Funcionário Gestor" avançado e o runtime
  // do AIAgent usam) e o Salvar faz PUT /api/settings/manager — logo é edição do gestor
  // ÚNICO do sistema (SUBSTITUI), não cria outro.
  useEffect(() => {
    // 1) Núcleo do gestor (bloco `manager` = AgentConfig que o runtime consome).
    apiGet<any>("/api/settings")
      .then((all) => {
        const m = all?.manager;
        if (m) {
          setState((prev) => ({
            ...prev,
            enabled: m.enabled ?? prev.enabled,
            provider: m.provider || prev.provider,
            model: m.model || prev.model,
            // Prompt: usa o do gestor salvo; se vazio, cai no prompt PADRÃO da conta
            // (o mesmo do atendente principal) em vez de um texto genérico placeholder.
            systemPrompt: m.system_message || all?.attendant?.system_message || prev.systemPrompt,
            managerApiKey: m.api_key || "",
            credentialId: m.credential_id || "",
          }));
          setSavedModel(m.model || "");
          setSavedBaseURL(m.base_url || "");
        }
        // Carregar owner_message_enabled e notify_telegram do bloco agent_chat (o que o servidor
        // usa de verdade). O bloco do assistente (abaixo) não sobrescreve esses dois.
        const ac = all?.agent_chat;
        if (ac) {
          setState((prev) => ({
            ...prev,
            selfChat: ac.owner_message_enabled ?? prev.selfChat,
            notifyTelegram: ac.notify_telegram ?? prev.notifyTelegram,
          }));
        }
      })
      .catch(logError("EasyManagerWizard"));
    // 2) Estado RICO do wizard (canais/telegram/ferramentas/superpoderes).
    apiGet<any>("/api/easy-manager/wizard")
      .then((res) => {
        const c = res?.config;
        if (!c) return;
        setState((prev) => ({
          ...prev,
          name: c.name || prev.name,
          whatsappMode: c.whatsapp_mode || prev.whatsappMode,
          welcomeMessage: c.welcome_message ?? prev.welcomeMessage,
          groupJid: c.group_jid ?? prev.groupJid,
          groupName: c.group_name ?? prev.groupName,
          audioCondition: c.audio_condition || prev.audioCondition,
          chunkMessages: c.chunk_messages ?? prev.chunkMessages,
          tools: Array.isArray(c.tools) && c.tools.length ? c.tools : prev.tools,
          openclawEnabled: c.openclaw_enabled ?? prev.openclawEnabled,
          openclawUrl: c.openclaw_url ?? prev.openclawUrl,
          fallbackProvider: c.fallback_provider || prev.fallbackProvider,
          cognitiveIndependence: c.cognitive_independence ?? prev.cognitiveIndependence,
          haltOverride: c.halt_override ?? prev.haltOverride,
          billingAlerts: c.billing_alerts ?? prev.billingAlerts,
          scheduledReports: c.scheduled_reports ?? prev.scheduledReports,
          promisesAccountability: c.promises_accountability ?? prev.promisesAccountability,
          criticalAlerts: c.critical_alerts ?? prev.criticalAlerts,
          handoffAlerts: c.handoff_alerts ?? prev.handoffAlerts,
          shadowingMode: c.shadowing_mode ?? prev.shadowingMode,
          memoryClustering: c.memory_clustering ?? prev.memoryClustering,
          swarmCollaboration: c.swarm_collaboration ?? prev.swarmCollaboration,
          osControl: c.os_control ?? prev.osControl,
          perpetualMemory: c.perpetual_memory ?? prev.perpetualMemory,
          taskDelegation: c.task_delegation ?? prev.taskDelegation,
          deepResearch: c.deep_research ?? prev.deepResearch,
        }));
        setTelegramToken(c.telegram_token || "");
        setTelegramChatId(c.telegram_chat_id || "");
      })
      .catch(logError("EasyManagerWizard/wizard"));
  }, []);

  const fetchGroups = async () => {
    setLoadingGroups(true);
    try {
      const list = await getAgentGroups();
      setGroups(list);
    } catch (e) {
      toast.error("Erro ao buscar grupos", { description: (e as Error).message });
      setGroups([]);
    } finally {
      setLoadingGroups(false);
    }
  };

  const handleCreateGroup = async () => {
    const name = prompt("Nome do grupo:", "Hermes Gestor IA");
    if (!name?.trim()) return;
    setCreatingGroup(true);
    try {
      const res = await apiPost<{ ok: boolean; group_jid: string; name: string }>("/api/settings/agent-chat/create-group", {
        name: name.trim(),
        welcome_msg: state.welcomeMessage || "👋 Olá! Sou o Hermes Gestor. Mande uma mensagem e eu respondo!",
      });
      toast.success(`Grupo "${res.name}" criado!`);
      setState(prev => ({ ...prev, groupJid: res.group_jid, groupName: res.name }));
      await fetchGroups(); // Recarrega a lista
    } catch (e) {
      toast.error("Erro ao criar grupo", { description: (e as Error).message });
    } finally {
      setCreatingGroup(false);
    }
  };

  useEffect(() => {
    if (state.whatsappMode === "group") {
      fetchGroups();
    }
  }, [state.whatsappMode]);

  const testTelegram = async () => {
    if (!telegramToken.trim()) { toast.error("Cole o Token do Bot primeiro."); return; }
    setTestingTg(true);
    try {
      const chatId = parseInt(telegramChatId, 10);
      // 1) Salva no bloco GLOBAL `telegram` — é esse PUT que dá reloadTelegram e INICIA
      //    o bot. Sem isso o teste dá "telegram bot not running" (o token do wizard
      //    sozinho não sobe bot nenhum).
      // Os chats já autorizados ficam: o chat do teste é ACRESCENTADO (antes a lista virava
      // só ele, ou vazia, e os outros chats perdiam acesso — auditoria do mês 2, F26).
      const body: Record<string, unknown> = { token: telegramToken.trim(), enabled: true };
      if (!isNaN(chatId) && chatId !== 0) {
        const cur = await apiGet<any>("/api/settings");
        const existing: number[] = Array.isArray(cur?.telegram?.chat_ids) ? cur.telegram.chat_ids : [];
        body.chat_ids = existing.includes(chatId) ? existing : [...existing, chatId];
      }
      await apiPut("/api/settings/telegram", body);
      // 2) Agora testa (bot já rodando).
      await apiPost("/api/settings/telegram/test", { chat_id: isNaN(chatId) ? 0 : chatId });
      toast.success("Bot conectado e mensagem de teste enviada no Telegram!");
    } catch (e) {
      toast.error("Falha no teste do Telegram", { description: "Confira o token (BotFather) e o Chat ID. " + (e as Error).message });
    } finally {
      setTestingTg(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // 1) Núcleo do gestor (motor + prompt + chave) — o que o runtime consome.
      await apiPut("/api/settings/manager", {
        enabled: state.enabled,
        provider: state.provider,
        model: state.model,
        api_key: state.managerApiKey,
        credential_id: state.credentialId,
        ...(!state.credentialId && state.managerApiKey ? { api_key: state.managerApiKey } : {}),
        base_url: savedBaseURL,
        system_message: state.systemPrompt,
      });
      // 2) Estado rico do wizard (canais/telegram/ferramentas/superpoderes) — persiste
      //    tudo pra não sumir no reload. Antes só o núcleo salvava.
      await apiPut("/api/easy-manager/wizard", { config: {
        enabled: state.enabled, name: state.name, system_prompt: state.systemPrompt,
        provider: state.provider, fallback_provider: state.fallbackProvider,
        model: savedModel, base_url: savedBaseURL, manager_api_key: state.managerApiKey,
        cognitive_independence: state.cognitiveIndependence,
        whatsapp_mode: state.whatsappMode, welcome_message: state.welcomeMessage,
        group_jid: state.groupJid, group_name: state.groupName,
        notify_telegram: state.notifyTelegram, telegram_token: telegramToken, telegram_chat_id: telegramChatId,
        self_chat: state.selfChat, audio_condition: state.audioCondition, chunk_messages: state.chunkMessages,
        tools: state.tools, openclaw_enabled: state.openclawEnabled, openclaw_url: state.openclawUrl, openclaw_key: state.openclawKey,
        halt_override: state.haltOverride, billing_alerts: state.billingAlerts, scheduled_reports: state.scheduledReports,
        promises_accountability: state.promisesAccountability, critical_alerts: state.criticalAlerts, handoff_alerts: state.handoffAlerts,
        shadowing_mode: state.shadowingMode, memory_clustering: state.memoryClustering, swarm_collaboration: state.swarmCollaboration,
        os_control: state.osControl, perpetual_memory: state.perpetualMemory, task_delegation: state.taskDelegation, deep_research: state.deepResearch,
      }});
      // 3) Persiste no bloco agent-chat: modo, grupo selecionado e self-chat (owner_message).
      await apiPut("/api/settings/agent-chat", {
        enabled: true,
        mode: state.whatsappMode,
        group_jid: state.groupJid || "",
        group_name: state.groupName || "",
        welcome_msg: state.welcomeMessage || "",
        owner_message_enabled: state.selfChat,
        // O interruptor "Notificar no Telegram" vale para o aviso de respostas (antes só ia para o
        // bloco do assistente, que nada usa). O OpenClaw NÃO vai daqui: o servidor mantém o salvo.
        notify_telegram: state.notifyTelegram,
      });
      toast.success("Gestor do sistema salvo (substituído) com sucesso!");
    } catch (e) {
      toast.error("Falha ao salvar o gestor: " + (e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const TOTAL_STEPS = 3; // o passo 4 ("Superpoderes") saiu em 05/10: o servidor não lê nenhuma daquelas chaves
  const prevStep = () => { if (step > 1) setStep(step - 1); };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-primary" />
            Configuração Fácil do Gestor
          </h2>
          <p className="text-muted-foreground text-sm">
            Orquestrador Mestre: Defina a IA Primária que gerencia os outros funcionários.
          </p>
        </div>
        <Button onClick={handleSave} disabled={saving} className="gap-2 shadow-glow hidden md:flex">
          <Save className="w-4 h-4" /> {saving ? "Salvando..." : "Salvar Gestor"}
        </Button>
      </div>

      {/* Progress Tabs */}
      <div className="flex items-center justify-between gap-2 overflow-x-auto pb-2 no-scrollbar">
        {[
          { s: 1, label: "Identidade & Motor" },
          { s: 2, label: "Comunicação & Canais" },
          { s: 3, label: "Ferramentas & Visão" },
        ].map(({ s, label }) => (
           <div key={s} className="flex flex-col items-center gap-2 min-w-[90px] cursor-pointer" onClick={() => setStep(s)}>
             <div className={cn(
               "h-10 w-10 rounded-full border-2 flex items-center justify-center font-bold transition-all duration-300",
               step > s ? "bg-primary border-primary text-primary-foreground" : 
               step === s ? "border-primary text-primary shadow-glow bg-background" : "border-border/50 text-muted-foreground bg-background/50"
             )}>
                {s}
             </div>
             <span className={cn("text-xs font-semibold text-center whitespace-nowrap", step === s ? "text-primary" : "text-muted-foreground")}>{label}</span>
           </div>
        ))}
      </div>

      <div className="relative overflow-hidden min-h-[400px]">
        {/* Passo 1: Inteligência e Identidade */}
        <div className={cn("transition-all duration-500", step === 1 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
             <h3 className="text-xl font-bold flex items-center gap-2 mb-6"><Brain className="h-5 w-5 text-indigo-500"/> 1. Identidade e Motor do Gestor</h3>
             
             <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
               <Field label="Nome do Gestor (Avatar)">
                 <Input className="bg-background" value={state.name} onChange={e => updateState("name", e.target.value)} placeholder="Ex: Hermes Gestor" />
               </Field>
               <Field label="Prompt de Sistema Principal (Personalidade)">
                 <Textarea className="bg-background text-sm font-mono" rows={3} value={state.systemPrompt} onChange={e => updateState("systemPrompt", e.target.value)} placeholder="Descreva as diretrizes do gestor..." />
               </Field>
             </div>

             <div className="flex items-center justify-between p-4 bg-background/50 border border-border/50 rounded-xl mb-6">
                <div>
                   <h4 className="font-bold text-sm">Independência Cognitiva</h4>
                   <p className="text-xs text-muted-foreground">Se ativo, usa credenciais próprias para o Gestor (não divide limites com os atendentes).</p>
                </div>
                <Switch checked={state.cognitiveIndependence} onCheckedChange={c => updateState("cognitiveIndependence", c)} />
             </div>

             {state.cognitiveIndependence && (
               <div className="space-y-4">
                 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2 p-4 bg-background/50 border border-border/50 rounded-xl">
                     <label className="text-sm font-bold text-emerald-500">Motor Principal</label>
                     <select className="w-full bg-background border border-border/50 rounded-lg p-2.5 text-sm" value={state.provider} onChange={e => updateState("provider", e.target.value)}>
                        {LLM_PROVIDERS.filter(p => p.value !== "custom").map(p => (
                           <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                     </select>
                  </div>
                  <div className="space-y-2 p-4 bg-background/50 border border-border/50 rounded-xl">
                     <label className="text-sm font-bold text-amber-500">Fallback</label>
                     <select className="w-full bg-background border border-border/50 rounded-lg p-2.5 text-sm" value={state.fallbackProvider} onChange={e => updateState("fallbackProvider", e.target.value)}>
                        {LLM_PROVIDERS.filter(p => p.value !== "custom").map(p => (
                           <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                     </select>
                  </div>
                  {/* type="llm": antes ia filterType (prop que não existe) e a lista vinha vazia. */}
                  <div className="mt-2">
                    <CredentialSelect
                      type="llm"
                      value={state.credentialId}
                      onChange={(id) => updateState("credentialId", id)}
                    />
                  </div>
                 </div>

                 <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                   <div className="space-y-2">
                     <label className="text-sm font-medium">Modelo</label>
                     <select
                       className="w-full bg-background border border-border/50 rounded-lg p-2.5 text-sm"
                       value={state.model}
                       onChange={e => updateState("model", e.target.value)}
                     >
                       <option value="">Modelo padrão do provider</option>
                       {availableModels.map(m => (
                         <option key={m} value={m}>{m}</option>
                       ))}
                     </select>
                   </div>
                   <div className="flex items-end">
                     <Button
                       variant="outline"
                       size="sm"
                       disabled={!state.credentialId || loadingModels}
                       onClick={() => fetchModelsForCredential(state.provider, state.credentialId)}
                       className="w-full"
                     >
                       <RotateCcw className={cn("h-4 w-4 mr-2", loadingModels && "animate-spin")} />
                       {loadingModels ? "Buscando..." : "Buscar Modelos"}
                     </Button>
                   </div>
                 </div>
               </div>
             )}
          </Card>
        </div>

        {/* Passo 2: Comunicação */}
        <div className={cn("transition-all duration-500", step === 2 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
             <h3 className="text-xl font-bold flex items-center gap-2 mb-6"><MonitorSmartphone className="h-5 w-5 text-sky-500"/> 2. Canais e Matriz de Comunicação</h3>
             
             <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div onClick={() => updateState("whatsappMode", "private")} className={cn("p-4 rounded-xl border flex flex-col items-center text-center gap-2 cursor-pointer transition-colors", state.whatsappMode === "private" ? "bg-emerald-500/10 border-emerald-500" : "bg-background/50 border-border/50")}>
                   <User className={cn("w-8 h-8", state.whatsappMode === "private" ? "text-emerald-500" : "text-muted-foreground")} />
                   <div>
                     <h4 className="font-bold text-sm">Só Privado</h4>
                     <p className="text-xs text-muted-foreground">Responde só DMs 1 a 1.</p>
                   </div>
                </div>
                <div onClick={() => updateState("whatsappMode", "group")} className={cn("p-4 rounded-xl border flex flex-col items-center text-center gap-2 cursor-pointer transition-colors", state.whatsappMode === "group" ? "bg-emerald-500/10 border-emerald-500" : "bg-background/50 border-border/50")}>
                   <Users className={cn("w-8 h-8", state.whatsappMode === "group" ? "text-emerald-500" : "text-muted-foreground")} />
                   <div>
                     <h4 className="font-bold text-sm">Só Grupo</h4>
                     <p className="text-xs text-muted-foreground">Atua apenas num grupo específico.</p>
                   </div>
                </div>
                <div onClick={() => updateState("whatsappMode", "all")} className={cn("p-4 rounded-xl border flex flex-col items-center text-center gap-2 cursor-pointer transition-colors", state.whatsappMode === "all" ? "bg-emerald-500/10 border-emerald-500" : "bg-background/50 border-border/50")}>
                   <Globe className={cn("w-8 h-8", state.whatsappMode === "all" ? "text-emerald-500" : "text-muted-foreground")} />
                   <div>
                     <h4 className="font-bold text-sm">Ambos</h4>
                     <p className="text-xs text-muted-foreground">Responde no PV e em grupos.</p>
                   </div>
                </div>
             </div>

             {(state.whatsappMode === "group" || state.whatsappMode === "all") && (
               <div className="p-4 bg-background/50 border border-border/50 rounded-xl space-y-3">
                 <label className="text-sm font-medium flex items-center gap-2">
                   <Users className="w-4 h-4 text-emerald-500" /> Grupo WhatsApp
                 </label>
                 <div className="flex items-center gap-2">
                   <select
                     className="flex-1 bg-background border border-border/50 rounded-lg p-2.5 text-sm"
                     value={state.groupJid}
                     onChange={e => {
                       const sel = groups.find(g => g.jid === e.target.value);
                       setState(prev => ({ ...prev, groupJid: e.target.value, groupName: sel?.name || "" }));
                     }}
                     disabled={loadingGroups}
                   >
                     <option value="">{loadingGroups ? "Carregando..." : "Selecione um grupo"}</option>
                     {groups.map(g => (
                       <option key={g.jid} value={g.jid}>{g.name}</option>
                     ))}
                   </select>
                   <Button variant="outline" size="sm" onClick={handleCreateGroup} disabled={creatingGroup}>
                     <Plus className="w-4 h-4 mr-1" /> {creatingGroup ? "Criando..." : "Criar Novo"}
                   </Button>
                 </div>
                 {state.groupJid && (
                   <p className="text-xs text-muted-foreground">Grupo selecionado: <span className="text-emerald-400 font-mono">{state.groupName || state.groupJid}</span></p>
                 )}
               </div>
             )}

             <Field label="Mensagem de Boas-vindas Automática">
                <Input className="bg-background" value={state.welcomeMessage} onChange={e => updateState("welcomeMessage", e.target.value)} placeholder="Ex: Olá! Sou o assistente de IA. Como posso ajudar?" />
             </Field>

             <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div className="flex items-center justify-between p-4 bg-background/50 border border-border/50 rounded-xl">
                   <div>
                     <h4 className="font-bold text-sm text-sky-400">Notificar no Telegram</h4>
                     <p className="text-xs text-muted-foreground">Receba relatórios curtos lá.</p>
                   </div>
                   <Switch checked={state.notifyTelegram} onCheckedChange={c => updateState("notifyTelegram", c)} />
                </div>
                <div className="flex items-center justify-between p-4 bg-background/50 border border-border/50 rounded-xl">
                   <div>
                     <h4 className="font-bold text-sm text-violet-400">Self-Chat</h4>
                     <p className="text-xs text-muted-foreground">Responde mensagens que você manda para si mesmo.</p>
                   </div>
                   <Switch checked={state.selfChat} onCheckedChange={c => updateState("selfChat", c)} />
                </div>
             </div>

             {state.notifyTelegram && (
               <div className="p-4 bg-sky-500/5 border border-sky-500/20 rounded-xl mt-4 space-y-3">
                 <p className="text-xs text-muted-foreground">Cole as credenciais do Telegram pra falar com o Gestor por lá. Crie um bot no @BotFather, copie o token, e o Chat ID você pega no @userinfobot.</p>
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                   <Field label="Token do Bot (BotFather)">
                     <Input className="bg-background" value={telegramToken} onChange={e => setTelegramToken(e.target.value)} placeholder="123456:ABC-DEF..." />
                     {telegramToken.includes("***") && (
                       <p className="text-[11px] text-muted-foreground mt-1">Token salvo (por segurança só o fim aparece). Para trocar, apague e cole o novo.</p>
                     )}
                   </Field>
                   <Field label="Chat ID">
                     <Input className="bg-background" value={telegramChatId} onChange={e => setTelegramChatId(e.target.value)} placeholder="Ex: 987654321" />
                   </Field>
                 </div>
                 <Button variant="outline" onClick={testTelegram} disabled={testingTg} className="gap-2 text-sky-400 border-sky-500/30 hover:bg-sky-500/10">
                   <CheckCircle2 className="w-4 h-4" /> {testingTg ? "Testando..." : "Testar Telegram"}
                 </Button>
               </div>
             )}

             <div className="border-t border-border/50 pt-6 mt-4">
               <h4 className="font-bold text-sm flex items-center gap-2 mb-4"><Volume2 className="w-4 h-4 text-sky-500"/> Notificações por Áudio</h4>
               <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {['never', 'text_and_audio', 'always_audio'].map((opt) => (
                    <div key={opt} onClick={() => updateState("audioCondition", opt)} className={cn("p-3 rounded-xl border cursor-pointer text-center", state.audioCondition === opt ? "bg-sky-500/10 border-sky-500/50" : "bg-background border-border/50")}>
                       <span className={cn("text-sm font-semibold", state.audioCondition === opt ? "text-sky-500" : "")}>
                          {opt === 'never' ? "Só Texto" : opt === 'text_and_audio' ? "Texto + Áudio" : "Só Áudio"}
                       </span>
                    </div>
                  ))}
               </div>
             </div>
          </Card>
        </div>

        {/* Passo 3: Ferramentas e Consultoria */}
        <div className={cn("transition-all duration-500", step === 3 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
             <h3 className="text-xl font-bold flex items-center gap-2 mb-6"><Globe className="h-5 w-5 text-emerald-500"/> 3. Matriz de Ferramentas & Análise</h3>
             <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { id: "web_search", name: "Pesquisa Web (Google)", desc: "Pode pesquisar no Google." },
                  { id: "company_consultant", name: "Leitura de Site e Dados (Consultoria)", desc: "Lê o site e dados da empresa para sugerir planos de ação." },
                  { id: "vision_analysis", name: "Análise de Imagens (Visão)", desc: "Pode ver imagens enviadas pelo dono ou clientes." },
                  { id: "weather", name: "Consultar Clima", desc: "Permite saber previsão do tempo." },
                  { id: "crm", name: "Gestor de CRM", desc: "Ler e mover funis." },
                  { id: "agenda", name: "Agenda", desc: "Gerenciar reuniões." },
                  { id: "code_sandbox", name: "Code Interpreter (Sandboxing)", desc: "Pode escrever e executar scripts Python isolados para cruzar tabelas e dados massivos sem estourar tokens." },
                  { id: "dynamic_webhook", name: "Webhook Autônomo", desc: "Gera uma URL própria para escutar Stripe/Shopify e reagir proativamente." },
                  { id: "content_creator", name: "Criador de Conteúdo (Social)", desc: "Gera imagens com IA e posta automaticamente no Instagram/Facebook." }
                ].map(tool => (
                   <div key={tool.id} onClick={() => {
                       const current = state.tools;
                       updateState("tools", current.includes(tool.id) ? current.filter(t => t !== tool.id) : [...current, tool.id]);
                   }} className={cn("p-4 rounded-xl border flex items-start gap-3 cursor-pointer transition-colors", state.tools.includes(tool.id) ? "bg-emerald-500/10 border-emerald-500/30" : "bg-background/50 border-border/50 hover:bg-background/80")}>
                      <Switch checked={state.tools.includes(tool.id)} className="mt-1 pointer-events-none" />
                      <div>
                        <h5 className={cn("font-bold text-sm", state.tools.includes(tool.id) ? "text-emerald-500" : "")}>{tool.name}</h5>
                        <p className="text-xs text-muted-foreground mt-0.5">{tool.desc}</p>
                      </div>
                   </div>
                ))}
             </div>
          </Card>
        </div>

      </div>

      <div className="flex items-center justify-between mt-8 border-t border-border/50 pt-4">
        <Button variant="ghost" onClick={prevStep} disabled={step === 1}>
           <ArrowLeft className="w-4 h-4 mr-2" /> Voltar
        </Button>
        {step < TOTAL_STEPS ? (
           <Button onClick={() => setStep(step + 1)} className="bg-primary hover:bg-primary/90 text-white shadow-glow">
              Próxima Etapa <ArrowRight className="w-4 h-4 ml-2" />
           </Button>
        ) : (
           <Button onClick={handleSave} disabled={saving} className="bg-emerald-600 hover:bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.3)]">
              <Save className="w-4 h-4 mr-2" /> {saving ? "Salvando..." : "Finalizar Gestor"}
           </Button>
        )}
      </div>

    </div>
  );
};