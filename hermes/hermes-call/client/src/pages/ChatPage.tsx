import { useState, useEffect, useRef, useCallback } from "react";
import { MessageCircle, Search, Send, Loader2, RefreshCcw, Phone, PhoneIncoming, ChevronDown, Smartphone } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AvatarInitial } from "@/components/shared/AvatarInitial";
import { apiGet, apiPost } from "@/lib/api";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useSessions, ensureSessionsWired, setActiveSession } from "@/stores/sessions";

// ChatPage — inbox de conversas REAIS do WhatsApp, estilo Chatwoot/Evolution:
// coluna esquerda com a lista de conversas (mais recente no topo), coluna direita
// com a thread da conversa selecionada e caixa pra responder. Diferente do Garimpo
// (que é seleção em massa pra campanha), aqui o foco é ATENDER 1 a 1.

type ChatItem = {
  id: string;          // JID ou "call:<uuid>"
  phone: string;
  name: string;
  lastMessage: string;
  time: string;
  date: string;
  unread: boolean;
  isUnknown: boolean;
  avatar?: string;
  isGroup?: boolean;
  source?: "whatsapp" | "call" | "both";
  resumo?: string;
  classificacao?: string;
  callId?: string;
};

type ChatFilter = "all" | "unread" | "groups" | "calls";

type Msg = { text: string; fromMe: boolean; time: string; ts: number };

