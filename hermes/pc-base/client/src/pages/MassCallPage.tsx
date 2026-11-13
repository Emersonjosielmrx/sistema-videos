import { useEffect, useState } from "react";
import { ArrowLeft, PhoneForwarded, XCircle, CheckCircle2, Clock, Phone, AlertCircle, Upload, Megaphone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { useMassCallStore } from "@/stores/masscall";
import { useSessions } from "@/stores/sessions";
import { Textarea } from "@/components/ui/textarea";
import { setView } from "@/stores/navigation";
import { startMassCall, getMassCallStatus, cancelMassCall } from "@/services/contacts";
import { logError } from "@/lib/log";
import { startBroadcast, generateTTS, listAudios, getAudio, deleteAudio, getCampaignDefaults, type SavedAudio } from "@/services/broadcast";
import type { MassCallJob, MassCallResult } from "@/types/contacts";

const ttsVoices = [
  { value: "pt-BR-FranciscaNeural", label: "Francisca (feminina)" },
  { value: "pt-BR-ThalitaNeural", label: "Thalita (feminina)" },
  { value: "pt-BR-AntonioNeural", label: "Antonio (masculina)" },
];

// converte um File de áudio em base64 puro (sem o prefixo data:)
const fileToBase64 = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",")[1] ?? "");
    r.onerror = reject;
    r.readAsDataURL(file);
  });

