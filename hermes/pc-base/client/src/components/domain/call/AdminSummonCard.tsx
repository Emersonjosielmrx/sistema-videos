import { useEffect, useRef, useState } from "react";
import { Phone, Headset, X, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { eventStream } from "@/lib/event-stream";
import { openCall, type OpenCall } from "@/lib/webrtc";
import { toast } from "sonner";
import { silentAll } from "@/lib/log";
import { apiDelete } from "@/lib/api";

// AdminSummonCard — card flutuante que aparece quando a IA (numa ligação) chama o admin
// pra entrar na conversa (evento SSE "call-admin-summon"). Mostra o resumo do que o
// cliente quer e deixa o admin ATENDER PELO NAVEGADOR (microfone) ou ver que já está
// tocando no telefone. Ver call_triggers.go / call_bridge.go no backend.

type Summon = {
  callId: string;
  sid: string;
  phone: string;
  reason: string;
  summary: string;
  channel: string;
  mode: string;
  on?: string; // gatilho: "human_request" | "hot_lead" | "price" | "stage:…"
};

export function AdminSummonCard() {
  const [summon, setSummon] = useState<Summon | null>(null);
  const [joining, setJoining] = useState(false);
  const [inCall, setInCall] = useState(false);
  const callRef = useRef<OpenCall | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const ringRef = useRef<{ ctx: AudioContext; timer: number } | null>(null);

  // startRing: toca um toque de chamada (dois bipes tipo WhatsApp) em loop, via Web Audio.
  const startRing = () => {
    stopRing();
    try {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      // O navegador suspende o áudio até um gesto do usuário. resume() destrava se a
      // página já recebeu algum clique (o unlock global abaixo garante isso).
      if (ctx.state === "suspended") ctx.resume().catch(silentAll());
      const beep = () => {
        const now = ctx.currentTime;
        [0, 0.35].forEach((off) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.frequency.value = 480 + off * 0; // tom estável
          osc.type = "sine";
          gain.gain.setValueAtTime(0.0001, now + off);
          gain.gain.exponentialRampToValueAtTime(0.25, now + off + 0.02);
          gain.gain.exponentialRampToValueAtTime(0.0001, now + off + 0.28);
          osc.connect(gain).connect(ctx.destination);
          osc.start(now + off);
          osc.stop(now + off + 0.3);
        });
      };
      beep();
      const timer = window.setInterval(beep, 2000);
      ringRef.current = { ctx, timer };
    } catch { /* navegador bloqueou áudio até interação — silencioso */ }
  };
  const stopRing = () => {
    if (ringRef.current) {
      clearInterval(ringRef.current.timer);
      try { ringRef.current.ctx.close(); } catch { /* noop */ }
      ringRef.current = null;
    }
  };

  // Destrava o áudio do navegador: no primeiro clique/tecla da página, cria e resume um
  // AudioContext "quente" pra o toque conseguir tocar depois (política de autoplay).
  const unlockedRef = useRef(false);
  useEffect(() => {
    const unlock = () => {
      if (unlockedRef.current) return;
      try {
        const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
        ctx.resume().finally(() => { try { ctx.close(); } catch { /* noop */ } });
        unlockedRef.current = true;
      } catch { /* noop */ }
    };
    window.addEventListener("click", unlock);
    window.addEventListener("keydown", unlock);
    return () => {
      window.removeEventListener("click", unlock);
      window.removeEventListener("keydown", unlock);
    };
  }, []);

  useEffect(() => {
    return eventStream.on((ev) => {
      if (ev.type === "call-admin-summon") {
        const s = ev as Summon;
        setSummon(s);
        if (s.on === "hot_lead") {
          // Lead quente é só um AVISO: toca uma vez, sem toque em loop.
          startRing();
          window.setTimeout(stopRing, 1500);
        } else {
          startRing(); // pedido de humano: toque sonoro tipo ligação, em loop
        }
        try { navigator.vibrate?.([400, 200, 400]); } catch { /* noop */ }
      }
    });
  }, []);

  // para o toque quando o card some ou o admin entra na chamada
  useEffect(() => {
    if (!summon || inCall) stopRing();
    return () => stopRing();
  }, [summon, inCall]);

  const answerInBrowser = async () => {
    if (!summon) return;
    stopRing();
    setJoining(true);
    try {
      const call = await openCall(summon.sid, summon.callId, null);
      callRef.current = call;
      // liga o áudio do cliente no <audio>
      const wire = () => {
        if (audioRef.current && call.remoteStream) {
          audioRef.current.srcObject = call.remoteStream;
          audioRef.current.play().catch(silentAll());
        }
      };
      wire();
      setTimeout(wire, 500);
      setInCall(true);
      toast.success("Você entrou na chamada. Pode falar!");
    } catch (e: any) {
      toast.error("Não consegui entrar na chamada: " + (e?.message || "erro"));
    } finally {
      setJoining(false);
    }
  };

  const hangup = () => {
    // Avisa o servidor ANTES de fechar: a IA volta a falar na hora e a ligação do cliente
    // continua (sem isso a IA só voltava quando a conexão do navegador caía, ~30 s de silêncio).
    if (summon) {
      apiDelete(`/api/sessions/${summon.sid}/calls/${summon.callId}/webrtc`).catch(silentAll());
    }
    try { callRef.current?.close(); } catch { /* noop */ }
    callRef.current = null;
    setInCall(false);
    setSummon(null);
  };

  const dismiss = () => {
    if (inCall) hangup();
    setSummon(null);
  };

  if (!summon) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] w-[360px] max-w-[92vw] animate-in slide-in-from-bottom-4">
      <div className="bg-background border-2 border-primary/60 rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-primary/10 px-4 py-3 flex items-center justify-between border-b border-border/50">
          <div className="flex items-center gap-2">
            <Headset className="h-5 w-5 text-primary animate-pulse" />
            <span className="font-bold text-sm">{summon.on === "hot_lead" ? "Lead quente na ligação" : "Cliente quer falar com você"}</span>
          </div>
          <button onClick={dismiss} className="text-muted-foreground hover:text-foreground"><X className="h-4 w-4" /></button>
        </div>
        <div className="p-4 space-y-3">
          <div className="flex items-center gap-2 text-sm">
            <User className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">+{summon.phone}</span>
            <span className="text-xs text-muted-foreground">• {summon.reason}</span>
          </div>
          {summon.summary && (
            <div className="text-xs bg-muted/50 rounded-lg p-3 max-h-40 overflow-y-auto whitespace-pre-wrap">
              {summon.summary}
            </div>
          )}
          {!inCall ? (
            <div className="flex gap-2">
              <Button onClick={answerInBrowser} disabled={joining} className="flex-1 gap-2 bg-emerald-600 hover:bg-emerald-700">
                <Headset className="h-4 w-4" /> {joining ? "Entrando..." : summon.on === "hot_lead" ? "Entrar na ligação" : "Atender no navegador"}
              </Button>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-emerald-500 font-semibold flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" /> Você está na chamada
              </span>
              <Button onClick={hangup} variant="destructive" size="sm" className="gap-2">
                <Phone className="h-4 w-4" /> Sair
              </Button>
            </div>
          )}
          {summon.channel !== "panel" && !inCall && (
            <p className="text-[11px] text-muted-foreground flex items-center gap-1">
              <Phone className="h-3 w-3" /> Também estamos ligando pro seu telefone.
            </p>
          )}
        </div>
      </div>
      <audio ref={audioRef} autoPlay className="hidden" />
    </div>
  );
}
