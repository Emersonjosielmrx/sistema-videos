import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Loader2, Trash2, MessageCircle, Mic, Square } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetTrigger } from "@/components/ui/sheet";
import { apiGet, apiPost } from "@/lib/api";
import { apiUrl, authHeaders } from "@/lib/auth";
import { getClientId } from "@/lib/client-id";
import { cn } from "@/lib/utils";
import { setChatOpen, useNavigation } from "@/stores/navigation";

// --- Types (mirroring backend console_chat.go) ---

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string;
}

interface MessagesResponse {
  messages: ChatMessage[];
}

interface SendResponse {
  reply: string;
  at: string;
}

interface ChatThread {
  id: string;
  name: string;
  product: string;
  is_agent: boolean;
}

// --- Chat message bubble ---

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={cn("flex gap-2", isUser ? "flex-row-reverse" : "flex-row")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div
        className={cn(
          // min-w-0 deixa o flex encolher a bolha; break-words + whitespace-pre-wrap
          // impedem que texto longo/URL sem espaço estoure a largura no celular.
          "min-w-0 max-w-[80%] overflow-hidden whitespace-pre-wrap break-words rounded-2xl px-4 py-2 text-sm sm:max-w-[75%]",
          isUser
            ? "bg-primary text-primary-foreground rounded-tr-md"
            : "bg-muted text-foreground rounded-tl-md",
        )}
      >
        {msg.content}
      </div>
    </div>
  );
}

// --- Main chat panel component ---

