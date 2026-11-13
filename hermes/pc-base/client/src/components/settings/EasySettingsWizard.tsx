import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { 
  BrainCircuit, Wand2, ChevronRight, CheckCircle2, 
  KeyRound, ExternalLink, MessageSquare, Palette, Users, Bell, 
  ChevronLeft, Save, Loader2, Ear, Volume2, Plus, Trash2, LayoutDashboard, ShieldCheck,
  Cpu, AlertTriangle, Play, RotateCcw
} from "lucide-react";
import { toast } from "sonner";
import { apiErrorMessage, apiPost } from "@/lib/api";
import { setView } from "@/stores/navigation";
import { logError, silentAll } from "@/lib/log";
import { apiUrl, authHeaders } from "@/lib/auth";
import { getClientId } from "@/lib/client-id";
import { FALLBACK_MODELS, PROVIDER_INFO } from "@/constants/ai-providers";

type Step = "welcome" | "credentials" | "llm_text" | "stt" | "tts" | "manager_chat" | "appearance" | "team" | "alerts" | "crm" | "summary" | "finish";

// Lista de modelos conhecidos por provedor — usada como FALLBACK quando a API do
// provedor recusa listar (ex: chave nova do Gemini com a API "Generative Language"
// ainda não ativada). Assim o cliente consegue escolher um modelo e continuar.
const KNOWN_MODELS_FALLBACK = FALLBACK_MODELS;

