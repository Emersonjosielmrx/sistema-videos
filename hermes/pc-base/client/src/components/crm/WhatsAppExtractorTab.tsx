import { useState, useMemo, useEffect } from "react";
import { Search, MessageCircle, CheckSquare, Square, Send, Tag, User, AlertCircle, X, CheckCheck, Inbox, RefreshCcw, Loader2, Download, UserMinus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AvatarInitial } from "@/components/shared/AvatarInitial";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { apiGet, apiPost } from "@/lib/api";
import { startBroadcast } from "@/services/broadcast";

// Tipo de retorno do /api/whatsapp/chats — conversa real do whatsmeow (não MOCK).
// Campos: id (JID), phone, name (cache waNames), lastMessage, time (HH:MM),
// date (RFC3339 UTC), unread, isUnknown, avatar, source ("chat"|"contact").
type GarimpoChat = {
  id: string;
  phone: string;
  name: string;
  lastMessage: string;
  time: string;
  date: string;
  unread: boolean;
  isUnknown: boolean;
  avatar?: string;
  source?: "chat" | "contact";
};

export function WhatsAppExtractorTab() {
  const [chats, setChats] = useState<GarimpoChat[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadTick, setReloadTick] = useState(0);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(null);
  const [filter, setFilter] = useState<"all" | "unknown" | "unread">("all");
  const [timeFilter, setTimeFilter] = useState<"all" | "today" | "24h" | "week">("all");
  // Default "Só Conversas" (pedido da dona 2026-07-22): o Garimpo deve mostrar as
  // CONVERSAS do WhatsApp (como o app), não a agenda de contatos (que já tem aba própria).
  const [includeContacts, setIncludeContacts] = useState(false);
  const [search, setSearch] = useState("");

  // UI States
  const [previewChatId, setPreviewChatId] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number, y: number, chatId: string } | null>(null);
  // Mensagens REAIS do chat aberto no preview (substitui o antigo MOCK_HISTORY que
  // quebrava a tela). Carrega de /api/sessions/{sid}/messages ao abrir cada conversa.
  const [previewMsgs, setPreviewMsgs] = useState<{ text: string; sender: "agent" | "client"; time: string }[]>([]);
  const [previewMsgsLoading, setPreviewMsgsLoading] = useState(false);

  // Close context menu on click outside
  useEffect(() => {
    const handleClick = () => setContextMenu(null);
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

  // AUTO-SYNC ao abrir a aba (pedido da dona 2026-07-22): sincroniza as conversas do
  // WhatsApp automaticamente na entrada, sem precisar clicar em "Sincronizar Conversas".
  // Roda 1x por montagem. O reload dos chats vem em seguida (setReloadTick no handler).
  useEffect(() => {
    handleSyncAppState(true); // silencioso: não pisca a tela nem mostra erro no auto
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // CARREGA OS CHATS REAIS do backend (whatsmeow listChats). Re-carrega ao mudar filtro
  // de tempo e ao pedir reload via botão. O backend já resolve nome/foto em background
  // (waNames) — segundo load vem completo.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    const qs = new URLSearchParams({
      filter,
      timeFilter,
      limit: includeContacts ? "5000" : "100",
    });
    if (includeContacts) qs.set("include", "contacts");
    apiGet<GarimpoChat[]>(`/api/whatsapp/chats?${qs.toString()}`)
      .then((data) => {
        if (cancelled) return;
        setChats(Array.isArray(data) ? data : []);
      })
      .catch((e) => {
        if (cancelled) return;
        setLoadError((e as Error).message || "Falha ao carregar conversas");
        setChats([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [filter, timeFilter, reloadTick, includeContacts]);

  const filteredChats = useMemo(() => {
    let res = chats;
    if (filter === "unknown") res = res.filter(c => c.isUnknown);
    if (filter === "unread") res = res.filter(c => c.unread);

    if (timeFilter === "today") {
      const today = new Date();
      const y = today.getFullYear(), m = today.getMonth(), d = today.getDate();
      res = res.filter(c => {
        const dt = new Date(c.date);
        return dt.getFullYear() === y && dt.getMonth() === m && dt.getDate() === d;
      });
    } else if (timeFilter === "24h") {
      const since = Date.now() - 86400000;
      res = res.filter(c => new Date(c.date).getTime() >= since);
    } else if (timeFilter === "week") {
      const since = Date.now() - 7 * 86400000;
      res = res.filter(c => new Date(c.date).getTime() >= since);
    }

    if (search) {
      const q = search.toLowerCase();
      res = res.filter(c => (c.name || "").toLowerCase().includes(q) || c.phone.includes(q));
    }
    return res;
  }, [chats, filter, timeFilter, search]);

  const toggleSelect = (id: string, index: number, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent opening preview
    
    let newSelection = [...selectedIds];
    const isSelecting = !selectedIds.includes(id);

    if (e.shiftKey && lastSelectedIndex !== null) {
      // Shift-click logic
      const start = Math.min(lastSelectedIndex, index);
      const end = Math.max(lastSelectedIndex, index);
      const slice = filteredChats.slice(start, end + 1).map(c => c.id);
      
      if (isSelecting) {
        newSelection = Array.from(new Set([...newSelection, ...slice]));
      } else {
        newSelection = newSelection.filter(x => !slice.includes(x));
      }
    } else {
      // Normal click logic
      if (isSelecting) {
        newSelection.push(id);
      } else {
        newSelection = newSelection.filter(x => x !== id);
      }
    }

    setSelectedIds(newSelection);
    setLastSelectedIndex(index);
  };

  const selectAll = () => {
    if (selectedIds.length === filteredChats.length) {
      setSelectedIds([]);
      setLastSelectedIndex(null);
    } else {
      setSelectedIds(filteredChats.map(c => c.id));
    }
  };

  const selectLastN = (n: number) => {
    const ids = filteredChats.slice(0, n).map(c => c.id);
    setSelectedIds(Array.from(new Set([...selectedIds, ...ids])));
    toast.success(`${ids.length} contatos selecionados`);
  };

  // silent=true (auto-sync ao abrir): sem toasts de erro e sem reload abrupto que
  // embaralha a lista enquanto o usuário lê. O clique manual (silent=false) dá feedback.
  const handleSyncAppState = async (silent = false) => {
    setSyncing(true);
    try {
      const r = await apiPost<{ ok: boolean; synced: string[]; error_critical_unblock_low?: string }>(
        "/api/whatsapp/sync-app-state",
        {}
      );
      const synced = r.synced?.length ?? 0;
      if (synced > 0) {
        if (!silent) {
          toast.success(`Sincronização concluída (${synced} coleções). Recarregando conversas...`);
          setTimeout(() => setReloadTick(t => t + 1), 1500);
        }
        // no modo silent NÃO forçamos reload: a lista já carrega sozinha; o sync
        // só enriquece o banco pro próximo load natural, sem piscar a tela.
      } else if (!silent) {
        toast.error("Sync não retornou coleções. Verifique a conexão do WhatsApp.");
      }
    } catch (e: any) {
      if (!silent) toast.error(`Falha no sync: ${e?.message ?? "erro desconhecido"}`);
    } finally {
      setSyncing(false);
    }
  };

  const [dispatching, setDispatching] = useState(false);
  // Disparo REAL de campanha de LIGAÇÃO IA a partir dos chats selecionados no Garimpo.
  // Antes isto era só um toast fake — não ligava nada. Agora: pega a linha pareada, os
  // números selecionados (resolve phone real do chat), pede o texto da oferta e chama
  // /api/sessions/{sid}/broadcast (mesma engine da campanha em massa).
  const handleCampaignTrigger = async (type: string) => {
    const ids = selectedIds.length > 0 ? selectedIds : (previewChatId ? [previewChatId] : []);
    if (ids.length === 0) { toast.error("Selecione ao menos uma conversa."); return; }
    // Monta numbers+names a partir dos chats selecionados (usa phone; ignora grupos).
    const chosen = chats.filter(c => ids.includes(c.id) && !c.id.endsWith("@g.us"));
    const numbers = chosen.map(c => (c.phone || c.id.split("@")[0]).replace(/\D/g, "")).filter(Boolean);
    const names = chosen.map(c => c.name || "");
    if (numbers.length === 0) { toast.error("Nenhum número válido (grupos não podem receber ligação)."); return; }
    const msg = window.prompt(
      `Disparar ligação IA para ${numbers.length} contato(s).\n\nEscreva a mensagem/oferta que a IA vai falar ao atender:`,
      "Olá! Aqui é da nossa equipe, tudo bem? Posso te fazer uma pergunta rapidinha?"
    );
    if (msg === null) return; // cancelou
    if (!msg.trim()) { toast.error("Mensagem vazia."); return; }
    setDispatching(true);
    try {
      const sess = await apiGet<{ sessions: { id: string; paired?: boolean }[] }>("/api/sessions");
      const sid = (sess.sessions || []).find(s => s.paired)?.id || (sess.sessions || [])[0]?.id;
      if (!sid) { toast.error("Nenhuma linha WhatsApp conectada."); return; }
      const res = await startBroadcast(sid, {
        name: `Garimpo — ${type} (${new Date().toLocaleDateString("pt-BR")})`,
        numbers, names,
        tts_message: msg.trim(),
        mode: "immediate",
        gap_min_ms: 8000, gap_max_ms: 12000, // espaçado (anti-ban)
        pre_notify: true, batch_size: 10, pre_notify_sec: 20,
        capture_reply: true,
      });
      toast.success(`Campanha disparada! ${res.total} contato(s) na fila.`);
      setSelectedIds([]);
    } catch (e: any) {
      toast.error(`Falha ao disparar: ${e?.message ?? "erro"}`);
    } finally {
      setDispatching(false);
    }
  };

  const markAsRead = async () => {
    // Grava no servidor (persiste entre recargas). Não envia "visto" pro WhatsApp do cliente.
    const ids = [...selectedIds];
    try {
      await apiPost("/api/whatsapp/chats/read", { chat_ids: ids });
      setChats(chats.map(c => ids.includes(c.id) ? { ...c, unread: false } : c));
      toast.success(`${ids.length} conversas marcadas como lidas.`);
    } catch (e: any) {
      toast.error(`Não consegui marcar como lidas: ${e?.message ?? "erro"}`);
      return;
    }
    setSelectedIds([]);
  };

  const handleContextMenu = (e: React.MouseEvent, chatId: string) => {
    e.preventDefault();
    setContextMenu({ x: e.pageX, y: e.pageY, chatId });
  };

  // Move o contato do menu de contexto pra 1ª etapa do funil (grava de verdade via
  // /api/crm/move). Antes era só um toast fake que não persistia nada.
  const ctxMoveToFunnel = async (chatId: string) => {
    setContextMenu(null);
    try {
      const board = await apiGet<{ stages: { name: string }[] }>("/api/crm/board");
      const firstStage = board.stages?.[0]?.name;
      if (!firstStage) { toast.error("Crie uma etapa no Funil primeiro."); return; }
      await apiPost("/api/crm/move", { jid: chatId, stage: firstStage });
      toast.success(`Adicionado à etapa "${firstStage}" do Funil.`);
    } catch (e: any) {
      toast.error(`Falha ao mover para o Funil: ${e?.message ?? "erro"}`);
    }
  };

  // Aplica uma tag existente ao contato (persiste via /api/contacts/tags/bulk). Antes
  // era um toast fake "Tag adicionada" que não gravava nada.
  const ctxAddTag = async (chatId: string) => {
    setContextMenu(null);
    try {
      const r = await apiGet<{ tags?: { id: string; name: string }[] } | { id: string; name: string }[]>("/api/contacts/tags");
      const list = Array.isArray(r) ? r : (r.tags ?? []);
      if (list.length === 0) { toast.error("Crie uma tag primeiro na aba Tags."); return; }
      const name = window.prompt("Aplicar qual tag? " + list.map(t => t.name).join(", "), list[0].name);
      if (!name) return;
      const tag = list.find(t => t.name.toLowerCase() === name.toLowerCase());
      if (!tag) { toast.error("Tag não encontrada."); return; }
      await apiPost("/api/contacts/tags/bulk", { jids: [chatId], tag_id: tag.id });
      toast.success(`Tag "${tag.name}" aplicada.`);
    } catch (e: any) {
      toast.error(`Falha ao aplicar tag: ${e?.message ?? "erro"}`);
    }
  };

  // Bloqueia o contato de verdade (blacklist de follow-up via /api/followup/blacklist).
  // Antes era um toast fake "Contato bloqueado/arquivado".
  const ctxBlock = async (chatId: string) => {
    setContextMenu(null);
    const chat = chats.find(c => c.id === chatId);
    const phone = (chat?.phone || chatId.split("@")[0]).replace(/\D/g, "");
    if (!phone) { toast.error("Número inválido."); return; }
    if (!window.confirm(`Bloquear o contato +${phone}? Ele não receberá mais campanhas/follow-ups.`)) return;
    try {
      await apiPost("/api/followup/blacklist", { phone, reason: "Bloqueado manualmente no Garimpo" });
      toast.success("Contato bloqueado.");
    } catch (e: any) {
      toast.error(`Falha ao bloquear: ${e?.message ?? "erro"}`);
    }
  };

  const previewChat = chats.find(c => c.id === previewChatId);

  // Carrega as mensagens REAIS do chat aberto (substitui o MOCK_HISTORY). Busca a
  // sessão pareada e pede /api/sessions/{sid}/messages?chatId=<jid>. Ordena antigas→novas.
  useEffect(() => {
    if (!previewChatId) { setPreviewMsgs([]); return; }
    let cancelled = false;
    setPreviewMsgsLoading(true);
    (async () => {
      try {
        const sess = await apiGet<{ sessions: { id: string; paired?: boolean }[] }>("/api/sessions");
        const sid = (sess.sessions || []).find(s => s.paired)?.id || (sess.sessions || [])[0]?.id;
        if (!sid) { if (!cancelled) setPreviewMsgs([]); return; }
        const raw = await apiGet<{ body?: string; fromMe?: boolean; timestamp?: number }[]>(
          `/api/sessions/${sid}/messages?chatId=${encodeURIComponent(previewChatId)}&limit=50`
        );
        if (cancelled) return;
        const arr = Array.isArray(raw) ? raw : [];
        const mapped = arr
          .map(m => ({
            text: m.body || "",
            sender: (m.fromMe ? "agent" : "client") as "agent" | "client",
            time: m.timestamp ? new Date(m.timestamp).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "",
          }))
          .filter(m => m.text)
          .reverse();
        setPreviewMsgs(mapped);
      } catch {
        if (!cancelled) setPreviewMsgs([]);
      } finally {
        if (!cancelled) setPreviewMsgsLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [previewChatId]);

  return (
    <div className="space-y-4 relative pb-24 h-[calc(100vh-200px)] flex flex-col">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-muted/10 p-4 rounded-2xl border border-border/50 shrink-0">
        <div>
           <h3 className="text-lg font-bold text-foreground flex items-center gap-2"><MessageCircle className="w-5 h-5 text-emerald-500" /> Garimpo WhatsApp</h3>
           <p className="text-sm text-muted-foreground mt-1 max-w-lg">
             Selecione conversas recentes, analise o contexto e crie campanhas em massa em um clique. Dica: Use Shift+Clique.
           </p>
        </div>
        
        <div className="flex items-center gap-2 w-full md:w-auto">
          <select 
            className="h-10 bg-background border-border/50 rounded-xl px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value as any)}
          >
            <option value="all">Todo o Período</option>
            <option value="today">Hoje</option>
            <option value="24h">Últimas 24h</option>
            <option value="week">Última Semana</option>
          </select>
          <div className="relative w-full md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar nome ou número..." 
              className="pl-9 bg-background border-border/50 rounded-xl h-10 w-full"
            />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 shrink-0 overflow-x-auto pb-1 custom-scrollbar">
        <Button 
          variant={filter === "all" ? "default" : "outline"} 
          className={cn("rounded-full px-4 h-8 text-xs font-medium", filter === "all" && "bg-emerald-500 hover:bg-emerald-600")}
          onClick={() => setFilter("all")}
        >
          Todos os Chats
        </Button>
        <Button 
          variant={filter === "unknown" ? "default" : "outline"} 
          className={cn("rounded-full px-4 h-8 text-xs font-medium", filter === "unknown" && "bg-emerald-500 hover:bg-emerald-600")}
          onClick={() => setFilter("unknown")}
        >
          Desconhecidos (S/ Agenda)
        </Button>
        <Button 
          variant={filter === "unread" ? "default" : "outline"} 
          className={cn("rounded-full px-4 h-8 text-xs font-medium", filter === "unread" && "bg-emerald-500 hover:bg-emerald-600")}
          onClick={() => setFilter("unread")}
        >
          Deixados no Vácuo
        </Button>
        <div className="w-px h-6 bg-border/50 mx-2"></div>
        <Button
          variant={includeContacts ? "default" : "outline"}
          className={cn("rounded-full px-4 h-8 text-xs font-medium", includeContacts && "bg-emerald-500 hover:bg-emerald-600")}
          onClick={() => setIncludeContacts(v => !v)}
          title="Inclui contatos sincronizados do WhatsApp (mesmo sem conversa) — útil para campanhas frias"
        >
          {includeContacts ? "✓ Agenda Completa" : "Só Conversas"}
        </Button>
        <Button variant="ghost" size="sm" onClick={selectAll} className="text-xs h-8">
          {selectedIds.length === filteredChats.length && filteredChats.length > 0 ? "Desmarcar Todos" : "Selecionar Todos"}
        </Button>
        <Button variant="ghost" size="sm" onClick={() => selectLastN(50)} className="text-xs h-8 text-emerald-500 hover:text-emerald-600 hover:bg-emerald-500/10">
          Selecionar Últimos 50
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={syncing}
          onClick={() => handleSyncAppState(false)}
          className="text-xs h-8 gap-1 ml-auto border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10"
          title="Força o WhatsApp a sincronizar contatos + chats do servidor (igual Evolution API faz no startup). Use se o app mostra conversas que não aparecem aqui."
        >
          {syncing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
          {syncing ? "Sincronizando..." : "Sincronizar Conversas"}
        </Button>
      </div>

      {/* Main Split View */}
      <div className="flex-1 flex gap-4 min-h-0">
        
        {/* Chat List */}
        <div className={cn("overflow-y-auto custom-scrollbar rounded-2xl border border-border/50 bg-card/30 transition-all duration-300", previewChatId ? "w-1/2 md:w-2/3" : "w-full")}>
          {loading ? (
            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
              <Loader2 className="h-8 w-8 mb-2 opacity-50 animate-spin" />
              <p className="text-sm">Carregando conversas do WhatsApp…</p>
            </div>
          ) : loadError ? (
            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground px-4 text-center">
              <AlertCircle className="h-8 w-8 mb-2 opacity-50 text-rose-400" />
              <p className="text-sm">{loadError}</p>
              <Button variant="outline" size="sm" className="mt-3 gap-2" onClick={() => setReloadTick(t => t + 1)}>
                <RefreshCcw className="h-3.5 w-3.5" /> Tentar de novo
              </Button>
            </div>
          ) : filteredChats.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
              <MessageCircle className="h-8 w-8 mb-2 opacity-20" />
              <p>Nenhuma conversa encontrada</p>
            </div>
          ) : (
            <div className="divide-y divide-border/30">
              {filteredChats.map((chat, index) => {
                const isSelected = selectedIds.includes(chat.id);
                return (
                  <div 
                    key={chat.id}
                    onClick={() => setPreviewChatId(chat.id)}
                    onContextMenu={(e) => handleContextMenu(e, chat.id)}
                    className={cn(
                      "flex items-center gap-4 p-4 hover:bg-muted/30 cursor-pointer transition-colors group",
                      isSelected && "bg-emerald-500/5 hover:bg-emerald-500/10",
                      previewChatId === chat.id && "bg-primary/5 ring-1 ring-inset ring-primary/20"
                    )}
                  >
                    {/* Checkbox */}
                    <div 
                      className="shrink-0 text-muted-foreground group-hover:text-emerald-500 transition-colors p-1"
                      onClick={(e) => toggleSelect(chat.id, index, e)}
                    >
                      {isSelected ? <CheckSquare className="h-5 w-5 text-emerald-500" /> : <Square className="h-5 w-5" />}
                    </div>

                    {/* Avatar */}
                    <div className="shrink-0 relative">
                      <AvatarInitial name={chat.name || chat.phone} className={cn("h-11 w-11", chat.isUnknown ? "bg-muted text-muted-foreground" : "bg-primary/10 text-primary")} />
                      {chat.unread && <div className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-background"></div>}
                    </div>

                    {/* Chat Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2 truncate">
                          <span className={cn("font-semibold truncate text-[0.95rem]", chat.isUnknown && "text-muted-foreground")}>
                            {chat.name || chat.phone}
                          </span>
                          {chat.source === "contact" && (
                            <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 border-blue-500/30 text-blue-400">Contato</Badge>
                          )}
                          {chat.isUnknown && chat.source !== "contact" && (
                            <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 border-amber-500/30 text-amber-500">Desconhecido</Badge>
                          )}
                        </div>
                        <span className={cn("text-xs shrink-0 ml-2", chat.unread ? "text-emerald-500 font-medium" : "text-muted-foreground")}>{chat.time || <span className="opacity-40 text-[10px]">—</span>}</span>
                      </div>
                      <p className="text-sm text-muted-foreground truncate flex items-center gap-1">
                        {chat.source === "contact" ? (
                          <span className="italic opacity-60">Sem mensagens ainda</span>
                        ) : (
                          <>
                            {!chat.unread && <CheckCheck className="h-3.5 w-3.5 text-blue-400" />}
                            {chat.lastMessage || <span className="italic opacity-60">Sem mensagens ainda</span>}
                          </>
                        )}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Preview Pane (Split View) */}
        {previewChatId && previewChat && (
          <div className="w-1/2 md:w-1/3 flex flex-col rounded-2xl border border-border/50 bg-background overflow-hidden animate-in fade-in slide-in-from-right-4">
            <div className="p-4 border-b border-border/50 bg-muted/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AvatarInitial name={previewChat.name || previewChat.phone} className="h-9 w-9" />
                <div className="flex flex-col">
                  <span className="font-semibold text-sm truncate">{previewChat.name || previewChat.phone}</span>
                  <span className="text-xs text-muted-foreground">{previewChat.phone}</span>
                </div>
              </div>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0 rounded-full" onClick={() => setPreviewChatId(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="flex-1 p-4 overflow-y-auto bg-[url('/wa-bg.png')] bg-repeat bg-opacity-5 relative custom-scrollbar flex flex-col gap-3">
              {/* Context Warning if unknown */}
              {previewChat.isUnknown && (
                <div className="bg-amber-500/10 text-amber-500 text-xs p-2 rounded-lg border border-amber-500/20 text-center mb-2 mx-4">
                  Número não está na base de contatos.
                </div>
              )}
              
              {/* Histórico REAL do chat */}
              {previewMsgsLoading ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground text-sm gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" /> Carregando conversa...
                </div>
              ) : previewMsgs.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground text-xs">Sem mensagens nesta conversa.</div>
              ) : (
                previewMsgs.map((msg, i) => (
                  <div key={i} className={cn("flex flex-col max-w-[85%]", msg.sender === "agent" ? "self-end items-end" : "self-start items-start")}>
                    <div className={cn("px-3 py-2 rounded-xl text-sm", msg.sender === "agent" ? "bg-emerald-600 text-white rounded-tr-none" : "bg-card border border-border/50 rounded-tl-none")}>
                      {msg.text}
                    </div>
                    <span className="text-[10px] text-muted-foreground mt-1 mx-1">{msg.time}</span>
                  </div>
                ))
              )}
            </div>

            <div className="p-3 border-t border-border/50 bg-muted/10 flex gap-2">
              <Button size="sm" variant="outline" className="flex-1 text-xs" onClick={() => {
                if (!selectedIds.includes(previewChat.id)) toggleSelect(previewChat.id, 0, { stopPropagation: () => {} } as any);
                toast.success("Adicionado à seleção");
              }}>
                <CheckSquare className="h-4 w-4 mr-2" /> Selecionar
              </Button>
              <Button size="sm" className="flex-1 text-xs bg-emerald-500 hover:bg-emerald-600" onClick={() => {
                setSelectedIds([previewChat.id]);
                handleCampaignTrigger("Oferta Individual");
              }}>
                <Send className="h-4 w-4 mr-2" /> Falar Agora
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Floating Action Bar */}
      {selectedIds.length > 0 && (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-zinc-950 dark:bg-zinc-100 dark:text-zinc-900 text-white rounded-2xl shadow-2xl p-4 flex flex-col md:flex-row items-center gap-4 border border-border/10 w-[95%] md:w-auto min-w-[500px] animate-in slide-in-from-bottom-5 z-20">
          <div className="flex items-center gap-3 shrink-0">
            <div className="bg-emerald-500/20 text-emerald-400 font-bold px-3 py-1.5 rounded-lg flex items-center gap-2">
              <User className="h-4 w-4" />
              {selectedIds.length} selecionados
            </div>
          </div>
          
          <div className="w-px h-8 bg-zinc-800 dark:bg-zinc-300 hidden md:block"></div>
          
          <div className="flex-1 flex items-center gap-2 justify-end w-full">
            <Button size="sm" variant="ghost" onClick={() => setSelectedIds([])} className="text-zinc-400 hover:text-white hover:bg-zinc-800">
              Cancelar
            </Button>
            <Button size="sm" variant="ghost" onClick={markAsRead} className="text-zinc-400 hover:text-white hover:bg-zinc-800 px-2" title="Marcar como Lido">
              <CheckCheck className="h-4 w-4" />
            </Button>
            <Button size="sm" disabled={dispatching} onClick={() => handleCampaignTrigger("Oferta")} className="bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl shadow-glow disabled:opacity-50">
              {dispatching ? <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" /> : <Send className="h-3.5 w-3.5 mr-2" />}
              {dispatching ? "Disparando..." : "Disparar Oferta"}
            </Button>
            <Button size="sm" variant="secondary" onClick={() => handleCampaignTrigger("Aviso")} className="bg-zinc-800 hover:bg-zinc-700 text-white border-none rounded-xl">
              <AlertCircle className="h-3.5 w-3.5 mr-2" />
              Aviso
            </Button>
          </div>
        </div>
      )}

      {/* Custom Context Menu */}
      {contextMenu && (
        <div 
          className="fixed z-50 w-56 bg-background border border-border/50 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-1">
            <button className="w-full flex items-center px-3 py-2 text-sm rounded-lg hover:bg-primary/10 hover:text-primary transition-colors text-left" onClick={() => ctxMoveToFunnel(contextMenu.chatId)}>
              <Inbox className="h-4 w-4 mr-2" /> Jogar no Funil
            </button>
            <button className="w-full flex items-center px-3 py-2 text-sm rounded-lg hover:bg-primary/10 hover:text-primary transition-colors text-left" onClick={() => ctxAddTag(contextMenu.chatId)}>
              <Tag className="h-4 w-4 mr-2" /> Adicionar Tag
            </button>
            <div className="h-px bg-border/50 my-1"></div>
            <button className="w-full flex items-center px-3 py-2 text-sm rounded-lg hover:bg-rose-500/10 text-rose-500 transition-colors text-left" onClick={() => ctxBlock(contextMenu.chatId)}>
              <UserMinus className="h-4 w-4 mr-2" /> Bloquear / Arquivar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
