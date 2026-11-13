import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { 
  Rocket, ArrowLeft, ArrowRight, CircleDollarSign, Headset, 
  CalendarCheck, Trash2, Plus, Brain, Mic, Volume2, Key,
  X, CalendarOff, AlertTriangle, Link as LinkIcon, MessageSquare, Phone, Bot, Play, Square,
  ShieldAlert, BarChart, RotateCcw, Wand2, Sparkles, FileText, SunMoon, Clock, Cpu, Flame, CheckCircle2, PhoneCall, Save, Database, AlignLeft, Briefcase, Filter
} from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { apiErrorMessage, apiGet, apiPost } from "@/lib/api";
import { parseExtras, parseList } from "@/lib/agent-extras";
import { apiUrl, authHeaders } from "@/lib/auth";
import { getClientId } from "@/lib/client-id";
import { setView, openSettingsTab } from "@/stores/navigation";
import { EasyFollowUpWizard } from "./EasyFollowUpWizard";
import { CredentialSelect } from "./CredentialSelect";
import { FALLBACK_MODELS, TTS_PROVIDERS as TTS_PROVIDERS_LIST, LLM_PROVIDERS } from "@/constants/ai-providers";

const ARCHETYPES = [
  {
    id: "vendas",
    category: "Vendas (B2B/B2C)",
    title: "Agente de Vendas (Closer)",
    description: "Focado em conversão, superação de objeções e fechamento de leads.",
    role: "Especialista em Fechamento B2B/B2C",
    icon: CircleDollarSign,
    color: "text-emerald-500",
    defaultTone: "Persuasivo, empático e direto ao ponto.",
    defaultSteps: "1. Saudação amigável e qualificação rápida.\n2. Descoberta do problema (spin selling leve).\n3. Apresentação da solução focada no benefício.\n4. Fechamento (chamada para ação clara).",
  },
  {
    id: "suporte",
    category: "Suporte e Retenção",
    title: "Atendimento (Tier 1)",
    description: "Empático e preciso, ideal para tirar dúvidas, enviar manuais e reduzir churn.",
    role: "Analista de Suporte",
    icon: Headset,
    color: "text-blue-500",
    defaultTone: "Paciente, amigável e extremamente resolutivo.",
    defaultSteps: "1. Recepção acolhedora.\n2. Entendimento e confirmação do problema reportado.\n3. Fornecimento da solução exata ou passo a passo.\n4. Confirmação se a dúvida foi resolvida.",
  },
  {
    id: "agendador",
    category: "Operações Internas",
    title: "Agendamento Dinâmico",
    description: "Conduz a conversa para marcar reuniões ou consultas na agenda.",
    role: "Concierge de Agendamentos",
    icon: CalendarCheck,
    color: "text-sky-500",
    defaultTone: "Educado, organizado e objetivo.",
    defaultSteps: "1. Saudação e identificação da necessidade de agendamento.\n2. Oferta de dias e horários disponíveis.\n3. Coleta de dados básicos (se necessário).\n4. Confirmação do agendamento.",
  },
  {
    id: "cobranca",
    category: "Suporte e Retenção",
    title: "Cobrança Amigável (Ativo)",
    description: "Aborda clientes inadimplentes com empatia para negociar dívidas e gerar boletos.",
    role: "Especialista em Negociação e Retenção",
    icon: ShieldAlert,
    color: "text-amber-500",
    defaultTone: "Firme, compreensivo e focado em resolver a pendência.",
    defaultSteps: "1. Confirmação de identidade de forma sutil.\n2. Informar sobre o valor em aberto amigavelmente.\n3. Ouvir a justificativa e oferecer condições de parcelamento.\n4. Formalizar o acordo e enviar link de pagamento.",
  },
  {
    id: "pesquisa",
    category: "Suporte e Retenção",
    title: "Pesquisa de NPS (Ativo)",
    description: "Faz pesquisas de satisfação rápidas, tabula notas e entende feedbacks.",
    role: "Pesquisador de Qualidade (NPS)",
    icon: BarChart,
    color: "text-indigo-500",
    defaultTone: "Curto, simpático e muito neutro ao ouvir feedbacks negativos.",
    defaultSteps: "1. Saudação informando que é uma pesquisa breve de 1 minuto.\n2. Pergunta da nota de 0 a 10.\n3. Se nota < 7, perguntar o que pode ser melhorado.\n4. Agradecimento rápido e encerramento.",
  },
  {
    id: "reativacao",
    category: "Vendas (B2B/B2C)",
    title: "Reativação de Leads (Ativo)",
    description: "Entra em contato com clientes antigos para oferecer novidades e resgatá-los.",
    role: "Especialista em Recuperação de Clientes",
    icon: RotateCcw,
    color: "text-rose-500",
    defaultTone: "Entusiástico, saudosista e focado em gerar curiosidade.",
    defaultSteps: "1. Saudação lembrando do último contato ou compra do cliente.\n2. Pergunta de sondagem ('Como estão as coisas desde então?').\n3. Apresentação de uma novidade imperdível ou desconto exclusivo de retorno.\n4. Fechamento com o próximo passo claro.",
  },
  {
    id: "sdr_b2b",
    category: "Vendas (B2B/B2C)",
    title: "SDR B2B (Cold Call)",
    description: "Faz prospecção fria para empresas, focado em passar pela secretária e agendar com o decisor.",
    role: "Sales Development Representative (SDR)",
    icon: Phone,
    color: "text-violet-500",
    defaultTone: "Autoridade, ritmo rápido e extremamente confiante.",
    defaultSteps: "1. Passar pela secretária/portaria com autoridade (Gatekeeper bypass).\n2. Abordagem inicial de valor (Elevator Pitch).\n3. Qualificação rápida de dor (BANT leve).\n4. Agendar reunião com o Executivo de Vendas.",
  },
  {
    id: "qualificador_inbound",
    category: "Vendas (B2B/B2C)",
    title: "Qualificador Inbound",
    description: "Atende leads que acabaram de preencher um formulário ou cair no WhatsApp.",
    role: "Qualificador de Leads Quentes",
    icon: Sparkles,
    color: "text-emerald-400",
    defaultTone: "Receptivo, ágil e curioso.",
    defaultSteps: "1. Agradecimento imediato pelo contato/cadastro.\n2. Perguntas de qualificação (Orçamento, Prazo, Decisor).\n3. Encaminhamento para o funil correto ou vendedor humano.",
  },
  {
    id: "cobrador_hard",
    category: "Operações Internas",
    title: "Recuperador Hard (Cobrança)",
    description: "Foco em dívidas antigas, gerando urgência extrema e acordos inegociáveis.",
    role: "Recuperador de Crédito High-Ticket",
    icon: AlertTriangle,
    color: "text-red-600",
    defaultTone: "Sério, incisivo e pautado em consequências (sem ser desrespeitoso).",
    defaultSteps: "1. Confirmação positiva de identidade.\n2. Aviso formal de notificação de débito avançado.\n3. Apresentação da ÚNICA proposta de acordo disponível hoje.\n4. Emissão imediata da chave PIX de acordo.",
  }
];

const MODELS_BY_PROVIDER: Record<string, string[]> = FALLBACK_MODELS;

