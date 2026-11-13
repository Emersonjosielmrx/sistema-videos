import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Field, ToggleField } from "@/components/ui/field";
import { CredentialSelect } from "@/components/settings/CredentialSelect";
import { updateVoice } from "@/services/settings";
import { apiGet, apiPost } from "@/lib/api";
import { t } from "@/lib/i18n";
import type { VoiceSettings as VoiceCfg } from "@/types/settings";
import { Mic, CheckCircle2 } from "lucide-react";
import { STT_PROVIDERS, TTS_PROVIDERS } from "@/constants/ai-providers";

// Hardcoded edge-tts voices (no API call needed)
const EDGE_TTS_VOICES = [
  { value: "pt-BR-FranciscaNeural", label: "Francisca — feminina (pt-BR) · padrão" },
  { value: "pt-BR-ThalitaNeural",   label: "Thalita — feminina (pt-BR)" },
  { value: "pt-BR-ManuelaNeural",   label: "Manuela — feminina (pt-BR)" },
  { value: "pt-BR-AntonioNeural",  label: "Antonio — masculino (pt-BR)" },
  { value: "en-US-JennyNeural",     label: "Jenny — feminina (en-US)" },
  { value: "es-ES-ElviraNeural",    label: "Elvira — feminina (es-ES)" },
  { value: "en-US-GuyNeural",       label: "Guy — masculino (en-US)" },
  { value: "en-GB-SoniaNeural",     label: "Sonia — feminina (en-GB)" },
  { value: "es-MX-DaliaNeural",     label: "Dalia — feminina (es-MX)" },
  { value: "pt-PT-FernandaNeural", label: "Fernanda — feminina (pt-PT)" },
  { value: "pt-PT-RaquelNeural",    label: "Raquel — feminina (pt-PT)" },
];

// Vozes do Piper (serviço local na VPS). Todas masculinas PT-BR.
const PIPER_VOICES = [
  { value: "faber", label: "Faber — masculina (pt-BR) · padrão" },
  { value: "jeff",  label: "Jeff — masculina (pt-BR)" },
  { value: "cadu",  label: "Cadu — masculina (pt-BR)" },
];

const DEFAULT_VOICE = "pt-BR-FranciscaNeural";