export const MassCallPage = () => {
  const { contacts, jobId, setJobId, clear } = useMassCallStore();
  const setContacts = useMassCallStore((s) => s.setContacts);
  const [job, setJob] = useState<MassCallJob | null>(null);
  const [loading, setLoading] = useState(false);
  const sessions = useSessions((s) => s.sessions);
  const pairedSession = sessions.find((s) => s.paired);

  // Entrada manual de números (pedido #10): cola vários separados por vírgula/linha.
  const [manualNumbers, setManualNumbers] = useState("");

  // Modo campanha com áudio (broadcast: persiste + mede escuta + capta resposta)
  const [audioMode, setAudioMode] = useState<"upload" | "ai" | "library">("upload");
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [ttsText, setTtsText] = useState("");
  const [ttsVoice, setTtsVoice] = useState("pt-BR-FranciscaNeural");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [campName, setCampName] = useState("");
  // A/B: texto opcional de uma 2ª variante de áudio (gerada por IA). Se preenchido, a
  // campanha alterna A/B entre os contatos e mede qual converte mais (Analytics).
  const [ttsTextB, setTtsTextB] = useState("");
  // Biblioteca de áudios salvos (áudios anteriores do cliente)
  const [savedAudios, setSavedAudios] = useState<SavedAudio[]>([]);
  const [selectedAudioId, setSelectedAudioId] = useState<string>("");
  const [libPreviewUrl, setLibPreviewUrl] = useState<string | null>(null);
  const [saveAudio, setSaveAudio] = useState(false);
  const [saveAudioName, setSaveAudioName] = useState("");
  const [gapMin, setGapMin] = useState(3);
  const [gapMax, setGapMax] = useState(8);
  const [startHour, setStartHour] = useState(0);
  const [endHour, setEndHour] = useState(0);
  const [captureReply, setCaptureReply] = useState(true);
  const [preNotify, setPreNotify] = useState(false);
  const [batchSize, setBatchSize] = useState(10);
  // Campanha v2 — modo de disparo (escolha obrigatória):
  //   immediate = dispara já; paced = ao longo do dia; multiline = várias linhas.
  const [dispatchMode, setDispatchMode] = useState<"immediate" | "paced" | "multiline">("immediate");
  const [perDay, setPerDay] = useState(48);
  const [perMin, setPerMin] = useState(1);
  const [rampStart, setRampStart] = useState(48);
  const [paceStartHour, setPaceStartHour] = useState(7);
  const [paceEndHour, setPaceEndHour] = useState(19);
  // Multi-linha: quais linhas conectadas usar (todas pareadas por padrão).
  const pairedLines = sessions.filter((s) => s.paired);
  const [selectedLines, setSelectedLines] = useState<string[]>([]);

  // Pré-carrega os PADRÕES de campanha salvos (aba Campanhas → Configurações de Campanha),
  // pra o formulário já vir com o modo/ritmo que o dono definiu. Dá pra ajustar por campanha.
  useEffect(() => {
    getCampaignDefaults()
      .then((d) => {
        if (d?.mode) setDispatchMode(d.mode);
        if (d?.per_day) setPerDay(d.per_day);
        if (d?.per_min) setPerMin(d.per_min);
        if (d?.ramp_start) setRampStart(d.ramp_start);
        if (typeof d?.start_hour === "number") setPaceStartHour(d.start_hour);
        if (typeof d?.end_hour === "number") setPaceEndHour(d.end_hour);
        if (d?.gap_min_sec) setGapMin(d.gap_min_sec);
        if (d?.gap_max_sec) setGapMax(d.gap_max_sec);
      })
      .catch(logError("getCampaignDefaults"));
  }, []);

  // Carrega os áudios salvos quando o cliente abre o modo "Áudios salvos"
  useEffect(() => {
    if (audioMode !== "library") return;
    listAudios()
      .then(setSavedAudios)
      .catch(() => toast.error("Erro ao carregar áudios salvos"));
  }, [audioMode]);

  // Ao escolher um áudio salvo, baixa os bytes pra tocar o preview
  const onSelectSavedAudio = async (id: string) => {
    setSelectedAudioId(id);
    setLibPreviewUrl(null);
    if (!id) return;
    try {
      const a = await getAudio(id);
      if (a.audio_base64) setLibPreviewUrl(`data:${a.mime || "audio/ogg"};base64,${a.audio_base64}`);
    } catch {
      toast.error("Erro ao carregar o áudio");
    }
  };

  const onDeleteSavedAudio = async (id: string) => {
    try {
      await deleteAudio(id);
      setSavedAudios((prev) => prev.filter((a) => a.id !== id));
      if (selectedAudioId === id) { setSelectedAudioId(""); setLibPreviewUrl(null); }
      toast.success("Áudio removido");
    } catch (e: any) {
      toast.error("Erro ao remover", { description: e.message });
    }
  };

  // Gera o áudio por IA (texto → voz) e toca um preview
  const onGenerateTTS = async () => {
    if (!ttsText.trim()) return toast.error("Digite o texto da mensagem");
    setGenerating(true);
    try {
      const res = await generateTTS(ttsText, ttsVoice);
      setPreviewUrl(`data:audio/ogg;base64,${res.audio_base64}`);
      toast.success("Áudio gerado — ouça o preview antes de disparar");
    } catch (e: any) {
      toast.error("Erro ao gerar áudio", { description: e.message });
    } finally {
      setGenerating(false);
    }
  };

  const onStartBroadcast = async () => {
    if (!pairedSession || contacts.length === 0) return;
    setLoading(true);
    try {
      let audio_base64 = "";
      let audio_id = "";
      if (audioMode === "library") {
        if (!selectedAudioId) { setLoading(false); return toast.error("Escolha um áudio salvo"); }
        audio_id = selectedAudioId;
      } else if (audioMode === "upload") {
        if (!audioFile) { setLoading(false); return toast.error("Escolha um arquivo de áudio"); }
        audio_base64 = await fileToBase64(audioFile);
      } else {
        if (!previewUrl) {
          if (!ttsText.trim()) { setLoading(false); return toast.error("Gere o áudio por IA primeiro"); }
          const res = await generateTTS(ttsText, ttsVoice);
          audio_base64 = res.audio_base64;
        } else {
          audio_base64 = previewUrl.split(",")[1];
        }
      }
      const res = await startBroadcast(pairedSession.id, {
        name: campName || `Campanha ${new Date().toLocaleString("pt-BR")}`,
        ...(audio_id ? { audio_id } : { audio_base64 }),
        // salva na biblioteca só quando o áudio é novo (não quando já veio da lib)
        ...(saveAudio && audioMode !== "library"
          ? { save_audio_as: saveAudioName || (campName || `Áudio ${new Date().toLocaleString("pt-BR")}`) }
          : {}),
        numbers: contacts.map((c) => c.phone),
        names: contacts.map((c) => c.name || c.push_name || c.business_name || ""),
        concurrency: 1,
        gap_min_ms: gapMin * 1000,
        gap_max_ms: gapMax * 1000,
        start_hour: dispatchMode === "immediate" ? startHour : paceStartHour,
        end_hour: dispatchMode === "immediate" ? endHour : paceEndHour,
        capture_reply: captureReply,
        pre_notify: preNotify,
        batch_size: batchSize,
        // A/B: envia a variante B por texto (IA gera) quando preenchida.
        ...(ttsTextB.trim() ? { tts_message_b: ttsTextB.trim() } : {}),
        // Campanha v2 — modo de disparo e config do cadenciador.
        mode: dispatchMode,
        ...(dispatchMode !== "immediate"
          ? { per_day: perDay, per_min: perMin, ramp_start: rampStart }
          : {}),
        ...(dispatchMode === "multiline"
          ? { session_ids: selectedLines.length ? selectedLines : pairedLines.map((l) => l.id) }
          : {}),
      });
      toast.success(`Campanha iniciada: ${res.total} contatos, áudio de ${res.seconds}s`);
      setView("crm");
      clear();
    } catch (e: any) {
      toast.error("Erro ao iniciar campanha", { description: e.message });
    } finally {
      setLoading(false);
    }
  };

  // Sync status if job exists
  useEffect(() => {
    if (!jobId) return;

    let mounted = true;
    const fetchStatus = async () => {
      try {
        const res = await getMassCallStatus(jobId);
        if (mounted) setJob(res);
        if (res.status === "done" || res.status === "cancelled" || res.status === "failed") {
          return; // Stop polling
        }
      } catch (err) {
        console.error("Failed to fetch mass call status", err);
      }
      if (mounted) {
        timer = setTimeout(fetchStatus, 1500);
      }
    };

    let timer = setTimeout(fetchStatus, 0);
    return () => {
      mounted = false;
      clearTimeout(timer);
    };
  }, [jobId]);

  const onStart = async () => {
    if (contacts.length === 0) return;
    setLoading(true);
    try {
      const res = await startMassCall(
        contacts.map((c) => c.phone),
        contacts.map((c) => c.name || c.push_name || c.phone),
        pairedSession?.id
      );
      if (res.success) {
        setJobId(res.job.id);
        setJob(res.job);
        toast.success("Chamada em massa iniciada");
      }
    } catch (err: any) {
      toast.error("Erro ao iniciar chamadas", { description: err.message });
    } finally {
      setLoading(false);
    }
  };

  const onCancel = async () => {
    if (!jobId) return;
    setLoading(true);
    try {
      await cancelMassCall(jobId);
      toast.success("Chamada em massa cancelada");
    } catch (err: any) {
      toast.error("Erro ao cancelar", { description: err.message });
    } finally {
      setLoading(false);
    }
  };

  const onBack = () => {
    if (job?.status === "running") {
      toast.error("Cancele a chamada em massa antes de sair");
      return;
    }
    clear();
    setView("crm");
  };

  // Converte os números colados manualmente em Contacts e junta com os já selecionados.
  // Aceita: um número por linha, vários por linha separados por vírgula/; , OU colar a lista
  // da captação no formato "telefone,Nome da Empresa" (ou telefone;Nome / telefone - Nome /
  // telefone <tab> Nome). O nome é guardado para a IA cumprimentar pelo nome da empresa.
  const addManualNumbers = () => {
    const novos: typeof contacts = [];
    const existing = new Set(contacts.map((c) => c.phone));
    const vistos = new Set<string>();
    for (const linha of manualNumbers.split(/\r?\n/)) {
      if (!linha.trim()) continue;
      // tem letra na linha? então é "telefone <separador> nome" (uma empresa por linha).
      // só números? então pode ter vários números na mesma linha (vírgula/espaço/;).
      const temNome = /[A-Za-zÀ-ÿ]/.test(linha);
      if (temNome) {
        const m = linha.match(/(\d[\d()\s.-]{8,})\s*[,;\-\t|]?\s*(.*)$/);
        if (!m) continue;
        const p = m[1].replace(/\D/g, "");
        if (p.length < 10) continue;
        const nome = m[2].replace(/^["']|["']$/g, "").trim();
        if (!existing.has(p) && !vistos.has(p)) {
          vistos.add(p);
          novos.push({ jid: `${p}@s.whatsapp.net`, phone: p, name: nome, push_name: "", business_name: nome, is_group: false });
        }
      } else {
        for (const bruto of linha.split(/[\s,;]+/)) {
          const p = bruto.replace(/\D/g, "");
          if (p.length < 10) continue;
          if (!existing.has(p) && !vistos.has(p)) {
            vistos.add(p);
            novos.push({ jid: `${p}@s.whatsapp.net`, phone: p, name: "", push_name: "", business_name: "", is_group: false });
          }
        }
      }
    }
    if (novos.length === 0) {
      if (vistos.size > 0) { toast.info("Todos os números já estavam na lista"); }
      else { toast.error("Nenhum número válido (use DDD, ex.: 11987654321)"); }
      return;
    }
    setContacts([...contacts, ...novos]);
    setManualNumbers("");
    const comNome = novos.filter((n) => n.name).length;
    toast.success(`${novos.length} número(s) adicionado(s)` + (comNome ? `, ${comNome} com nome` : ""));
  };

  // NÃO renderizar early-return "Nenhum contato" — isso impedia adicionar números manualmente
  // (pedido #10). Agora mostra a entrada manual no topo e o empty-state dentro da lista.

  // Determine state mapping
  const activeJob = job !== null;
  const isRunning = job?.status === "running";
  const isFinished = job?.status === "done" || job?.status === "cancelled" || job?.status === "failed";
  const progressPct = activeJob ? Math.round((job.progress / job.total) * 100) : 0;

  // Merge results with planned contacts to show the full list
  const displayList = contacts.map((c, i) => {
    if (activeJob && i < job.results.length) {
      return job.results[i]; // Actual result from backend
    }
    return { name: c.name, phone: c.phone, status: "pending", duration_ms: 0 } as MassCallResult;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending": return <Clock className="h-4 w-4 text-muted-foreground" />;
      case "ringing": return <Phone className="h-4 w-4 text-primary animate-pulse" />;
      case "answered": return <CheckCircle2 className="h-4 w-4 text-primary" />;
      case "timeout": return <Clock className="h-4 w-4 text-amber-500" />;
      case "failed": return <AlertCircle className="h-4 w-4 text-destructive" />;
      case "REJECTED": return <XCircle className="h-4 w-4 text-destructive" />;
      default: return <XCircle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const statusLabel = (status: string) => {
    switch (status) {
      case "pending": return "Aguardando";
      case "ringing": return "Ligando...";
      case "answered": return "Atendido";
      case "timeout": return "Não atendeu";
      case "failed": return "Falha";
      case "REJECTED": return "Rejeitou";
      default: return status.toLowerCase();
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={onBack} disabled={isRunning}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <PhoneForwarded className="h-5 w-5" />
          {activeJob ? "Chamada em Massa" : "Confirmar Chamadas"}
        </h2>
      </div>

      {!activeJob && (
        <>
          {/* Modo 1: campanha com ÁUDIO (broadcast — toca áudio, mede escuta, capta resposta) */}
          <Card className="p-6 space-y-4 border-primary/30">
            <div className="flex items-center gap-2">
              <Megaphone className="h-5 w-5 text-primary" />
              <h3 className="text-lg font-medium">Campanha com áudio</h3>
              <Badge variant="secondary">recomendado</Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Toca um áudio quando o cliente atende, mede quanto cada um ouviu e transcreve a resposta.
              Aparece na aba Campanhas com as métricas.
            </p>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-muted-foreground">Nome da campanha</label>
                <Input value={campName} onChange={(e) => setCampName(e.target.value)} placeholder="Ex: Promoção de Julho" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Teste A/B — 2º roteiro (opcional)</label>
                <Input value={ttsTextB} onChange={(e) => setTtsTextB(e.target.value)} placeholder="Deixe vazio p/ não testar. Preenchido = alterna com o áudio principal (IA gera a voz da variante B) e mede qual converte." />
                <p className="mt-1 text-xs text-muted-foreground">A campanha alterna entre o áudio principal (A) e este texto (B). Veja a conversão por variante em Custos & ROI → Analytics.</p>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Áudio da chamada</label>
                <div className="flex gap-2 mb-2">
                  <button
                    type="button"
                    onClick={() => setAudioMode("upload")}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium ${audioMode === "upload" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                  >
                    Gravar / subir áudio
                  </button>
                  <button
                    type="button"
                    onClick={() => setAudioMode("ai")}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium ${audioMode === "ai" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                  >
                    Gerar por IA (texto)
                  </button>
                  <button
                    type="button"
                    onClick={() => setAudioMode("library")}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium ${audioMode === "library" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                  >
                    Áudios salvos
                  </button>
                </div>

                {audioMode === "upload" ? (
                  <label className="flex items-center gap-2 cursor-pointer rounded-md border border-dashed p-3 hover:bg-muted/40">
                    <Upload className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm truncate">{audioFile ? audioFile.name : "Escolher arquivo de áudio (mp3, ogg, wav)"}</span>
                    <input
                      type="file"
                      accept="audio/*"
                      className="hidden"
                      onChange={(e) => setAudioFile(e.target.files?.[0] ?? null)}
                    />
                  </label>
                ) : audioMode === "ai" ? (
                  <div className="space-y-2">
                    <textarea
                      value={ttsText}
                      onChange={(e) => { setTtsText(e.target.value); setPreviewUrl(null); }}
                      rows={3}
                      placeholder="Digite a mensagem que a IA vai falar na ligação..."
                      className="w-full rounded-md border bg-background p-2 text-sm"
                    />
                    <div className="flex items-center gap-2">
                      <select
                        className="rounded-md border bg-background px-2 py-1.5 text-sm"
                        value={ttsVoice}
                        onChange={(e) => { setTtsVoice(e.target.value); setPreviewUrl(null); }}
                      >
                        {ttsVoices.map((v) => <option key={v.value} value={v.value}>{v.label}</option>)}
                      </select>
                      <Button type="button" variant="outline" size="sm" onClick={onGenerateTTS} disabled={generating}>
                        {generating ? "Gerando..." : "Ouvir preview"}
                      </Button>
                    </div>
                    {previewUrl && <audio controls src={previewUrl} className="w-full h-9" />}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {savedAudios.length === 0 ? (
                      <p className="text-sm text-muted-foreground rounded-md border border-dashed p-3">
                        Nenhum áudio salvo ainda. Grave ou gere um áudio e marque "Salvar na biblioteca" pra reusar depois.
                      </p>
                    ) : (
                      <div className="divide-y rounded-md border max-h-56 overflow-y-auto">
                        {savedAudios.map((a) => (
                          <label
                            key={a.id}
                            className={`flex items-center gap-2 p-2.5 text-sm cursor-pointer hover:bg-muted/40 ${selectedAudioId === a.id ? "bg-primary/10" : ""}`}
                          >
                            <input
                              type="radio"
                              name="savedAudio"
                              checked={selectedAudioId === a.id}
                              onChange={() => onSelectSavedAudio(a.id)}
                              className="h-4 w-4"
                            />
                            <div className="flex-1 min-w-0">
                              <p className="font-medium truncate">{a.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {a.duration_ms ? `${Math.round(a.duration_ms / 1000)}s · ` : ""}
                                {new Date(a.created_at).toLocaleDateString("pt-BR")}
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={(e) => { e.preventDefault(); onDeleteSavedAudio(a.id); }}
                              className="text-muted-foreground hover:text-destructive"
                              aria-label="Remover áudio"
                            >
                              <XCircle className="h-4 w-4" />
                            </button>
                          </label>
                        ))}
                      </div>
                    )}
                    {libPreviewUrl && <audio controls src={libPreviewUrl} className="w-full h-9" />}
                  </div>
                )}

                {/* Salvar na biblioteca (só faz sentido pra áudio novo) */}
                {audioMode !== "library" && (
                  <div className="mt-2 space-y-2">
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={saveAudio} onChange={(e) => setSaveAudio(e.target.checked)} className="h-4 w-4" />
                      Salvar este áudio na biblioteca (pra reusar em campanhas futuras)
                    </label>
                    {saveAudio && (
                      <Input
                        value={saveAudioName}
                        onChange={(e) => setSaveAudioName(e.target.value)}
                        placeholder="Nome do áudio (ex: Comercial Promoção)"
                      />
                    )}
                  </div>
                )}
              </div>
              {/* MODO DE DISPARO (escolha obrigatória) */}
              <div>
                <label className="text-xs text-muted-foreground">Como disparar</label>
                <div className="flex gap-2 mt-1">
                  <button
                    type="button"
                    onClick={() => setDispatchMode("immediate")}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium ${dispatchMode === "immediate" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                  >
                    Agora
                  </button>
                  <button
                    type="button"
                    onClick={() => setDispatchMode("paced")}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium ${dispatchMode === "paced" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                  >
                    Ao longo do dia
                  </button>
                  <button
                    type="button"
                    onClick={() => setDispatchMode("multiline")}
                    disabled={pairedLines.length < 2}
                    title={pairedLines.length < 2 ? "Precisa de 2+ linhas conectadas" : ""}
                    className={`flex-1 rounded-md px-3 py-2 text-sm font-medium disabled:opacity-40 ${dispatchMode === "multiline" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                  >
                    Múltiplas linhas
                  </button>
                </div>
              </div>

              {dispatchMode === "immediate" ? (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-muted-foreground">Intervalo mín (s)</label>
                    <Input type="number" value={gapMin} onChange={(e) => setGapMin(Math.max(0, +e.target.value))} />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Intervalo máx (s)</label>
                    <Input type="number" value={gapMax} onChange={(e) => setGapMax(Math.max(0, +e.target.value))} />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Hora início (0=sem limite)</label>
                    <Input type="number" min={0} max={23} value={startHour} onChange={(e) => setStartHour(+e.target.value)} />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Hora fim (0=sem limite)</label>
                    <Input type="number" min={0} max={23} value={endHour} onChange={(e) => setEndHour(+e.target.value)} />
                  </div>
                </div>
              ) : (
                <div className="space-y-3 rounded-md border border-border/50 p-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-muted-foreground">Ligações por dia (alvo)</label>
                      <Input type="number" min={1} value={perDay} onChange={(e) => setPerDay(Math.max(1, +e.target.value))} />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Por minuto</label>
                      <Input type="number" min={1} value={perMin} onChange={(e) => setPerMin(Math.max(1, +e.target.value))} />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Começar o dia com (aquecimento)</label>
                      <Input type="number" min={1} value={rampStart} onChange={(e) => setRampStart(Math.max(1, +e.target.value))} />
                    </div>
                    <div />
                    <div>
                      <label className="text-xs text-muted-foreground">Hora início</label>
                      <Input type="number" min={0} max={23} value={paceStartHour} onChange={(e) => setPaceStartHour(+e.target.value)} />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Hora fim</label>
                      <Input type="number" min={0} max={23} value={paceEndHour} onChange={(e) => setPaceEndHour(+e.target.value)} />
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Dispara aos poucos ({perMin}/min, até {perDay}/dia), das {paceStartHour}h às {paceEndHour}h,
                    e continua amanhã até acabar a lista. O limite de segurança de cada linha (anti-bloqueio) sempre prevalece.
                  </p>
                  {dispatchMode === "multiline" && (
                    <div>
                      <label className="text-xs text-muted-foreground">Linhas a usar (a lista é dividida entre elas)</label>
                      <div className="mt-1 flex flex-wrap gap-2">
                        {pairedLines.map((l) => {
                          const on = selectedLines.length === 0 || selectedLines.includes(l.id);
                          return (
                            <button
                              key={l.id}
                              type="button"
                              onClick={() =>
                                setSelectedLines((prev) => {
                                  const base = prev.length === 0 ? pairedLines.map((x) => x.id) : prev;
                                  return base.includes(l.id) ? base.filter((x) => x !== l.id) : [...base, l.id];
                                })
                              }
                              className={`rounded-md px-2 py-1 text-xs font-medium ${on ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                            >
                              {l.name || l.jid || l.id.slice(0, 6)}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={captureReply} onChange={(e) => setCaptureReply(e.target.checked)} className="h-4 w-4" />
                Transcrever a resposta do cliente e detectar interesse
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={preNotify} onChange={(e) => setPreNotify(e.target.checked)} className="h-4 w-4" />
                Pré-avisar no Telegram antes de cada lote (permite remover números de última hora)
              </label>
              {preNotify && (
                <div className="flex items-center gap-2 pl-6">
                  <label className="text-xs text-muted-foreground">Avisar de quantos em quantos:</label>
                  <Input type="number" min={1} value={batchSize} onChange={(e) => setBatchSize(Math.max(1, +e.target.value))} className="w-20" />
                </div>
              )}
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={onBack}>Cancelar</Button>
              <Button
                onClick={onStartBroadcast}
                disabled={loading || !pairedSession || (audioMode === "upload" ? !audioFile : audioMode === "library" ? !selectedAudioId : !ttsText.trim())}
                className="gap-2"
              >
                <Megaphone className="h-4 w-4" />
                {dispatchMode === "immediate"
                  ? `Disparar campanha (${contacts.length})`
                  : dispatchMode === "paced"
                  ? `Agendar ao longo do dia (${contacts.length})`
                  : `Dividir entre linhas (${contacts.length})`}
              </Button>
            </div>
          </Card>

          {/* Modo 2: só toca (campainha, sem áudio) */}
          <Card className="p-6 text-center space-y-4">
            <div>
              <h3 className="text-base font-medium">Ou apenas tocar (sem áudio)</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Liga em sequência estrita, aguardando cada chamada (timeout 30s). Não toca áudio nem mede escuta.
              </p>
            </div>
            <div className="flex justify-center gap-3">
              <Button variant="outline" onClick={onStart} disabled={loading}>Só tocar</Button>
            </div>
          </Card>
        </>
      )}

      {activeJob && (
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">
                Progresso: {job.progress} de {job.total}
              </p>
              <p className="text-sm text-muted-foreground">
                Status geral: <Badge variant={job.status === "running" ? "default" : "secondary"}>{job.status}</Badge>
              </p>
            </div>
            {isRunning && (
              <Button variant="destructive" size="sm" onClick={onCancel} disabled={loading}>
                Parar Agora
              </Button>
            )}
            {isFinished && (
              <Button variant="outline" size="sm" onClick={onBack}>
                Voltar
              </Button>
            )}
          </div>

          <div className="w-full bg-secondary rounded-full h-2.5">
            <div
              className="bg-primary h-2.5 rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            ></div>
          </div>
        </Card>
      )}

      {/* Entrada manual de números (pedido #10): antes só vinha da aba Contatos. */}
      {!activeJob && (
        <Card className="p-3 space-y-2">
          <h3 className="font-medium text-sm">Adicionar números manualmente</h3>
          <Textarea
            value={manualNumbers}
            onChange={(e) => setManualNumbers(e.target.value)}
            placeholder={"Cole números com DDD (vírgula ou uma por linha).\nOu a lista da captação: telefone,Nome da Empresa — um por linha.\nEx.: 11987654321, 21998765432"}
            className="min-h-[70px] text-sm resize-y"
          />
          <div className="flex gap-2">
            <Button size="sm" variant="outline" className="flex-1" onClick={addManualNumbers} disabled={!manualNumbers.trim()}>
              Adicionar à fila
            </Button>
            {contacts.length > 0 && (
              <Button size="sm" variant="ghost" className="text-destructive" onClick={clear}>
                Limpar tudo
              </Button>
            )}
          </div>
          {contacts.length === 0 && (
            <p className="text-xs text-muted-foreground text-center py-2">
              Adicione números acima ou selecione contatos na aba Contatos.
            </p>
          )}
        </Card>
      )}

      <div className="space-y-2">
        <h3 className="font-medium text-sm text-muted-foreground">Fila de Contatos ({contacts.length})</h3>
        <Card className="divide-y overflow-hidden">
          {displayList.map((res, i) => (
            <div key={`${res.phone}-${i}`} className="flex items-center justify-between p-3 text-sm transition-colors hover:bg-muted/30">
              <div className="flex items-center gap-3">
                <span className="text-muted-foreground w-5 text-right text-xs">{i + 1}.</span>
                <div>
                  <p className="font-medium">{res.name || `+${res.phone}`}</p>
                  <p className="text-xs text-muted-foreground">+{res.phone}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="flex items-center gap-1.5 font-normal">
                  {getStatusIcon(res.status)}
                  {statusLabel(res.status)}
                </Badge>
              </div>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
};