export function EasyAgentWizard({ initialProfile, editMode = false, onSaved, onComplete }: { initialProfile?: any, editMode?: boolean, onSaved?: () => void, onComplete?: () => void }) {
  const [step, setStep] = useState(1);
  const [deploying, setDeploying] = useState(false);
  const [loaderText, setLoaderText] = useState("");

  // Campos avançados gravados (o extras pode vir como texto de /api/agent-profiles). Sem isto a
  // edição salvava os padrões por cima do que estava gravado (F15).
  const ex = parseExtras(initialProfile?.extras);

  // State objects mapping exactly to Inovare HTML logic
  const [state, setState] = useState({
    archetype: null as string | null,
    identity: {
      name: initialProfile?.name || "",
      role: initialProfile?.role || "",
      provider: initialProfile?.ai_provider || "openai",
      model: initialProfile?.ai_model || "gpt-4o-mini",
      fallbackProvider: ex.fallbackProvider ?? "groq", fallbackModel: ex.fallbackModel ?? "llama3-8b-8192", fallbackCredentialId: ex.fallbackCredentialId ?? "",
      instance: initialProfile?.instance_name || "",
      channel: initialProfile?.kind || "both",
      avatar: "", credentialId: "", dualPersona: ex.dualPersona ?? false, dualPersonaRules: ex.dualPersonaRules ?? ""
    },
    rag: { 
      knowledge: initialProfile?.knowledge_base || "", 
      guardrails: initialProfile?.guardrails || "", 
      targetAudience: ex.targetAudience ?? "", objections: ex.objections ?? "", maxLength: Number(ex.maxLength) || 0, dataToCollect: ex.dataToCollect ?? "", autoTrain: ex.autoTrain ?? false,
      extractToForm: false, mandatoryCollection: false, // em breve: ainda não são gravados
    },
    behavior: { 
      tone: initialProfile?.tone || "Profissional, acolhedor e direto ao ponto", 
      kpi: ex.kpi ?? "", 
      steps: initialProfile?.system_prompt || "", 
      temperature: ex.temperature ?? initialProfile?.temperature ?? 0.7, 
      salesPressure: Number(ex.salesPressure ?? 5), maxDiscount: Number(ex.maxDiscount) || 0, 
      listen_audio: initialProfile?.listen_audio ?? true, 
      reply_audio: initialProfile?.reply_audio ?? false, 
      voice_id: initialProfile?.voice || "pt-BR-FranciscaNeural",
      vision_enabled: initialProfile?.vision_enabled ?? false, 
      useProfileName: ex.useProfileName ?? false, validateProfileNameWithAI: ex.validateProfileNameWithAI ?? false, knowLocalTime: ex.knowLocalTime ?? false,
      hotLeadTagger: ex.hotLeadTagger ?? false, simulateTypingStatus: ex.simulateTypingStatus ?? false, humanTyping: ex.humanTyping ?? false,
      empathyThermometer: typeof ex.empathyThermometer === "number" ? ex.empathyThermometer : (ex.empathyThermometer === true ? 70 : 50),
      typingSpeedMs: Number(ex.typingSpeedMs ?? 50), splitMessages: ex.splitMessages ?? false, audioCondition: ex.audioCondition ?? "never",
      copilotMode: ex.copilotMode ?? false, dynamicMargin: ex.dynamicMargin ?? false,
      // Padrão: responde QUALQUER pessoa que mandar mensagem. Se o dono ligar, passa a
      // responder só quem o Hermes já ligou (outbound_only). Grupo nunca responde.
      outboundOnly: ex.outboundOnly ?? false,
      ttsProvider: ex.ttsProvider || "edge-tts",
      ttsCredentialId: ex.ttsCredentialId || "",
      backgroundNoise: initialProfile?.background_noise ?? ex.backgroundNoise ?? "",
    },
    agenda: { excludedDays: [] as string[], excludedDates: [] as string[] },
    handoff: { 
      keywords: initialProfile?.escalation_keywords || "", 
      message: initialProfile?.handoff_message || "Um momento, vou chamar a equipe humana...", 
      messageVoice: "Um momento por favor, não desligue...", 
      method: ex.handoffMethod || initialProfile?.handoff_method || "panel", 
      destAgent: initialProfile?.handoff_agent || "", destAgent2: "", 
      notifyTo: initialProfile?.handoff_notify || "panel", summaryText: true, summaryVoice: true, adminNumber: ex.handoffAdminNumber || "", askForHelp: false, sirenMode: false,
      toContact: ex.handoffToContact ?? false,
      callTriggers: (Array.isArray(ex.callTriggers) ? ex.callTriggers : []) as any[] },
    automations: parseList(initialProfile?.automations),
    tools: [] as string[],
  });

  const [instances, setInstances] = useState<any[]>([]);
  const [credentials, setCredentials] = useState<any[]>([]);

  // Chat de simulação (etapa final) — usa o PROMPT EM CONSTRUÇÃO via /api/ai/simulate.
  const [simMsgs, setSimMsgs] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [simInput, setSimInput] = useState("");
  const [simSending, setSimSending] = useState(false);
  const [rudeMode, setRudeMode] = useState(false);

  // Simulação por voz (Web Speech API)
  const [voiceSimActive, setVoiceSimActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [voiceSimMsgs, setVoiceSimMsgs] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const voiceSimMsgsRef = useRef(voiceSimMsgs);
  const bgAudioRef = useRef<HTMLAudioElement | null>(null);
  const [bgPlaying, setBgPlaying] = useState(false);

  const toggleBgPreview = () => {
    const noise = state.behavior.backgroundNoise;
    if (!noise) return;
    if (bgPlaying && bgAudioRef.current) {
      bgAudioRef.current.pause();
      bgAudioRef.current.currentTime = 0;
      bgAudioRef.current = null;
      setBgPlaying(false);
      return;
    }
    const audio = new Audio("/audio/ambient/" + noise + ".mp3");
    audio.loop = true;
    audio.volume = 0.5;
    audio.onended = () => setBgPlaying(false);
    audio.onerror = () => { toast.error("Não foi possível carregar o áudio de fundo."); setBgPlaying(false); };
    audio.play().then(() => setBgPlaying(true)).catch(() => { toast.error("Erro ao reproduzir áudio."); });
    bgAudioRef.current = audio;
  };

  useEffect(() => {
    return () => {
      if (bgAudioRef.current) {
        bgAudioRef.current.pause();
        bgAudioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (bgAudioRef.current) {
      bgAudioRef.current.pause();
      bgAudioRef.current.currentTime = 0;
      bgAudioRef.current = null;
      setBgPlaying(false);
    }
  }, [state.behavior.backgroundNoise]);
  useEffect(() => { voiceSimMsgsRef.current = voiceSimMsgs; }, [voiceSimMsgs]);

  // Monta o prompt atual do agente a partir do estado do wizard (mesma base do deploy).
  const buildCurrentPrompt = () => {
    const p: string[] = [];
    if (state.identity.name) p.push(`Seu nome é ${state.identity.name}.`);
    if (state.identity.role) p.push(`Sua função: ${state.identity.role}.`);
    if (state.behavior.tone) p.push(`Tom de voz: ${state.behavior.tone}.`);
    if (state.rag.knowledge) p.push(`\nBASE DE CONHECIMENTO:\n${state.rag.knowledge}`);
    if (state.rag.guardrails) p.push(`\nREGRAS:\n${state.rag.guardrails}`);
    if (state.behavior.steps) p.push(`\nETAPAS/INSTRUÇÕES:\n${state.behavior.steps}`);
    return p.join("\n").trim() || "Você é um atendente prestativo e simpático.";
  };

  const sendSim = async () => {
    const text = simInput.trim();
    if (!text || simSending) return;
    const newHist = [...simMsgs, { role: "user" as const, content: text }];
    setSimMsgs(newHist);
    setSimInput("");
    setSimSending(true);
    try {
      let systemPrompt = buildCurrentPrompt();
      if (rudeMode) systemPrompt += "\n\n[NOTA DE TESTE: o cliente está impaciente e grosseiro; mantenha a calma e contorne.]";
      const res: any = await apiPost("/api/ai/simulate", {
        system_prompt: systemPrompt,
        message: text,
        history: simMsgs,
        credential_id: state.identity.credentialId || "",
        provider: state.identity.provider,
        model: state.identity.model,
        ...(inlineKey && !state.identity.credentialId ? { api_key: inlineKey } : {}),
      });
      setSimMsgs([...newHist, { role: "assistant", content: res.reply || "(sem resposta)" }]);
    } catch (e) {
      // Erro genérico não ajuda o dono. Consulta a saúde da chave de IA e mostra o
      // motivo real (cota esgotada / chave inválida / timeout) + quantos erros hoje.
      let desc = (e as Error).message;
      try {
        const h: any = await apiGet("/api/ai/key-health");
        if (h && h.ok === false && h.reason) {
          desc = `${h.reason} (${h.errors_24h} erro(s) de IA nas últimas 24h)`;
        }
      } catch { /* mantém a msg original */ }
      toast.error("Falha na simulação", { description: desc });
      setSimMsgs([...newHist, { role: "assistant", content: "⚠️ " + desc }]);
    } finally {
      setSimSending(false);
    }
  };

  const startVoiceSim = async () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { toast.error("Seu navegador não suporta reconhecimento de voz. Use Chrome."); return; }
    if (!window.speechSynthesis) { toast.error("Seu navegador não suporta síntese de voz."); return; }
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      toast.error("Permissão de microfone negada.");
      return;
    }
    setVoiceSimActive(true);
    setVoiceSimMsgs([]);
    setVoiceTranscript("");
    toast.success("Simulação de voz iniciada! Fale algo...");
    startListening();
  };

  const stopVoiceSim = () => {
    setVoiceSimActive(false);
    setIsListening(false);
    setIsSpeaking(false);
    setVoiceTranscript("");
    window.speechSynthesis.cancel();
  };

  const startListening = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    const recognition = new SR();
    recognition.lang = "pt-BR";
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = () => setIsListening(true);

    recognition.onresult = (event: any) => {
      const result = event.results[event.results.length - 1];
      const transcript = result[0].transcript;
      setVoiceTranscript(transcript);
      if (result.isFinal && transcript.trim()) {
        processVoiceInput(transcript.trim());
      }
    };

    recognition.onerror = (event: any) => {
      setIsListening(false);
      if (event.error !== "no-speech" && event.error !== "aborted") {
        toast.error("Erro no reconhecimento: " + event.error);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const processVoiceInput = async (text: string) => {
    setIsListening(false);
    setVoiceTranscript("");
    const currentMsgs = voiceSimMsgsRef.current;
    const newHist = [...currentMsgs, { role: "user" as const, content: text }];
    setVoiceSimMsgs(newHist);
    try {
      let systemPrompt = buildCurrentPrompt();
      if (rudeMode) systemPrompt += "\n\n[NOTA DE TESTE: o cliente está impaciente e grosseiro; mantenha a calma e contorne.]";
      const res: any = await apiPost("/api/ai/simulate", {
        system_prompt: systemPrompt,
        message: text,
        history: currentMsgs,
        credential_id: state.identity.credentialId || "",
        provider: state.identity.provider,
        model: state.identity.model,
        ...(inlineKey && !state.identity.credentialId ? { api_key: inlineKey } : {}),
      });
      const reply = res.reply || "(sem resposta)";
      setVoiceSimMsgs(prev => [...prev, { role: "assistant", content: reply }]);
      speakText(reply);
    } catch (e) {
      const errMsg = (e as Error).message;
      setVoiceSimMsgs(prev => [...prev, { role: "assistant", content: "⚠️ " + errMsg }]);
      toast.error("Falha na simulação", { description: errMsg });
      setTimeout(() => { setVoiceSimActive(active => { if (active) startListening(); return active; }); }, 1500);
    }
  };

  const speakText = (text: string) => {
    setIsSpeaking(true);
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "pt-BR";
    utterance.rate = 1.05;
    utterance.onend = () => {
      setIsSpeaking(false);
      setVoiceSimActive(active => { if (active) startListening(); return active; });
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      setVoiceSimActive(active => { if (active) startListening(); return active; });
    };
    window.speechSynthesis.speak(utterance);
  };

  const [keysConfig, setKeysConfig] = useState<any>({});
  const [missingKey, setMissingKey] = useState(false);
  const [inlineKey, setInlineKey] = useState("");
  const [magicUrl, setMagicUrl] = useState("");
  const [isMagicScraping, setIsMagicScraping] = useState(false);
  const [magicStep, setMagicStep] = useState(0);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [diffView, setDiffView] = useState<{ original: string; refined: string; summary?: string } | null>(null);
  const [magicModalOpen, setMagicModalOpen] = useState(false);
  const [followUpModalOpen, setFollowUpModalOpen] = useState(false);
  const [magicForm, setMagicForm] = useState({ sector: "", goal: "", personality: "" });

  // Modelos buscados EM TEMPO REAL da credencial (GET /api/ai/models). Fallback pra lista fixa.
  const [availableModels, setAvailableModels] = useState<Record<string, string[]>>({});
  const [loadingModels, setLoadingModels] = useState(false);
  const [testingKey, setTestingKey] = useState(false);
  const [credModalOpen, setCredModalOpen] = useState(false);
  const [credForm, setCredForm] = useState({ name: "", provider: "openai", api_key: "", base_url: "" });
  const [credTesting, setCredTesting] = useState(false);
  const [credSaving, setCredSaving] = useState(false);

  // modelsFor: modelos reais da credencial se já buscados, senão a lista fixa de segurança.
  const modelsFor = (provider: string) => availableModels[provider] || MODELS_BY_PROVIDER[provider] || [];

  // Busca modelos reais de um provider. A chave real fica no backend: mandamos
  // credential_id e o servidor resolve (o GET /api/credentials devolve chave mascarada).
  const fetchModelsForCredential = async (provider: string, credentialId: string) => {
    if (!provider || !credentialId) return;
    setLoadingModels(true);
    // Fallback conhecido do provider (MODELS_BY_PROVIDER). Se a API recusar listar,
    // caímos nele e mostramos msg clara — o cliente escolhe um modelo e continua.
    const fb = MODELS_BY_PROVIDER[provider] || [];
    try {
      // fetch direto (não apiGet) pra LER o corpo do erro limpo {error, hint} do backend.
      const qs = new URLSearchParams({ provider, credential_id: credentialId });
      const resp = await fetch(apiUrl(`/api/ai/models?${qs.toString()}`), {
        headers: { "X-Client-Id": getClientId(), ...authHeaders() },
      });
      const res: any = await resp.json().catch(() => ({}));

      if (!resp.ok || !res?.models?.length) {
        // Erro do provedor ou lista vazia: mensagem amigável + cai no fallback.
        if (!resp.ok) {
          const friendly = res?.error || res?.message || "Não consegui listar os modelos.";
          const hint = res?.hint ? ` ${res.hint}` : "";
          toast.warning("Não consegui listar da API — usando modelos conhecidos; confirme sua chave depois.", { description: `${friendly}${hint}` });
        } else {
          toast.warning("Nenhum modelo retornado pela API — usando modelos conhecidos; confirme sua chave depois.");
        }
        if (fb.length) {
          setAvailableModels(prev => ({ ...prev, [provider]: fb }));
          if (!fb.includes(state.identity.model)) updateState("identity", "model", fb[0]);
        }
        return;
      }

      setAvailableModels(prev => ({ ...prev, [provider]: res.models }));
      if (!res.models.includes(state.identity.model)) {
        updateState("identity", "model", res.models[0]);
      }
    } catch (e: any) {
      // Falha de rede: também cai no fallback conhecido em vez de só sumir com toast de erro.
      toast.warning("Não consegui conectar à API — usando modelos conhecidos; confirme sua chave depois.", { description: e?.message });
      if (fb.length) {
        setAvailableModels(prev => ({ ...prev, [provider]: fb }));
        if (!fb.includes(state.identity.model)) updateState("identity", "model", fb[0]);
      }
    }
    finally { setLoadingModels(false); }
  };

  const handleTestKey = async () => {
    if (!state.identity.credentialId) { toast.error("Selecione uma credencial primeiro."); return; }
    const c = credentials.find(x => x.id === state.identity.credentialId);
    setTestingKey(true);
    try {
      const res: any = await apiPost("/api/ai/test", { provider: c?.provider || state.identity.provider, credential_id: state.identity.credentialId, model: state.identity.model });
      if (res?.ok) toast.success("Chave válida! Conexão com a IA confirmada.");
      else toast.error("Chave inválida: " + (res?.error || "falha ao conectar"));
    } catch (e: any) {
      toast.error("Erro ao testar: " + (e.message || "desconhecido"));
    } finally { setTestingKey(false); }
  };

  const handleTestCredForm = async () => {
    if (!credForm.api_key || !credForm.provider) { toast.error("Preencha provedor e chave."); return; }
    setCredTesting(true);
    try {
      const res: any = await apiPost("/api/ai/test", { provider: credForm.provider, api_key: credForm.api_key, base_url: credForm.base_url });
      if (res?.ok) toast.success("Chave válida!");
      else toast.error("Chave inválida: " + (res?.error || "falha"));
    } catch (e: any) { toast.error("Erro: " + (e.message || "")); }
    finally { setCredTesting(false); }
  };

  const handleSaveCred = async () => {
    if (!credForm.name || !credForm.api_key || !credForm.provider) { toast.error("Preencha nome, provedor e chave."); return; }
    setCredSaving(true);
    try {
      await apiPost("/api/credentials", { name: credForm.name, type: "llm", provider: credForm.provider, api_key: credForm.api_key, base_url: credForm.base_url || undefined });
      // re-fetch e seleciona a nova
      const credRes: any = await apiGet("/api/credentials").catch(() => ({ credentials: [] }));
      const list = credRes.credentials || [];
      setCredentials(list);
      const nova = list.find((c: any) => c.name === credForm.name && c.provider === credForm.provider);
      if (nova) {
        updateState("identity", "credentialId", nova.id);
        updateState("identity", "provider", nova.provider);
        fetchModelsForCredential(nova.provider, nova.id);
      }
      toast.success("Credencial salva!");
      setCredModalOpen(false);
      setCredForm({ name: "", provider: "openai", api_key: "", base_url: "" });
    } catch (e: any) {
      toast.error("Erro ao salvar: " + (e.message || ""));
    } finally { setCredSaving(false); }
  };

  // distribuiGeneration: pega o JSON extraído pela IA e joga cada campo no lugar certo
  // das etapas 3/4. É o "distribuído corretamente" que a dona pediu.
  const distributeGeneration = (d: any) => {
    setState(prev => ({
      ...prev,
      identity: {
        ...prev.identity,
        name: prev.identity.name || d.companyName || prev.identity.name,
        role: d.companyName || prev.identity.role,
      },
      rag: {
        ...prev.rag,
        knowledge: d.knowledge || prev.rag.knowledge,
        targetAudience: d.targetAudience || prev.rag.targetAudience,
        objections: d.objections || prev.rag.objections,
        guardrails: d.guardrails || prev.rag.guardrails,
      },
      behavior: {
        ...prev.behavior,
        steps: d.steps || prev.behavior.steps,
        tone: d.tone || prev.behavior.tone,
      },
    }));
  };

  // runAgentGeneration: chama o backend REAL (/api/agents/generate). Lê o site (se url)
  // ou usa o formulário, extrai a estratégia via IA da credencial e distribui nos campos.
  const runAgentGeneration = async (opts: { url?: string; sector?: string; goal?: string; personality?: string }) => {
    if (!state.identity.credentialId) {
      toast.error("Escolha uma credencial de IA no Passo 2 antes de gerar.");
      setStep(2);
      return false;
    }
    const arch = ARCHETYPES.find(a => a.id === state.archetype);
    const c = credentials.find(x => x.id === state.identity.credentialId);
    try {
      const res: any = await apiPost("/api/agents/generate", {
        url: opts.url || "",
        sector: opts.sector || "",
        goal: opts.goal || "",
        personality: opts.personality || "",
        archetype: state.archetype || "",
        role_template: arch?.role || state.identity.role || "",
        steps_template: arch?.defaultSteps || "",
        provider: c?.provider || state.identity.provider,
        model: state.identity.model,
        credential_id: state.identity.credentialId,
      });
      if (!res?.success || !res?.data) throw new Error(res?.error || "A IA não retornou dados.");
      distributeGeneration(res.data);
      return true;
    } catch (e: any) {
      toast.error("Erro ao gerar: " + (e.message || "desconhecido"));
      return false;
    }
  };

  const handleMagicGeneration = async () => {
    if (!magicForm.sector || !magicForm.goal) {
       toast.error("Preencha o ramo de negócio e objetivo!");
       return;
    }
    setLoaderText("Gerando estratégia via IA...");
    setIsMagicScraping(true);
    // guarda o KPI/objetivo (o backend não devolve isso)
    updateState("behavior", "kpi", magicForm.goal);
    const ok = await runAgentGeneration({ sector: magicForm.sector, goal: magicForm.goal, personality: magicForm.personality });
    setIsMagicScraping(false);
    if (ok) {
      setMagicModalOpen(false);
      toast.success("Pronto! Revise os campos preenchidos e ajuste se quiser.");
      setStep(4); // vai pra etapa de conhecimento/prompt pra revisar o que a IA gerou
    }
  };

  useEffect(() => {
    // Initial fetch for providers, instances and models
    const init = async () => {
      try {
        const [instRes, settRes, credRes] = await Promise.all([
          apiGet<{success:boolean; data: any[]}>("/api/whatsapp/instances").catch(() => ({ success: false, data: [] })),
          apiGet<{success:boolean; keys: any}>("/api/settings").catch(() => ({ success: false, keys: {} })),
          apiGet<{credentials: any[]}>("/api/credentials").catch(() => ({ credentials: [] }))
        ]);
        if (instRes.success && instRes.data) {
          setInstances(instRes.data);
          // Compat: perfis antigos salvaram instance_name como NOME ("WhatsApp"). Agora
          // o select usa o id da sessão. Converte o valor salvo pro id correspondente
          // (casa por id, nome ou número) pra o select refletir a linha certa ao editar.
          const saved = (initialProfile?.instance_name || "").trim();
          if (saved) {
            const match = instRes.data.find((i: any) =>
              i.id === saved ||
              (i.name && i.name.toLowerCase() === saved.toLowerCase()) ||
              (i.jid && i.jid.replace(/\D/g, "").includes(saved.replace(/\D/g, "")) && saved.replace(/\D/g, "") !== "")
            );
            if (match && match.id !== saved) {
              updateState("identity", "instance", match.id);
            }
          }
        }
        if (settRes.success && settRes.keys) {
          setKeysConfig(settRes.keys);
        }
        if (credRes.credentials) {
          setCredentials(credRes.credentials);
        }
        // Initialize automations if empty
        if (state.automations.length === 0) {
          addAutomationRule();
        }
      } catch (e) {
        console.error("Erro ao carregar dados do wizard:", e);
      }
    };
    init();
  }, []);

  const updateState = (section: keyof typeof state, field: string, value: any) => {
    setState(prev => ({
      ...prev,
      [section]: {
        ...(prev[section] as any),
        [field]: value
      }
    }));
  };

  const handleArchetypeSelect = (arch: typeof ARCHETYPES[0]) => {
    setState(prev => ({
      ...prev,
      archetype: arch.id,
      identity: { ...prev.identity, role: arch.role },
      behavior: {
        ...prev.behavior,
        tone: arch.defaultTone,
        steps: arch.defaultSteps,
      }
    }));
  };

  const addAutomationRule = () => {
    const id = 'auto_' + Math.random().toString(36).substring(2, 9);
    setState(prev => ({
      ...prev,
      automations: [
        ...(Array.isArray(prev.automations) ? prev.automations : []),
        { id, trigger: "Qualquer Intenção", condition: "", action: "Disparar Webhook N8N (Substituir)" }
      ]
    }));
  };

  const updateAutomation = (id: string, field: string, value: unknown) => {
    setState(prev => ({
      ...prev,
      automations: (Array.isArray(prev.automations) ? prev.automations : []).map(a => a.id === id ? { ...a, [field]: value } : a)
    }));
  };

  const removeAutomation = (id: string) => {
    setState(prev => ({
      ...prev,
      automations: (Array.isArray(prev.automations) ? prev.automations : []).filter(a => a.id !== id)
    }));
  };

  const validateStep = () => {
    // Temporariamente desativado para testes do usuário
    return true;
    /*
    if (step === 1 && !state.archetype) { toast.error('Selecione um arquétipo cognitivo.'); return false; }
    if (step === 2 && !state.identity.name.trim()) { toast.error('O nome do agente é obrigatório.'); return false; }
    return true;
    */
  };

  const nextStep = () => {
    if (!validateStep()) return;
    if (step === 7) {
      // Prepare compilation step (Step 8)
      const provider = state.identity.provider;
      if (keysConfig && keysConfig[provider] === false) {
         setMissingKey(true);
      } else {
         setMissingKey(false);
      }
    }
    if (step < 9) setStep(step + 1);
  };

  const prevStep = () => {
    if (step > 1) setStep(step - 1);
  };

  const deployAgent = async () => {
    setDeploying(true);
    try {
      if (missingKey) {
        if (!inlineKey) throw new Error("Chave de API é obrigatória para este provedor.");
        setLoaderText("Salvando credencial de IA...");
        // Salva como credencial reutilizável (fonte única: aparece em Credenciais/IA).
        const credSaveResult: any = await apiPost("/api/credentials", {
          name: `${state.identity.provider} (Funcionário Fácil)`,
          type: "llm",
          provider: state.identity.provider,
          api_key: inlineKey,
        });
        if (credSaveResult?.id) {
          updateState("identity", "credentialId", credSaveResult.id);
        }
      }

      setLoaderText("Sintetizando Mega-Prompt via LLM...");
      
      let finalGuardrails = state.rag.guardrails;
      if (state.agenda.excludedDays.length > 0 || state.agenda.excludedDates.length > 0) {
         finalGuardrails += "\n\n=== REGRAS DE AGENDA (RESTRIÇÕES ABSOLUTAS) ===\n";
         if (state.agenda.excludedDays.length > 0) {
            finalGuardrails += `- DIAS DA SEMANA PROIBIDOS PARA AGENDAR: ${state.agenda.excludedDays.join(', ')}.\n`;
         }
         if (state.agenda.excludedDates.length > 0) {
            finalGuardrails += `- DATAS ESPECÍFICAS PROIBIDAS PARA AGENDAR: ${state.agenda.excludedDates.join(', ')}.\n`;
         }
         finalGuardrails += "Você está terminantemente proibido de oferecer, sugerir ou confirmar agendamentos nestes dias/datas sob qualquer circunstância.";
      }

      const refineRes: any = await apiPost("/api/agents/refine", {
         name: state.identity.name, role: state.identity.role, tone: state.behavior.tone,
         steps: state.behavior.steps, knowledge: state.rag.knowledge,
         guardrails: finalGuardrails, automations: state.automations
      });
      // O backend responde { refined_prompt }. Se vazio, cai pro prompt base montado.
      const finalPrompt = refineRes.refined_prompt || refineRes.refinedPrompt || finalGuardrails;
      setLoaderText("Injetando regras no banco de dados...");

      // extras: campos avançados do Funcionário Fácil que não têm coluna própria no
      // banco. O backend guarda como JSONB e os comportamentais entram no system prompt.
      const extras = {
         dualPersona: state.identity.dualPersona, dualPersonaRules: state.identity.dualPersonaRules,
         targetAudience: state.rag.targetAudience, objections: state.rag.objections,
         maxLength: state.rag.maxLength, dataToCollect: state.rag.dataToCollect, autoTrain: state.rag.autoTrain,
         salesPressure: state.behavior.salesPressure, maxDiscount: state.behavior.maxDiscount,
         empathyThermometer: state.behavior.empathyThermometer, hotLeadTagger: state.behavior.hotLeadTagger,
         splitMessages: state.behavior.splitMessages, humanTyping: state.behavior.humanTyping,
         typingSpeedMs: state.behavior.typingSpeedMs, audioCondition: state.behavior.audioCondition,
         copilotMode: state.behavior.copilotMode, dynamicMargin: state.behavior.dynamicMargin,
         kpi: state.behavior.kpi,
         // Grupo 1: toggles que antes morriam no navegador (não iam ao backend).
         useProfileName: state.behavior.useProfileName,
         validateProfileNameWithAI: state.behavior.validateProfileNameWithAI,
         knowLocalTime: state.behavior.knowLocalTime,
         simulateTypingStatus: state.behavior.simulateTypingStatus,
         listenAudio: state.behavior.listen_audio,
         // Grupo 2: criatividade (temperature) e motor de emergência (fallback) — antes
         // eram descartados; agora persistem no extras e o runtime aplica.
         temperature: state.behavior.temperature,
         fallbackProvider: state.identity.fallbackProvider,
         fallbackModel: state.identity.fallbackModel,
         fallbackCredentialId: state.identity.fallbackCredentialId,
         // Handoff avançado (antes descartado): número do admin pra ligação + método +
         // se pode ligar pro telefone do próprio contato/lead quando existir.
         handoffMethod: state.handoff.method,
         handoffAdminNumber: state.handoff.adminNumber,
         handoffToContact: state.handoff.toContact,
         callTriggers: state.handoff.callTriggers || [],
         ttsProvider: state.behavior.ttsProvider,
         ttsCredentialId: state.behavior.ttsCredentialId,
         backgroundNoise: state.behavior.backgroundNoise,
      };

      const payload = {
         name: state.identity.name, prompt: finalPrompt, ai_provider: state.identity.provider,
         ai_model: state.identity.model, temperature: state.behavior.temperature,
         instance_name: state.identity.instance || null, knowledge_base: state.rag.knowledge,
         guardrails: finalGuardrails, tone: state.behavior.tone, automations: state.automations,
         listen_audio: state.behavior.listen_audio, reply_audio: state.behavior.reply_audio,
         voice_id: state.behavior.voice_id, vision_enabled: state.behavior.vision_enabled,
         background_noise: state.behavior.backgroundNoise, background_noise_volume: state.behavior.backgroundNoise ? 0.15 : 0,
         escalation_keywords: state.handoff.keywords, handoff_message: state.handoff.message,
         handoff_method: state.handoff.method, handoff_agent: state.handoff.destAgent, handoff_notify: state.handoff.notifyTo,
         credential_id: state.identity.credentialId,
         outbound_only: state.behavior.outboundOnly,
         extras
      };

      if (editMode && initialProfile?.id) {
         // FIX (QA IA): antes ia pra POST /api/agent-profiles, que faz UPSERT de TODAS as
         // colunas com EXCLUDED — os ~30 campos omitidos (tts_default, wake_word, voz,
         // trigger_audio/offer_audio, background_noise, etc.) eram ZERADOS a cada edição, e o
         // `extras` (objeto JSON) fazia o decoder Go falhar em silêncio (campo string),
         // descartando os 30 campos avançados. O adaptador /api/agents/{id} CARREGA o perfil
         // existente e mescla só os campos do Lab, preservando o resto e aceitando extras como
         // objeto (json.RawMessage). `kind` precisa ir junto pois o adaptador o sobrescreve.
         await apiPost(`/api/agents/${initialProfile.id}`, {
            ...payload,
            kind: state.identity.channel,
         });
         toast.success("Configurações salvas com sucesso!");
         if (onSaved) onSaved();
      } else {
         const deployRes: any = await apiPost("/api/agents", payload);
         if (!deployRes.success) throw new Error(deployRes.error || "Falha no deploy.");
         toast.success("Agente instanciado com sucesso!");
         setTimeout(() => {
            // Se o wizard faz parte do fluxo encadeado (Configura → Funcionário → Gestor),
            // avança pra próxima aba. Senão, comportamento antigo: volta pra lista.
            if (onComplete) onComplete();
            else setView("specialized");
         }, 1500);
      }

    } catch (e: any) {
      const msg = e?.message || "";
      // BUG-1: o backend valida voz x gênero do nome (trava de UX anti-trote). Antes o
      // erro 500 cru assustava. Detecta esse caso e mostra mensagem clara + leva o
      // usuário de volta ao passo da voz pra corrigir sem adivinhar.
      if (/incompat|renomeie|voz feminina|voz masculina/i.test(msg)) {
        toast.error("A voz escolhida não combina com o nome do agente", {
          description: "Escolha uma voz do mesmo gênero do nome (ex.: voz feminina para nome feminino) ou ajuste o nome. Isso evita que a ligação pareça trote.",
          duration: 8000,
        });
        setStep(2);
      } else {
        // 409 = já existe um agente com esse nome: mostra a frase do servidor, sem o código.
        toast.error(apiErrorMessage(e, msg || "Erro durante o deploy."));
      }
    } finally {
      setDeploying(false);
    }
  };

  const handleMagicScrape = async () => {
    if (!magicUrl) return;
    if (!state.identity.credentialId) {
      toast.error("Escolha uma credencial de IA no Passo 2 antes de ler o site.");
      setStep(2);
      return;
    }
    setIsMagicScraping(true);
    setMagicStep(1); // lendo o site
    // pequeno avanço visual enquanto a requisição roda (é uma chamada só, mas mostra progresso)
    const t2 = setTimeout(() => setMagicStep(2), 1200); // extraindo ICP/dores
    const t3 = setTimeout(() => setMagicStep(3), 3000); // montando prompt
    const ok = await runAgentGeneration({ url: magicUrl });
    clearTimeout(t2); clearTimeout(t3);
    setIsMagicScraping(false);
    setMagicStep(0);
    if (ok) {
      setStep(4); // vai revisar o conhecimento/prompt gerado
      toast.success("Pronto! Extraí do site e distribuí nos campos. Revise abaixo.");
    }
  };

  return (
    <div className="relative max-w-7xl mx-auto py-8 flex flex-col xl:flex-row gap-8">
      {/* Neural Canvas Mock Effect */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-20 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/20 via-background to-background rounded-2xl" />

      {/* Main Wizard Column */}
      <div className="relative z-10 flex-1 space-y-12 animate-in fade-in duration-500">

        {/* Header */}
        {!editMode && (
          <div className="text-left space-y-2 mb-6">
            <h2 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-emerald-400 drop-shadow-sm flex items-center gap-3">
              <Rocket className="h-8 w-8 text-primary" /> Gerar Funcionário
            </h2>
            <p className="text-muted-foreground text-lg">Crie e configure seu funcionário através de um site ou preenchendo as opções abaixo.</p>
          </div>
        )}

        {/* Stepper Visual */}
        <div className="relative flex items-center justify-between mb-8 before:absolute before:top-1/2 before:left-0 before:w-full before:h-0.5 before:bg-border/50 before:-z-10 before:-translate-y-1/2">
           {/* Progress Line */}
           <div className="absolute top-1/2 left-0 h-0.5 bg-primary -z-10 -translate-y-1/2 transition-all duration-500" style={{ width: `${((step - 1) / 8) * 100}%` }} />
           
           {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((s) => (
             <div key={s} className={cn(
               "h-10 w-10 rounded-full border-2 flex items-center justify-center font-bold bg-background transition-all duration-300",
               step > s ? "bg-primary border-primary text-primary-foreground" : 
               step === s ? "border-primary text-primary shadow-[0_0_15px_rgba(59,130,246,0.4)]" : "border-border/50 text-muted-foreground"
             )}>
                {s === 9 ? <Rocket className="h-4 w-4" /> : s}
             </div>
           ))}
        </div>

        {/* Passo 1: Canal e Arquétipos */}
        <div className={cn("transition-all duration-500", step === 1 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft">
            <h3 className="text-2xl font-bold mb-2">1. Canal e Função (Arquétipo)</h3>
            <p className="text-muted-foreground mb-8">Defina onde este funcionário irá trabalhar e qual o seu objetivo principal.</p>
            
            <div className="mb-10">
              <h4 className="font-semibold text-lg mb-4 text-primary">A) Onde ele vai atender?</h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { id: "call", icon: Headset, title: "Só Ligação", desc: "Focado em voz com latência zero (sem RAG)." },
                  { id: "message", icon: MessageSquare, title: "Só Mensagens", desc: "WhatsApp, Texto, Imagens e Áudio." },
                  { id: "both", icon: Bot, title: "Ambos (Híbrido)", desc: "Atende ligação e WhatsApp." }
                ].map(chan => (
                  <div
                    key={chan.id}
                    onClick={() => updateState("identity", "channel", chan.id)}
                    className={cn(
                      "p-5 rounded-2xl border cursor-pointer transition-all hover:-translate-y-1 hover:shadow-lg flex flex-col items-center text-center gap-3",
                      state.identity.channel === chan.id ? "bg-primary/10 border-primary shadow-[0_0_15px_rgba(59,130,246,0.2)]" : "bg-black/10 border-border/50 hover:bg-black/20"
                    )}
                  >
                    <chan.icon className={cn("h-8 w-8", state.identity.channel === chan.id ? "text-primary" : "text-muted-foreground")} />
                    <div>
                      <h4 className="font-bold">{chan.title}</h4>
                      <p className="text-xs text-muted-foreground mt-1 leading-tight">{chan.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <h4 className="font-semibold text-lg mb-4 text-primary mt-8">B) Qual será a função dele? (Cognição Base)</h4>
            
            {["Vendas (B2B/B2C)", "Suporte e Retenção", "Operações Internas"].map((cat) => (
              <div key={cat} className="mb-6">
                <h5 className="font-bold text-sm text-muted-foreground uppercase tracking-wider mb-3">{cat}</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {ARCHETYPES.filter(a => a.category === cat).map((arch) => (
                    <div 
                      key={arch.id}
                      onClick={() => handleArchetypeSelect(arch)}
                      className={cn(
                        "p-5 rounded-2xl border cursor-pointer transition-all hover:border-primary flex flex-col items-start gap-3 bg-black/10 relative overflow-hidden group",
                        state.archetype === arch.id ? "border-primary bg-blue-500/10 ring-1 ring-inset ring-primary" : "border-border/50"
                      )}
                    >
                      <arch.icon className={cn("h-8 w-8 mb-1 transition-transform group-hover:scale-110", arch.color)} />
                      <div>
                        <h4 className="font-bold mb-1 text-md">{arch.title}</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">{arch.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </Card>
        </div>

        {/* Passo 2: Identidade */}
        <div className={cn("transition-all duration-500", step === 2 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
            <div>
              <h3 className="text-2xl font-bold mb-2">Identidade & Motor de IA</h3>
              <p className="text-muted-foreground">Defina quem o agente é e qual motor cognitivo o alimentará.</p>
            </div>
            
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 mb-6">
              <div className="flex flex-col items-center gap-2 shrink-0">
                <div className="h-24 w-24 rounded-full border-2 border-dashed border-border/50 bg-black/20 flex items-center justify-center overflow-hidden relative group cursor-pointer">
                  {state.identity.avatar ? (
                    <img src={state.identity.avatar} className="h-full w-full object-cover" />
                  ) : (
                    <Bot className="h-8 w-8 text-muted-foreground" />
                  )}
                  <div className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="text-xs font-semibold text-white">Mudar Foto</span>
                  </div>
                  <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" accept="image/*" onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      const reader = new FileReader();
                      reader.onload = (ev) => updateState("identity", "avatar", ev.target?.result);
                      reader.readAsDataURL(file);
                    }
                  }} />
                </div>
                {state.identity.credentialId && (
                  <Button variant="ghost" size="sm" className="text-xs text-primary mt-1 hover:bg-primary/10" onClick={() => {
                    toast.promise(new Promise(resolve => setTimeout(resolve, 2000)), {
                      loading: 'Gerando Avatar via IA...',
                      success: () => {
                         updateState("identity", "avatar", "https://i.pravatar.cc/150?img=" + Math.floor(Math.random() * 70));
                         return 'Avatar exclusivo gerado!';
                      },
                      error: 'Erro na geração'
                    });
                  }}>
                    <Sparkles className="h-3 w-3 mr-1" /> Gerar Rosto AI
                  </Button>
                )}
              </div>
              <div className="flex-1 w-full space-y-4">
                 <div className="space-y-2">
                    <label className="text-sm font-medium">Nome do Agente</label>
                    <Input value={state.identity.name} onChange={e => updateState("identity", "name", e.target.value)} placeholder="Ex: Emerson" className="h-12 bg-background/50 focus-visible:ring-primary" />
                 </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6">
               <div className="space-y-2">
                  <label className="text-sm font-medium">Papel Principal / Profissão</label>
                  <Input value={state.identity.role} onChange={e => updateState("identity", "role", e.target.value)} placeholder="Ex: Especialista em Fechamento B2B" className="h-12 bg-background/50 focus-visible:ring-primary" />
               </div>
            </div>

            <div className="p-4 bg-black/20 border border-border/50 rounded-xl space-y-4">
              <div className="flex items-center space-x-2">
                <Switch checked={state.identity.dualPersona} onCheckedChange={c => updateState("identity", "dualPersona", c)} />
                <label className="text-sm font-medium flex items-center gap-2">Dupla Personalidade (Turno Dia / Noite)</label>
              </div>
              {state.identity.dualPersona && (
                <div className="space-y-2 pt-2 animate-in fade-in slide-in-from-top-2">
                   <label className="text-xs font-semibold text-muted-foreground flex items-center gap-1"><SunMoon className="h-4 w-4 text-primary" /> Qual a diferença entre os turnos?</label>
                   <Input 
                     value={state.identity.dualPersonaRules} 
                     onChange={e => updateState("identity", "dualPersonaRules", e.target.value)} 
                     placeholder='Ex: "Dia: Atendente corporativo. Noite: Gírias e descontraído."' 
                     className="bg-background/50 h-10 border-primary/30 focus-visible:ring-primary" 
                   />
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                 <label className="text-sm font-medium">Credencial de IA</label>
                 <div className="flex gap-2">
                   <select className="flex flex-1 h-12 rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={state.identity.credentialId} onChange={e => {
                     const cid = e.target.value;
                     const c = credentials.find(x => x.id === cid);
                     updateState("identity", "credentialId", cid);
                     if (c) {
                       updateState("identity", "provider", c.provider);
                       // busca modelos REAIS dessa credencial (backend resolve a chave)
                       fetchModelsForCredential(c.provider, cid);
                     }
                   }}>
                      <option value="">Selecione a Credencial</option>
                      {credentials.map(c => <option key={c.id} value={c.id}>{c.name || c.label} ({c.provider})</option>)}
                   </select>
                   <Button variant="outline" className="h-12 px-3" onClick={handleTestKey} disabled={testingKey || !state.identity.credentialId} title="Testar a chave desta credencial">
                     {testingKey ? "..." : <><CheckCircle2 className="h-4 w-4" /> Testar</>}
                   </Button>
                   <Button variant="outline" className="h-12 px-3" onClick={() => setCredModalOpen(true)}>
                     <Plus className="h-4 w-4" /> Nova
                   </Button>
                 </div>
              </div>
              <div className="space-y-2">
                 <label className="text-sm font-medium flex items-center gap-2">Modelo Específico (Primário) {loadingModels && <span className="text-xs text-primary animate-pulse">buscando modelos...</span>}</label>
                 <div className="flex gap-2">
                   <select className="flex flex-1 h-12 rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={state.identity.model} onChange={e => updateState("identity", "model", e.target.value)}>
                      {modelsFor(state.identity.provider).map(m => (
                         <option key={m} value={m}>{m}</option>
                      ))}
                   </select>
                   <Button variant="outline" className="h-12 px-3" disabled={loadingModels || !state.identity.credentialId}
                     onClick={() => fetchModelsForCredential(state.identity.provider, state.identity.credentialId)}
                     title="Buscar a lista real de modelos direto da API da credencial selecionada">
                     {loadingModels ? "..." : <><RotateCcw className="h-4 w-4" /> Buscar</>}
                   </Button>
                 </div>
              </div>
            </div>

            {/* Fallback Engine */}
            <div className="p-4 bg-amber-500/5 border border-amber-500/20 rounded-xl space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                <h4 className="text-sm font-bold text-amber-500">Motor de Emergência (Fallback Automático)</h4>
              </div>
              <p className="text-xs text-muted-foreground">Se o modelo primário falhar ou cair, a IA assumirá este motor secundário sem interromper a chamada.</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                   <label className="text-xs font-medium text-muted-foreground">Provedor Secundário</label>
                   <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-xs shadow-sm focus-visible:ring-amber-500" value={state.identity.fallbackProvider} onChange={e => {
                     updateState("identity", "fallbackProvider", e.target.value);
                     updateState("identity", "fallbackModel", MODELS_BY_PROVIDER[e.target.value]?.[0] || "");
                     updateState("identity", "fallbackCredentialId", "");
                   }}>
                      {LLM_PROVIDERS.filter(p => p.value !== "custom").map(p => (
                         <option key={p.value} value={p.value}>{p.label}</option>
                      ))}
                   </select>
                </div>
                <div className="space-y-2">
                   <label className="text-xs font-medium text-muted-foreground">Credencial do Fallback</label>
                   <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-xs shadow-sm focus-visible:ring-amber-500" value={state.identity.fallbackCredentialId} onChange={e => updateState("identity", "fallbackCredentialId", e.target.value)}>
                      <option value="">Auto-detectar do cofre</option>
                      {credentials.filter(c => c.provider === state.identity.fallbackProvider).map(c => <option key={c.id} value={c.id}>{c.name || c.label} ({c.provider})</option>)}
                   </select>
                   {!state.identity.fallbackCredentialId && credentials.filter(c => c.provider === state.identity.fallbackProvider).length === 0 && (
                     <p className="text-[10px] text-amber-500 flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> Nenhuma credencial de {state.identity.fallbackProvider} no cofre — o fallback não funcionará.</p>
                   )}
                </div>
                <div className="space-y-2">
                   <label className="text-xs font-medium text-muted-foreground">Modelo Secundário</label>
                   <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-xs shadow-sm focus-visible:ring-amber-500" value={state.identity.fallbackModel} onChange={e => updateState("identity", "fallbackModel", e.target.value)}>
                      {modelsFor(state.identity.fallbackProvider)?.map(m => (
                         <option key={m} value={m}>{m}</option>
                      ))}
                   </select>
                </div>
              </div>
            </div>

            <div className="space-y-2 pt-4 border-t border-border/50">
               <label className="text-sm font-medium">Vincular Instância do WhatsApp (Opcional)</label>
               <select className="flex h-12 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={state.identity.instance} onChange={e => updateState("identity", "instance", e.target.value)}>
                  <option value="">Sem instância (Apenas Criação)</option>
                  {instances.map((i: any) => {
                     const num = i.jid ? i.jid.replace(/:.*/, "").replace(/@.*/, "") : "";
                     const status = i.connected ? "🟢" : i.paired ? "🟡" : "⚪";
                     const label = num ? `${status} ${i.name} — +${num}` : `${status} ${i.name}`;
                     return <option key={i.name} value={i.name}>{label}</option>;
                  })}
               </select>
            </div>
          </Card>
        </div>

        {/* Passo 3: Criação Mágica via Site */}
        <div className={cn("transition-all duration-500", step === 3 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-8">
            <div className="text-center mb-8">
              <h3 className="text-3xl font-extrabold mb-3 bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-400">Geração de Conhecimento Base</h3>
              <p className="text-muted-foreground text-lg">Para alimentar a memória do agente, escolha uma das 2 formas automáticas abaixo.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Opção 1: Via Site */}
              <Card className="p-6 rounded-2xl bg-gradient-to-br from-black/40 to-black/20 border border-primary/20 hover:border-primary/50 transition-colors flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <div className="bg-primary/20 p-3 rounded-xl"><Wand2 className="h-6 w-6 text-primary" /></div>
                  <h4 className="text-xl font-bold">1. Ler URL do Site</h4>
                </div>
                <p className="text-sm text-muted-foreground flex-1">A IA vai escanear seu site, extrair o ICP (público-alvo), mapear as dores e injetar as informações no RAG (Passo 4).</p>
                
                <div className="space-y-3 mt-4">
                  <Input 
                    placeholder="Ex: https://sua-empresa.com.br" 
                    value={magicUrl}
                    onChange={e => setMagicUrl(e.target.value)}
                    disabled={isMagicScraping}
                    className="bg-black/60 border-primary/30 h-12"
                  />
                  <Button 
                    onClick={handleMagicScrape} 
                    disabled={!magicUrl || isMagicScraping}
                    className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground font-bold"
                  >
                    {isMagicScraping ? "Escaneando..." : "Analisar Site"}
                  </Button>
                </div>
              </Card>

              {/* Opção 2: Descrever Manualmente */}
              <Card className="p-6 rounded-2xl bg-gradient-to-br from-black/40 to-black/20 border border-emerald-500/20 hover:border-emerald-500/50 transition-colors flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <div className="bg-emerald-500/20 p-3 rounded-xl"><Bot className="h-6 w-6 text-emerald-500" /></div>
                  <h4 className="text-xl font-bold">2. Descrever Negócio</h4>
                </div>
                <p className="text-sm text-muted-foreground flex-1">Responda 3 perguntas simples e a IA redigirá toda a estrutura comercial e comportamental por você.</p>
                
                <div className="flex items-end mt-4">
                  <Button 
                    onClick={() => setMagicModalOpen(true)} 
                    className="w-full h-12 bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                  >
                    Preencher Formulário Mágico
                  </Button>
                </div>
              </Card>
              
            </div>
            
            {/* Loading Steps Centralizado */}
            {isMagicScraping && (
              <div className="bg-primary/10 p-4 rounded-xl border border-primary/20 flex flex-col md:flex-row items-center justify-center gap-6 animate-in fade-in">
                <div className={cn("text-sm font-bold transition-all", magicStep >= 1 ? "text-primary" : "text-muted-foreground")}>1. Lendo Páginas...</div>
                <div className={cn("text-sm font-bold transition-all", magicStep >= 2 ? "text-primary" : "text-muted-foreground")}>2. Extraindo Dores...</div>
                <div className={cn("text-sm font-bold transition-all", magicStep >= 3 ? "text-primary" : "text-muted-foreground")}>3. Moldando RAG...</div>
              </div>
            )}

            <div className="flex justify-center pt-6 border-t border-border/50">
              <Button variant="ghost" onClick={nextStep} className="text-muted-foreground hover:text-white">
                Ignorar automação e configurar RAG manualmente (Apenas DEV) <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </Card>
        </div>

        {/* Passo 4: RAG & Prompt Estruturado */}
        <div className={cn("transition-all duration-500", step === 4 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
            <div>
              <h3 className="text-2xl font-bold mb-2">Cérebro do Agente (Prompt & Conhecimento)</h3>
              <p className="text-muted-foreground">Modele a personalidade, o funil e injete a base de conhecimento (RAG).</p>
            </div>

            {state.identity.channel === 'call' ? (
              <div className="p-6 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                 <p className="text-blue-400 font-medium text-center">Agentes exclusivos de ligação (Voz) não utilizam RAG local nesta versão. O conhecimento é inferido diretamente no Mega-Prompt e no motor LLM.</p>
              </div>
            ) : (
              <div className="space-y-8">
                {/* Diretrizes de Comportamento */}
                <div className="space-y-4 p-5 bg-background/50 border border-border/50 rounded-xl">
                   <div className="border-b border-border/50 pb-2 mb-4">
                     <h4 className="text-lg font-bold flex items-center gap-2"><Bot className="h-5 w-5 text-primary"/> Comportamento e Prompt Principal</h4>
                     <p className="text-xs text-muted-foreground mt-1">Essas são as regras de ouro. O Agente sempre dará mais peso ao que estiver configurado aqui.</p>
                   </div>

                   <div className="space-y-3">
                     <div className="flex flex-col gap-1">
                       <label className="text-sm font-medium">Radar de Personalidade (Tom de Voz)</label>
                     </div>
                     <div className="flex flex-wrap gap-2 mb-2">
                       {["Empático", "Insistente (Closer)", "Sarcástico", "Técnico/Formal", "Jovem/Descolado", "Educado", "Incisivo", "Conciso"].map(trait => {
                         const isSelected = state.behavior.tone === trait;
                         return (
                           <Badge 
                             key={trait} 
                             variant="outline" 
                             className={cn("cursor-pointer hover:bg-primary/20", isSelected ? "bg-primary text-primary-foreground border-primary" : "bg-background/50 text-muted-foreground border-border/50")}
                             onClick={() => updateState("behavior", "tone", trait)}
                           >
                             {trait}
                           </Badge>
                         );
                       })}
                     </div>
                     <Input 
                       placeholder="Ou digite o tom manualmente..." 
                       value={state.behavior.tone} 
                       onChange={e => updateState("behavior", "tone", e.target.value)}
                       className="bg-background h-10 border-primary/30 focus-visible:ring-primary"
                     />
                   </div>

                   <div className="space-y-2 pt-2">
                     <label className="text-sm font-medium">Etapas de Atendimento / Funil</label>
                     <p className="text-[10px] text-muted-foreground">Como o agente deve conduzir a conversa (Passo 1, Passo 2...)</p>
                     <Textarea 
                        value={state.behavior.steps} 
                        onChange={e => updateState("behavior", "steps", e.target.value)}
                        placeholder="Exemplo:&#10;1. Saudação acolhedora e identificação da dor.&#10;2. Qualificação.&#10;3. Chamada para a Ação." 
                        className="min-h-[100px] bg-background focus-visible:ring-primary" 
                     />
                   </div>

                   <div className="space-y-2 pt-2 pb-2">
                     <label className="text-sm font-medium flex items-center gap-2"><Rocket className="h-4 w-4 text-emerald-500" /> Meta Principal (KPI Alvo)</label>
                     <select className="flex h-12 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" value={state.behavior.kpi} onChange={e => updateState("behavior", "kpi", e.target.value)}>
                        <option value="">Nenhuma meta definida (Conversa livre)</option>
                        <option value="Agendar uma reunião/visita">🎯 Agendar uma Reunião/Visita</option>
                        <option value="Emitir segunda via de boleto/PIX">💰 Fechar Acordo de Pagamento/PIX</option>
                        <option value="Resolver o chamado no primeiro contato">🛠️ Resolver Ticket/Chamado (FCR)</option>
                        <option value="Qualificar perfil (Orçamento e Prazo)">📋 Qualificar Lead (Orçamento e Prazo)</option>
                     </select>
                   </div>
                   
                   <div className="space-y-2">
                      <label className="text-sm font-medium text-destructive flex items-center gap-2">Guardrails Absolutos (Restrições)</label>
                      <p className="text-[10px] text-muted-foreground">Regras que o agente NUNCA deve quebrar (Ex: Não prometer devolução, Não dar desconto maior que X%).</p>
                      <Textarea 
                         value={state.rag.guardrails || ""} 
                         onChange={e => updateState("rag", "guardrails", e.target.value)}
                         placeholder="Exemplo:&#10;1. Nunca mencione plataformas concorrentes.&#10;2. Não ofereça descontos." 
                         className="min-h-[80px] bg-destructive/5 border-destructive/30 focus-visible:ring-destructive" 
                      />
                   </div>
                </div>

                {/* Base de Conhecimento Manual */}
                <div className="space-y-4 p-5 bg-background/50 border border-border/50 rounded-xl">
                   <div className="border-b border-border/50 pb-2 mb-4">
                     <h4 className="text-lg font-bold flex items-center gap-2"><FileText className="h-5 w-5 text-emerald-500"/> Conhecimento Estático (Normal)</h4>
                     <p className="text-xs text-muted-foreground mt-1">Conhecimento fixo que é injetado diretamente no prompt (Texto, Preços, Regras). Gasta tokens em cada mensagem.</p>
                   </div>
                   
                   <div className="space-y-2">
                      <label className="text-sm font-medium">Público-Alvo (Quem o agente atende?)</label>
                      <Input 
                         value={state.rag.targetAudience || ""} 
                         onChange={e => updateState("rag", "targetAudience", e.target.value)}
                         placeholder="Ex: Clientes de 20-35 anos, mães, donos de pequenas empresas..." 
                         className="bg-background h-10" 
                      />
                   </div>

                   <div className="space-y-2 pt-2">
                      <div className="flex justify-between items-center">
                        <label className="text-sm font-medium">Textos Base e FAQs (Manual)</label>
                        <span className="text-xs text-muted-foreground font-mono bg-muted px-2 py-0.5 rounded">Tokens Est.: {Math.round((state.rag.knowledge?.length || 0) / 4)}</span>
                      </div>
                      <Textarea 
                         value={state.rag.knowledge || ""} 
                         onChange={e => updateState("rag", "knowledge", e.target.value)}
                         placeholder="Exemplo:&#10;A Empresa X vende a plataforma Y.&#10;O plano básico custa R$ 199." 
                         className="min-h-[120px] bg-background focus-visible:ring-primary" 
                      />
                   </div>

                   <div className="space-y-2 pt-2">
                      <label className="text-sm font-medium">Tratamento de Objeções Comuns</label>
                      <p className="text-[10px] text-muted-foreground">Como rebater as principais desculpas do cliente ("Tá caro", "Vou pensar").</p>
                      <Textarea 
                         value={state.rag.objections || ""} 
                         onChange={e => updateState("rag", "objections", e.target.value)}
                         placeholder="Exemplo:&#10;- Se disser 'Está caro', diga que a qualidade compensa e parcele em 12x.&#10;- Se quiser pensar, crie senso de urgência." 
                         className="min-h-[100px] bg-background focus-visible:ring-primary" 
                      />
                   </div>

                   {/* Custom RAG Limits & Data Collection */}
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 mt-4 border-t border-border/50">
                      <div className="space-y-3">
                        <label className="text-sm font-medium text-emerald-500 flex items-center gap-2"><Database className="h-4 w-4"/> Formulário de Coleta Dinâmico</label>
                        <p className="text-[10px] text-muted-foreground leading-tight">Quais perguntas o agente deve fazer ao lead para extrair dados?</p>
                        <Textarea 
                          value={state.rag.dataToCollect || ""} 
                          onChange={e => updateState("rag", "dataToCollect", e.target.value)} 
                          placeholder="Ex: Qual o seu Nome? Qual o seu E-mail? Qual o tamanho da sua empresa?" 
                          className="min-h-[60px] bg-background/50 border-emerald-500/20 focus-visible:ring-emerald-500/50 mt-1" 
                        />
                        <div className="flex flex-col gap-2 mt-2">
                           <p className="text-[11px] font-semibold text-amber-600">Em breve: estas duas opções ainda não são gravadas.</p>
                           <div className="flex items-center space-x-2">
                             <Switch 
                               checked={state.rag.extractToForm} 
                               onCheckedChange={c => updateState("rag", "extractToForm", c)} 
                             />
                             <label className="text-[11px] font-medium leading-none">
                               Preencher painel CRM com essas respostas
                             </label>
                           </div>
                           <div className="flex items-center space-x-2">
                             <Switch 
                               checked={state.rag.mandatoryCollection} 
                               onCheckedChange={c => updateState("rag", "mandatoryCollection", c)} 
                               disabled={!state.rag.extractToForm}
                             />
                             <label className={cn("text-[11px] font-medium leading-none", !state.rag.extractToForm && "opacity-50")}>
                               Tornar perguntas obrigatórias (trava o funil)
                             </label>
                           </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-sky-500 flex items-center gap-2"><AlignLeft className="h-4 w-4"/> Tamanho Máximo da Resposta</label>
                        <p className="text-[10px] text-muted-foreground">O agente não ultrapassará esse número de caracteres. 0 = Ilimitado.</p>
                        <div className="flex items-center gap-4 mt-4 bg-background/50 p-4 rounded-xl border border-border/50">
                          <Slider 
                            value={[state.rag.maxLength || 0]} 
                            min={0} max={1000} step={50}
                            className="flex-1"
                            onValueChange={v => updateState("rag", "maxLength", v[0])}
                          />
                          <span className="text-xs font-mono bg-background px-3 py-1.5 rounded-md w-24 text-center border border-border/50">{state.rag.maxLength ? `${state.rag.maxLength} chars` : 'Ilimitado'}</span>
                        </div>
                      </div>
                   </div>
                 </div>

                {/* RAG Dinâmico */}
                <div className="space-y-4 p-5 bg-background/50 border border-border/50 rounded-xl">
                   <div className="border-b border-border/50 pb-2 mb-4">
                     <h4 className="text-lg font-bold flex items-center gap-2"><Database className="h-5 w-5 text-sky-500"/> Conhecimento Dinâmico (RAG)</h4>
                     <p className="text-xs text-muted-foreground mt-1">O Agente vai <strong>pesquisar</strong> nestas fontes automaticamente só quando precisar. Bom para textos longos e catálogos (economiza tokens).</p>
                   </div>
                   
                   <div className="flex flex-col sm:flex-row gap-3 pt-2">
                     <div className="relative flex-1">
                       <Input 
                         type="file" 
                         className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
                         onChange={(e) => {
                           const f = e.target.files?.[0];
                           if (!f) return;
                           const nm = f.name.toLowerCase();
                           // Texto: lê o conteúdo REAL e injeta no conhecimento (antes era
                           // placeholder fake). PDF/binário: só é vetorizado de verdade no
                           // painel de RAG do agente (upload multipart real, extrai PDF no backend).
                           if (/\.(txt|md|csv|json)$/.test(nm)) {
                             const rd = new FileReader();
                             rd.onload = () => {
                               const txt = String(rd.result || "").trim();
                               if (txt) {
                                 updateState("rag", "knowledge", (state.rag.knowledge || "") + `\n\n=== ${f.name} ===\n${txt}`);
                                 toast.success(`"${f.name}" adicionado ao conhecimento.`);
                               }
                             };
                             rd.readAsText(f);
                           } else {
                             toast.info("PDF/documento: crie o agente e suba o arquivo na aba 'Conhecimento (RAG)' do agente — lá o PDF é extraído e vetorizado de verdade.");
                           }
                         }}
                         accept=".pdf,.txt,.md,.csv,.json"
                       />
                       <Button variant="outline" className="w-full h-12 text-sm border-dashed gap-2 hover:border-sky-500 hover:text-sky-500 hover:bg-sky-500/5">
                         <FileText className="h-5 w-5" /> Adicionar PDF / Documento
                       </Button>
                     </div>

                     <Button variant="outline" className="flex-1 h-12 text-sm border-dashed gap-2 hover:border-sky-500 hover:text-sky-500 hover:bg-sky-500/5" onClick={async () => {
                        const url = prompt("Digite a URL do site (Ex: www.minhaloja.com.br):");
                        if (!url) return;
                        // REAL: usa o mesmo leitor de site do gerador (fetchSiteText no backend),
                        // que baixa o texto visível da página e adapta ao agente. Injeta no
                        // conhecimento de verdade (antes era setTimeout com placeholder).
                        setIsMagicScraping(true);
                        toast.info("Lendo o site...");
                        try {
                          const res: any = await apiPost("/api/agents/generate", {
                            site_url: url.startsWith("http") ? url : "https://" + url,
                            provider: state.identity.provider, model: state.identity.model,
                            credential_id: state.identity.credentialId, archetype: state.archetype,
                          });
                          const d = res.data || {};
                          const add = [d.knowledge, d.objections].filter(Boolean).join("\n");
                          if (add.trim()) {
                            updateState("rag", "knowledge", (state.rag.knowledge || "") + `\n\n=== SITE: ${url} ===\n${add}`);
                            toast.success("Conteúdo do site adicionado ao conhecimento.");
                          } else {
                            toast.error("Não consegui extrair conteúdo desse site.");
                          }
                        } catch (e: any) {
                          toast.error("Erro ao ler o site", { description: e.message });
                        } finally {
                          setIsMagicScraping(false);
                        }
                     }}>
                       <LinkIcon className="h-5 w-5" /> Sincronizar Site / Loja
                     </Button>
                   </div>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Passo 5: Cognição */}
        <div className={cn("transition-all duration-500", step === 5 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
            <div>
              <h3 className="text-2xl font-bold mb-2">Habilidades e Ajuste Fino</h3>
              <p className="text-muted-foreground">Ligue módulos de visão, áudio e calibre a criatividade e empatia.</p>
            </div>

            <div className="flex flex-wrap gap-6 mb-6 p-4 rounded-xl border border-border/50 bg-background/30">
               <div className="flex items-center space-x-2">
                 <Switch checked={state.behavior.listen_audio} onCheckedChange={c => updateState("behavior", "listen_audio", c)} />
                 <label className="text-sm font-medium flex items-center gap-2"><Mic className="h-4 w-4"/> Ouvir Áudios (Whisper)</label>
                 {/* Whisper (STT) e credenciais de voz são globais: atalho direto pra aba (relato #14). */}
                 <button type="button" onClick={() => openSettingsTab("voice")} className="text-xs text-sky-400 hover:underline ml-1">Configurar Voz &amp; Whisper</button>
               </div>
               <div className="flex items-center space-x-2">
                 <Switch checked={state.behavior.reply_audio} onCheckedChange={c => updateState("behavior", "reply_audio", c)} />
                 <label className="text-sm font-medium flex items-center gap-2"><Volume2 className="h-4 w-4"/> Responder com Voz (TTS)</label>
               </div>
               <div className="flex items-center space-x-2">
                 <Switch checked={state.behavior.vision_enabled} onCheckedChange={c => updateState("behavior", "vision_enabled", c)} />
                 <label className="text-sm font-medium flex items-center gap-2"><Brain className="h-4 w-4"/> Ler Imagens (Visão)</label>
               </div>
               <div className="flex items-center space-x-2">
                 <Switch checked={state.behavior.hotLeadTagger} onCheckedChange={c => updateState("behavior", "hotLeadTagger", c)} />
                 <label className="text-sm font-medium flex items-center gap-2"><ShieldAlert className="h-4 w-4 text-orange-500"/> Etiquetar Leads Automaticamente (🔥)</label>
               </div>
               <div className="flex items-center space-x-2" title="Extrai o nome público do WhatsApp do cliente e já utiliza na conversa como variável.">
                 <Switch checked={state.behavior.useProfileName} onCheckedChange={c => updateState("behavior", "useProfileName", c)} />
                 <label className="text-sm font-medium flex items-center gap-2"><Database className="h-4 w-4 text-indigo-400"/> Extrair e Usar Nome do Perfil</label>
               </div>
               <div className="flex items-center space-x-2" title="Usa a IA para validar se o nome do perfil é de fato um nome de pessoa (evitando chamar alguém de 'Vendas iPhone' ou emojis). Gasta tokens.">
                 <Switch checked={state.behavior.validateProfileNameWithAI} onCheckedChange={c => updateState("behavior", "validateProfileNameWithAI", c)} />
                 <label className="text-sm font-medium flex items-center gap-2"><Brain className="h-4 w-4 text-violet-400"/> Validar Nome com IA (Anti-spam)</label>
               </div>
               <div className="flex items-center space-x-2" title="O agente saberá a data e hora exata para poder dizer bom dia/boa tarde ou validar horários comerciais.">
                 <Switch checked={state.behavior.knowLocalTime} onCheckedChange={c => updateState("behavior", "knowLocalTime", c)} />
                 <label className="text-sm font-medium flex items-center gap-2"><Clock className="h-4 w-4 text-sky-400"/> Acesso a Data e Hora</label>
               </div>
               <div className="flex items-center space-x-2" title="LIGADO: responde qualquer pessoa que mandar mensagem (padrão). DESLIGADO... na verdade este atalho: se ligar, o agente SÓ responde números que o Hermes já ligou antes (útil pra campanhas outbound). Por padrão fica desligado = atende todo mundo.">
                 <Switch checked={state.behavior.outboundOnly} onCheckedChange={c => updateState("behavior", "outboundOnly", c)} />
                 <label className="text-sm font-medium flex items-center gap-2"><Filter className="h-4 w-4 text-amber-400"/> Responder só quem eu já liguei</label>
               </div>
               <div className="flex flex-col space-y-2 w-full mt-2 border-t border-border/30 pt-4">
                   <div className="flex flex-wrap items-center gap-6">
                     <div className="flex items-center space-x-2">
                       <Switch checked={state.behavior.simulateTypingStatus} onCheckedChange={c => updateState("behavior", "simulateTypingStatus", c)} />
                       <label className="text-sm font-medium flex items-center gap-2"><Bot className="h-4 w-4 text-violet-400"/> Mostrar Status "Digitando..." no WhatsApp</label>
                     </div>
                     <div className="flex items-center space-x-2">
                       <Switch checked={state.behavior.humanTyping} onCheckedChange={c => updateState("behavior", "humanTyping", c)} />
                       <label className="text-sm font-medium flex items-center gap-2"><Bot className="h-4 w-4 text-violet-400"/> Atraso Inteligente (Tempo de Digitação Humana)</label>
                     </div>
                   </div>
                   
                   {state.behavior.humanTyping && (
                     <div className="pl-6 pt-2 space-y-4 animate-in fade-in slide-in-from-top-1 border-l-2 border-violet-500/20 ml-2">
                       <div>
                         <label className="text-xs font-semibold text-muted-foreground flex justify-between">
                           <span>Velocidade de Digitação (ms por caractere)</span>
                         </label>
                         <div className="flex items-center gap-4 mt-2">
                           <Slider 
                             value={[state.behavior.typingSpeedMs || 50]} 
                             min={10} max={200} step={10}
                             className="flex-1"
                             onValueChange={v => updateState("behavior", "typingSpeedMs", v[0])}
                           />
                           <Input 
                             type="number" 
                             value={state.behavior.typingSpeedMs || 50} 
                             onChange={e => updateState("behavior", "typingSpeedMs", Number(e.target.value))} 
                             className="w-24 h-9 bg-background font-mono text-violet-400 text-center" 
                           />
                           <span className="text-xs text-muted-foreground">ms/char</span>
                         </div>
                       </div>
                       <div className="flex items-center space-x-2 bg-black/10 p-2 rounded-lg border border-border/30">
                         <Switch checked={state.behavior.splitMessages} onCheckedChange={c => updateState("behavior", "splitMessages", c)} className="data-[state=checked]:bg-violet-500 scale-75" />
                         <label className="text-xs font-medium text-foreground">Dividir textões em múltiplas mensagens de WhatsApp (sempre que houver quebra de linha dupla)</label>
                       </div>
                     </div>
                   )}
                 </div>
            </div>

             <div className="flex items-start space-x-3 bg-indigo-500/10 border border-indigo-500/20 p-4 rounded-xl">
               <Switch 
                 checked={state.rag.autoTrain} 
                 onCheckedChange={c => updateState("rag", "autoTrain", c)} 
                 className="mt-0.5 data-[state=checked]:bg-indigo-500" 
               />
               <div>
                 <label className="text-sm font-bold text-indigo-400 flex items-center gap-2">
                   <Brain className="h-4 w-4" /> Auto-Treinamento de Sucesso (RAG Refletivo)
                 </label>
                 <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                   Sempre que este agente conseguir converter uma venda ou agendamento, ele salvará automaticamente o argumento matador (Golden Argument) na memória para usar com futuros clientes parecidos.
                 </p>
               </div>
             </div>

            <div className="flex items-start gap-3 p-3 bg-amber-500/10 border border-amber-500/20 text-amber-500/90 rounded-lg text-xs font-medium animate-in fade-in">
               <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
               <p>Aviso: Ativar recursos avançados (Ouvir Áudios, Visão, Termômetro Anti-Crise) adicionará complexidade à cognição da IA e consumirá consideravelmente <strong>mais tokens</strong> a cada interação.</p>
            </div>

            <div className="p-4 bg-black/20 border border-border/50 rounded-xl space-y-4">
              <div className="flex flex-col space-y-4">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium flex items-center gap-2">Termômetro de Empatia Sensorial (Anti-Crise)</label>
                  <span className="text-xs font-bold bg-primary/20 text-primary px-2 py-1 rounded-md">{state.behavior.empathyThermometer}%</span>
                </div>
                
                <Slider 
                  min={0} max={100} step={1}
                  value={[state.behavior.empathyThermometer]}
                  onValueChange={v => updateState("behavior", "empathyThermometer", v[0])}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground font-medium px-1">
                  <span>Frio/Sério</span>
                  <span>Equilibrado</span>
                  <span>Caloroso/Emojis</span>
                </div>
              </div>
              
              <div className="space-y-3 pt-2 animate-in fade-in slide-in-from-top-2 border-t border-border/30">
                 <p className="text-xs text-muted-foreground">Exemplo de abertura baseada no termômetro em {state.behavior.empathyThermometer}%:</p>
                 
                 <div className="space-y-2">
                   {state.behavior.empathyThermometer > 60 ? (
                     <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg animate-in fade-in">
                       <span className="text-xs font-bold text-emerald-500 block mb-1">Tom Altamente Receptivo:</span>
                       <span className="text-sm text-foreground">"Oi! Tudo ótimo por aqui! Como posso ajudar você hoje? 😊🚀 Vamos resolver juntos!"</span>
                     </div>
                   ) : state.behavior.empathyThermometer < 40 ? (
                     <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg animate-in fade-in">
                       <span className="text-xs font-bold text-rose-500 block mb-1">Tom Sério / Solene:</span>
                       <span className="text-sm text-foreground">"Olá. Compreendo a situação reportada. Por favor, informe os detalhes para darmos continuidade."</span>
                     </div>
                   ) : (
                     <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg animate-in fade-in">
                       <span className="text-xs font-bold text-blue-500 block mb-1">Tom Equilibrado:</span>
                       <span className="text-sm text-foreground">"Olá! Entendo a situação. Vamos resolver isso agora mesmo. Como posso te ajudar?"</span>
                     </div>
                   )}
                 </div>
              </div>
            </div>

            {state.behavior.reply_audio && (
              <div className="space-y-4 animate-in fade-in bg-black/20 p-5 rounded-xl border border-border/50">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2"><Mic className="h-4 w-4 text-violet-400"/> Provedor TTS</label>
                    <select className="flex h-12 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1" value={state.behavior.ttsProvider} onChange={e => {
                      const prov = e.target.value;
                      updateState("behavior", "ttsProvider", prov);
                      if (prov === "edge-tts" || prov === "piper") {
                        updateState("behavior", "ttsCredentialId", "");
                        if (prov === "edge-tts" && !state.behavior.voice_id?.includes("Neural")) {
                          updateState("behavior", "voice_id", "pt-BR-FranciscaNeural");
                        }
                        if (prov === "piper") {
                          updateState("behavior", "voice_id", "faber");
                        }
                      }
                    }}>
                      {TTS_PROVIDERS_LIST.map(p => (
                         <option key={p.value} value={p.value}>{p.label}</option>
                      ))}
                    </select>
                    <p className="text-[11px] text-muted-foreground mt-1">Edge TTS e Piper são grátis. ElevenLabs/Gemini/OpenAI usam credencial.</p>
                  </div>

                  {state.behavior.ttsProvider !== "edge-tts" && state.behavior.ttsProvider !== "piper" && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium flex items-center gap-2"><Key className="h-4 w-4 text-amber-400"/> Credencial TTS</label>
                      <CredentialSelect
                        type="tts"
                        value={state.behavior.ttsCredentialId}
                        onChange={(id) => updateState("behavior", "ttsCredentialId", id)}
                        emptyLabel="— Nenhuma (usa config global) —"
                      />
                      <p className="text-[11px] text-muted-foreground mt-1">Selecione a credencial do provedor de voz. Cadastre em 🔑 Credenciais.</p>
                    </div>
                  )}

                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2"><Volume2 className="h-4 w-4 text-primary"/> Voz da IA</label>
                    {state.behavior.ttsProvider === "piper" ? (
                      <select className="flex h-12 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1" value={state.behavior.voice_id} onChange={e => updateState("behavior", "voice_id", e.target.value)}>
                        <option value="faber">Faber — masculina (pt-BR) · padrão</option>
                        <option value="jeff">Jeff — masculina (pt-BR)</option>
                        <option value="cadu">Cadu — masculina (pt-BR)</option>
                      </select>
                    ) : state.behavior.ttsProvider === "edge-tts" ? (
                      <select className="flex h-12 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1" value={state.behavior.voice_id} onChange={e => updateState("behavior", "voice_id", e.target.value)}>
                        <option value="pt-BR-FranciscaNeural">Francisca (Feminino, padrão BR)</option>
                        <option value="pt-BR-AntonioNeural">Antonio (Masculino, BR grave)</option>
                        <option value="pt-BR-ThalitaNeural">Thalita (Feminino, BR jovem)</option>
                        <option value="en-US-AriaNeural">Aria (Feminino, EN)</option>
                        <option value="en-US-GuyNeural">Guy (Masculino, EN)</option>
                        <option value="es-ES-ElviraNeural">Elvira (Feminino, ES)</option>
                      </select>
                    ) : (
                      <Input
                        className="h-12 bg-background/50"
                        value={state.behavior.voice_id}
                        onChange={e => updateState("behavior", "voice_id", e.target.value)}
                        placeholder={
                          state.behavior.ttsProvider === "elevenlabs" ? "ID da voz (ex: EXAVITQu4vr4xnSDxMaL)" :
                          state.behavior.ttsProvider === "gemini" ? "Nome da voz (ex: Fenrir)" :
                          "Nome da voz (ex: alloy)"
                        }
                      />
                    )}
                    <p className="text-[11px] text-muted-foreground mt-1">
                      {state.behavior.ttsProvider === "edge-tts" || state.behavior.ttsProvider === "piper"
                        ? "Voz grátis, sem chave necessária."
                        : "Cole o ID/nome da voz do provedor escolhido."}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2"><Bot className="h-4 w-4 text-sky-400"/> Quando responder em Áudio?</label>
                    <select className="flex h-12 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1" value={state.behavior.audioCondition || "never"} onChange={e => updateState("behavior", "audioCondition", e.target.value)}>
                      <option value="never">Nunca (Apenas Configurado no Perfil)</option>
                      <option value="always">Sempre responder com áudio no WhatsApp</option>
                      <option value="when_audio">Apenas se o cliente mandar áudio</option>
                      <option value="long_text">Apenas para explicações longas (&gt; 500 chars)</option>
                    </select>
                  </div>
                </div>

                
              </div>
            )}

            <div className="space-y-2 mt-4">
              <label className="text-sm font-medium flex items-center gap-2"><Volume2 className="h-4 w-4 text-emerald-400"/> Fundo Sonoro (Ambiente da Ligação)</label>
              <select className="flex h-12 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1" value={state.behavior.backgroundNoise || ""} onChange={e => updateState("behavior", "backgroundNoise", e.target.value)}>
                <option value="">Sem fundo sonoro</option>
                <option value="office">🏢 Escritório (Teclados, Telefones)</option>
                <option value="call_center">📞 Call Center (Conversas, Digitação)</option>
                <option value="coffee_shop">☕ Cafeteria (Conversas abafadas)</option>
                <option value="street">🛣️ Rua (Trânsito sutil)</option>
                <option value="car">🚗 Carro (Motor, Trânsito)</option>
                <option value="park">🌳 Parque (Pássaros, Natureza)</option>
                <option value="bus">🚌 Ônibus (Motor, Pessoas)</option>
                <option value="airport">✈️ Aeroporto (Anúncios, Multidão)</option>
                <option value="restaurant">🍽️ Restaurante (Talheres, Conversa)</option>
              </select>
              {state.behavior.backgroundNoise && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-2 gap-2"
                  onClick={toggleBgPreview}
                >
                  {bgPlaying ? <Square className="h-3 w-3" /> : <Play className="h-3 w-3" />}
                  {bgPlaying ? "Parar" : "Ouvir Preview"}
                </Button>
              )}
              <p className="text-[11px] text-muted-foreground mt-1">Som ambiente que toca durante a ligação para torná-la mais natural.</p>
            </div>



            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-4">
               <div className="space-y-4">
                  <label className="text-sm font-medium flex justify-between">
                    <span>Criatividade (Temp)</span>
                    <span className="font-bold text-primary">{state.behavior.temperature}</span>
                  </label>
                  <Slider 
                     value={[state.behavior.temperature]} 
                     min={0} max={1} step={0.1}
                     onValueChange={v => updateState("behavior", "temperature", v[0])}
                  />
                  <p className="text-[10px] text-muted-foreground">0 = Robótico, 1 = Criativo</p>
               </div>
               
               <div className="space-y-4">
                  <label className="text-sm font-medium flex justify-between">
                    <span>Insistência (Vendas)</span>
                    <span className={cn("font-bold", state.behavior.salesPressure > 7 ? "text-rose-500" : state.behavior.salesPressure > 4 ? "text-amber-500" : "text-emerald-500")}>{state.behavior.salesPressure}/10</span>
                  </label>
                  <Slider 
                     value={[state.behavior.salesPressure]} 
                     min={0} max={10} step={1}
                     onValueChange={v => updateState("behavior", "salesPressure", v[0])}
                  />
                  <p className="text-[10px] text-muted-foreground">
                    {state.behavior.salesPressure < 4 ? "Consultivo" : state.behavior.salesPressure < 8 ? "Pró-ativo" : "Lobo de Wall Street"}
                  </p>
               </div>

               <div className="space-y-4">
                  <label className="text-sm font-medium flex justify-between">
                    <span>Desconto Máx.</span>
                    <span className={cn("font-bold", state.behavior.maxDiscount > 15 ? "text-rose-500" : state.behavior.maxDiscount > 0 ? "text-amber-500" : "text-emerald-500")}>{state.behavior.maxDiscount}%</span>
                  </label>
                  <Slider 
                     value={[state.behavior.maxDiscount]} 
                     min={0} max={50} step={1}
                     onValueChange={v => updateState("behavior", "maxDiscount", v[0])}
                  />
                  <p className="text-[10px] text-muted-foreground">
                    {state.behavior.maxDiscount === 0 
                      ? "Sem desconto." 
                      : `Regra: Ofereça máx ${state.behavior.maxDiscount}%, mas escale aos poucos.`}
                  </p>
               </div>
            </div>
            {/* Arquétipos de venda (ids reais em ARCHETYPES; antes comparava com "sales" dentro de
                identity, que não existe, e a seção nunca aparecia). */}
            {["vendas", "sdr_b2b", "qualificador_inbound", "reativacao"].includes(state.archetype ?? "") && (
              <div className="space-y-4 pt-4 border-t border-border/50 animate-in fade-in">
                 <h4 className="font-bold flex items-center gap-2"><Briefcase className="h-5 w-5 text-primary" /> Catálogo / Produtos de Venda</h4>
                 <p className="text-xs text-muted-foreground">Descreva brevemente os produtos, preços ou planos que o agente pode oferecer na negociação.</p>
                 <Textarea 
                    value={state.rag.knowledge} // For simplicity, we append to RAG or maybe just use RAG directly here
                    onChange={e => updateState("rag", "knowledge", e.target.value)}
                    placeholder="Exemplo:&#10;- Plano Básico: R$ 99/mês&#10;- Plano Pro: R$ 199/mês&#10;- Tênis Nike Air: R$ 500" 
                    className="min-h-[120px] bg-background/50 focus-visible:ring-primary" 
                 />
              </div>
            )}

            {state.archetype === "agendador" && (
              <div className="space-y-4 pt-4 border-t border-border/50 animate-in fade-in">
                 <h4 className="font-bold flex items-center gap-2"><CalendarOff className="h-5 w-5 text-destructive" /> Exclusões de Agenda</h4>
                 <p className="text-xs text-muted-foreground">Marque os dias que o agente não deve realizar agendamentos.</p>
                 
                 <div className="space-y-2">
                   <label className="text-sm font-medium">Dias da Semana (Recorrentes)</label>
                   <div className="flex flex-wrap gap-2">
                     {["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"].map(day => (
                       <Badge 
                         key={day}
                         variant="outline"
                         className={cn(
                           "cursor-pointer text-xs py-1.5 px-3 transition-colors",
                           state.agenda.excludedDays.includes(day) 
                             ? "bg-destructive text-destructive-foreground border-destructive" 
                             : "hover:bg-destructive/10 hover:text-destructive hover:border-destructive/50"
                         )}
                         onClick={() => {
                           const current = state.agenda.excludedDays;
                           if (current.includes(day)) {
                             updateState("agenda", "excludedDays", current.filter(d => d !== day));
                           } else {
                             updateState("agenda", "excludedDays", [...current, day]);
                           }
                         }}
                       >
                         {day}
                       </Badge>
                     ))}
                   </div>
                 </div>
                 
                 <div className="space-y-2 pt-2">
                   <label className="text-sm font-medium">Datas Específicas (Feriados / Férias)</label>
                   <div className="flex gap-2">
                     <Input 
                       type="date" 
                       id="date-exclude-input"
                       className="bg-background/50 h-10 w-40" 
                     />
                     <Button 
                       type="button" 
                       variant="outline" 
                       className="h-10"
                       onClick={() => {
                         const input = document.getElementById('date-exclude-input') as HTMLInputElement;
                         if (input && input.value) {
                           const dateStr = input.value.split('-').reverse().join('/'); // Format to DD/MM/YYYY
                           if (!state.agenda.excludedDates.includes(dateStr)) {
                             updateState("agenda", "excludedDates", [...state.agenda.excludedDates, dateStr]);
                           }
                           input.value = '';
                         }
                       }}
                     >
                       Adicionar
                     </Button>
                   </div>
                   
                   {state.agenda.excludedDates.length > 0 && (
                     <div className="flex flex-wrap gap-2 mt-3 p-3 bg-destructive/5 rounded-lg border border-destructive/20">
                       {state.agenda.excludedDates.map(date => (
                         <Badge key={date} variant="destructive" className="flex items-center gap-1">
                           {date}
                           <X className="h-3 w-3 cursor-pointer" onClick={() => updateState("agenda", "excludedDates", state.agenda.excludedDates.filter(d => d !== date))} />
                         </Badge>
                       ))}
                     </div>
                   )}
                 </div>
              </div>
            )}
          </Card>
        </div>

        {/* Passo 6: Handoff */}
        <div className={cn("transition-all duration-500", step === 6 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
            <div>
              <h3 className="text-2xl font-bold mb-2 flex items-center gap-2"><Headset className="h-6 w-6 text-primary"/> Passar para a Equipe Humana {/* Handoff (Intervenção Humana) */}</h3>
              <p className="text-muted-foreground">Regras e gatilhos para acionar a equipe de atendimento humano.</p>
            </div>

            <div className="space-y-4 pt-4">
               <p className="text-sm text-muted-foreground mb-4">Defina como a IA deve agir se o cliente pedir para falar com um humano ou demonstrar insatisfação severa. Os comportamentos são automaticamente adaptados para texto ou voz.</p>
               
               <div className="space-y-2 mb-6">
                  <label className="text-sm font-semibold text-foreground">Gatilhos Universais (Palavras-Chave)</label>
                  <p className="text-xs text-muted-foreground">Se o cliente usar essas palavras em qualquer canal, a IA aciona o transbordo.</p>
                  <Input 
                    value={state.handoff.keywords} 
                    onChange={e => updateState("handoff", "keywords", e.target.value)} 
                    placeholder='Ex: "falar com humano", "cancelar", "reclamação", "procon"' 
                    className="bg-background/50 h-10" 
                  />
               </div>

               <div className="flex flex-col gap-4 pt-2 border-t border-border/30">
                 {/* Bloco de Texto */}
                 <div className="p-5 bg-emerald-500/5 border border-emerald-500/20 rounded-xl space-y-4 relative overflow-hidden">
                   <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
                   
                   <div>
                     <h5 className="text-sm font-bold text-emerald-500 flex items-center gap-2"><MessageSquare className="h-4 w-4"/> Se o Agente estiver em Texto (WhatsApp/Web):</h5>
                     <p className="text-xs text-muted-foreground mt-1">Ele enviará a Mensagem de Transição abaixo e <b>pausará imediatamente</b>. A sessão de chat fica congelada aguardando que o humano assuma a conversa pelo painel.</p>
                   </div>
                   
                   <div className="space-y-2 pt-2 border-t border-emerald-500/10">
                      <label className="text-xs font-semibold text-emerald-600/80">Mensagem de Transição (Texto)</label>
                      <Input 
                        value={state.handoff.message} 
                        onChange={e => updateState("handoff", "message", e.target.value)} 
                        placeholder='Ex: "Um momento, vou chamar a equipe humana..."' 
                        className="bg-background/50 h-10 border-emerald-500/20 focus-visible:ring-emerald-500" 
                      />
                   </div>
                 </div>
                 
                 {/* Bloco de Voz */}
                 <div className="p-5 bg-blue-500/5 border border-blue-500/20 rounded-xl space-y-4 relative overflow-hidden">
                   <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                   
                   <div>
                     <h5 className="text-sm font-bold text-blue-500 flex items-center gap-2"><Phone className="h-4 w-4"/> Se o Agente estiver em Voz (Telefone):</h5>
                     <p className="text-xs text-muted-foreground mt-1">Ele dirá a Mensagem de Transição abaixo e alertará a equipe, <b>mas NÃO desligará a chamada nem vai parar de falar</b>. Ele continuará engajando o cliente até que um humano intercepte a linha.</p>
                   </div>

                   <div className="space-y-2 pt-2 border-t border-blue-500/10">
                      <label className="text-xs font-semibold text-blue-600/80">Mensagem de Transição (Voz)</label>
                      <Input 
                        value={state.handoff.messageVoice || ""} 
                        onChange={e => updateState("handoff", "messageVoice", e.target.value)} 
                        placeholder='Ex: "Aguarde só um instante na linha enquanto eu chamo um especialista..."' 
                        className="bg-background/50 h-10 border-blue-500/20 focus-visible:ring-blue-500" 
                      />
                   </div>
                 </div>
               </div>
               
               <div className="p-4 bg-background/20 border border-border/50 rounded-xl space-y-4">
                 <div>
                   <h5 className="text-sm font-bold flex items-center gap-2"><Bot className="h-4 w-4"/> Dossiê Instantâneo (Resumo de Handoff)</h5>
                   <p className="text-xs text-muted-foreground mt-1">Ao transferir, um LLM secundário lerá todo o histórico e entregará um resumo de 3 linhas na tela do gerente (Qual o problema, o que o cliente quer, o que a IA já tentou).</p>
                 </div>
                 <div className="flex flex-wrap gap-6 mt-2 pt-2 border-t border-border/30">
                   <div className="flex items-center space-x-2">
                     <Switch checked={state.handoff?.summaryText ?? true} onCheckedChange={c => updateState("handoff", "summaryText", c)} className="data-[state=checked]:bg-emerald-500" />
                     <label className="text-sm font-medium text-emerald-500">Ativar no Texto</label>
                   </div>
                   <div className="flex items-center space-x-2">
                     <Switch checked={state.handoff?.summaryVoice ?? true} onCheckedChange={c => updateState("handoff", "summaryVoice", c)} className="data-[state=checked]:bg-blue-500" />
                     <label className="text-sm font-medium text-blue-500">Ativar na Voz</label>
                   </div>
                 </div>
               </div>

               <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl space-y-4">
                 <div className="flex items-center justify-between">
                   <div>
                     <h5 className="text-sm font-bold text-blue-500 flex items-center gap-2"><Phone className="h-4 w-4"/> Modo Retorno de Campanha (Ligar Primeiro)</h5>
                     <p className="text-xs text-muted-foreground mt-1">Se o lead mandar mensagem (ex: respondeu anúncio), a IA tenta LIGAR imediatamente antes de mandar texto.</p>
                   </div>
                   <Switch checked={Array.isArray(state.automations) && state.automations.some(a => a.id === "return_mode")} onCheckedChange={(c) => {
                     const cur = Array.isArray(state.automations) ? state.automations : [];
                     if(c) {
                       setState(prev => ({...prev, automations: [...cur, {id: "return_mode", condition: "Lead inbound_msg", actionType: "call_first", action: ""}]}))
                     } else {
                       setState(prev => ({...prev, automations: cur.filter(a => a.id !== "return_mode")}))
                     }
                   }} className="data-[state=checked]:bg-blue-500" />
                 </div>
                 {Array.isArray(state.automations) && state.automations.some(a => a.id === "return_mode") && (
                   <div className="pt-3 animate-in fade-in slide-in-from-top-2 border-t border-blue-500/20">
                      <p className="text-xs text-blue-400/80 font-medium">Fluxo Ativado: Se o cliente enviar mensagem, a IA de Voz liga. Se ele não atender, a IA de Texto manda: <i>"Vi que você me chamou, tentei te ligar rapidinho. Posso te ligar de novo agora?"</i></p>
                   </div>
                 )}
               </div>

               <div className="p-4 bg-violet-500/10 border border-violet-500/20 rounded-xl space-y-3">
                 <div>
                   <h5 className="text-sm font-bold text-violet-500 flex items-center gap-2"><PhoneCall className="h-4 w-4"/> Gatilhos de Conferência na Ligação</h5>
                   <p className="text-xs text-muted-foreground mt-1">Durante uma LIGAÇÃO, a IA pode te chamar automaticamente (avisar + te trazer pra chamada) quando detectar estas situações. Você atende pelo telefone ou pelo painel.</p>
                 </div>
                 {[
                   {key: "human_request", label: "Cliente pede pra falar com humano"},
                   {key: "price", label: "Cliente pergunta preço/valor"},
                   {key: "hot_lead", label: "Cliente demonstra forte intenção de compra"},
                 ].map(g => {
                   const trigs = state.handoff.callTriggers || [];
                   const cur = trigs.find((t:any) => t.on === g.key);
                   return (
                     <div key={g.key} className="flex items-center justify-between gap-2 pt-2 border-t border-violet-500/10">
                       <div className="flex items-center space-x-2 flex-1">
                         <Switch checked={!!cur} onCheckedChange={(c) => {
                           setState(prev => {
                             const list = (prev.handoff.callTriggers || []).filter((t:any) => t.on !== g.key);
                             if (c) list.push({ on: g.key, action: "bridge", mode: "silent_relay", client: g.key === "human_request" ? "announce" : "silent", channel: "both" });
                             return {...prev, handoff: {...prev.handoff, callTriggers: list}};
                           });
                         }} className="data-[state=checked]:bg-violet-500" />
                         <label className="text-sm">{g.label}</label>
                       </div>
                       {cur && (
                         <select className="h-8 rounded-md border border-input bg-background/50 px-2 text-xs" value={cur.client} onChange={e => {
                           setState(prev => ({...prev, handoff: {...prev.handoff, callTriggers: (prev.handoff.callTriggers||[]).map((t:any) => t.on===g.key ? {...t, client: e.target.value} : t)}}));
                         }}>
                           <option value="silent">Sem avisar cliente</option>
                           <option value="announce">Avisar cliente</option>
                         </select>
                       )}
                     </div>
                   );
                 })}
               </div>

                  <div className="space-y-2">
                     <label className="text-xs font-semibold text-muted-foreground">Método de Transferência</label>
                     <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm" value={state.handoff.method} onChange={e => updateState("handoff", "method", e.target.value)}>
                        <option value="panel">Deixar Humano assumir pelo Painel (Mutar IA)</option>
                        <option value="swarm">Transferir para Outro Agente IA (Swarm)</option>
                     </select>
                  </div>
                  {state.handoff.method === 'swarm' && (
                    <>
                      <div className="space-y-2">
                         <label className="text-xs font-semibold text-muted-foreground">ID da Outra IA (Fallback Nível 1)</label>
                         <Input 
                           value={state.handoff.destAgent} 
                           onChange={e => updateState("handoff", "destAgent", e.target.value)} 
                           placeholder='Ex: "Closer_Vendas"' 
                           className="bg-background/50 h-10 border-primary/50" 
                         />
                      </div>
                      <div className="space-y-2">
                         <label className="text-xs font-semibold text-muted-foreground flex items-center gap-1">
                           ID da Terceira IA (Fallback Nível 2) <Badge variant="outline" className="text-[9px] h-4">Escada de Gerentes</Badge>
                         </label>
                         <Input 
                           value={state.handoff.destAgent2} 
                           onChange={e => updateState("handoff", "destAgent2", e.target.value)} 
                           placeholder='Ex: "Gerente_Retencao" (Deixe em branco para Humano)' 
                           className="bg-background/50 h-10" 
                         />
                      </div>
                    </>
                  )}
                  {state.handoff.method !== 'swarm' && (
                    <div className="space-y-2">
                       <label className="text-xs font-semibold text-muted-foreground">Como avisar o Humano?</label>
                       <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm" value={state.handoff.notifyTo} onChange={e => updateState("handoff", "notifyTo", e.target.value)}>
                          <option value="panel">Aviso Visual no Painel (Sino de Notificação)</option>
                          <option value="telegram">Mandar mensagem no Telegram</option>
                          <option value="whatsapp">Mandar mensagem no Meu WhatsApp</option>
                       </select>
                    </div>
                  )}

                  <div className="p-5 bg-amber-500/5 border border-amber-500/20 rounded-xl space-y-4 mt-6">
                    <div>
                      <h5 className="text-sm font-bold text-amber-500 flex items-center gap-2"><ShieldAlert className="h-4 w-4"/> Notificação e Pedido de Ajuda (Humano no Loop)</h5>
                      <p className="text-xs text-muted-foreground mt-1">Defina o número do gerente que será notificado. Você também pode permitir que a IA peça ajuda ativamente caso não saiba responder a uma pergunta do cliente.</p>
                    </div>
                    
                    <div className="space-y-2">
                       <label className="text-xs font-semibold text-amber-600/80">Número de WhatsApp do Administrador</label>
                       <Input 
                         value={state.handoff.adminNumber || ""} 
                         onChange={e => updateState("handoff", "adminNumber", e.target.value)} 
                         placeholder='Ex: 5511999999999' 
                         className="bg-background/50 h-10 border-amber-500/20 focus-visible:ring-amber-500" 
                       />
                    </div>
                    
                    <div className="flex items-center space-x-2 pt-2">
                      <Switch checked={state.handoff?.askForHelp ?? false} onCheckedChange={c => updateState("handoff", "askForHelp", c)} className="data-[state=checked]:bg-amber-500" />
                      <label className="text-sm font-medium text-amber-500/90">Permitir que a IA pause e peça ajuda ao Admin quando não souber a resposta</label>
                    </div>

                    <div className="flex items-center space-x-2 pt-2 border-t border-amber-500/20 mt-2">
                      <Switch checked={state.handoff?.toContact ?? false} onCheckedChange={c => updateState("handoff", "toContact", c)} className="data-[state=checked]:bg-amber-500" />
                      <label className="text-sm font-medium text-amber-500/90">Numa ligação, se o contato tiver um telefone próprio salvo, transferir pra ELE (não pro admin fixo)</label>
                    </div>
                  </div>
               </div>

          </Card>
        </div>

        {/* Passo 7: Integrações & Webhooks */}
        <div className={cn("transition-all duration-500", step === 7 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
            <div>
              <h3 className="text-2xl font-bold mb-2 flex items-center gap-2"><LinkIcon className="h-6 w-6 text-primary"/> Integrações (Webhooks)</h3>
              <p className="text-muted-foreground">Defina gatilhos para enviar os dados da conversa para N8N, Make, ou seu próprio sistema.</p>
            </div>
            
            <div className="space-y-4">
               {(Array.isArray(state.automations) ? state.automations : []).map((auto) => (
                  <div key={auto.id} className="flex flex-col md:flex-row gap-4 items-start bg-black/10 p-5 rounded-xl border border-border/50 relative group">
                     
                     <div className="flex-1 space-y-3 w-full">
                       <div>
                         <label className="text-xs font-semibold text-muted-foreground">Quando acontecer...</label>
                         <Input 
                           value={auto.condition} 
                           onChange={e => updateAutomation(auto.id, "condition", e.target.value)} 
                           placeholder="Ex: O cliente confirmar que deseja fazer a compra..." 
                           className="bg-background/50 h-10 mt-1" 
                         />
                       </div>
                       
                       <div className="grid grid-cols-2 gap-4">
                         <div>
                           <label className="text-xs font-semibold text-muted-foreground">Ação a Tomar</label>
                           <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1" value={auto.actionType || "webhook"} onChange={e => updateAutomation(auto.id, "actionType", e.target.value)}>
                              <option value="webhook">Disparar Webhook (POST)</option>
                              <option value="alert">Gerar Alerta Interno (Painel)</option>
                              <option value="webhook_fixed">Enviar Payload Fixo (JSON)</option>
                              <option value="api_query">Consultar API (Dinâmico no Prompt)</option>
                           </select>
                         </div>
                         <div>
                           <label className="text-xs font-semibold text-muted-foreground">
                             {auto.actionType === 'alert' ? 'Título do Alerta' : 'URL do Webhook / API'}
                           </label>
                           <Input 
                             value={auto.action} 
                             onChange={e => updateAutomation(auto.id, "action", e.target.value)} 
                             placeholder={auto.actionType === 'alert' ? "Ex: Lead Quente!" : "https://n8n.seu-dominio.com..."} 
                             className="bg-background/50 h-10 mt-1 font-mono text-sm" 
                           />
                         </div>
                       </div>
                       
                       {auto.actionType === 'webhook_fixed' && (
                         <div className="mt-3 animate-in fade-in slide-in-from-top-1">
                           <label className="text-xs font-semibold text-muted-foreground">Payload Fixo (JSON)</label>
                           <p className="text-[10px] text-muted-foreground mb-1">Os dados exatos que serão enviados toda vez que o gatilho for acionado.</p>
                           <textarea
                             value={auto.payload || ""}
                             onChange={e => updateAutomation(auto.id, "payload", e.target.value)}
                             className="flex min-h-[80px] w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm mt-1 font-mono text-emerald-400"
                             placeholder='{"status": "finalizado", "produto": "plano VIP"}'
                           />
                         </div>
                       )}
                       
                       {auto.actionType === 'api_query' && (
                         <div className="mt-3 animate-in fade-in slide-in-from-top-1">
                           <label className="text-xs font-semibold text-muted-foreground">Instrução para a IA (Como usar o retorno)</label>
                           <p className="text-[10px] text-muted-foreground mb-1">O que a IA deve fazer com os dados que a API retornar? (Esses dados serão injetados temporariamente no prompt da IA).</p>
                           <textarea
                             value={auto.instruction || ""}
                             onChange={e => updateAutomation(auto.id, "instruction", e.target.value)}
                             className="flex min-h-[60px] w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm mt-1 text-blue-400"
                             placeholder="Ex: Leia o campo 'status_entrega' e avise o cliente quando o pedido chega."
                           />
                         </div>
                       )}
                       
                       {auto.actionType !== 'alert' && (
                         <div className="mt-4 flex items-center space-x-2 pt-2 border-t border-border/30">
                           <Switch checked={auto.waitForResponse ?? false} onCheckedChange={c => updateAutomation(auto.id, "waitForResponse", c)} />
                           <div>
                             <label className="text-sm font-medium text-foreground">Aguardar retorno (Requisição Síncrona)</label>
                             <p className="text-[10px] text-muted-foreground">A IA deve esperar o webhook/API responder antes de continuar conversando com o cliente?</p>
                           </div>
                         </div>
                       )}
                     </div>

                     <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10 shrink-0 self-center md:self-start md:mt-6" onClick={() => removeAutomation(auto.id)}>
                        <Trash2 className="h-5 w-5" />
                     </Button>
                  </div>
               ))}
               
               <Button variant="outline" className="w-full border-dashed py-8 mt-4 bg-background/20 hover:bg-background/40 hover:border-primary/50 transition-colors" onClick={() => {
                 const id = 'auto_' + Math.random().toString(36).substring(2, 9);
                 setState(prev => ({
                   ...prev,
                   automations: [...(Array.isArray(prev.automations) ? prev.automations : []), { id, condition: "", actionType: "webhook", action: "" }]
                 }));
               }}>
                  <Plus className="h-4 w-4 mr-2" /> Adicionar Gatilho Webhook
               </Button>
            </div>
          </Card>
        </div>

        {/* Passo 8: Sandbox, Otimização e Deploy */}
        <div className={cn("transition-all duration-500", step === 8 ? "block animate-in slide-in-from-bottom-4" : "hidden")}>
          <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold mb-2">Testes, Otimização & Deploy</h3>
              <p className="text-muted-foreground">Teste seu agente, peça para a IA otimizar as regras e publique o robô finalizado.</p>
            </div>

            {missingKey && (
              <div className="p-6 bg-destructive/10 border border-destructive rounded-xl animate-in slide-in-from-top-2 mb-6">
                 <h4 className="text-destructive font-bold flex items-center gap-2 mb-2"><Key className="h-5 w-5"/> Chave de API Necessária</h4>
                 <p className="text-sm text-foreground mb-4">O provedor <span className="font-bold capitalize">{state.identity.provider}</span> exige uma chave para refinar o prompt e inicializar o agente.</p>
                 <Input 
                   type="password" 
                   placeholder="Cole sua API Key aqui..." 
                   className="bg-background"
                   value={inlineKey}
                   onChange={e => setInlineKey(e.target.value)}
                 />
              </div>
            )}
            
            <div className="flex flex-col md:flex-row gap-6 mb-6">
              <div className="flex-1 p-6 bg-black/30 border border-border/50 rounded-xl h-[400px] flex flex-col justify-end">
                <div className="space-y-4 flex flex-col h-full">
                  <div className="flex items-center justify-between border-b border-border/50 pb-2 mb-2">
                      <div className="flex items-center gap-2 text-indigo-400 font-bold"><Bot className="h-4 w-4"/> Chat de Simulação</div>
                      <Button variant="outline" size="sm" className={cn("h-7 text-[10px] gap-1 border-destructive/30 text-destructive hover:bg-destructive/10", rudeMode && "bg-destructive/20")} onClick={() => { setRudeMode(v => !v); toast.info(rudeMode ? "Modo cliente grosseiro DESLIGADO" : "Modo cliente grosseiro LIGADO — teste como a IA contorna."); }}>
                        <Flame className="w-3 h-3"/> Simular Cliente Grosseiro
                      </Button>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar flex flex-col">
                      {simMsgs.length === 0 && (
                        <div className="text-xs text-muted-foreground text-center m-auto">Mande uma mensagem pra testar seu agente com o prompt que você está montando agora.</div>
                      )}
                      {simMsgs.map((m, i) => (
                        m.role === "user" ? (
                          <div key={i} className="p-3 bg-muted/50 rounded-xl rounded-tr-none self-end max-w-[90%] text-sm ml-auto whitespace-pre-wrap">{m.content}</div>
                        ) : (
                          <div key={i} className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-xl rounded-tl-none self-start max-w-[90%] text-sm whitespace-pre-wrap">{m.content}</div>
                        )
                      ))}
                      {simSending && <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-xl rounded-tl-none self-start text-sm text-muted-foreground animate-pulse">digitando...</div>}
                  </div>

                  <div className="flex gap-2 mt-4 pt-2 border-t border-border/50 mt-auto">
                      <Input placeholder="Tente 'quebrar' a IA..." className="h-10 bg-background" value={simInput} onChange={e => setSimInput(e.target.value)} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendSim(); } }} disabled={simSending} />
                      <Button className="h-10 px-4 bg-indigo-500 hover:bg-indigo-600 shadow-glow" onClick={sendSim} disabled={simSending || !simInput.trim()}><Rocket className="h-4 w-4"/></Button>
                  </div>
                </div>
              </div>
              
              <div className="w-full md:w-64 space-y-4 flex flex-col justify-center">
                <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl text-center h-full flex flex-col justify-center items-center">
                  {!voiceSimActive ? (
                    <>
                      <Mic className="h-8 w-8 text-blue-500 mx-auto mb-2 opacity-80" />
                      <h4 className="font-bold text-sm text-blue-400 mb-1">Simular Chamada</h4>
                      <p className="text-xs text-muted-foreground mb-4">Converse por voz com o seu Agente.</p>
                      <Button
                        className="w-full bg-blue-500 hover:bg-blue-600 text-white mt-auto"
                        onClick={startVoiceSim}
                      >
                        <PhoneCall className="h-4 w-4 mr-2" /> Iniciar Teste de Voz
                      </Button>
                    </>
                  ) : (
                    <>
                      <div className="relative mb-3">
                        {isListening ? (
                          <div className="relative">
                            <Mic className="h-10 w-10 text-red-500 animate-pulse" />
                            <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full animate-ping" />
                          </div>
                        ) : isSpeaking ? (
                          <Volume2 className="h-10 w-10 text-emerald-500 animate-pulse" />
                        ) : (
                          <Phone className="h-10 w-10 text-blue-400 animate-pulse" />
                        )}
                      </div>
                      <p className="text-xs font-medium mb-1">
                        {isListening ? "🎤 Ouvindo..." : isSpeaking ? "🔊 Falando..." : "⏳ Processando..."}
                      </p>
                      {voiceTranscript && (
                        <p className="text-[10px] text-muted-foreground italic mb-2 max-w-full truncate">"{voiceTranscript}"</p>
                      )}
                      <div className="w-full max-h-32 overflow-y-auto space-y-1 mb-3 text-left">
                        {voiceSimMsgs.map((m, i) => (
                          <div key={i} className={`text-[10px] p-1.5 rounded ${m.role === "user" ? "bg-blue-500/20 text-blue-300" : "bg-emerald-500/20 text-emerald-300"}`}>
                            <span className="font-bold">{m.role === "user" ? "Você" : "IA"}:</span> {m.content.length > 80 ? m.content.slice(0, 80) + "…" : m.content}
                          </div>
                        ))}
                      </div>
                      <Button
                        variant="outline"
                        className="w-full border-red-500/30 text-red-400 hover:bg-red-500/10 mt-auto"
                        onClick={stopVoiceSim}
                      >
                        <X className="h-4 w-4 mr-2" /> Encerrar Chamada
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="flex flex-col items-center justify-center p-8 bg-black/30 border border-border/50 rounded-xl">
                 {deploying ? (
                   <pre className="text-emerald-500 font-mono text-sm whitespace-pre-wrap text-center">
{`> ${loaderText}
> Inicializando handshake neural...
> Construindo pipeline Multi-Model...
> Validando ${state.tools.length} Superpoderes...
> Compilando...`}
                   </pre>
                 ) : (
                    <div className="space-y-4 text-center max-w-md w-full">
                      <Button 
                        variant="outline" 
                        className="w-full h-14 bg-gradient-to-r from-violet-600/10 to-emerald-500/10 border-violet-500/30 hover:bg-violet-500/20 text-violet-400 font-bold text-lg"
                        onClick={async () => {
                          if (!state.behavior.steps) {
                            toast.error("Preencha as Etapas de Atendimento primeiro para otimizar.");
                            return;
                          }
                          setIsOptimizing(true);
                          toast.info("A IA está reestruturando seu Funil e Guardrails...");
                          try {
                            // Otimização REAL via IA da credencial (antes era setTimeout com
                            // texto fixo). O backend reescreve o prompt de sistema completo.
                            const res: any = await apiPost("/api/agents/refine", {
                              name: state.identity.name, role: state.identity.role, tone: state.behavior.tone,
                              steps: state.behavior.steps, knowledge: state.rag.knowledge,
                              guardrails: state.rag.guardrails, automations: state.automations,
                            });
                            const refined = res.refined_prompt || res.refinedPrompt || "";
                            // Explicação semântica do que a IA mudou (backend /api/agents/refine → change_summary).
                            const summary = (res.change_summary || res.changeSummary || "").trim();
                            if (refined.trim()) {
                              setDiffView({ original: state.rag.guardrails || "(vazio)", refined: refined.trim(), summary });
                              toast.info("Revise as mudanças abaixo antes de aceitar.");
                            } else {
                              toast.error("A IA não retornou um prompt otimizado. Tente de novo.");
                            }
                          } catch (e: any) {
                            toast.error("Erro ao otimizar", { description: e.message });
                          } finally {
                            setIsOptimizing(false);
                          }
                        }}
                        disabled={isOptimizing}
                      >
                        <Wand2 className="h-5 w-5 mr-3 text-violet-400" /> 
                        {isOptimizing ? "Otimizando..." : "Otimizar Prompt com IA"}
                      </Button>

                      {diffView && (
                        <div className="w-full text-left space-y-3 p-4 bg-black/40 border border-violet-500/30 rounded-xl animate-in fade-in slide-in-from-top-2">
                          <h4 className="text-sm font-bold text-violet-400 flex items-center gap-2"><Wand2 className="h-4 w-4" /> Comparação de Prompt</h4>
                          {diffView.summary && (
                            <p className="text-xs text-muted-foreground whitespace-pre-line"><Sparkles className="inline h-3 w-3 mr-1 text-violet-400" />{diffView.summary}</p>
                          )}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div>
                              <p className="text-[10px] font-bold text-red-400 mb-1 uppercase tracking-wider">Antes</p>
                              <pre className="text-[11px] p-3 bg-red-500/5 border border-red-500/20 rounded-lg whitespace-pre-wrap max-h-48 overflow-y-auto text-muted-foreground">{diffView.original}</pre>
                            </div>
                            <div>
                              <p className="text-[10px] font-bold text-emerald-400 mb-1 uppercase tracking-wider">Depois (IA)</p>
                              <pre className="text-[11px] p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-lg whitespace-pre-wrap max-h-48 overflow-y-auto text-muted-foreground">{diffView.refined}</pre>
                            </div>
                          </div>
                          <div className="flex gap-2 justify-end">
                            <Button variant="outline" size="sm" className="border-red-500/30 text-red-400 hover:bg-red-500/10" onClick={() => setDiffView(null)}>
                              <X className="h-3 w-3 mr-1" /> Descartar
                            </Button>
                            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white" onClick={() => { updateState("rag", "guardrails", diffView.refined); setDiffView(null); toast.success("Prompt otimizado aplicado!"); }}>
                              <CheckCircle2 className="h-3 w-3 mr-1" /> Aceitar
                            </Button>
                          </div>
                        </div>
                      )}

                      <Button variant="outline" className="w-full h-12 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 gap-2" onClick={() => setFollowUpModalOpen(true)}>
                        <Clock className="h-4 w-4" /> Configurar Follow-up Fácil
                      </Button>

                   </div>
                 )}
            </div>
              
            <div className="p-6 bg-glass border border-border/50 rounded-xl space-y-4">
               <h4 className="font-bold text-sm mb-4">Resumo da Engenharia</h4>
               <div className="space-y-3 text-sm">
                  <div className="flex justify-between border-b border-border/50 pb-2">
                     <span className="text-muted-foreground">Motor Primário</span>
                     <span className="font-semibold text-emerald-500">{state.identity.model}</span>
                  </div>
                  <div className="flex justify-between border-b border-border/50 pb-2">
                     <span className="text-muted-foreground">Motor Emergência</span>
                     <span className="font-semibold text-amber-500">{state.identity.fallbackModel}</span>
                  </div>
                  <div className="flex justify-between border-b border-border/50 pb-2">
                     <span className="text-muted-foreground">Pressão (Vendas)</span>
                     <span className="font-semibold">{state.behavior.salesPressure}/10</span>
                  </div>
                  <div className="flex justify-between border-b border-border/50 pb-2">
                     <span className="text-muted-foreground">Superpoderes</span>
                     <span className="font-semibold">{state.tools.length} ativos</span>
                  </div>
               </div>
            </div>
          </Card>
        </div>

        {/* Wizard Footer Controls */}
        <div className="flex items-center justify-between mt-10 pt-6 border-t border-border/50 px-4">
           <Button variant="ghost" onClick={prevStep} disabled={step === 1 || deploying} className="gap-2 rounded-xl h-12 px-6">
             <ArrowLeft className="h-4 w-4" /> Voltar
           </Button>
           
           {step < 8 ? (
             <Button onClick={nextStep} className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow rounded-xl h-12 px-8 font-bold">
               Próxima Etapa <ArrowRight className="h-4 w-4" />
             </Button>
           ) : (
             <Button onClick={deployAgent} disabled={deploying} className="gap-2 bg-emerald-600 hover:bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.3)] rounded-xl h-12 px-8 font-bold">
               {deploying ? <span className="animate-pulse flex items-center gap-2">Processando...</span> : <><Rocket className="h-4 w-4" /> {editMode ? "Salvar Alterações" : "Finalizar e Publicar"}</>}
             </Button>
           )}
        </div>

      </div>

      {/* Preview Dinâmico Removido para exibição apenas no final */}

      {/* Modal Nova Credencial de IA (salva sem sair do wizard) */}
      <Dialog open={credModalOpen} onOpenChange={setCredModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Key className="h-5 w-5 text-primary" /> Nova Credencial de IA</DialogTitle>
            <DialogDescription>Cole a chave, teste e salve. Ela fica disponível pra reutilizar em outros agentes.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Nome / Apelido</label>
              <Input value={credForm.name} onChange={e => setCredForm(prev => ({ ...prev, name: e.target.value }))} placeholder="Ex: OpenAI Produção" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Provedor</label>
              <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm shadow-sm focus-visible:ring-primary" value={credForm.provider} onChange={e => setCredForm(prev => ({ ...prev, provider: e.target.value }))}>
                <option value="openai">OpenAI</option>
                <option value="gemini">Google Gemini</option>
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="groq">Groq</option>
                <option value="elevenlabs">ElevenLabs</option>
                <option value="cartesia">Cartesia</option>
                <option value="custom">Custom / Proxy</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Chave de API</label>
              <Input type="password" value={credForm.api_key} onChange={e => setCredForm(prev => ({ ...prev, api_key: e.target.value }))} placeholder="sk-..." />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Base URL (opcional — proxy)</label>
              <Input value={credForm.base_url} onChange={e => setCredForm(prev => ({ ...prev, base_url: e.target.value }))} placeholder="https://api.openai.com" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={handleTestCredForm} disabled={credTesting} className="gap-2">
              {credTesting ? "Testando..." : <><CheckCircle2 className="h-4 w-4" /> Testar</>}
            </Button>
            <Button onClick={handleSaveCred} disabled={credSaving} className="bg-primary gap-2">
              {credSaving ? "Salvando..." : <><Save className="h-4 w-4" /> Salvar</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal Mágica IA */}
      <Dialog open={magicModalOpen} onOpenChange={setMagicModalOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Wand2 className="h-5 w-5 text-emerald-500" /> Gerador de Funcionário (Magia IA)
            </DialogTitle>
            <DialogDescription>
              Responda estas 3 perguntas e eu preencho todas as 5 etapas com a estratégia ideal.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Ramo de Negócio / Empresa</label>
              <Input 
                value={magicForm.sector} 
                onChange={e => setMagicForm(prev => ({...prev, sector: e.target.value}))}
                placeholder="Ex: Clínica Odontológica, Imobiliária, E-commerce de Roupas" 
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Objetivo Principal</label>
              <Input 
                value={magicForm.goal} 
                onChange={e => setMagicForm(prev => ({...prev, goal: e.target.value}))}
                placeholder="Ex: Agendar avaliações, Vender pacotes, Tirar dúvidas" 
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Personalidade Desejada (Opcional)</label>
              <Input 
                value={magicForm.personality} 
                onChange={e => setMagicForm(prev => ({...prev, personality: e.target.value}))}
                placeholder="Ex: Agressivo nas vendas, Empático e acolhedor, Jovem" 
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="ghost" onClick={() => setMagicModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleMagicGeneration} disabled={isMagicScraping} className="bg-emerald-500 hover:bg-emerald-600 shadow-glow gap-2">
              {isMagicScraping ? "Processando..." : <><Cpu className="h-4 w-4" /> Gerar Agente</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog open={followUpModalOpen} onOpenChange={setFollowUpModalOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto p-0 border-0 bg-transparent shadow-none">
          <div className="bg-background border border-border/50 rounded-2xl overflow-hidden shadow-2xl relative p-6">
            <DialogHeader className="sr-only">
              <DialogTitle>Follow-Up & Retargeting</DialogTitle>
            </DialogHeader>
            <EasyFollowUpWizard />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}