export function VoiceSettings({ initial, onSaved }: { initial: VoiceCfg; onSaved: () => void }) {
  const [cfg, setCfg] = useState<VoiceCfg>({
    ...initial,
    stt_provider:  initial.stt_provider  || "local",
    stt_model:    initial.stt_model     || "",
    tts_provider: initial.tts_provider   || "edge-tts",
    tts_voice:    initial.tts_voice      || DEFAULT_VOICE,
    vad_silence_ms: initial.vad_silence_ms || 550,
    filler_words:  initial.filler_words?.length ? initial.filler_words : ["Certo.", "Entendo.", "Ok.", "Perfeito.", "Sei.", "Aham.", "Claro.", "Compreendo.", "Sim.", "Uhum.", "Com certeza.", "Entendi.", "Isso.", "Tá.", "Pois é.", "Deixa eu ver.", "Um momento.", "Já verifico."],
  });

  const [saving, setSaving]       = useState(false);
  const [fillerInput, setFillerInput] = useState(cfg.filler_words?.join(", ") || "");
  // Palavras de reconhecimento do barge-in ("ok/certo/entendi" tocadas quando o
  // cliente INTERROMPE a fala da IA). Vazio = usa o default do backend.
  const [bargeAckInput, setBargeAckInput] = useState(cfg.barge_ack_words?.join(", ") || "");

  // STT state
  const [sttModels, setSttModels]     = useState<string[]>([]);
  const [sttLoading, setSttLoading]   = useState(false);
  const [sttTesting, setSttTesting]   = useState(false);

  // TTS state
  const [ttsVoices, setTtsVoices]   = useState<{id: string; name: string}[]>([]);
  const [ttsLoadingVoices, setTtsLoadingVoices] = useState(false);
  const [ttsTesting, setTtsTesting]  = useState(false);

  // Audio test state
  const [playingAudio, setPlayingAudio] = useState<HTMLAudioElement | null>(null);

  const toggleTestAudio = () => {
    if (playingAudio) {
      playingAudio.pause();
      setPlayingAudio(null);
      return;
    }
    if (!cfg.background_noise) return;
    const audio = new Audio(`/audio/ambient/${cfg.background_noise}.mp3`);
    audio.loop = true;
    audio.volume = cfg.background_noise_volume ?? 0.1;
    audio.play().catch((e) => toast.error("Erro ao reproduzir", { description: e.message }));
    setPlayingAudio(audio);
  };
  const isCustomSTT   = cfg.stt_provider === "custom";
  // Piper e edge-tts são locais/grátis — não pedem chave nem credencial.
  const isLocalTTS    = cfg.tts_provider === "edge-tts" || cfg.tts_provider === "piper";
  const needsTTSKey   = !isLocalTTS;

  // ----- STT helpers -----

  const loadSttModels = async () => {
    if (!cfg.stt_api_key) {
      toast.error("Preencha a API Key primeiro");
      return;
    }
    setSttLoading(true);
    try {
      const p = new URLSearchParams({ provider: cfg.stt_provider, api_key: cfg.stt_api_key });
      if (cfg.stt_base_url) p.set("base_url", cfg.stt_base_url);
      const data = await apiGet<{ models: string[] }>(`/api/ai/models?${p.toString()}`);
      setSttModels(data.models ?? []);
      toast.success(`${(data.models ?? []).length} modelos encontrados`);
    } catch (e) {
      toast.error("Erro ao buscar modelos", { description: (e as Error).message });
    } finally {
      setSttLoading(false);
    }
  };

  const testSttKey = async () => {
    if (!cfg.stt_provider) {
      toast.error("Selecione um provider primeiro");
      return;
    }
    if (cfg.stt_provider === "groq" && !cfg.stt_api_key) {
      toast.info("Groq usa a chave gratuita padrão — não precisa de chave própria.");
      return;
    }
    setSttTesting(true);
    try {
      // Usa apiPost (injeta Authorization/Bearer); o fetch cru anterior nao mandava
      // o header e o endpoint respondia 401 "unauthorized" mesmo com chave correta.
      const res = await apiPost<{ ok?: boolean; error?: string }>("/api/stt/test", {
        provider: cfg.stt_provider,
        api_key: cfg.stt_api_key,
        base_url: cfg.stt_base_url,
        model: cfg.stt_model,
        credential_id: cfg.stt_credential_id,
      });
      if (res.ok) {
        toast.success("Chave STT OK!");
      } else {
        toast.error("Chave STT não funcionou", { description: res.error });
      }
    } catch (e) {
      toast.error("Erro ao testar STT", { description: (e as Error).message });
    } finally {
      setSttTesting(false);
    }
  };

  // ----- TTS helpers -----

  const loadTtsVoices = async () => {
    setTtsLoadingVoices(true);
    try {
      const p = new URLSearchParams({ provider: cfg.tts_provider });
      if (cfg.tts_api_key) p.set("api_key", cfg.tts_api_key);
      if (cfg.tts_base_url) p.set("base_url", cfg.tts_base_url);
      // credential_id: backend resolve a chave real server-side (só selecionar a credencial basta).
      if (cfg.tts_credential_id) p.set("credential_id", cfg.tts_credential_id);

      const data = await apiGet<{ voices: { id: string; name: string }[] }>(`/api/tts/voices?${p.toString()}`);
      setTtsVoices(data.voices ?? []);
      if ((data.voices ?? []).length === 0) {
        toast.info("Nenhuma voz encontrada para este provider.");
      } else {
        toast.success(`${(data.voices ?? []).length} vozes encontradas`);
      }
    } catch (e) {
      toast.error("Erro ao buscar vozes TTS", { description: (e as Error).message });
    } finally {
      setTtsLoadingVoices(false);
    }
  };

  const testTtsKey = async () => {
    if (!cfg.tts_provider) {
      toast.error("Selecione um provider primeiro");
      return;
    }
    if (!isLocalTTS && !cfg.tts_api_key && !cfg.tts_credential_id) {
      toast.error("Preencha a API Key (ou escolha uma chave do cofre) primeiro para este provider.");
      return;
    }
    setTtsTesting(true);
    try {
      // Usa apiPost (injeta Authorization/Bearer); o fetch cru anterior nao mandava
      // o header e o endpoint respondia 401 "unauthorized" mesmo com chave correta.
      const res = await apiPost<{ ok?: boolean; error?: string }>("/api/tts/test", {
        credential_id: cfg.tts_credential_id || "", // chave do cofre (o servidor resolve)
        provider: cfg.tts_provider,
        api_key: cfg.tts_api_key,
        base_url: cfg.tts_base_url,
        voice_id: cfg.tts_voice,
      });
      if (res.ok) {
        toast.success("TTS OK! Voz sintetizada com sucesso.");
      } else {
        toast.error("TTS não funcionou", { description: res.error });
      }
    } catch (e) {
      toast.error("Erro ao testar TTS", { description: (e as Error).message });
    } finally {
      setTtsTesting(false);
    }
  };

  // When TTS provider changes, reload the voice list and set a sensible default voice
  const handleTtsProviderChange = (provider: string) => {
    setCfg(prev => {
      const next = { ...prev, tts_provider: provider };
      // Reset voice selection — will be repopulated by loadTtsVoices
      if (provider === "edge-tts") {
        next.tts_voice = DEFAULT_VOICE;
        next.tts_api_key = "";
        next.tts_base_url = "";
        setTtsVoices([]);
      } else if (provider === "piper") {
        // Piper é local (sem chave); vozes fixas (faber/jeff/cadu).
        next.tts_voice = "faber";
        next.tts_api_key = "";
        next.tts_base_url = "";
        setTtsVoices([]);
      } else {
        next.tts_voice = "";
        setTtsVoices([]);
      }
      return next;
    });
  };

  // ----- Save -----

  const save = async () => {
    setSaving(true);
    try {
      const words = fillerInput.split(",").map((w) => w.trim()).filter(Boolean);
      const ackWords = bargeAckInput.split(",").map((w) => w.trim()).filter(Boolean);
      await updateVoice({
        ...cfg,
        filler_words: words,
        barge_ack_words: ackWords,
        tts_voice: cfg.tts_voice || DEFAULT_VOICE,
      });
      toast.success(t("saved_success"));
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  // Determine which voices to show in the dropdown
  const ttsVoiceOptions = cfg.tts_provider === "piper"
    ? PIPER_VOICES
    : cfg.tts_provider === "edge-tts" || ttsVoices.length === 0
    ? EDGE_TTS_VOICES
    : ttsVoices.map(v => ({ value: v.id, label: v.name }));

  // Piper e edge-tts têm vozes fixas: não mostra o botão "Buscar vozes".
  const isEdgeTTS = cfg.tts_provider === "edge-tts" || cfg.tts_provider === "piper";

  return (
    <Card className="bg-glass border-border/50 shadow-soft overflow-hidden mt-4">
      <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Mic className="w-5 h-5 text-indigo-500" />
          <h3 className="font-bold text-sm">Configuração de Voz (TTS e STT)</h3>
        </div>
      </div>

      <div className="p-6 space-y-6">
        <div className="rounded-md bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800 p-4 text-sm text-muted-foreground">
          <strong className="text-indigo-700 dark:text-indigo-400">Motor de Áudio.</strong> Controla como o áudio é gerado (TTS) e transcrito (STT), além de comportamento do detector de voz (VAD). A voz da IA é usada nas ligações e áudios gerados pelo sistema.
        </div>

        <div className="flex flex-col md:flex-row gap-4">
           <div className="flex-1 flex flex-col justify-between p-4 bg-background/50 rounded-xl border border-border/50">
             <div>
                <p className="font-semibold">Atender chamadas</p>
                <p className="text-xs text-muted-foreground mt-0.5">A IA conversa por voz ao vivo quando alguém ligar.</p>
             </div>
             <div className="mt-4">
                <ToggleField label="" checked={cfg.auto_answer} onChange={(v) => setCfg({ ...cfg, auto_answer: v })} />
             </div>
           </div>

           <div className="flex-1 flex flex-col justify-between p-4 bg-background/50 rounded-xl border border-border/50">
             <div>
                <p className="font-semibold">Retornar ligações perdidas</p>
                <p className="text-xs text-muted-foreground mt-0.5">Agente de IA retorna a chamada e conversa se o lead não foi atendido.</p>
             </div>
             <div className="mt-4">
                <ToggleField label="" checked={cfg.callback_missed} onChange={(v) => setCfg({ ...cfg, callback_missed: v })} />
             </div>
           </div>

           <div className="flex-1 flex flex-col justify-between p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
             <div>
                <p className="font-semibold text-emerald-500 flex items-center gap-2">Aviso de retorno de campanha</p>
                <p className="text-xs text-emerald-500/80 mt-0.5">Quando quem recebeu ligação de campanha manda mensagem no WhatsApp, você recebe aviso no Telegram na hora.</p>
             </div>
             <div className="mt-4">
                <ToggleField label="" checked={cfg.return_campaign_mode ?? true} onChange={(v) => setCfg({ ...cfg, return_campaign_mode: v })} />
             </div>
           </div>
        </div>

      {/* ========== STT Section ========== */}
      <div className="rounded-md border border-border bg-card p-4 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Transcrição de voz (STT)</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Define como o áudio da ligação é convertido em texto.
          </p>
        </div>

        <Field label="Provider" hint="Provedor de transcrição.">
          <select
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            value={cfg.stt_provider}
            onChange={(e) => setCfg({ ...cfg, stt_provider: e.target.value })}
          >
            {STT_PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </Field>

        <Field
          label="Credencial STT"
          hint="Escolha uma credencial do tipo Transcrição salva na aba 🔑 Credenciais. A chave/Base URL vêm dela. 'Nenhuma' = chave manual (ou Whisper local grátis)."
        >
          <CredentialSelect
            type="stt"
            value={cfg.stt_credential_id ?? ""}
            onChange={(id, cred) =>
              setCfg({
                ...cfg,
                stt_credential_id: id,
                ...(id
                  ? { stt_api_key: "", stt_provider: cred?.provider || cfg.stt_provider, stt_base_url: cred?.base_url || "" }
                  : {}),
              })
            }
          />
        </Field>

        {/* Chave/Base URL manuais — só quando NÃO há credencial STT selecionada. */}
        {!cfg.stt_credential_id && (
          <>
            <Field label="API Key" hint="Chave do provider. Para Groq, a chave gratuita padrão é usada automaticamente. Prefira a aba 🔑 Credenciais.">
              <Input
                type="password"
                value={cfg.stt_api_key}
                onChange={(e) => setCfg({ ...cfg, stt_api_key: e.target.value })}
                placeholder={cfg.stt_provider === "groq" ? "não precisa se usar Groq gratuito" : "sk-..."}
              />
            </Field>

            <Field label="Base URL" hint="URL base da API.">
              <Input
                value={cfg.stt_base_url}
                onChange={(e) => setCfg({ ...cfg, stt_base_url: e.target.value })}
                placeholder={cfg.stt_provider === "groq" ? "https://api.groq.com/openai" : "http://IP:9000"}
              />
            </Field>
          </>
        )}

        <Field label="Modelo" hint="Clique em 'Buscar modelos' para listar os disponíveis na sua chave.">
          <div className="flex gap-2">
            {sttModels.length > 0 && !isCustomSTT ? (
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={cfg.stt_model}
                onChange={(e) => setCfg({ ...cfg, stt_model: e.target.value })}
              >
                <option value="">Selecione um modelo...</option>
                {sttModels.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            ) : (
              <Input
                className="flex-1"
                value={cfg.stt_model}
                onChange={(e) => setCfg({ ...cfg, stt_model: e.target.value })}
                placeholder={isCustomSTT ? "faster-whisper-base" : "whisper-large-v3"}
              />
            )}
            {!isCustomSTT && (
              <Button type="button" variant="outline" size="sm" onClick={loadSttModels} disabled={sttLoading}>
                {sttLoading ? "Buscando..." : "Buscar modelos"}
              </Button>
            )}
          </div>
        </Field>

        <Button type="button" variant="outline" size="sm" onClick={testSttKey} disabled={sttTesting}>
          {sttTesting ? "Testando..." : "Testar chave STT"}
        </Button>
      </div>

      {/* ========== TTS Section ========== */}
      <div className="rounded-md border border-border bg-card p-4 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Geração de voz (TTS)</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Define como o texto é convertido em áudio. Edge TTS é grátis; ElevenLabs, Gemini e OpenAI
            usam a API key da respectivos provedores.
          </p>
        </div>

        {/* Provider */}
        <Field label="Provider" hint="Provedor de síntese de voz.">
          <select
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            value={cfg.tts_provider || "edge-tts"}
            onChange={(e) => handleTtsProviderChange(e.target.value)}
          >
            {TTS_PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </Field>

        {/* Credencial TTS (só faz sentido para providers com chave, não edge-tts) */}
        {needsTTSKey && (
          <Field
            label="Credencial TTS"
            hint="Escolha uma credencial do tipo Voz salva na aba 🔑 Credenciais. A chave/Base URL vêm dela. Selecione 'Nenhuma' para usar chave manual."
          >
            <CredentialSelect
              type="tts"
              value={cfg.tts_credential_id ?? ""}
              onChange={(id, cred) =>
                setCfg({
                  ...cfg,
                  tts_credential_id: id,
                  ...(id
                    ? { tts_api_key: "", tts_base_url: cred?.base_url || "" }
                    : {}),
                })
              }
            />
          </Field>
        )}

        {/* API Key (hidden for edge-tts e quando há credencial TTS selecionada) */}
        {needsTTSKey && !cfg.tts_credential_id && (
          <Field
            label="API Key"
            hint={`Chave do ${cfg.tts_provider === "elevenlabs" ? "ElevenLabs" : cfg.tts_provider === "gemini" ? "Google Gemini" : "OpenAI"}. Prefira a aba 🔑 Credenciais.`}
          >
            <Input
              type="password"
              value={cfg.tts_api_key}
              onChange={(e) => setCfg({ ...cfg, tts_api_key: e.target.value })}
              placeholder={
                cfg.tts_provider === "elevenlabs" ? "sk_..." :
                cfg.tts_provider === "gemini"      ? "AIza..." :
                "sk-..."
              }
            />
          </Field>
        )}

        {/* Base URL (optional, for custom endpoints) */}
        {needsTTSKey && !cfg.tts_credential_id && (
          <Field
            label="Base URL"
            hint={`URL base da API do ${cfg.tts_provider === "elevenlabs" ? "ElevenLabs" : cfg.tts_provider === "gemini" ? "Google Gemini" : "OpenAI"}. Deixe em branco para usar o padrão.`}
          >
            <Input
              value={cfg.tts_base_url}
              onChange={(e) => setCfg({ ...cfg, tts_base_url: e.target.value })}
              placeholder={
                cfg.tts_provider === "elevenlabs" ? "https://api.elevenlabs.io" :
                cfg.tts_provider === "gemini"    ? "https://generativelanguage.googleapis.com" :
                "https://api.openai.com"
              }
            />
          </Field>
        )}

        {/* Voice selector */}
        <Field
          label="Voz"
          hint={
            cfg.tts_provider === "edge-tts"
              ? "Voz Edge TTS. Grátis e sem chave."
              : ttsVoices.length > 0
              ? `Carregadas ${ttsVoices.length} vozes do ${cfg.tts_provider}. Clique em 'Buscar vozes' para atualizar.`
              : `Clique em 'Buscar vozes' para carregar as vozes do ${cfg.tts_provider}.`
          }
        >
          <div className="flex gap-2">
            {ttsVoiceOptions.length > 0 ? (
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={cfg.tts_voice || ""}
                onChange={(e) => setCfg({ ...cfg, tts_voice: e.target.value })}
              >
                <option value="">Selecione uma voz...</option>
                {ttsVoiceOptions.map((v) => (
                  <option key={v.value} value={v.value}>{v.label}</option>
                ))}
              </select>
            ) : (
              <Input
                className="flex-1"
                value={cfg.tts_voice || ""}
                onChange={(e) => setCfg({ ...cfg, tts_voice: e.target.value })}
                placeholder={
                  cfg.tts_provider === "edge-tts" ? "pt-BR-FranciscaNeural" :
                  cfg.tts_provider === "elevenlabs" ? "ID da voz ElevenLabs (ex: EXAVITQu4vr4xnSDxMaL)" :
                  cfg.tts_provider === "gemini" ? "Fenrir" :
                  "alloy"
                }
              />
            )}
            {!isEdgeTTS && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={loadTtsVoices}
                disabled={ttsLoadingVoices || (needsTTSKey && !cfg.tts_api_key && !cfg.tts_credential_id)}
                title={needsTTSKey && !cfg.tts_api_key && !cfg.tts_credential_id ? "Preencha a API Key primeiro" : ""}
              >
                {ttsLoadingVoices ? "Buscando..." : "Buscar vozes"}
              </Button>
            )}
          </div>
        </Field>

        {/* Test button */}
        <Button type="button" variant="outline" size="sm" onClick={testTtsKey} disabled={ttsTesting}>
          {ttsTesting ? "Testando..." : "Testar voz TTS"}
        </Button>
      </div>

      {/* ========== VAD Section ========== */}
      <div className="grid grid-cols-2 gap-3">
        <Field
          label="Tempo de Escuta (Quando o robô decide responder)"
          hint="Tempo de silêncio em ms antes de considerar que a pessoa terminou de falar. Padrão: 550ms."
        >
          <Input
            type="number"
            value={cfg.vad_silence_ms}
            onChange={(e) => setCfg({ ...cfg, vad_silence_ms: parseInt(e.target.value) || 550 })}
            placeholder="550"
          />
        </Field>
        <Field
          label="Limiar VAD (threshold)"
          hint="Sensibilidade do detector (0 a 1). Padrão: 0.005."
        >
          <Input
            type="number"
            step="0.001"
            value={cfg.vad_threshold}
            onChange={(e) => setCfg({ ...cfg, vad_threshold: parseFloat(e.target.value) || 0.005 })}
            placeholder="0.005"
          />
        </Field>
      </div>

      {/* ========== Barge-In (Interrupção) Section ========== */}
      <div className="border-t pt-4 space-y-4">
        <ToggleField
          label="Interrupção ao Vivo (Barge-in / Handoff)"
          hint="Permite que o cliente interrompa a fala do robô ou que o Vendedor humano assuma a ligação."
          checked={cfg.barge_in_enabled !== false}
          onChange={(v) => setCfg({ ...cfg, barge_in_enabled: v })}
        />
        {cfg.barge_in_enabled !== false && (
          <div className="grid grid-cols-2 gap-3">
            <Field
              label="Sensibilidade da Interrupção"
              hint="O quanto de som (em ms) do cliente é necessário para a IA parar de falar. Baixo = IA para fácil."
            >
              <select
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={cfg.barge_in_sensitivity ?? "medium"}
                onChange={(e) => setCfg({ ...cfg, barge_in_sensitivity: e.target.value })}
              >
                <option value="high">Alta (Qualquer tosse ela para)</option>
                <option value="medium">Média (Padrão)</option>
                <option value="low">Baixa (Evita parar por ruído)</option>
              </select>
            </Field>
            <Field
              label="Palavras de reconhecimento (ao interromper)"
              hint="Frases curtas tocadas quando o cliente corta a fala da IA (ex.: 'Certo.', 'Pode falar.'). Deixe vazio para não tocar nada ao ser interrompido."
            >
              <Input
                value={bargeAckInput}
                onChange={(e) => {
                  setBargeAckInput(e.target.value);
                  setCfg({ ...cfg, barge_ack_words: e.target.value.split(",").map((w) => w.trim()).filter(Boolean) });
                }}
                placeholder="Certo., Pode falar., Entendi."
              />
            </Field>
          </div>
        )}
      </div>

      {/* ========== Filler Section ========== */}
      <div className="border-t pt-4 space-y-4">
        <ToggleField
          label="Sons de Humanização (ex: humm, entendi)"
          hint="Palavras curtas como 'ok', 'entendo' tocadas enquanto a IA pensa. Deixa a conversa mais natural."
          checked={cfg.filler_enabled}
          onChange={(v) => setCfg({ ...cfg, filler_enabled: v })}
        />
        {cfg.filler_enabled && (
          <Field label="Palavras filler" hint="Liste palavras curtas separadas por vírgula.">
            <Input
              value={fillerInput}
              onChange={(e) => {
                setFillerInput(e.target.value);
                setCfg({ ...cfg, filler_words: e.target.value.split(",").map((w) => w.trim()).filter(Boolean) });
              }}
              placeholder="Certo., Entendo., Ok., Perfeito., Aham."
            />
          </Field>
        )}
      </div>

      {/* ========== Ambiente Section ========== */}
      <div className="border-t pt-4 space-y-4">
        <ToggleField
          label="Som Ambiente Autêntico (Ruído de Fundo)"
          hint="Toca um áudio sutil em loop (ex: rua, escritório) para disfarçar a limpeza robótica e soar 100% humano."
          checked={!!cfg.background_noise}
          onChange={(v) => setCfg({ ...cfg, background_noise: v ? "office" : "" })}
        />

        {cfg.background_noise && (
          <div className="space-y-3 bg-muted/30 p-4 rounded-xl border border-border/50">
            <Field label="Qual ambiente?" hint="Selecione o cenário que mais combina com o seu atendente.">
              <div className="flex gap-2 items-center">
                <select
                  className="flex-1 rounded-md border bg-background px-3 py-2 text-sm"
                  value={cfg.background_noise || "office"}
                  onChange={(e) => setCfg({ ...cfg, background_noise: e.target.value })}
                >
                  <option value="office">🏢 Escritório (Teclados, vozes distantes)</option>
                  <option value="reais/office_2">🏢 Escritório 2 (Dinâmico, vozes próximas)</option>
                  <option value="reais/office_3">🏢 Escritório 3 (Mais denso, movimento)</option>
                  <option value="call_center">🎧 Call Center (Telemarketing movimentado)</option>
                  <option value="reais/call_center_2">🎧 Call Center 2 (Vozes agudas, intenso)</option>
                  <option value="reais/call_center_3">🎧 Call Center 3 (Mais eco, abafado)</option>
                  <option value="street">🚗 Rua / Trânsito Leve (Passos, tráfego abafado)</option>
                  <option value="reais/street_2">🚗 Rua 2 (Trânsito rápido)</option>
                  <option value="reais/street_3">🚗 Rua 3 (Ambiente aberto)</option>
                  <option value="coffee_shop">☕ Cafeteria (Copos, murmúrios relaxantes)</option>
                  <option value="reais/coffee_shop_2">☕ Cafeteria 2 (Mais vozes e pratos)</option>
                  <option value="reais/coffee_shop_3">☕ Cafeteria 3 (Tranquilo)</option>
                  <option value="car">🚙 Dirigindo Carro (Movimento abafado)</option>
                  <option value="restaurant">🍽️ Restaurante Lotado (Talheres, vozes altas)</option>
                  <option value="park">🌳 Parque / Caminhada (Pássaros, passos ao ar livre)</option>
                  <option value="airport">✈️ Saguão de Aeroporto (Eco, multidão)</option>
                  <option value="bus">🚌 Transporte Público (Motor, freios)</option>
                  <option value="lofi_static">📻 Estática Analógica (Chiado de linha telefônica)</option>
                </select>
                <Button 
                  variant={playingAudio ? "destructive" : "secondary"}
                  onClick={toggleTestAudio}
                  title="Testar áudio de fundo"
                >
                  {playingAudio ? "⏹ Parar" : "▶ Ouvir"}
                </Button>
              </div>
            </Field>

            <Field label="Volume do Ambiente" hint="Define a altura do fundo. Deixe baixo (10%) para não engolir a voz.">
              <div className="flex items-center gap-4">
                <input 
                  type="range" 
                  min="0.01" 
                  max="0.30" 
                  step="0.01" 
                  className="w-full accent-primary"
                  value={cfg.background_noise_volume ?? 0.1}
                  onChange={(e) => {
                    const newVol = parseFloat(e.target.value);
                    setCfg({ ...cfg, background_noise_volume: newVol });
                    if (playingAudio) playingAudio.volume = newVol;
                  }}
                />
                <span className="text-sm font-medium w-12 text-right">
                  {Math.round((cfg.background_noise_volume ?? 0.1) * 100)}%
                </span>
              </div>
            </Field>
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-border/50 flex items-center justify-between">
         <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Mic className="w-4 h-4 text-indigo-500" /> Teste a fala antes de salvar.
         </div>
         <div className="flex items-center gap-2">
            <Button onClick={save} disabled={saving} className="gap-2 shadow-glow">
              <CheckCircle2 className="w-4 h-4"/> Salvar Motor de Voz
            </Button>
         </div>
      </div>
      </div>
    </Card>
  );
}