export function EasySettingsWizard() {
  const [step, setStep] = useState<Step>("welcome");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // --- STATES ---
  const [credentials, setCredentials] = useState<{id: string, provider: string, key: string, isFallback?: boolean}[]>([]);
  const [newCredProvider, setNewCredProvider] = useState("groq");
  const [newCredKey, setNewCredKey] = useState("");
  const [newCredFallback, setNewCredFallback] = useState(false);
  const [fallbackProvider, setFallbackProvider] = useState("openai");
  const [fallbackKey, setFallbackKey] = useState("");

  const [textOption, setTextOption] = useState("new");
  const [textSavedId, setTextSavedId] = useState("");
  const [textNewProv, setTextNewProv] = useState("gemini");
  const [textNewKey, setTextNewKey] = useState("");
  const [textModel, setTextModel] = useState("");
  const [textModelsList, setTextModelsList] = useState<string[]>([]);
  const [fetchingText, setFetchingText] = useState(false);
  const [textTemp, setTextTemp] = useState(0.7);

  const [sttOption, setSttOption] = useState("gratis");
  const [sttSavedId, setSttSavedId] = useState("");
  const [sttNewProv, setSttNewProv] = useState("groq");
  const [sttNewKey, setSttNewKey] = useState("");
  const [sttModel, setSttModel] = useState("");
  const [sttModelsList, setSttModelsList] = useState<string[]>([]);
  const [fetchingStt, setFetchingStt] = useState(false);
  const [sttLang, setSttLang] = useState("pt");

  const [ttsOption, setTtsOption] = useState("gratis");
  const [ttsSavedId, setTtsSavedId] = useState("");
  const [ttsNewProv, setTtsNewProv] = useState("elevenlabs");
  const [ttsNewKey, setTtsNewKey] = useState("");
  const [ttsModel, setTtsModel] = useState("");
  const [ttsModelsList, setTtsModelsList] = useState<string[]>([]);
  const [fetchingTts, setFetchingTts] = useState(false);
  const [ttsSpeed, setTtsSpeed] = useState(1.0);
  const [ttsAmbient, setTtsAmbient] = useState(false);
  const [ttsAmbientType, setTtsAmbientType] = useState("office");

  const [chatChannel, setChatChannel] = useState("panel");
  const [botToken, setBotToken] = useState("");
  const [chatId, setChatId] = useState("");
  const [botVerified, setBotVerified] = useState<{name: string, user: string} | null>(null);
  const [wppGroupName, setWppGroupName] = useState("");
  const [wppGroupCreated, setWppGroupCreated] = useState(false);
  const [managerCognitive, setManagerCognitive] = useState(true);
  const [managerRag, setManagerRag] = useState(true);
  const [managerTools, setManagerTools] = useState(true);
  
  const [brandColor, setBrandColor] = useState("#10b981");
  const [bgColor, setBgColor] = useState("#09090b");
  const [workspaceName, setWorkspaceName] = useState("");
  const [teamMembers, setTeamMembers] = useState<{id: string, email: string, pass: string}[]>([]);
  
  const [alerts, setAlerts] = useState({ sales: true, lost: false, errors: true, summary: true, newLead: false });
  const [customAlerts, setCustomAlerts] = useState<{id: string, text: string}[]>([]);
  const [newCustomAlert, setNewCustomAlert] = useState("");
  const [crmSetup, setCrmSetup] = useState({ defaultFunnel: true, basicTags: true });
  const [customTags, setCustomTags] = useState<{id: string, text: string}[]>([]);
  const [newCustomTag, setNewCustomTag] = useState("");

  const [generatingTips, setGeneratingTips] = useState(false);
  const [tips, setTips] = useState<string[]>([]);

  // TESTING FLAGS
  const [testedFlags, setTestedFlags] = useState<Record<string, boolean>>({});
  const [testingModel, setTestingModel] = useState<string | null>(null);
  // Marca por tipo ("text"/"stt"/"tts") quando a lista de modelos veio do FALLBACK
  // (a API do provedor recusou listar). Nesse caso liberamos o "Próximo" com aviso.
  const [usedFallback, setUsedFallback] = useState<Record<string, boolean>>({});

  const providersInfo = PROVIDER_INFO;

  // 1. LOCALSTORAGE DRAFT
  useEffect(() => {
    const draft = localStorage.getItem("easy_wizard_draft");
    if (draft) {
      try {
        const d = JSON.parse(draft);
        if (d.step && d.step !== "finish") {
           setStep(d.step);
           if (d.credentials) setCredentials(d.credentials);
           if (d.textModel) setTextModel(d.textModel);
           if (d.sttModel) setSttModel(d.sttModel);
           if (d.ttsModel) setTtsModel(d.ttsModel);
           if (d.botToken) setBotToken(d.botToken);
           if (d.workspaceName) setWorkspaceName(d.workspaceName);
           if (d.brandColor) setBrandColor(d.brandColor);
           if (d.ttsAmbient) setTtsAmbient(d.ttsAmbient);
           if (d.ttsAmbientType) setTtsAmbientType(d.ttsAmbientType);
           if (d.testedFlags) setTestedFlags(d.testedFlags);
           if (d.wppGroupName) { setWppGroupName(d.wppGroupName); setWppGroupCreated(true); }
           if (d.teamMembers) setTeamMembers(d.teamMembers);
           if (d.alerts) setAlerts(d.alerts);
           if (d.customAlerts) setCustomAlerts(d.customAlerts);
           if (d.customTags) setCustomTags(d.customTags);
           toast.info("Rascunho anterior restaurado automaticamente!");
        }
      } catch (e) {}
    }
    setLoaded(true);
  }, []);

  const savePartial = async (currentStep: Step, nextStep: Step, requiresValidation: boolean = false) => {
    // Validação estrita
    if (requiresValidation) {
       const typeMap: Record<string, string> = { "llm_text": "text", "stt": "stt", "tts": "tts" };
       const t = typeMap[currentStep];
       const optionVal = currentStep === "llm_text" ? textOption : (currentStep === "stt" ? sttOption : ttsOption);
       
       // Regra normal: precisa ter testado com sucesso. EXCEÇÃO (anti-beco-sem-saída):
       // se a listagem caiu no fallback (API do provedor recusou listar) e o cliente
       // escolheu um modelo, liberamos com AVISO em vez de travar o onboarding.
       const modelChosen = t === "text" ? textModel : (t === "stt" ? sttModel : ttsModel);
       if (optionVal !== "gratis" && !testedFlags[t]) {
          if (usedFallback[t] && modelChosen) {
             toast.warning("Seguindo com um modelo conhecido sem validação completa. Confirme sua chave depois nas Configurações.");
          } else {
             return toast.error(`Você não pode continuar sem testar se a IA de ${t.toUpperCase()} está respondendo com sucesso e tem créditos.`);
          }
       }
    }

    setSaving(true);
    try {
      const draft = { step: nextStep, credentials, textModel, sttModel, ttsModel, botToken, workspaceName, brandColor, ttsAmbient, ttsAmbientType, testedFlags, wppGroupName, teamMembers, alerts, customAlerts, customTags };
      localStorage.setItem("easy_wizard_draft", JSON.stringify(draft));
      
      await apiPost("/api/settings/easy-wizard-partial", { step: currentStep }).catch(logError("easy-wizard-partial"));
      setStep(nextStep);
    } finally {
      setSaving(false);
    }
  };

  const forceBypass = (nextStep: Step) => {
    toast.warning("Modo Dev: Pulando Validação");
    setSaving(true);
    setTimeout(() => {
       const draft = { step: nextStep, credentials, textModel, sttModel, ttsModel, botToken, workspaceName, brandColor, ttsAmbient, ttsAmbientType, testedFlags, wppGroupName, teamMembers, alerts, customAlerts, customTags };
       localStorage.setItem("easy_wizard_draft", JSON.stringify(draft));
       setStep(nextStep);
       setSaving(false);
    }, 500);
  };

  const finishWizard = async () => {
    setSaving(true);
    try {
      // Envia o payload COMPLETO (antes só mandava {done:true} e tudo se perdia).
      const payload = {
        done: true,
        credentials: credentials.map(c => ({ id: c.id, provider: c.provider, key: c.key })),
        // savedId = o id que o navegador deu à chave no passo 1; o servidor troca pelo id real do cofre.
        llm_text: {
          option: textOption,
          provider: textOption === "new" ? textNewProv : "",
          key: textOption === "new" ? textNewKey : "",
          savedId: textOption === "saved" ? textSavedId : "",
          model: textModel,
          temperature: textTemp,
        },
        stt: {
          option: sttOption,
          provider: sttOption === "new" ? sttNewProv : "",
          key: sttOption === "new" ? sttNewKey : "",
          savedId: sttOption === "saved" ? sttSavedId : "",
          model: sttModel,
          language: sttLang,
        },
        tts: {
          option: ttsOption,
          provider: ttsOption === "new" ? ttsNewProv : "",
          key: ttsOption === "new" ? ttsNewKey : "",
          savedId: ttsOption === "saved" ? ttsSavedId : "",
          model: ttsModel,
          speed: ttsSpeed,
        },
        manager_chat: { channel: chatChannel, botToken, chatId },
        appearance: { workspaceName, brandColor },
        alerts: { sales: alerts.sales, errors: alerts.errors },
        crm: { defaultFunnel: crmSetup.defaultFunnel, basicTags: crmSetup.basicTags },
        // Campos novos (antes capturados no front mas nunca enviados):
        ttsAmbient,
        ttsAmbientType,
        wppGroupName,
        teamMembers: teamMembers.map(m => ({ email: m.email, pass: m.pass })),
        customTags: customTags.map(t => ({ text: t.text })),
        customAlerts: customAlerts.map(a => ({ text: a.text })),
      };
      // Antes o erro era engolido e a tela dizia "sucesso" mesmo sem gravar nada.
      const res = await apiPost<{ ok?: boolean; warnings?: string[] }>("/api/settings/easy-wizard-ai", payload);
      localStorage.removeItem("easy_wizard_draft");
      if (res?.warnings?.length) {
        toast.warning("Configurado, mas confira: " + res.warnings.join("; "), { duration: 10000 });
      } else {
        toast.success("Plataforma configurada com sucesso!");
      }
      setStep("finish");
    } catch (e) {
      logError("easy-wizard-ai")(e);
      toast.error(apiErrorMessage(e, "Não consegui salvar a configuração. Tente de novo."));
    } finally {
      setSaving(false);
    }
  };

  const isKeyLooksValid = (provider: string, key: string) => {
    if (!key) return false;
    if (provider === "openai" && !key.startsWith("sk-")) return false;
    if (provider === "groq" && !key.startsWith("gsk_")) return false;
    if (provider === "anthropic" && !key.startsWith("sk-ant-")) return false;
    return key.length > 15; 
  };

  const testTelegram = async () => {
    if (!botToken) return toast.error("Preencha o Token do Bot primeiro.");
    try {
      const res = await fetch(`https://api.telegram.org/bot${botToken}/getMe`);
      const data = await res.json();
      if (data.ok) {
        setBotVerified({ name: data.result.first_name, user: data.result.username });
        toast.success(`Conectado ao bot: @${data.result.username}`);
      } else {
        setBotVerified(null);
        toast.error("Token Inválido. O Telegram não reconheceu esse token.");
      }
    } catch {
      toast.error("Erro na comunicação com o Telegram.");
    }
  };

  // Resolve provider/chave/credencial e o modelo escolhido para um tipo (text/stt/tts).
  const resolveCred = (type: string) => {
    if (type === "text") {
      if (textOption === "saved") { const c = credentials.find(x => x.id === textSavedId); return { provider: c?.provider || "", api_key: c?.key || "", credential_id: textSavedId, model: textModel }; }
      return { provider: textNewProv, api_key: textNewKey, credential_id: "", model: textModel };
    }
    if (type === "stt") {
      if (sttOption === "saved") { const c = credentials.find(x => x.id === sttSavedId); return { provider: c?.provider || "", api_key: c?.key || "", credential_id: sttSavedId, model: sttModel }; }
      return { provider: sttNewProv, api_key: sttNewKey, credential_id: "", model: sttModel };
    }
    if (ttsOption === "saved") { const c = credentials.find(x => x.id === ttsSavedId); return { provider: c?.provider || "", api_key: c?.key || "", credential_id: ttsSavedId, model: ttsModel }; }
    return { provider: ttsNewProv, api_key: ttsNewKey, credential_id: "", model: ttsModel };
  };

  const executeRealAiTest = async (type: string) => {
     setTestingModel(type);
     try {
       const c = resolveCred(type);
       if (type === "tts") {
         // TTS: valida sintetizando uma frase de teste no provedor/voz escolhidos.
         const r = await apiPost<{ ok: boolean; error?: string }>("/api/tts/test", {
           provider: c.provider, api_key: c.api_key, voice_id: c.model,
         });
         if (!r.ok) throw new Error(r.error || "falha ao sintetizar voz");
       } else if (type === "stt") {
         // Transcrição se testa transcrevendo (antes ia para o teste de chat e a chave de
         // transcrição nunca passava — auditoria do mês 2, F22).
         const r = await apiPost<{ ok: boolean; error?: string }>("/api/stt/test", {
           provider: c.provider, api_key: c.api_key, credential_id: c.credential_id, model: c.model,
         });
         if (!r.ok) throw new Error(r.error || "a transcrição não respondeu");
       } else {
         const r = await apiPost<{ ok: boolean; error?: string }>("/api/ai/test", {
           provider: c.provider, api_key: c.api_key, credential_id: c.credential_id, model: c.model,
         });
         if (!r.ok) throw new Error(r.error || "a IA não respondeu");
       }
       setTestedFlags(f => ({ ...f, [type]: true }));
       toast.success("✨ SUCESSO! A chave é válida e o modelo respondeu.");
     } catch (e) {
       setTestedFlags(f => ({ ...f, [type]: false }));
       toast.error("Falha na validação", { description: (e as Error).message });
     } finally {
       setTestingModel(null);
     }
  }

  const analyzeWithAI = async () => {
    if (!testedFlags.text && textOption !== "gratis") return toast.error("Você não validou o Cérebro IA (Passo 2). Volte e teste a chave antes de gerar análises.");
    setGeneratingTips(true);
    // Dicas locais determinísticas como base/fallback (sempre úteis, sem depender de rede).
    const localTips = [
       ttsAmbient ? `A velocidade da sua voz TTS está em ${ttsSpeed}x. Como você selecionou o som ambiente '${ttsAmbientType}', ajuste para ~1.1x para a dicção sobressair no ruído e soar natural.` : `Você não ativou o Som Ambiente — a ligação fica com 'silêncio absoluto' ao fundo, o que soa robótico. Considere ligar na aba de voz.`,
       customTags.length > 0 ? `Você adicionou ${customTags.length} tags personalizadas. Cruze-as no funil para segmentar os leads automaticamente.` : `Você não criou nenhuma Tag no CRM. Crie tags como "Urgente", "Caro", "Curioso" para a IA classificar cada ligação.`,
       `Seu Gestor de IA responderá pelo canal escolhido. Avise seus ${teamMembers.length || 0} colaboradores para pedir o resumo das ligações ao Gestor.`
    ];
    try {
      // Pede à IA real do dono dicas específicas de conversão para esta config.
      const prompt = `Você é um consultor de vendas por telefone. Com base nesta configuração de um agente de voz, dê 3 dicas curtas e específicas de ALTA CONVERSÃO (uma por linha, sem numeração, sem markdown). Config: som_ambiente=${ttsAmbient ? ttsAmbientType : "desligado"}, velocidade_voz=${ttsSpeed}x, tags_crm=${customTags.join(", ") || "nenhuma"}, colaboradores=${teamMembers.length}.`;
      const r = await apiPost<{ reply: string }>("/api/chat/send", { thread: "wizard-tips", text: prompt });
      const lines = (r.reply || "").split("\n").map(l => l.replace(/^[-*\d.\s]+/, "").trim()).filter(l => l.length > 8);
      setTips(lines.length >= 2 ? lines.slice(0, 5) : localTips);
      toast.success("Análise inteligente concluída!");
    } catch {
      // IA indisponível → entrega as dicas locais (ainda úteis), sem mentir que foi a IA.
      setTips(localTips);
      toast.success("Dicas geradas (modo básico — IA indisponível no momento).");
    } finally {
      setGeneratingTips(false);
    }
  };

  const elevenLabsVoices = [
    { id: "21m00Tcm4TlvDq8ikWAM", name: "Rachel (Feminino)" },
    { id: "EXAVITQu4vr4xnSDxMaL", name: "Bella (Feminino)" },
    { id: "ErXwobaYiN019PkySvjV", name: "Antoni (Masculino)" },
    { id: "TxGEqnHWrfWFTfGW9XjX", name: "Josh (Masculino)" }
  ];

  const edgeVoices = [
    { id: "pt-BR-FranciscaNeural", name: "Francisca (Feminino)" },
    { id: "pt-BR-AntonioNeural", name: "Antônio (Masculino)" },
    { id: "pt-BR-ThalitaNeural", name: "Thalita (Feminino)" }
  ];

  const playVoiceTest = async (voiceId: string, apiOption: string) => {
    // Resolve provider/chave conforme a opção (grátis=edge-tts, salva=cofre, nova=digitada).
    let provider = "edge-tts";
    let apiKey = "";
    if (apiOption === "gratis") {
      provider = "edge-tts";
    } else if (apiOption === "saved") {
      const c = credentials.find(x => x.id === ttsSavedId);
      if (!c) return toast.error("Selecione uma chave salva primeiro.");
      provider = c.provider; apiKey = c.key;
    } else {
      if (!ttsNewKey.trim()) return toast.error("Cole sua Chave API primeiro para testar vozes Premium!");
      provider = ttsNewProv; apiKey = ttsNewKey;
    }
    toast.info("Gerando amostra da voz...");
    try {
      const r = await apiPost<{ audio_base64: string }>("/api/tts/generate", {
        text: "Olá! Esta é uma amostra da minha voz. Assim vou soar nas suas ligações.",
        voice: voiceId, provider, api_key: apiKey,
      });
      if (!r.audio_base64) throw new Error("sem áudio retornado");
      const audio = new Audio(`data:audio/ogg;base64,${r.audio_base64}`);
      await audio.play().catch(silentAll());
      toast.success("Reproduzindo amostra real da voz.");
    } catch (e) {
      toast.error("Falha ao gerar a voz", { description: (e as Error).message });
    }
  };

  // Live Color Injection
  const hexToHsl = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }
    return { h: h * 360, s: s * 100, l: l * 100 };
  };

  useEffect(() => {
    if (brandColor) {
       const applyPrimaryColor = (hex: string) => {
         const { h, s, l } = hexToHsl(hex);
         const hslVal = `${h.toFixed(0)} ${s.toFixed(0)}% ${l.toFixed(0)}%`;
         document.documentElement.style.setProperty('--primary', hslVal);
         document.documentElement.style.setProperty('--ring', hslVal);
       };
       applyPrimaryColor(brandColor);
    }
  }, [brandColor]);

  useEffect(() => {
    const props = ['--background', '--card', '--popover', '--muted', '--border'];
    // Cor default = deixa o CSS do tema mandar (remove inline). Sem isso o fundo escuro
    // default era forçado inline mesmo no tema claro e não revertia ao trocar de tema.
    if (!bgColor || bgColor === "#09090b") {
      props.forEach((p) => document.documentElement.style.removeProperty(p));
      return;
    }
    const { h, s, l } = hexToHsl(bgColor);
    const isDark = document.documentElement.classList.contains('dark');
    const hVal = h.toFixed(0);
    const sVal = s.toFixed(0);
    if (isDark) {
      document.documentElement.style.setProperty('--background', `${hVal} ${sVal}% ${l.toFixed(0)}%`);
      document.documentElement.style.setProperty('--card', `${hVal} ${sVal}% ${(l + 2).toFixed(0)}%`);
      document.documentElement.style.setProperty('--popover', `${hVal} ${sVal}% ${(l + 2).toFixed(0)}%`);
      document.documentElement.style.setProperty('--muted', `${hVal} ${sVal}% ${(l + 6).toFixed(0)}%`);
      document.documentElement.style.setProperty('--border', `${hVal} ${sVal}% ${(l + 12).toFixed(0)}%`);
    } else {
      document.documentElement.style.setProperty('--background', `${hVal} ${sVal}% ${l.toFixed(0)}%`);
      document.documentElement.style.setProperty('--card', `${hVal} ${sVal}% ${(l > 2 ? l - 2 : 0).toFixed(0)}%`);
      document.documentElement.style.setProperty('--popover', `${hVal} ${sVal}% ${(l > 2 ? l - 2 : 0).toFixed(0)}%`);
      document.documentElement.style.setProperty('--muted', `${hVal} ${sVal}% ${(l > 6 ? l - 6 : 0).toFixed(0)}%`);
      document.documentElement.style.setProperty('--border', `${hVal} ${sVal}% ${(l > 12 ? l - 12 : 0).toFixed(0)}%`);
    }
  }, [bgColor]);

  const resetToDefault = () => {
    setBrandColor("#10b981");
    setBgColor("#09090b");
    document.documentElement.style.removeProperty('--background');
    document.documentElement.style.removeProperty('--card');
    document.documentElement.style.removeProperty('--popover');
    document.documentElement.style.removeProperty('--muted');
    document.documentElement.style.removeProperty('--border');
  };

  const renderAiSetup = (
    type: "text" | "stt" | "tts",
    allowFree: boolean,
    option: string, setOption: (v: string) => void,
    savedId: string, setSavedId: (v: string) => void,
    newProvider: string, setNewProvider: (v: string) => void,
    newKey: string, setNewKey: (v: string) => void,
    model: string, setModel: (v: string) => void,
    modelsList: string[], setModelsList: (v: string[]) => void,
    fetching: boolean, setFetching: (v: boolean) => void,
    extraConfig?: React.ReactNode
  ) => {
    if (!allowFree && option === "gratis") setOption(credentials.length > 0 ? "saved" : "new");

    const handleFetch = async () => {
      let prov = "";
      let keyToUse = "";
      if (option === "saved") {
         const c = credentials.find(x => x.id === savedId);
         prov = c?.provider || "";
         keyToUse = c?.key || "";
      } else {
         prov = newProvider;
         keyToUse = newKey;
      }

      if (!keyToUse.trim()) return toast.error("Insira a chave da API primeiro.");
      if (!isKeyLooksValid(prov, keyToUse)) {
         toast.warning("Essa chave parece estar num formato inválido para este provedor, mas vou tentar mesmo assim.");
      }

      setFetching(true);
      try {
        if (type === "tts") {
          // TTS: as "opções" são VOZES (não modelos de chat). Lista curada por provedor —
          // é o catálogo real de vozes suportadas, não um mock de placeholder.
          if (prov === "elevenlabs") setModelsList(elevenLabsVoices.map(v => v.id));
          else setModelsList(edgeVoices.map(v => v.id));
          toast.success("Vozes carregadas! Escolha e clique em ouvir a amostra.");
        } else {
          // text/stt: busca os modelos REAIS direto no provedor (a chave valida de quebra).
          // Usamos fetch direto (não apiGet) pra conseguir LER o corpo do erro — o backend
          // agora manda {error, provider_status, hint} legível, e apiGet descarta o corpo.
          const credId = option === "saved" ? savedId : "";
          const qs = new URLSearchParams({ provider: prov, api_key: keyToUse, ...(credId ? { credential_id: credId } : {}) });
          const resp = await fetch(apiUrl(`/api/ai/models?${qs.toString()}`), {
            headers: { "X-Client-Id": getClientId(), ...authHeaders() },
          });
          const data = await resp.json().catch(() => ({} as any));

          if (!resp.ok) {
            // Erro do provedor: mostra a mensagem AMIGÁVEL + hint (não o JSON cru) e
            // cai no FALLBACK de modelos conhecidos pra o cliente não ficar travado.
            const friendly = (data && (data.error || data.message)) || "Não consegui listar os modelos.";
            const hint = data && data.hint ? `\n${data.hint}` : "";
            const fb = KNOWN_MODELS_FALLBACK[prov] || [];
            if (fb.length > 0) {
              setModelsList(fb);
              setUsedFallback(f => ({ ...f, [type]: true }));
              toast.warning("Não consegui listar da API — usando modelos conhecidos; confirme sua chave depois.", { description: `${friendly}${hint}` });
            } else {
              toast.error("Falha ao carregar modelos", { description: `${friendly}${hint}` });
            }
            return;
          }

          const list = data.models || [];
          if (list.length === 0) {
            // Sem erro mas lista vazia: também cai no fallback pra destravar.
            const fb = KNOWN_MODELS_FALLBACK[prov] || [];
            if (fb.length > 0) {
              setModelsList(fb);
              setUsedFallback(f => ({ ...f, [type]: true }));
              toast.warning("Nenhum modelo retornado pela API — usando modelos conhecidos; confirme sua chave depois.");
            } else {
              toast.warning("Nenhum modelo retornado. Verifique a chave/provedor.");
            }
          } else {
            setModelsList(list);
            setUsedFallback(f => ({ ...f, [type]: false }));
            toast.success(`${list.length} modelos carregados! Escolha o desejado.`);
          }
        }
      } catch (e) {
        // Falha de rede/inesperada: também tenta o fallback conhecido pra não travar.
        const fb = KNOWN_MODELS_FALLBACK[prov] || [];
        if (type !== "tts" && fb.length > 0) {
          setModelsList(fb);
          setUsedFallback(f => ({ ...f, [type]: true }));
          toast.warning("Não consegui conectar à API — usando modelos conhecidos; confirme sua chave depois.", { description: (e as Error).message });
        } else {
          toast.error("Falha ao carregar modelos", { description: (e as Error).message });
        }
      } finally {
        setFetching(false);
      }
    };

    const isTested = testedFlags[type] === true;

    return (
      <div className="space-y-6 animate-in fade-in">
        <div className="space-y-3">
          <label className="text-sm font-semibold">Qual Chave de API vamos usar?</label>
          <select value={option} onChange={(e) => { setOption(e.target.value); setModelsList([]); setModel(""); setTestedFlags(f=>({...f,[type]:false})); }} className="w-full rounded-xl border border-input bg-background px-4 py-4 text-sm shadow-sm font-bold text-primary">
            {allowFree && <option value="gratis">🤖 Opção Grátis / Nativa (Mais Lenta e Simples)</option>}
            {credentials.length > 0 && <option value="saved">🔑 Usar uma Chave já guardada no Cofre</option>}
            <option value="new">➕ Inserir uma Nova Chave de API</option>
          </select>
        </div>

        {option === "saved" && (
          <div className="space-y-3">
            <label className="text-sm font-semibold">Selecione a chave guardada:</label>
            <select value={savedId} onChange={(e) => { setSavedId(e.target.value); setModelsList([]); setModel(""); setTestedFlags(f=>({...f,[type]:false})); }} className="w-full rounded-xl border border-input bg-background px-4 py-4 text-sm shadow-sm">
              <option value="" disabled>Escolha...</option>
              {credentials.map(c => <option key={c.id} value={c.id}>{providersInfo[c.provider]?.name || c.provider} (Final: {c.key.slice(-4)})</option>)}
            </select>
          </div>
        )}

        {option === "new" && (
          <div className="space-y-4 bg-muted/20 p-5 rounded-2xl border border-dashed border-border/50 relative overflow-hidden">
            <div className="space-y-2">
              <label className="text-sm font-semibold">Qual empresa (Provedor)?</label>
              <select value={newProvider} onChange={(e) => { setNewProvider(e.target.value); setModelsList([]); setModel(""); setTestedFlags(f=>({...f,[type]:false})); }} className="w-full rounded-xl border border-input bg-background px-4 py-3 text-sm shadow-sm">
                {Object.entries(providersInfo).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}
              </select>
            </div>
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-2">
              <a href={providersInfo[newProvider].link} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm font-bold text-primary hover:underline"><ExternalLink className="h-4 w-4" /> Link para criar a chave da API</a>
              <p className="text-xs text-muted-foreground">{providersInfo[newProvider].tut}</p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold flex justify-between">Cole a sua Chave aqui: {isKeyLooksValid(newProvider, newKey) && <span className="text-primary flex items-center text-xs"><CheckCircle2 className="w-3 h-3 mr-1"/> Formato Válido</span>}</label>
              <Input type="password" value={newKey} onChange={(e) => {setNewKey(e.target.value); setTestedFlags(f=>({...f,[type]:false}));}} placeholder="sk-..." className={`rounded-xl py-6 ${newKey && !isKeyLooksValid(newProvider, newKey) ? 'border-destructive' : ''}`} />
            </div>
          </div>
        )}

        {option !== "gratis" && (
          <div className="space-y-4 bg-background p-5 rounded-2xl border border-border/50 shadow-sm">
            <Button onClick={handleFetch} disabled={fetching} variant="secondary" className="w-full rounded-xl py-6 border-primary/20 bg-primary/10 hover:bg-primary/20 text-primary transition-all duration-300 font-bold">
              {fetching ? <><Loader2 className="h-5 w-5 mr-2 animate-spin" /> Conectando à Provedora...</> : "1. Buscar Modelos Disponíveis (Listar da API)"}
            </Button>
            
            {fetching && (
              <div className="animate-pulse space-y-2 mt-4">
                 <div className="h-4 bg-muted rounded w-1/3"></div>
                 <div className="h-14 bg-muted rounded-xl w-full"></div>
              </div>
            )}

            {!fetching && modelsList.length > 0 && (
              <div className="space-y-4 animate-in fade-in mt-6 bg-muted/10 p-4 rounded-xl border border-border/50">
                <label className="text-sm font-bold text-primary block">2. Selecione qual Modelo de Inteligência quer usar:</label>
                <div className="flex flex-col gap-4">
                  <select value={model} onChange={(e) => {setModel(e.target.value); setTestedFlags(f=>({...f,[type]:false}));}} className="flex-1 rounded-xl border-2 border-primary/50 bg-background px-4 py-4 text-sm font-bold shadow-sm focus:border-primary transition-colors">
                    <option value="" disabled>Selecione na lista...</option>
                    {modelsList.filter(m => type !== "stt" || m.toLowerCase().includes("whisper")).map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                  
                  {model && type === "tts" && (
                    <Button onClick={() => playVoiceTest(model, option)} variant="secondary" className="w-full rounded-xl py-4 font-bold shadow-soft bg-background hover:bg-muted border border-border text-primary"><Play className="h-4 w-4 mr-2" /> Ouvir Amostra de Voz Premium</Button>
                  )}
                  
                  {model && (
                    <Button 
                      onClick={() => executeRealAiTest(type)} 
                      disabled={testingModel === type || isTested} 
                      className={`w-full rounded-xl py-6 font-bold shadow-glow text-base ${isTested ? 'bg-primary hover:bg-primary cursor-default text-white' : 'bg-primary hover:bg-primary/90'}`}
                    >
                      {testingModel === type ? (
                         <><Loader2 className="h-5 w-5 mr-2 animate-spin" /> Enviando requisição de teste...</>
                      ) : isTested ? (
                         <><CheckCircle2 className="h-5 w-5 mr-2" /> Validação Concluída com Sucesso!</>
                      ) : (
                         <><Cpu className="h-5 w-5 mr-2" /> 3. Testar Resposta e Saldo da API</>
                      )}
                    </Button>
                  )}
                </div>
              </div>
            )}
            
            {!isTested && modelsList.length > 0 && model && !usedFallback[type] && (
               <div className="bg-amber-500/10 text-amber-600 p-3 rounded-lg text-xs font-semibold flex items-center border border-amber-500/20 mt-2">
                 <AlertTriangle className="h-4 w-4 mr-2" /> Você precisa clicar no botão de testar acima para garantir que sua chave tem saldo antes de prosseguir.
               </div>
            )}

            {!isTested && usedFallback[type] && model && (
               <div className="bg-amber-500/10 text-amber-600 p-3 rounded-lg text-xs font-semibold flex items-start border border-amber-500/20 mt-2">
                 <AlertTriangle className="h-4 w-4 mr-2 shrink-0 mt-0.5" /> Não consegui listar os modelos direto da API, então usei uma lista de modelos conhecidos. Você pode continuar, mas confirme sua chave depois nas Configurações (ou tente testar acima).
               </div>
            )}

            {extraConfig}
          </div>
        )}

        {option === "gratis" && (
          <div className="space-y-4 bg-background p-5 rounded-2xl border border-destructive/20 shadow-sm opacity-90 relative overflow-hidden animate-in fade-in">
            <div className="absolute top-0 right-0 p-8 bg-destructive/5 rounded-bl-full pointer-events-none"></div>
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-destructive shrink-0 mt-1" />
              <div>
                <h4 className="font-bold text-destructive">Atenção: A opção gratuita é severamente Limitada!</h4>
                <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
                  Esta opção roda localmente no nosso próprio servidor e não gasta seus créditos, porém é <strong>EXTREMAMENTE MAIS LENTA</strong> e a voz é altamente robótica. Uma transcrição de áudio grátis pode demorar de 3 a 5 segundos para processar, o que fará seu cliente desligar na cara do robô por achar que a linha caiu. <br/><br/>
                  Se você quer ligações instantâneas (abaixo de 0.8s) e voz hiper-realista, crie uma chave da Groq ou ElevenLabs nas opções acima.
                </p>
              </div>
            </div>
            
            {type === "tts" && (
               <div className="pt-4 border-t border-border/50">
                 <label className="text-sm font-bold text-primary block mb-3">Selecione uma voz gratuita (Edge TTS / Local):</label>
                 <select value={model} onChange={(e) => setModel(e.target.value)} className="w-full flex-1 rounded-xl border-2 border-primary/50 bg-background px-4 py-4 text-sm font-bold shadow-sm focus:border-primary transition-colors">
                   <option value="" disabled>Selecione...</option>
                   {edgeVoices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                 </select>
                 {model && (
                   <Button onClick={(e) => { e.preventDefault(); playVoiceTest(model, "gratis"); }} variant="secondary" className="w-full mt-3 rounded-xl py-4 font-bold shadow-soft bg-background hover:bg-muted border border-border text-primary"><Play className="h-4 w-4 mr-2" /> Ouvir Amostra de Voz Grátis</Button>
                 )}
               </div>
            )}
            
            {extraConfig}
          </div>
        )}
      </div>
    );
  };

  if (!loaded) return null;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {step !== "welcome" && step !== "finish" && (
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8 px-4 text-[10px] sm:text-xs font-medium text-muted-foreground bg-glass border border-border/50 rounded-full py-3 shadow-soft sticky top-2 z-10 overflow-x-auto no-scrollbar whitespace-nowrap">
          <span className={step === "credentials" ? "text-primary font-bold" : ""}>Chaves</span><ChevronRight className="h-3 w-3 opacity-30" />
          <span className={step === "llm_text" ? "text-primary font-bold" : ""}>Texto</span><ChevronRight className="h-3 w-3 opacity-30" />
          <span className={step === "stt" ? "text-primary font-bold" : ""}>Audição</span><ChevronRight className="h-3 w-3 opacity-30" />
          <span className={step === "tts" ? "text-primary font-bold" : ""}>Falar</span><ChevronRight className="h-3 w-3 opacity-30" />
          <span className={step === "manager_chat" ? "text-primary font-bold" : ""}>Gestor</span><ChevronRight className="h-3 w-3 opacity-30" />
          <span className={step === "appearance" ? "text-primary font-bold" : ""}>Visual</span><ChevronRight className="h-3 w-3 opacity-30" />
          <span className={step === "team" ? "text-primary font-bold" : ""}>Equipe</span><ChevronRight className="h-3 w-3 opacity-30" />
          <span className={step === "alerts" ? "text-primary font-bold" : ""}>Alertas</span><ChevronRight className="h-3 w-3 opacity-30" />
          <span className={step === "crm" ? "text-primary font-bold" : ""}>CRM</span><ChevronRight className="h-3 w-3 opacity-30" />
          <span className={step === "summary" ? "text-primary font-bold" : ""}>Resumo</span>
        </div>
      )}

      {step === "welcome" && (
        <Card className="p-10 text-center bg-gradient-to-br from-primary/10 via-background to-background border-primary/20 shadow-glow rounded-3xl animate-in zoom-in-95 duration-500">
          <div className="mx-auto w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mb-6"><Wand2 className="h-12 w-12 text-primary" /></div>
          <h2 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-emerald-400 drop-shadow-sm mb-4">Configuração Guiada Premium</h2>
          <p className="text-muted-foreground text-lg mb-8 max-w-2xl mx-auto">Vamos preparar sua plataforma de ponta a ponta. Configure IAs, automações e a identidade da sua marca em poucos passos.</p>
          <Button onClick={() => setStep("credentials")} className="px-10 py-6 text-lg rounded-xl shadow-glow">Iniciar Jornada <ChevronRight className="ml-2 h-5 w-5" /></Button>
        </Card>
      )}

      {step === "credentials" && (
        <Card className="p-8 bg-background/50 border-primary/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500">
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-primary/10 rounded-2xl"><KeyRound className="h-8 w-8 text-primary" /></div><div><h3 className="text-2xl font-bold">1. Cofre de Chaves</h3><p className="text-muted-foreground">Opcional: Salve suas API Keys aqui para puxar rápido nas próximas telas.</p></div></div>
          <div className="space-y-8">
            <div className="grid grid-cols-1 gap-4 bg-muted/20 p-6 rounded-2xl border border-dashed border-border/50">
              <h4 className="font-semibold text-lg">Adicionar Nova Chave</h4>
              <select value={newCredProvider} onChange={(e) => setNewCredProvider(e.target.value)} className="w-full rounded-xl border border-input bg-background px-4 py-3 text-sm shadow-sm">{Object.entries(providersInfo).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}</select>
              <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-2"><a href={providersInfo[newCredProvider].link} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm font-bold text-primary hover:underline"><ExternalLink className="h-4 w-4" /> Link para criar a chave no provedor</a><p className="text-xs text-muted-foreground">{providersInfo[newCredProvider].tut}</p></div>
              <div className="flex flex-col gap-2">
                <div className="flex flex-col sm:flex-row gap-2">
                  <Input type="password" value={newCredKey} onChange={(e) => setNewCredKey(e.target.value)} placeholder="sk-..." className={`rounded-xl flex-1 ${newCredKey && !isKeyLooksValid(newCredProvider, newCredKey) ? 'border-destructive' : ''}`} />
                  <div className="flex items-center gap-2 bg-background px-3 py-2 rounded-xl border border-border/50">
                     <input type="checkbox" id="chk-fallback" checked={newCredFallback} onChange={(e) => setNewCredFallback(e.target.checked)} className="rounded border-border/50" />
                     <label htmlFor="chk-fallback" className="text-xs font-semibold cursor-pointer whitespace-nowrap">Adicionar Fallback</label>
                  </div>
                </div>
                
                {newCredFallback && (
                  <div className="bg-amber-500/10 border border-amber-500/20 p-4 rounded-xl mt-2 animate-in fade-in space-y-3">
                    <h5 className="text-sm font-bold text-amber-500 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" /> Configurar Credencial Reserva (Fallback)
                    </h5>
                    <p className="text-xs text-muted-foreground">Se a chave principal falhar (fora do ar ou sem saldo), o sistema usará esta chave reserva automaticamente.</p>
                    <div className="flex gap-2">
                      <select value={fallbackProvider} onChange={(e) => setFallbackProvider(e.target.value)} className="w-1/3 rounded-xl border border-input bg-background px-3 py-2 text-sm shadow-sm">{Object.entries(providersInfo).map(([k, v]) => <option key={k} value={k}>{v.name}</option>)}</select>
                      <Input type="password" value={fallbackKey} onChange={(e) => setFallbackKey(e.target.value)} placeholder="sk-..." className="rounded-xl flex-1" />
                    </div>
                  </div>
                )}
                
                <Button onClick={() => { 
                  if (!newCredKey.trim()) return toast.error("Preencha a chave principal."); 
                  if (newCredFallback && !fallbackKey.trim()) return toast.error("Preencha a chave de fallback."); 
                  
                  const creds = [...credentials, { id: Math.random().toString(), provider: newCredProvider, key: newCredKey }];
                  if (newCredFallback) {
                    creds.push({ id: Math.random().toString(), provider: fallbackProvider, key: fallbackKey, isFallback: true });
                  }
                  setCredentials(creds); 
                  setNewCredKey(""); 
                  setFallbackKey("");
                  setNewCredFallback(false); 
                  toast.success("Chave(s) salva(s) no cofre!"); 
                }} className="rounded-xl mt-2"><Plus className="h-4 w-4 mr-1" /> Salvar Cofre</Button>
              </div>
            </div>
            {credentials.length > 0 && (
              <div className="space-y-3"><h4 className="font-semibold text-lg">Chaves no Cofre:</h4><div className="grid gap-2">{credentials.map((cred) => (<div key={cred.id} className="flex items-center justify-between p-3 rounded-xl border border-border/50 bg-background"><div className="flex items-center gap-3"><CheckCircle2 className="h-5 w-5 text-primary" /><span className="font-bold">{providersInfo[cred.provider]?.name || cred.provider} {cred.isFallback && <Badge variant="outline" className="ml-2 text-[10px] bg-amber-500/10 text-amber-500 border-amber-500/20">Fallback</Badge>}</span><span className="text-xs text-muted-foreground">•••• {cred.key.slice(-4)}</span></div><Button variant="ghost" size="icon" onClick={() => setCredentials(credentials.filter(c => c.id !== cred.id))} className="text-destructive"><Trash2 className="h-4 w-4" /></Button></div>))}</div></div>
            )}
            <div className="flex justify-between pt-6 border-t border-border/50 mt-6"><Button variant="ghost" onClick={() => setStep("welcome")}><ChevronLeft className="mr-2 h-4 w-4" /> Voltar</Button><Button onClick={() => savePartial("credentials", "llm_text", false)} disabled={saving} className="rounded-xl px-8 shadow-glow">{saving ? "Salvando..." : "Salvar e Continuar"} <ChevronRight className="ml-2 h-4 w-4" /></Button></div>
          </div>
        </Card>
      )}

      {step === "llm_text" && (
        <Card className="p-8 bg-background/50 border-primary/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500">
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-primary/10 rounded-2xl"><BrainCircuit className="h-8 w-8 text-primary" /></div><div><h3 className="text-2xl font-bold">2. O Cérebro Principal (Texto)</h3><p className="text-muted-foreground mt-1">Este modelo é quem processa as regras de negócio e cria a inteligência real por trás das conversas telefônicas. <strong className="text-primary">Não há opção gratuita para esta etapa</strong>, pois requer muita velocidade de processamento avançado.</p></div></div>
          <div className="space-y-6">
            {renderAiSetup("text", false, textOption, setTextOption, textSavedId, setTextSavedId, textNewProv, setTextNewProv, textNewKey, setTextNewKey, textModel, setTextModel, textModelsList, setTextModelsList, fetchingText, setFetchingText,
              (<div className="space-y-4 pt-4 mt-4 border-t border-border/50 animate-in fade-in"><label className="text-sm font-semibold flex items-center justify-between">Temperatura (Criatividade) <span>{textTemp}</span></label><p className="text-xs text-muted-foreground mb-2">Valores próximos a 0 fazem o robô dar respostas diretas e lógicas. Próximos a 1, ele fica altamente criativo e conversacional.</p><Slider value={[textTemp]} min={0} max={1} step={0.1} onValueChange={(v) => setTextTemp(v[0])} /></div>)
            )}
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-6 border-t border-border/50">
              <Button variant="ghost" onClick={() => setStep("credentials")} className="w-full sm:w-auto"><ChevronLeft className="mr-2 h-4 w-4" /> Voltar</Button>
              <div className="flex flex-col items-end gap-1 w-full sm:w-auto">
                 <Button onClick={() => savePartial("llm_text", "stt", true)} disabled={saving} className="rounded-xl px-8 shadow-glow w-full sm:w-auto">{saving ? "Salvando..." : "Salvar e Continuar"} <ChevronRight className="ml-2 h-4 w-4" /></Button>
                 <button onClick={() => forceBypass("stt")} className="text-[10px] text-muted-foreground hover:text-primary underline">Pular validação (Apenas DEV local)</button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {step === "stt" && (
        <Card className="p-8 bg-background/50 border-sky-500/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500">
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-sky-500/10 rounded-2xl"><Ear className="h-8 w-8 text-sky-500" /></div><div><h3 className="text-2xl font-bold">3. Audição (Whisper)</h3><p className="text-muted-foreground mt-1">Este é o "ouvido" da IA. Ele é responsável por transcrever exatamente o que a pessoa falou na ligação para que o Cérebro possa ler.</p></div></div>
          <div className="space-y-6">
            <div className="bg-sky-500/10 p-5 rounded-2xl border border-sky-500/20 text-sm text-sky-600 dark:text-sky-400 font-bold">Recomendamos FORTEMENTE utilizar o Groq (pois é incrivelmente rápido e o crédito é praticamente de graça) em vez do Whisper Local nativo (que é lento e trava a ligação).</div>
            {renderAiSetup("stt", true, sttOption, setSttOption, sttSavedId, setSttSavedId, sttNewProv, setSttNewProv, sttNewKey, setSttNewKey, sttModel, setSttModel, sttModelsList, setSttModelsList, fetchingStt, setFetchingStt,
              (<div className="space-y-3 pt-4 mt-4 border-t border-border/50 animate-in fade-in"><label className="text-sm font-semibold">Idioma Forçado da Audição</label><p className="text-xs text-muted-foreground mb-2">Forçar a língua evita que o Whisper se confunda com chiados e traduza errado.</p><select value={sttLang} onChange={(e) => setSttLang(e.target.value)} className="w-full rounded-xl border border-input bg-background px-4 py-3 text-sm"><option value="pt">Português (Brasil)</option><option value="en">Inglês (US)</option><option value="es">Espanhol</option></select></div>)
            )}
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-6 border-t border-border/50">
              <Button variant="ghost" onClick={() => setStep("llm_text")} className="w-full sm:w-auto"><ChevronLeft className="mr-2 h-4 w-4" /> Voltar</Button>
              <div className="flex flex-col items-end gap-1 w-full sm:w-auto">
                 <Button onClick={() => savePartial("stt", "tts", true)} disabled={saving} className="rounded-xl px-8 shadow-glow bg-sky-600 hover:bg-sky-700 text-white w-full sm:w-auto">{saving ? "Salvando..." : "Salvar e Continuar"} <ChevronRight className="ml-2 h-4 w-4" /></Button>
                 <button onClick={() => forceBypass("tts")} className="text-[10px] text-muted-foreground hover:text-sky-500 underline">Pular validação (Apenas DEV local)</button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {step === "tts" && (
        <Card className="p-8 bg-background/50 border-teal-500/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500">
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-teal-500/10 rounded-2xl"><Volume2 className="h-8 w-8 text-teal-500" /></div><div><h3 className="text-2xl font-bold">4. A Voz (Falar)</h3><p className="text-muted-foreground mt-1">Quem gera a voz falada do robô. A opção Grátis/Local roda direto na máquina, mas soa robótica. A ElevenLabs gera vozes idênticas a de humanos reais.</p></div></div>
          <div className="space-y-6">
            {renderAiSetup("tts", true, ttsOption, setTtsOption, ttsSavedId, setTtsSavedId, ttsNewProv, setTtsNewProv, ttsNewKey, setTtsNewKey, ttsModel, setTtsModel, ttsModelsList, setTtsModelsList, fetchingTts, setFetchingTts,
              (
                <>
                  <div className="space-y-4 pt-4 mt-4 border-t border-border/50 animate-in fade-in"><label className="text-sm font-semibold flex items-center justify-between">Velocidade da Fala <span>{ttsSpeed}x</span></label><Slider value={[ttsSpeed]} min={0.5} max={2.0} step={0.1} onValueChange={(v) => setTtsSpeed(v[0])} /></div>
                  <div className="space-y-4 pt-4 mt-4 border-t border-border/50 animate-in fade-in">
                    <div onClick={() => setTtsAmbient(!ttsAmbient)} className={`p-4 rounded-xl border-2 flex justify-between items-center cursor-pointer transition-all ${ttsAmbient ? "border-teal-500 bg-teal-500/10" : "border-border/50 opacity-50"}`}>
                      <div>
                        <h4 className="font-semibold text-sm">Adicionar Som Ambiente (Fundo)</h4>
                        <p className="text-xs text-muted-foreground mt-1">Toca um áudio no fundo das ligações (ex: escritório) para parecer um humano real numa sala.</p>
                      </div>
                      {ttsAmbient && <CheckCircle2 className="text-teal-500" />}
                    </div>
                    {ttsAmbient && (
                      <div className="space-y-2 mt-3 pl-2">
                        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Qual ambiente deseja simular?</label>
                        <select value={ttsAmbientType} onChange={(e) => setTtsAmbientType(e.target.value)} className="w-full rounded-xl border border-input bg-background px-4 py-3 text-sm">
                          <option value="office">🏢 Escritório (Teclados, Telefones ao fundo)</option>
                          <option value="street">🛣️ Rua (Trânsito sutil, Passos leves)</option>
                          <option value="cafe">☕ Cafeteria (Conversas abafadas, Copos)</option>
                        </select>
                      </div>
                    )}
                  </div>
                </>
              )
            )}
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-6 border-t border-border/50">
              <Button variant="ghost" onClick={() => setStep("stt")} className="w-full sm:w-auto"><ChevronLeft className="mr-2 h-4 w-4" /> Voltar</Button>
              <div className="flex flex-col items-end gap-1 w-full sm:w-auto">
                 <Button onClick={() => savePartial("tts", "manager_chat", true)} disabled={saving} className="rounded-xl px-8 shadow-glow bg-teal-600 hover:bg-teal-700 text-white w-full sm:w-auto">{saving ? "Salvando..." : "Salvar e Continuar"} <ChevronRight className="ml-2 h-4 w-4" /></Button>
                 <button onClick={() => forceBypass("manager_chat")} className="text-[10px] text-muted-foreground hover:text-teal-500 underline">Pular validação (Apenas DEV local)</button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {step === "manager_chat" && (
        <Card className="p-8 bg-background/50 border-violet-500/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500">
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-violet-500/10 rounded-2xl"><MessageSquare className="h-8 w-8 text-violet-500" /></div><div><h3 className="text-2xl font-bold">5. Gestor de Inteligência</h3><p className="text-muted-foreground mt-1">O Gestor é um <strong className="text-violet-500">Assistente Pessoal VIP que trabalha SÓ para você</strong>. Ele NÃO fala com clientes da rua. Ele fica no seu WhatsApp ou Telegram. É para ele que você manda mensagem perguntando: "Quantas vendas fiz hoje?" ou "Toca um resumo da última ligação".</p></div></div>
          <div className="space-y-6">
            <div className="bg-violet-500/10 p-5 rounded-2xl border border-violet-500/20 text-sm text-violet-600 dark:text-violet-400 font-bold mb-4">Escolha o canal onde você prefere conversar no privado com o seu Gestor de IA:</div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div onClick={() => setChatChannel("panel")} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${chatChannel === "panel" ? "border-violet-500 bg-violet-500/10 shadow-glow" : "border-border/50 hover:border-violet-500/50"}`}><div className="font-semibold mb-1 flex items-center"><LayoutDashboard className="w-4 h-4 mr-2"/> Aqui mesmo no Painel</div><div className="text-xs text-muted-foreground">O chat flutuante embutido neste site administrativo.</div></div>
              <div onClick={() => setChatChannel("telegram_bot")} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${chatChannel === "telegram_bot" ? "border-violet-500 bg-violet-500/10 shadow-glow" : "border-border/50 hover:border-violet-500/50"}`}><div className="font-semibold mb-1 flex items-center"><MessageSquare className="w-4 h-4 mr-2 text-sky-500"/> Bot do Telegram</div><div className="text-xs text-muted-foreground">Uma conversa direto no seu Telegram pessoal via Bot.</div></div>
              <div onClick={() => setChatChannel("whatsapp_pv")} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${chatChannel === "whatsapp_pv" ? "border-primary bg-primary/10 shadow-glow" : "border-border/50 hover:border-primary/50"}`}><div className="font-semibold mb-1 flex items-center"><MessageSquare className="w-4 h-4 mr-2 text-primary"/> WhatsApp (Privado)</div><div className="text-xs text-muted-foreground">O gestor se loga num número de WhatsApp exclusivo para você.</div></div>
              <div onClick={() => setChatChannel("whatsapp_group")} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${chatChannel === "whatsapp_group" ? "border-primary bg-primary/10 shadow-glow" : "border-border/50 hover:border-primary/50"}`}><div className="font-semibold mb-1 flex items-center"><Users className="w-4 h-4 mr-2 text-primary"/> WhatsApp (No Grupo)</div><div className="text-xs text-muted-foreground">Ele participa de um grupo da equipe jogando alertas lá.</div></div>
            </div>

            {chatChannel === "telegram_bot" && (
              <div className="space-y-6 animate-in fade-in bg-violet-500/10 p-5 rounded-2xl border border-violet-500/20 mt-4">
                <div>
                  <h4 className="font-bold text-violet-500 mb-2">Passo A: Token do Bot</h4>
                  <div className="text-sm space-y-1 text-muted-foreground mb-3">
                    <p>1. Abra o Telegram, pesquise por <strong>@BotFather</strong>.</p>
                    <p>2. Envie o comando <code className="bg-background px-1 rounded">/newbot</code>, dê um nome e copie o Token enorme que ele entregar.</p>
                  </div>
                  <div className="flex gap-2">
                    <Input value={botToken} onChange={(e) => {setBotToken(e.target.value); setBotVerified(null);}} placeholder="Ex: 123456789:AAH..." className="rounded-xl py-6 border-violet-500/30 flex-1" />
                    <Button onClick={testTelegram} variant="outline" className="rounded-xl py-6 text-violet-500 border-violet-500/30 hover:bg-violet-500/10 font-bold"><CheckCircle2 className="w-4 h-4 mr-2"/> Validar Token</Button>
                  </div>
                  {botVerified && (
                     <div className="mt-3 bg-primary/20 text-primary p-3 rounded-lg text-sm font-bold flex items-center border border-primary/30">
                        <CheckCircle2 className="w-4 h-4 mr-2" /> Bot "{botVerified.name}" (@{botVerified.user}) validado! API Conectada.
                     </div>
                  )}
                </div>
                
                <div className="pt-4 border-t border-violet-500/20">
                  <h4 className="font-bold text-violet-500 mb-2">Passo B: ID da sua Conversa Pessoal (Chat ID)</h4>
                  <div className="text-sm space-y-1 text-muted-foreground mb-3">
                    <p>Para o Gestor poder te avisar proativamente quando vender (push notifications), ele precisa do ID da SUA conta do Telegram.</p>
                    <p>Pesquise por <strong>@userinfobot</strong> no Telegram, envie <code className="bg-background px-1 rounded">/start</code> e copie o número que diz "Id:"</p>
                  </div>
                  <Input value={chatId} onChange={(e) => setChatId(e.target.value)} placeholder="Ex: 12345678" className="rounded-xl py-6 border-violet-500/30" />
                </div>
              </div>
            )}

            <div className="pt-6 border-t border-border/50 space-y-4">
               <div className="mb-4">
                 <h4 className="font-bold text-lg">Módulos de Inteligência do Gestor</h4>
                 <p className="text-sm text-muted-foreground">Ative os módulos complementares que tornarão o seu Agente Gestor ainda mais inteligente e proativo.</p>
                 <div className="mt-2 inline-flex items-center gap-2 bg-amber-500/10 text-amber-600 border border-amber-500/20 px-3 py-1.5 rounded-lg text-xs font-semibold">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Atenção: Ativar estes módulos aumenta significativamente o consumo de tokens.</span>
                 </div>
               </div>
               
               <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div onClick={() => setManagerCognitive(!managerCognitive)} className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${managerCognitive ? "border-primary bg-primary/10 shadow-glow" : "border-border/50 hover:border-primary/50"}`}>
                     <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-sm">Motor Cognitivo</h4>
                        {managerCognitive && <CheckCircle2 className="w-4 h-4 text-primary" />}
                     </div>
                     <p className="text-xs text-muted-foreground">Permite ao Gestor analisar sentimentos, detectar urgências e pensar estrategicamente, não apenas dar respostas programadas.</p>
                  </div>
                  
                  <div onClick={() => setManagerRag(!managerRag)} className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${managerRag ? "border-primary bg-primary/10 shadow-glow" : "border-border/50 hover:border-primary/50"}`}>
                     <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-sm">RAG (Memória)</h4>
                        {managerRag && <CheckCircle2 className="w-4 h-4 text-primary" />}
                     </div>
                     <p className="text-xs text-muted-foreground">Conecta o Gestor à base de dados da empresa para que ele lembre do histórico de clientes e documentos ao responder.</p>
                  </div>
                  
                  <div onClick={() => setManagerTools(!managerTools)} className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${managerTools ? "border-primary bg-primary/10 shadow-glow" : "border-border/50 hover:border-primary/50"}`}>
                     <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-sm">Uso de Ferramentas</h4>
                        {managerTools && <CheckCircle2 className="w-4 h-4 text-primary" />}
                     </div>
                     <p className="text-xs text-muted-foreground">Dá permissão ao Gestor para executar ações reais, como enviar e-mails, acionar webhooks e agendar reuniões.</p>
                  </div>
               </div>
            </div>

            {chatChannel === "whatsapp_pv" && (
              <div className="space-y-4 animate-in fade-in bg-primary/10 p-5 rounded-2xl border border-primary/20 text-primary text-sm font-semibold mt-4">
                Para plugar o Gestor no WhatsApp Privado, basta ir na aba principal "Central de Telefonia" e escanear o QRCode com um celular que será o número exclusivo do Gestor.
              </div>
            )}
            
            {chatChannel === "whatsapp_group" && (
              <div className="space-y-4 animate-in fade-in bg-primary/10 p-5 rounded-2xl border border-primary/20 mt-4">
                <h4 className="font-bold text-primary dark:text-primary">Qual será o nome do Grupo da Equipe?</h4>
                <div className="text-sm space-y-1 text-emerald-700/80 dark:text-primary/80 mb-3">
                  <p>O Gestor vai criar um grupo novo no WhatsApp e te colocar como administrador para ele enviar os relatórios diários e alertas de vendas lá dentro.</p>
                </div>
                <div className="flex gap-2">
                   <Input value={wppGroupName} onChange={(e) => {setWppGroupName(e.target.value); setWppGroupCreated(false);}} placeholder="Ex: Equipe de Vendas" className="rounded-xl py-6 border-primary/30 flex-1 border-2" />
                   <Button onClick={async () => {
                     if(!wppGroupName) return toast.error("Digite um nome para o grupo!");
                     try {
                       await apiPost("/api/settings/agent-chat/create-group", { name: wppGroupName });
                       toast.success(`Grupo "${wppGroupName}" criado no WhatsApp!`);
                       setWppGroupCreated(true);
                     } catch (e) {
                       setWppGroupCreated(false);
                       toast.error("Não consegui criar o grupo", { description: (e as Error).message });
                     }
                   }} className="rounded-xl py-6 px-6 bg-primary hover:bg-primary/90 text-white font-bold"><Users className="w-5 h-5 mr-2"/> Cadastrar Grupo</Button>
                </div>
                {wppGroupCreated && (
                   <div className="mt-3 bg-primary/20 text-primary p-3 rounded-lg text-sm font-bold flex items-center border border-primary/30">
                      <CheckCircle2 className="w-4 h-4 mr-2" /> Grupo "{wppGroupName}" agendado com sucesso. Ele será criado pelo número do robô na Central.
                   </div>
                )}
              </div>
            )}

            <div className="flex justify-between pt-6 border-t border-border/50"><Button variant="ghost" onClick={() => setStep("tts")}><ChevronLeft className="mr-2 h-4 w-4" /> Voltar</Button><Button onClick={() => savePartial("manager_chat", "appearance")} disabled={saving} className="rounded-xl px-8 shadow-glow bg-primary hover:bg-primary/90 text-primary-foreground">{saving ? "Salvando..." : "Salvar e Continuar"} <ChevronRight className="ml-2 h-4 w-4" /></Button></div>
          </div>
        </Card>
      )}

      {step === "appearance" && (
        <Card className="p-8 bg-background/50 border-primary/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500">
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-primary/10 rounded-2xl"><Palette className="h-8 w-8 text-primary" /></div><div><h3 className="text-2xl font-bold">6. Identidade Visual</h3><p className="text-muted-foreground">A cara da sua empresa no sistema. A cor escolhida aqui vai alterar todos os botões e painéis da plataforma em tempo real.</p></div></div>
          <div className="flex flex-col md:flex-row gap-8">
            <div className="space-y-6 flex-1">
              <div className="space-y-3"><label className="text-sm font-semibold">Nome da Empresa (Workspace)</label><Input value={workspaceName} onChange={(e) => setWorkspaceName(e.target.value)} placeholder="Ex: Acme Corp" className="rounded-xl py-6 text-lg" /></div>
              <div className="space-y-6">
                 <div>
                   <label className="text-sm font-semibold">Cor Principal (Botões e Destaques)</label>
                   <div className="flex flex-col items-start gap-2 mt-1">
                     <div className="flex gap-4">
                       <input type="color" value={brandColor} onChange={(e) => setBrandColor(e.target.value)} className="h-14 w-20 rounded-xl cursor-pointer border-0 bg-transparent p-0" /> 
                       <span className="text-xs text-muted-foreground self-center">Muda botões, toggles, badges e destaques visuais.</span>
                     </div>
                   </div>
                 </div>

                 <div>
                   <label className="text-sm font-semibold">Cor de Fundo (Painéis e Interface)</label>
                   <div className="flex flex-col items-start gap-2 mt-1">
                     <div className="flex gap-4">
                       <input type="color" value={bgColor} onChange={(e) => setBgColor(e.target.value)} className="h-14 w-20 rounded-xl cursor-pointer border-0 bg-transparent p-0" /> 
                       <span className="text-xs text-muted-foreground self-center">Altera o fundo global, menu lateral e os cartões flutuantes.</span>
                     </div>
                     {(brandColor !== "#10b981" || bgColor !== "#09090b") && (
                       <Button variant="outline" size="sm" onClick={resetToDefault} className="mt-2 h-8 text-xs font-bold"><RotateCcw className="w-3 h-3 mr-2"/> Restaurar Cores Padrão</Button>
                     )}
                   </div>
                 </div>
              </div>
            </div>
            
            <div className="w-full md:w-64 bg-card rounded-2xl border border-border/50 shadow-soft p-4 flex flex-col gap-4">
               <div className="text-xs font-bold text-muted-foreground mb-2">PREVIEW EM TEMPO REAL</div>
               <div className="flex items-center gap-2 mb-4">
                 <div className="w-8 h-8 rounded-lg shadow-sm" style={{ backgroundColor: brandColor }}></div>
                 <span className="font-black text-sm">{workspaceName || "Sua Empresa"}</span>
               </div>
               <div className="space-y-2">
                 <div className="h-8 rounded-lg opacity-20" style={{ backgroundColor: brandColor }}></div>
                 <div className="h-8 bg-muted rounded-lg"></div>
                 <div className="h-8 bg-muted rounded-lg"></div>
               </div>
               <div className="mt-auto h-10 rounded-lg flex items-center justify-center text-white text-xs font-bold shadow-md" style={{ backgroundColor: brandColor }}>Botão de Ação</div>
            </div>
          </div>
          <div className="flex justify-between pt-6 border-t border-border/50 mt-6"><Button variant="ghost" onClick={() => setStep("manager_chat")}><ChevronLeft className="mr-2 h-4 w-4" /> Voltar</Button><Button onClick={() => savePartial("appearance", "team")} disabled={saving} className="rounded-xl px-8 shadow-glow bg-primary hover:bg-primary/90 text-primary-foreground">{saving ? "Salvando..." : "Salvar e Continuar"} <ChevronRight className="ml-2 h-4 w-4" /></Button></div>
        </Card>
      )}

      {step === "team" && (
        <Card className="p-8 bg-background/50 border-orange-500/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500">
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-orange-500/10 rounded-2xl"><Users className="h-8 w-8 text-orange-500" /></div><div><h3 className="text-2xl font-bold">7. Colaboradores (Humanos)</h3><p className="text-muted-foreground mt-1">Aqui você cria o acesso para os membros reais da sua equipe, como vendedores ou suporte, que vão logar no painel e falar com os clientes.</p></div></div>
          <div className="space-y-6">
            <div className="bg-orange-500/10 p-5 rounded-2xl border border-orange-500/20">
               <h4 className="font-semibold text-lg mb-4">Cadastrar Novo Colaborador</h4>
               <div className="flex gap-2">
                 <Input type="email" id="t_email" placeholder="Email do colaborador (vendedor@empresa.com)" className="rounded-xl py-6 flex-1" />
                 <Input type="password" id="t_pass" placeholder="Senha provisória" className="rounded-xl py-6 flex-1" />
                 <Button onClick={() => {
                   const em = (document.getElementById("t_email") as HTMLInputElement).value;
                   const pa = (document.getElementById("t_pass") as HTMLInputElement).value;
                   if(!em || !pa) return toast.error("Preencha email e senha.");
                   setTeamMembers([...teamMembers, { id: Math.random().toString(), email: em, pass: pa }]);
                   (document.getElementById("t_email") as HTMLInputElement).value = "";
                   (document.getElementById("t_pass") as HTMLInputElement).value = "";
                   toast.success("Colaborador agendado para criação!");
                 }} className="rounded-xl py-6 px-6 bg-orange-600 hover:bg-orange-700 text-white font-bold"><Plus className="w-4 h-4 mr-2"/> Adicionar</Button>
               </div>
            </div>
            
            {teamMembers.length > 0 && (
              <div className="space-y-3"><h4 className="font-semibold text-lg">Colaboradores Agendados:</h4><div className="grid gap-2">{teamMembers.map((m) => (<div key={m.id} className="flex items-center justify-between p-3 rounded-xl border border-border/50 bg-background"><div className="flex items-center gap-3"><Users className="h-5 w-5 text-orange-500" /><span className="font-bold">{m.email}</span><span className="text-xs text-muted-foreground">Senha: {m.pass}</span></div><Button variant="ghost" size="icon" onClick={() => setTeamMembers(teamMembers.filter(c => c.id !== m.id))} className="text-destructive"><Trash2 className="h-4 w-4" /></Button></div>))}</div></div>
            )}
            
            <div className="flex justify-between pt-6 border-t border-border/50"><Button variant="ghost" onClick={() => setStep("appearance")}><ChevronLeft className="mr-2 h-4 w-4" /> Voltar</Button><Button onClick={() => savePartial("team", "alerts")} disabled={saving} className="rounded-xl px-8 shadow-glow bg-orange-600 hover:bg-orange-700 text-white">{saving ? "Salvando..." : teamMembers.length ? "Salvar Colaboradores e Continuar" : "Pular sem Equipe"} <ChevronRight className="ml-2 h-4 w-4" /></Button></div>
          </div>
        </Card>
      )}

      {step === "alerts" && (
        <Card className="p-8 bg-background/50 border-yellow-500/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500">
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-yellow-500/10 rounded-2xl"><Bell className="h-8 w-8 text-yellow-500" /></div><div><h3 className="text-2xl font-bold">8. Alertas Automáticos</h3><p className="text-muted-foreground mt-1">O que a IA deve te avisar proativamente e quando ela deve chamar a sua atenção.</p></div></div>
          <div className="space-y-4">
            <h4 className="font-bold text-lg">Alertas Pré-Programados (Clique para ligar/desligar):</h4>
            <div onClick={() => setAlerts(s=>({...s,sales:!s.sales}))} className={`p-4 rounded-xl border-2 flex justify-between items-center cursor-pointer transition-all ${alerts.sales ? "border-yellow-500 bg-yellow-500/10" : "border-border/50 opacity-50"}`}><div><h4 className="font-semibold">Avisar sobre Nova Venda ou Reunião Marcada</h4></div>{alerts.sales && <CheckCircle2 className="text-yellow-500" />}</div>
            <div onClick={() => setAlerts(s=>({...s,newLead:!s.newLead}))} className={`p-4 rounded-xl border-2 flex justify-between items-center cursor-pointer transition-all ${alerts.newLead ? "border-yellow-500 bg-yellow-500/10" : "border-border/50 opacity-50"}`}><div><h4 className="font-semibold">Avisar sempre que um Novo Lead for capturado</h4></div>{alerts.newLead && <CheckCircle2 className="text-yellow-500" />}</div>
            <div onClick={() => setAlerts(s=>({...s,errors:!s.errors}))} className={`p-4 rounded-xl border-2 flex justify-between items-center cursor-pointer transition-all ${alerts.errors ? "border-yellow-500 bg-yellow-500/10" : "border-border/50 opacity-50"}`}><div><h4 className="font-semibold">Transbordo: Avisar se o Cliente pedir para falar com um Humano real</h4></div>{alerts.errors && <CheckCircle2 className="text-yellow-500" />}</div>
            <div onClick={() => setAlerts(s=>({...s,lost:!s.lost}))} className={`p-4 rounded-xl border-2 flex justify-between items-center cursor-pointer transition-all ${alerts.lost ? "border-yellow-500 bg-yellow-500/10" : "border-border/50 opacity-50"}`}><div><h4 className="font-semibold">Avisar se o Cliente se irritar ou abandonar a ligação cedo</h4></div>{alerts.lost && <CheckCircle2 className="text-yellow-500" />}</div>
            <div onClick={() => setAlerts(s=>({...s,summary:!s.summary}))} className={`p-4 rounded-xl border-2 flex justify-between items-center cursor-pointer transition-all ${alerts.summary ? "border-yellow-500 bg-yellow-500/10" : "border-border/50 opacity-50"}`}><div><h4 className="font-semibold">Me enviar um Resumo de Vendas todo final de dia</h4></div>{alerts.summary && <CheckCircle2 className="text-yellow-500" />}</div>
            
            <div className="pt-6 mt-4 border-t border-border/50">
               <h4 className="font-bold text-lg mb-4">Regras Customizadas de Alertas</h4>
               <div className="flex gap-2">
                 <Input value={newCustomAlert} onChange={(e) => setNewCustomAlert(e.target.value)} placeholder="Ex: Me avise se o cliente falar a palavra 'processo judicial'" className="rounded-xl py-6 flex-1 border-2 border-yellow-500/30" />
                 <Button onClick={() => {
                   if(!newCustomAlert.trim()) return toast.error("Escreva a regra.");
                   setCustomAlerts([...customAlerts, { id: Math.random().toString(), text: newCustomAlert }]);
                   setNewCustomAlert("");
                   toast.success("Regra de alerta adicionada!");
                 }} className="rounded-xl py-6 px-6 bg-yellow-600 hover:bg-yellow-700 text-white font-bold"><Plus className="w-4 h-4 mr-2"/> Adicionar Regra</Button>
               </div>
               
               {customAlerts.length > 0 && (
                 <div className="mt-4 space-y-2">
                   {customAlerts.map(al => (
                      <div key={al.id} className="flex items-center justify-between p-3 rounded-xl border border-yellow-500/30 bg-yellow-500/5">
                        <span className="font-semibold text-sm">{al.text}</span>
                        <Button variant="ghost" size="icon" onClick={() => setCustomAlerts(customAlerts.filter(x => x.id !== al.id))} className="text-destructive h-6 w-6"><Trash2 className="h-4 w-4" /></Button>
                      </div>
                   ))}
                 </div>
               )}
            </div>

            <div className="flex justify-between pt-6 border-t border-border/50 mt-4"><Button variant="ghost" onClick={() => setStep("team")}><ChevronLeft className="mr-2 h-4 w-4" /> Voltar</Button><Button onClick={() => savePartial("alerts", "crm")} disabled={saving} className="rounded-xl px-8 shadow-glow bg-yellow-600 hover:bg-yellow-700 text-white">{saving ? "Salvando..." : "Salvar e Continuar"} <ChevronRight className="ml-2 h-4 w-4" /></Button></div>
          </div>
        </Card>
      )}

      {step === "crm" && (
        <Card className="p-8 bg-background/50 border-primary/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500">
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-primary/10 rounded-2xl"><LayoutDashboard className="h-8 w-8 text-primary" /></div><div><h3 className="text-2xl font-bold">9. CRM Estrutural</h3></div></div>
          <div className="space-y-6">
            <div onClick={() => setCrmSetup(s=>({...s,defaultFunnel:!s.defaultFunnel}))} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${crmSetup.defaultFunnel ? "border-primary bg-primary/10 shadow-glow" : "border-border/50 opacity-50"}`}>
               <h4 className="font-bold text-lg mb-3">Pré-Criar Funil de Vendas Inteligente</h4>
               <div className="flex gap-2 text-xs overflow-x-auto no-scrollbar pb-2">
                 <div className="bg-background border border-border p-2 rounded-lg w-28 shrink-0 text-center font-semibold">Prospectar</div>
                 <div className="bg-background border border-border p-2 rounded-lg w-28 shrink-0 text-center font-semibold">Qualificar</div>
                 <div className="bg-primary/20 text-primary border border-primary p-2 rounded-lg w-28 shrink-0 text-center font-bold">Negociar</div>
                 <div className="bg-primary/20 text-primary dark:text-primary border border-primary p-2 rounded-lg w-28 shrink-0 text-center font-black flex items-center justify-center"><CheckCircle2 className="w-3 h-3 mr-1"/> Fechar</div>
               </div>
            </div>
            
            <div onClick={() => setCrmSetup(s=>({...s,basicTags:!s.basicTags}))} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all mt-4 ${crmSetup.basicTags ? "border-primary bg-primary/10 shadow-glow" : "border-border/50 opacity-50"}`}>
               <div className="flex justify-between items-center mb-1">
                 <h4 className="font-bold text-lg">IA de Tagueamento Automático</h4>
                 {crmSetup.basicTags && <CheckCircle2 className="text-primary w-5 h-5" />}
               </div>
               <p className="text-sm">Permitir que a Inteligência Artificial interprete o tom da conversa e aplique etiquetas nos seus clientes automaticamente no CRM.</p>
            </div>

            {crmSetup.basicTags && (
              <div className="pt-6 mt-4 border-t border-border/50 animate-in fade-in">
                 <h4 className="font-bold text-lg mb-4">Tags Personalizadas</h4>
                 <p className="text-sm text-muted-foreground mb-4">Quais tags (etiquetas) você quer que a IA procure e aplique quando ouvir a conversa?</p>
                 <div className="flex gap-2">
                   <Input value={newCustomTag} onChange={(e) => setNewCustomTag(e.target.value)} placeholder="Ex: Casado, Curioso, Fechou Negócio" className="rounded-xl py-6 flex-1 border-2 border-primary/30" />
                   <Button onClick={() => {
                     if(!newCustomTag.trim()) return toast.error("Escreva a tag.");
                     setCustomTags([...customTags, { id: Math.random().toString(), text: newCustomTag }]);
                     setNewCustomTag("");
                     toast.success("Tag adicionada!");
                   }} className="rounded-xl py-6 px-6 bg-primary hover:bg-primary/90 text-white font-bold"><Plus className="w-4 h-4 mr-2"/> Adicionar Tag</Button>
                 </div>
                 
                 {customTags.length > 0 && (
                   <div className="mt-4 flex flex-wrap gap-2">
                     {customTags.map(tag => (
                        <div key={tag.id} className="flex items-center gap-2 p-2 px-3 rounded-xl border border-primary/30 bg-primary/10 text-primary dark:text-primary font-bold text-sm">
                          {tag.text}
                          <button onClick={() => setCustomTags(customTags.filter(x => x.id !== tag.id))} className="text-destructive hover:text-destructive/80"><Trash2 className="h-4 w-4" /></button>
                        </div>
                     ))}
                   </div>
                 )}
              </div>
            )}

            <div className="flex justify-between pt-6 border-t border-border/50 mt-4"><Button variant="ghost" onClick={() => setStep("alerts")}><ChevronLeft className="mr-2 h-4 w-4" /> Voltar</Button><Button onClick={() => savePartial("crm", "summary")} disabled={saving} className="rounded-xl px-8 shadow-glow bg-primary hover:bg-primary/90 text-white">{saving ? "Preparando Resumo..." : "Ver Resumo da Configuração"} <ChevronRight className="ml-2 h-4 w-4" /></Button></div>
          </div>
        </Card>
      )}

      {step === "summary" && (
        <Card className="p-8 bg-background/50 border-primary/20 shadow-glow rounded-3xl animate-in slide-in-from-right duration-500 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-12 bg-primary/5 rounded-bl-full pointer-events-none"></div>
          <div className="flex items-center gap-4 mb-6"><div className="p-4 bg-primary/10 rounded-2xl"><ShieldCheck className="h-8 w-8 text-primary" /></div><div><h3 className="text-2xl font-bold">10. Resumo Final</h3><p className="text-muted-foreground">Tudo pronto para ligar os motores.</p></div></div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8 relative z-10">
            <div className="p-4 rounded-xl border border-border/50 bg-background/50 flex gap-3"><BrainCircuit className="text-primary w-5 h-5 shrink-0" /><div><div className="font-bold text-sm">Cérebro IA</div><div className="text-xs text-muted-foreground">{textModel || "Nenhum selecionado"}</div></div></div>
            <div className="p-4 rounded-xl border border-border/50 bg-background/50 flex gap-3"><Ear className="text-sky-500 w-5 h-5 shrink-0" /><div><div className="font-bold text-sm">Audição STT</div><div className="text-xs text-muted-foreground">{sttModel || "Padrão/Local"}</div></div></div>
            <div className="p-4 rounded-xl border border-border/50 bg-background/50 flex gap-3"><Volume2 className="text-teal-500 w-5 h-5 shrink-0" /><div><div className="font-bold text-sm">Voz TTS</div><div className="text-xs text-muted-foreground">{ttsModel || "Padrão/Local"}{ttsAmbient ? ` • Som: ${ttsAmbientType}` : ''}</div></div></div>
            <div className="p-4 rounded-xl border border-border/50 bg-background/50 flex gap-3"><MessageSquare className="text-violet-500 w-5 h-5 shrink-0" /><div><div className="font-bold text-sm">Gestor IA</div><div className="text-xs text-muted-foreground uppercase">{chatChannel.replace('_', ' ')} {botVerified ? `(@${botVerified.user})` : ''}</div></div></div>
            <div className="p-4 rounded-xl border border-border/50 bg-background/50 flex gap-3"><Palette className="text-pink-500 w-5 h-5 shrink-0" /><div><div className="font-bold text-sm">Empresa</div><div className="text-xs text-muted-foreground flex items-center gap-1">{workspaceName || "Não definido"} <span className="w-3 h-3 rounded-full inline-block" style={{background: brandColor}}></span></div></div></div>
            <div className="p-4 rounded-xl border border-border/50 bg-background/50 flex gap-3"><LayoutDashboard className="text-primary w-5 h-5 shrink-0" /><div><div className="font-bold text-sm">Integrações</div><div className="text-xs text-muted-foreground">CRM: {crmSetup.defaultFunnel ? 'Ativo' : 'Não'} | Alertas: {alerts.sales ? 'Ligados' : 'Desl.'}</div></div></div>
          </div>

          <div className="mb-8 border border-primary/30 bg-primary/5 rounded-2xl p-6 relative z-10">
            <h4 className="font-bold text-lg text-primary flex items-center gap-2 mb-2"><BrainCircuit className="w-5 h-5"/> Auditoria por Inteligência Artificial</h4>
            <p className="text-sm text-muted-foreground mb-4">Mande a sua própria Inteligência Artificial ler todas as suas escolhas acima e sugerir melhorias de performance e táticas de vendas.</p>
            {tips.length === 0 ? (
               <Button onClick={analyzeWithAI} disabled={generatingTips} className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold rounded-xl py-6 shadow-glow">
                 {generatingTips ? <><Loader2 className="w-5 h-5 mr-2 animate-spin"/> Analisando Setup e Cruzando Dados...</> : <><Wand2 className="w-5 h-5 mr-2"/> Gerar Dicas de Alta Conversão</>}
               </Button>
            ) : (
               <div className="space-y-3">
                 {tips.map((tip, i) => (
                    <div key={i} className="flex gap-3 p-4 rounded-xl border border-primary/20 bg-background">
                       <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                       <p className="text-sm font-semibold">{tip}</p>
                    </div>
                 ))}
               </div>
            )}
          </div>

          <div className="flex justify-between pt-6 border-t border-border/50 mt-4 relative z-10"><Button variant="ghost" onClick={() => setStep("crm")}><ChevronLeft className="mr-2 h-4 w-4" /> Voltar para ajustar</Button><Button onClick={finishWizard} disabled={saving} className="rounded-xl px-10 py-6 text-lg shadow-glow bg-primary hover:bg-primary text-white">{saving ? "Finalizando Servidores..." : "Finalizar & Ligar Servidor"} <Save className="ml-2 h-5 w-5" /></Button></div>
        </Card>
      )}

      {step === "finish" && (
        <Card className="p-10 text-center bg-gradient-to-br from-primary/20 via-background to-background border-primary/30 shadow-glow rounded-3xl animate-in zoom-in-95 duration-500">
          <div className="mx-auto w-24 h-24 bg-primary/20 rounded-full flex items-center justify-center mb-6"><Wand2 className="h-12 w-12 text-primary" /></div>
          <h2 className="text-4xl font-extrabold tracking-tight mb-4 text-primary drop-shadow-sm">Seu SaaS está Pronto!</h2>
          <p className="text-muted-foreground text-xl mb-8 max-w-lg mx-auto">A infraestrutura foi alocada com as suas chaves e o sistema foi personalizado.</p>
          <Button onClick={() => setView("specialized")} className="rounded-xl px-10 py-6 text-lg shadow-glow bg-primary hover:bg-primary text-white w-full max-w-md animate-pulse-glow">
            Criar "Funcionário Fácil" Agora
          </Button>
        </Card>
      )}
    </div>
  );
}