export function ManagerChat({ trigger }: { trigger?: React.ReactNode }) {
  const globalChatOpen = useNavigation((s) => s.chatOpen);
  const initialMessage = useNavigation((s) => s.chatInitialMessage);
  const [open, setOpenState] = useState(false);

  const setOpen = (v: boolean) => {
    setOpenState(v);
    setChatOpen(v, v ? initialMessage : ""); // limpa message ao fechar
  };

  useEffect(() => {
    if (globalChatOpen !== open) setOpenState(globalChatOpen);
  }, [globalChatOpen]);

  useEffect(() => {
    if (globalChatOpen && initialMessage) setInput(initialMessage);
  }, [globalChatOpen, initialMessage]);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [currentThread, setCurrentThread] = useState("geral");
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // --- Áudio (gravação pelo navegador via MediaRecorder) ---
  const [recording, setRecording] = useState(false);
  const [sendingAudio, setSendingAudio] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // Load threads + history when panel opens
  useEffect(() => {
    if (!open) return;
    loadThreads();
    loadHistory(currentThread);
  }, [open]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadThreads = async () => {
    try {
      const data = await apiGet<{ threads: ChatThread[] }>("/api/chat/threads");
      setThreads(data.threads);
    } catch {
      // fallback: single thread
      setThreads([{ id: "geral", name: "Assistente", product: "", is_agent: true }]);
    }
  };

  const loadHistory = async (thread: string) => {
    setHistoryLoading(true);
    try {
      const data = await apiGet<MessagesResponse>(`/api/chat/messages?thread=${encodeURIComponent(thread)}`);
      setMessages(data.messages ?? []);
    } catch {
      setMessages([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleThreadChange = (threadId: string) => {
    setCurrentThread(threadId);
    loadHistory(threadId);
  };

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    // Optimistic user message
    const userMsg: ChatMessage = {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);

    setLoading(true);
    try {
      const data = await apiPost<SendResponse>("/api/chat/send", {
        thread: currentThread,
        text,
      });
      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        role: "assistant",
        content: data.reply,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      const errMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: "Erro ao enviar mensagem. Tente novamente.",
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }, [input, loading, currentThread]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = async () => {
    try {
      await apiPost("/api/chat/clear", { thread: currentThread });
      setMessages([]);
    } catch {
      // ignore
    }
  };

  // Envia o áudio gravado pro backend (transcreve + IA responde). Pede voz de volta
  // (voice=1) e toca a resposta em áudio se o backend devolver.
  const uploadAudio = useCallback(async (blob: Blob) => {
    setSendingAudio(true);
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("audio", blob, "audio.webm");
      const url = apiUrl(`/api/chat/audio?thread=${encodeURIComponent(currentThread)}&voice=1`);
      const res = await fetch(url, {
        method: "POST",
        headers: { "X-Client-Id": getClientId(), ...authHeaders() }, // sem Content-Type: o browser define o boundary
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        toast.error(data.error || "Não consegui processar o áudio");
        return;
      }
      // Mostra a transcrição como mensagem do usuário e a resposta da IA.
      if (data.transcript) {
        setMessages((prev) => [...prev, { id: `u-${Date.now()}`, role: "user", content: data.transcript }]);
      }
      if (data.reply) {
        setMessages((prev) => [...prev, { id: `b-${Date.now()}`, role: "assistant", content: data.reply }]);
      }
      // Toca a resposta em voz, se veio.
      if (data.audio_ogg_b64) {
        try {
          const audio = new Audio(`data:audio/ogg;base64,${data.audio_ogg_b64}`);
          void audio.play();
        } catch { /* autoplay pode ser bloqueado — ignora */ }
      }
    } catch (e) {
      toast.error("Erro ao enviar áudio", { description: (e as Error).message });
    } finally {
      setSendingAudio(false);
      setLoading(false);
    }
  }, [currentThread]);

  const startRecording = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      toast.error("Seu navegador não suporta gravação de áudio");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      audioChunksRef.current = [];
      const mr = new MediaRecorder(stream);
      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: mr.mimeType || "audio/webm" });
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        if (blob.size > 0) void uploadAudio(blob);
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setRecording(true);
    } catch {
      toast.error("Não consegui acessar o microfone. Verifique a permissão.");
    }
  }, [uploadAudio]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    setRecording(false);
  }, []);

  // Segurança: se o componente desmontar no meio da gravação, solta o microfone.
  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        {trigger ? (
          trigger
        ) : (
          <Button variant="ghost" size="icon" aria-label="Chat com assistente" title="Chat com assistente">
            <MessageCircle className="h-5 w-5" />
          </Button>
        )}
      </SheetTrigger>
      <SheetContent side="right" className="flex w-full flex-col p-0 sm:max-w-md">
        <SheetHeader className="border-b px-4 py-3">
          <SheetTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            Assistente Hermes
          </SheetTitle>
          <SheetDescription className="sr-only">
            Converse com o agente gerenciador. A memória é compartilhada com Telegram e WhatsApp.
          </SheetDescription>
          {/* Thread selector */}
          {threads.length > 1 && (
            <div className="flex gap-1 overflow-x-auto pb-1">
              {threads.map((t) => (
                <button
                  key={t.id}
                  onClick={() => handleThreadChange(t.id)}
                  className={cn(
                    "shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors",
                    currentThread === t.id
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/80",
                  )}
                >
                  {t.name}
                </button>
              ))}
            </div>
          )}
        </SheetHeader>

        {/* Messages */}
        <ScrollArea className="flex-1" ref={scrollRef}>
          <div className="flex flex-col gap-4 p-4">
            {historyLoading ? (
              <div className="flex items-center justify-center py-8 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="ml-2 text-sm">Carregando histórico...</span>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                <Bot className="mb-3 h-10 w-10 opacity-30" />
                <p className="text-sm font-medium">Assistente Hermes</p>
                <p className="mt-1 text-xs">
                  Envie uma mensagem para conversar.<br />
                  Memória compartilhada com Telegram e WhatsApp.
                </p>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} msg={msg} />
                ))}
                {loading && (
                  <div className="flex gap-2">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="flex items-center gap-1 rounded-2xl rounded-tl-md bg-muted px-4 py-2 text-sm text-muted-foreground">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>pensando...</span>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>

        {/* Input — no celular ocupa a largura toda; botões grandes p/ toque */}
        <div className="border-t p-2 sm:p-3">
          {recording && (
            <div className="mb-2 flex items-center gap-2 rounded-md bg-destructive/10 px-3 py-1.5 text-xs text-destructive">
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-destructive" />
              Gravando… toque no quadrado para enviar.
            </div>
          )}
          <div className="flex items-end gap-1.5 sm:gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 text-muted-foreground hover:text-destructive"
              onClick={handleClear}
              title="Limpar conversa"
              disabled={messages.length === 0 || recording}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 text-muted-foreground hover:text-primary"
              onClick={() => {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'image/*,application/pdf';
                input.onchange = (e) => {
                   const file = (e.target as HTMLInputElement).files?.[0];
                   if (file) toast.info(`Arquivo ${file.name} anexado (Simulação). Upload real requer backend.`);
                };
                input.click();
              }}
              title="Anexar arquivo"
              disabled={loading || recording}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-paperclip"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
            </Button>
            <Textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={recording ? "Gravando áudio…" : "Mensagem..."}
              className="min-h-[44px] max-h-[120px] flex-1 resize-none text-base sm:text-sm"
              rows={1}
              disabled={loading || recording}
            />
            {/* Botão de microfone: grava/para. Enquanto grava, vira quadrado vermelho. */}
            <Button
              size="icon"
              variant={recording ? "destructive" : "outline"}
              onClick={recording ? stopRecording : startRecording}
              disabled={sendingAudio || (loading && !recording)}
              className="shrink-0"
              aria-label={recording ? "Parar e enviar áudio" : "Gravar áudio"}
              title={recording ? "Parar e enviar" : "Gravar áudio"}
            >
              {sendingAudio ? <Loader2 className="h-4 w-4 animate-spin" /> : recording ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>
            <Button
              size="icon"
              onClick={handleSend}
              disabled={!input.trim() || loading || recording}
              className="shrink-0"
              aria-label="Enviar"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mt-1.5 text-xs text-muted-foreground">
            Memória compartilhada com Telegram e WhatsApp
          </p>
        </div>
      </SheetContent>
    </Sheet>
  );
}