export const ChatPage = () => {
  const [chats, setChats] = useState<ChatItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [chatFilter, setChatFilter] = useState<ChatFilter>("all");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [msgsLoading, setMsgsLoading] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [reloadTick, setReloadTick] = useState(0);
  const [pickerOpen, setPickerOpen] = useState(false);
  const threadRef = useRef<HTMLDivElement>(null);

  // Zustand store: sessões do WhatsApp (múltiplos números).
  const sessions = useSessions((s) => s.sessions);
  const storeActiveId = useSessions((s) => s.activeId);
  useEffect(() => { ensureSessionsWired(); }, []);

  const pairedSessions = sessions.filter((s) => s.paired);
  const sid = storeActiveId ?? pairedSessions[0]?.id ?? null;

  // Carrega a lista de conversas (só conversas reais — include=contacts fica de fora:
  // aqui é inbox, não agenda). Recarrega a cada 15s pra pegar msgs novas.
  const loadChats = useCallback(() => {
    const params = new URLSearchParams({ limit: "500" });
    if (sid) params.set("sid", sid);
    apiGet<ChatItem[]>(`/api/inbox?${params}`)
      .then((data) => setChats(Array.isArray(data) ? data : []))
      .catch(() => setChats([]))
      .finally(() => setLoading(false));
  }, [sid]);

  useEffect(() => {
    loadChats();
    const iv = setInterval(loadChats, 15000);
    return () => clearInterval(iv);
  }, [loadChats, reloadTick]);

  // Carrega mensagens reais do chat selecionado.
  // Quantas mensagens carregar (as mais recentes). "Carregar mensagens antigas" aumenta.
  const PAGE = 200;
  const [msgLimit, setMsgLimit] = useState(PAGE);
  const [hasOlder, setHasOlder] = useState(false);

  const loadMsgs = useCallback(() => {
    if (!activeId || !sid) return;

    // Para entries de chamada, busca transcrições via /api/transcripts
    if (activeId.startsWith("call:")) {
      const callChat = chats.find((c) => c.id === activeId);
      if (!callChat) return;
      setMsgsLoading(true);
      apiGet<{ transcripts: { transcript?: string; resumo?: string; classificacao?: string; created_at?: string }[] }>(
        `/api/transcripts?q=${encodeURIComponent(callChat.phone)}&limit=50`
      )
        .then((res) => {
          const transcripts = res?.transcripts || [];
          const mapped: Msg[] = [];
          for (const t of transcripts) {
            if (!t.transcript) continue;
            const lines = t.transcript.split("\n").filter(Boolean);
            const ts = t.created_at ? new Date(t.created_at).getTime() : 0;
            const time = ts ? new Date(ts).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "";
            for (const line of lines) {
              const isAgent = /^(Agente|Agent|Atendente)/i.test(line);
              mapped.push({
                text: line.replace(/^(Cliente|Agente|Agent|Atendente)[:\s]*/i, ""),
                fromMe: isAgent,
                ts,
                time,
              });
            }
            if (t.resumo) {
              mapped.push({ text: `📋 Resumo: ${t.resumo}`, fromMe: false, ts: ts + 1, time });
            }
          }
          setMsgs(mapped);
        })
        .catch(() => setMsgs([]))
        .finally(() => setMsgsLoading(false));
      return;
    }

    setMsgsLoading(true);
    // Histórico guardado no servidor: GET /api/sessions/{sid}/chats/{chatId}/messages
    // (mais recentes primeiro; limit até 1000).
    apiGet<{ body?: string; fromMe?: boolean; timestamp?: number; type?: string }[]>(
      `/api/sessions/${sid}/chats/${encodeURIComponent(activeId)}/messages?limit=${msgLimit}`
    )
      .then((raw) => {
        const arr = Array.isArray(raw) ? raw : [];
        setHasOlder(arr.length >= msgLimit && msgLimit < 1000);
        const mediaLabel = (t?: string) => {
          switch (t) {
            case "audio": return "🎤 Áudio";
            case "image": return "🖼️ Imagem";
            case "video": return "🎬 Vídeo";
            case "document": return "📄 Documento";
            case "sticker": return "Figurinha";
            default: return "";
          }
        };
        const mapped: Msg[] = arr
          .map((m) => ({
            // Mostra o texto; se for mídia sem texto (áudio/imagem), usa rótulo em vez de sumir.
            text: m.body || mediaLabel(m.type),
            fromMe: !!m.fromMe,
            ts: m.timestamp || 0,
            time: m.timestamp
              ? new Date(m.timestamp).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
              : "",
          }))
          .filter((m) => m.text) // agora mídia tem rótulo, só cai fora o que é vazio de verdade
          .sort((a, b) => a.ts - b.ts);
        setMsgs(mapped);
      })
      .catch(() => setMsgs([]))
      .finally(() => setMsgsLoading(false));
  }, [activeId, sid, chats, msgLimit]);

  // Trocou de conversa: limpa e volta a carregar só as mais recentes.
  useEffect(() => {
    setMsgs([]);
    setMsgLimit(PAGE);
    setHasOlder(false);
  }, [activeId]);

  useEffect(() => {
    loadMsgs();
    if (!activeId) return;
    const iv = setInterval(loadMsgs, 8000); // polling da thread aberta
    return () => clearInterval(iv);
  }, [activeId, loadMsgs]);

  // Mensagens mais antigas: pede mais itens do histórico guardado no servidor. Antes
  // chamava POST /api/sessions/{sid}/chats/{jid}/history, que não existe no servidor
  // (dava erro toda vez que uma conversa abria, porque também era chamado sozinho).
  const [fetchingHistory, setFetchingHistory] = useState(false);
  const loadOlder = () => {
    if (!activeId || !sid || fetchingHistory) return;
    setFetchingHistory(true);
    setMsgLimit((n) => Math.min(n + PAGE, 1000));
    setTimeout(() => setFetchingHistory(false), 1500);
  };

  // Autoscroll pro fim quando chegam mensagens.
  useEffect(() => {
    if (threadRef.current) threadRef.current.scrollTop = threadRef.current.scrollHeight;
  }, [msgs]);

  const send = async () => {
    const text = draft.trim();
    if (!text || !activeId || !sid || sending) return;
    setSending(true);
    // otimista
    setMsgs((prev) => [...prev, { text, fromMe: true, ts: Date.now(), time: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) }]);
    setDraft("");
    try {
      await apiPost(`/api/sessions/${sid}/messages/text`, { to: activeId, text });
      setTimeout(loadMsgs, 1200);
    } catch {
      toast.error("Não consegui enviar. Tenta de novo.");
    } finally {
      setSending(false);
    }
  };

  const isCallEntry = (id: string | null) => id?.startsWith("call:");

  const filtered = chats.filter((c) => {
    if (chatFilter === "unread" && !c.unread) return false;
    if (chatFilter === "groups" && !c.isGroup) return false;
    if (chatFilter === "calls" && c.source !== "call" && c.source !== "both") return false;
    if (!search) return true;
    const q = search.toLowerCase();
    return (c.name || "").toLowerCase().includes(q) || (c.phone || "").includes(q);
  });
  const unreadCount = chats.filter((c) => c.unread).length;

  const active = chats.find((c) => c.id === activeId);

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto h-[calc(100vh-100px)] flex flex-col">
      <div className="flex items-center justify-between mb-4 shrink-0">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-emerald-500" /> Chat
        </h2>
        <div className="flex items-center gap-2">
          {/* Seletor de número (Fix 4) — só aparece se há mais de 1 sessão pareada */}
          {pairedSessions.length > 1 && (
            <div className="relative">
              <button
                onClick={() => setPickerOpen((v) => !v)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-border/50 bg-card/60 hover:bg-muted/40 transition-colors text-sm"
              >
                <Smartphone className="w-4 h-4 text-emerald-500" />
                <span className="max-w-[140px] truncate">
                  {pairedSessions.find((s) => s.id === sid)?.jid?.split("@")[0]?.replace(/^\d{2}/, "+$&") || "Selecionar número"}
                </span>
                <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", pickerOpen && "rotate-180")} />
                {pairedSessions.find((s) => s.id === sid)?.connected ? (
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-red-400" />
                )}
              </button>
              {pickerOpen && (
                <div className="absolute right-0 top-full mt-1 z-50 min-w-[220px] rounded-xl border border-border/50 bg-card shadow-lg shadow-black/20 py-1 animate-in fade-in slide-in-from-top-2 duration-150">
                  {pairedSessions.map((ps) => {
                    const phone = ps.jid?.split("@")[0] || ps.id.slice(0, 8);
                    const label = ps.name || phone;
                    const isCurrent = ps.id === sid;
                    return (
                      <button
                        key={ps.id}
                        onClick={() => { setActiveSession(ps.id); setPickerOpen(false); setActiveId(null); }}
                        className={cn(
                          "w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-muted/30 transition-colors text-sm",
                          isCurrent && "bg-emerald-500/10"
                        )}
                      >
                        <Smartphone className={cn("w-4 h-4 shrink-0", isCurrent ? "text-emerald-500" : "text-muted-foreground")} />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate">{label}</div>
                          {ps.name && <div className="text-xs text-muted-foreground">{phone}</div>}
                        </div>
                        <span className={cn("w-2 h-2 rounded-full shrink-0", ps.connected ? "bg-emerald-500" : "bg-red-400")} />
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}
          <Button variant="outline" size="sm" className="gap-2 text-xs" onClick={() => setReloadTick((t) => t + 1)}>
            <RefreshCcw className="w-3 h-3" /> Atualizar
          </Button>
        </div>
      </div>

      <div className="flex-1 flex gap-0 min-h-0 rounded-2xl border border-border/50 overflow-hidden bg-card/30">
        {/* Lista de conversas */}
        <div className="w-full md:w-[360px] shrink-0 border-r border-border/50 flex flex-col min-h-0">
          <div className="p-3 border-b border-border/50 shrink-0 space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar conversa..."
                className="pl-9 bg-background border-border/50 rounded-xl h-10"
              />
            </div>
            <div className="flex items-center gap-2">
              {([
                { k: "all", label: "Tudo" },
                { k: "unread", label: unreadCount > 0 ? `Não lidas ${unreadCount}` : "Não lidas" },
                { k: "calls", label: "Chamadas" },
                { k: "groups", label: "Grupos" },
              ] as { k: ChatFilter; label: string }[]).map((f) => (
                <button
                  key={f.k}
                  onClick={() => setChatFilter(f.k)}
                  className={cn(
                    "text-xs px-3 py-1 rounded-full border transition-colors",
                    chatFilter === f.k
                      ? "bg-emerald-500 text-white border-emerald-500"
                      : "border-border/50 text-muted-foreground hover:bg-muted/30"
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {loading ? (
              <div className="flex items-center justify-center py-10 text-muted-foreground gap-2 text-sm">
                <Loader2 className="h-4 w-4 animate-spin" /> Carregando conversas...
              </div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-10 text-muted-foreground text-sm">Nenhuma conversa.</div>
            ) : (
              filtered.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveId(c.id)}
                  className={cn(
                    "w-full flex items-center gap-3 p-3 hover:bg-muted/30 transition-colors text-left border-b border-border/30",
                    activeId === c.id && "bg-emerald-500/5"
                  )}
                >
                  <div className="shrink-0 relative">
                    <AvatarInitial name={c.name || c.phone} src={c.avatar} />
                    {c.unread && <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-background" />}
                    {(c.source === "call" || c.source === "both") && (
                      <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-blue-500 rounded-full border-2 border-background flex items-center justify-center">
                        <Phone className="w-2.5 h-2.5 text-white" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-sm truncate">{c.name || c.phone}</span>
                      <span className="text-[10px] text-muted-foreground shrink-0">{c.time}</span>
                    </div>
                    <p className="text-xs text-muted-foreground truncate">{c.lastMessage || "Sem mensagens ainda"}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Thread */}
        <div className="hidden md:flex flex-1 flex-col min-h-0">
          {!active ? (
            <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm flex-col gap-2">
              <MessageCircle className="w-10 h-10 opacity-30" />
              Selecione uma conversa
            </div>
          ) : (
            <>
              <div className="p-3 border-b border-border/50 flex items-center gap-3 shrink-0">
                <AvatarInitial name={active.name || active.phone} src={active.avatar} />
                <div className="flex flex-col">
                  <span className="font-semibold text-sm">{active.name || active.phone}</span>
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    {active.phone}
                    {(active.source === "call" || active.source === "both") && (
                      <span className="inline-flex items-center gap-1 ml-2 px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px]">
                        <PhoneIncoming className="w-3 h-3" /> Chamada de voz
                      </span>
                    )}
                  </span>
                </div>
              </div>

              <div ref={threadRef} className="flex-1 p-4 overflow-y-auto custom-scrollbar flex flex-col gap-2 bg-background/40">
                {!isCallEntry(activeId) && hasOlder && (
                  <button
                    onClick={loadOlder}
                    disabled={fetchingHistory}
                    className="self-center mb-2 text-xs text-emerald-500 hover:text-emerald-400 flex items-center gap-1 disabled:opacity-50"
                  >
                    {fetchingHistory ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCcw className="h-3 w-3" />}
                    {fetchingHistory ? "Carregando..." : "Carregar mensagens antigas"}
                  </button>
                )}
                {msgsLoading && msgs.length === 0 ? (
                  <div className="flex items-center justify-center py-8 text-muted-foreground gap-2 text-sm">
                    <Loader2 className="h-4 w-4 animate-spin" /> Carregando...
                  </div>
                ) : msgs.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground text-xs">Sem mensagens nesta conversa.</div>
                ) : (
                  msgs.map((m, i) => (
                    <div key={i} className={cn("flex flex-col max-w-[75%]", m.fromMe ? "self-end items-end" : "self-start items-start")}>
                      <div className={cn("px-3 py-2 rounded-xl text-sm whitespace-pre-wrap break-words", m.fromMe ? "bg-emerald-600 text-white rounded-tr-none" : "bg-card border border-border/50 rounded-tl-none")}>
                        {m.text}
                      </div>
                      <span className="text-[10px] text-muted-foreground mt-0.5 mx-1">{m.time}</span>
                    </div>
                  ))
                )}
              </div>

              {!isCallEntry(activeId) ? (
                <div className="p-3 border-t border-border/50 flex gap-2 shrink-0">
                  <Input
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                    placeholder="Escreva uma mensagem..."
                    className="bg-background border-border/50 rounded-xl"
                    disabled={sending}
                  />
                  <Button onClick={send} disabled={sending || !draft.trim()} className="bg-emerald-500 hover:bg-emerald-600 shrink-0">
                    {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </Button>
                </div>
              ) : (
                <div className="p-3 border-t border-border/50 text-center text-xs text-muted-foreground">
                  <PhoneIncoming className="w-4 h-4 inline mr-1 opacity-50" />
                  Transcrição de chamada de voz — somente leitura
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
