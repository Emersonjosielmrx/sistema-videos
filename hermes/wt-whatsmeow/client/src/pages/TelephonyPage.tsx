import { Tabs, TabsContent, TabsList } from "@/components/ui/tabs";
import { Phone, FileText, Mic, Server, PhoneOff, LogOut, QrCode, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { CallsPage } from "@/pages/CallsPage";
import { TranscriptsPage } from "@/pages/TranscriptsPage";
import { RecordingsPage } from "@/pages/RecordingsPage";
import { EmptyState } from "@/components/shared/EmptyState";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { HideableTab } from "@/components/ui/HideableTab";
import { Switch } from "@/components/ui/switch";
import { AudioLines, Ear, BrainCircuit, ShieldAlert, Ghost } from "lucide-react";
import { useCalls } from "@/stores/calls";
import { useSessions } from "@/stores/sessions";
import { endCall } from "@/services/calls";
import { logError } from "@/lib/log";
import { createSession, logoutSession, pairSession } from "@/services/sessions";
import { setView } from "@/stores/navigation";
import { useState, useEffect } from "react";

// fmtPhone: transforma o JID (55DDDNUM@s.whatsapp.net) num telefone legível.
function fmtPhone(jid: string): string {
  const d = (jid || "").split("@")[0].split(":")[0].replace(/\D/g, "");
  if (!d) return "—";
  if (d.startsWith("55") && d.length >= 12) {
    const ddd = d.slice(2, 4);
    const rest = d.slice(4);
    return `+55 ${ddd} ${rest.length > 8 ? rest.slice(0, 5) + "-" + rest.slice(5) : rest.slice(0, 4) + "-" + rest.slice(4)}`;
  }
  return "+" + d;
}

function fmtDur(startedAt: number): string {
  if (!startedAt) return "00:00";
  const s = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
  const m = Math.floor(s / 60);
  return `${String(m).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

export const TelephonyPage = ({ sid }: { sid: string }) => {
  const calls = useCalls((s) => s.calls);
  const sessions = useSessions((s) => s.sessions);
  const activeCalls = calls.filter((c) => c.status !== "ended");
  const [, forceTick] = useState(0);
  // Atualiza a duração exibida a cada segundo enquanto houver chamada ativa.
  useEffect(() => {
    if (activeCalls.length === 0) return;
    const t = setInterval(() => forceTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, [activeCalls.length]);

  // Reconecta (gera QR) ou desloga uma linha WhatsApp.
  const [busyLine, setBusyLine] = useState<string | null>(null);
  const toggleLine = async (id: string, isOnline: boolean) => {
    setBusyLine(id);
    try {
      if (isOnline) {
        await logoutSession(id);
        toast.success("Linha desconectada. Clique em Reconectar pra ler o QR e reparear.");
      } else {
        await pairSession(id);
        toast.success("Gerando QR... abra a Central de Ligações pra escanear.");
        setView("calls");
      }
    } catch (e) {
      toast.error(`Falha: ${(e as Error)?.message ?? "erro"}`);
    } finally {
      setBusyLine(null);
    }
  };

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-10">
      {/* Cabeçalho Voice Ops */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-500/10 via-background to-background border border-indigo-500/20 p-5 shadow-glow flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
          <AudioLines className="w-24 h-24 text-indigo-500" />
        </div>
        <div className="relative z-10 flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 shadow-glow hidden sm:block">
            <AudioLines className="h-6 w-6 text-indigo-500" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-indigo-500 to-indigo-400 drop-shadow-sm">
                Voice Ops (Central IA)
              </h2>
              {/* Removido: "Latência: 120ms" era hardcoded (não há medição real de latência). */}
              <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0 gap-1">
                <ShieldAlert className="w-3 h-3" /> Monitoramento Ativo
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Controle de Tráfego Aéreo para as chamadas telefônicas. Ouça, intervenha e analise o sentimento em tempo real.
            </p>
          </div>
        </div>
      </div>

      <Tabs defaultValue="active" className="w-full overflow-hidden">
        <div className="w-full overflow-x-auto pb-2 custom-scrollbar">
          <TabsList className="bg-muted/50 p-1 rounded-xl inline-flex w-max flex-nowrap justify-start gap-1 mb-4">
          <HideableTab value="active" className="rounded-lg font-semibold data-[state=active]:bg-indigo-500 data-[state=active]:text-white data-[state=active]:shadow-sm px-4 py-2 gap-2 transition-all shrink-0">
            <Ear className="h-4 w-4" /> Radar Ao Vivo
          </HideableTab>
          <HideableTab value="calls" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 gap-2 transition-all shrink-0">
            <Phone className="h-4 w-4" /> Histórico & Sentimento
          </HideableTab>

          <HideableTab value="transcripts" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 gap-2 shrink-0">
            <FileText className="h-4 w-4" /> Transcrições
          </HideableTab>
          <HideableTab value="recordings" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 gap-2 shrink-0">
            <Mic className="h-4 w-4" /> Gravações
          </HideableTab>
          <HideableTab value="instances" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 gap-2 shrink-0">
            <Server className="h-4 w-4" /> Instâncias
          </HideableTab>
        </TabsList>
        </div>

        <TabsContent value="calls" className="mt-0">
          <CallsPage sid={sid} />
        </TabsContent>
        <TabsContent value="active" className="mt-0">
          {activeCalls.length === 0 ? (
            <EmptyState
              icon={<PhoneOff className="h-6 w-6" />}
              title="Nenhuma ligação em andamento"
              description="Quando houver uma chamada ativa (recebida ou disparada pela IA), ela aparece aqui em tempo real com número, duração e status."
            />
          ) : (
            <div className="space-y-4">
              {activeCalls.map((call) => (
                <div key={call.callId} className="bg-glass border border-indigo-500/30 rounded-xl shadow-soft overflow-hidden">
                  <div className="flex items-center justify-between p-4 bg-background/50">
                    <div className="flex items-center gap-3">
                      <span className="relative flex h-4 w-4">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-4 w-4 bg-indigo-500"></span>
                      </span>
                      <div>
                        <h4 className="font-bold text-foreground flex items-center gap-2">
                          {call.direction === "inbound" ? "Recebendo" : "Ligando"} · {call.peer || "—"}
                          {call.direction === "inbound" && <Badge variant="secondary" className="text-[0.65rem]">Em andamento</Badge>}
                        </h4>
                        <p className="text-xs text-muted-foreground">
                          {fmtDur(call.startedAt)} · {call.status}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled
                        className="text-xs gap-2 border-indigo-500/20 text-indigo-500 hover:bg-indigo-500/10 opacity-50 cursor-not-allowed"
                        title="Handoff para atendente humano ainda não disponível"
                      >
                        <Ear className="w-3.5 h-3.5" /> Assumir (Handoff)
                        <Badge variant="muted" className="ml-1 h-4 text-[0.55rem] px-1">Em breve</Badge>
                      </Button>
                      <Button
                        size="sm"
                        className="bg-rose-500 hover:bg-rose-600 text-white text-xs gap-2"
                        onClick={() => endCall(call.sessionId, call.callId).catch(logError("endCall"))}
                      >
                        <PhoneOff className="w-3.5 h-3.5" /> Encerrar
                      </Button>
                    </div>
                  </div>

                  {/* Copilot Ghost Mode Panel */}
                  <div className="border-t border-indigo-500/20 bg-indigo-500/5 p-4">
                    <div className="flex items-start gap-4">
                       <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center shrink-0 border border-indigo-500/30">
                         <Ghost className="w-4 h-4 text-indigo-500 animate-pulse" />
                       </div>
                       <div className="flex-1 space-y-3">
                          <div className="flex items-center justify-between">
                            <h5 className="text-xs font-bold text-indigo-500 uppercase tracking-wider flex items-center gap-1.5">
                              Copiloto (Modo Fantasma)
                              <Badge variant="muted" className="h-4 text-[0.55rem] px-1 normal-case tracking-normal">Em breve</Badge>
                            </h5>
                            {/* Switch desabilitado: o copiloto em tempo real ainda não está ligado ao backend. */}
                            <Switch disabled checked={false} id={`copilot-${call.callId}`} className="opacity-50 cursor-not-allowed" />
                          </div>
                          
                          {/* Antes: transcrição e sugestão FIXAS (exemplo) exibidas como se fossem desta ligação. */}
                          <p className="text-xs text-muted-foreground">A transcrição e as sugestões da IA em tempo real aparecerão aqui quando o copiloto for lançado.</p>
                       </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>
        <TabsContent value="transcripts" className="mt-0">
          <TranscriptsPage />
        </TabsContent>
        <TabsContent value="recordings" className="mt-0">
          <RecordingsPage />
        </TabsContent>
        <TabsContent value="instances" className="mt-0 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
             {sessions.length === 0 && (
                <Card className="p-5 bg-glass border-border/50 shadow-soft md:col-span-2 flex items-center gap-3">
                   <PhoneOff className="w-5 h-5 text-muted-foreground" />
                   <div>
                      <h3 className="font-bold text-sm text-foreground">Nenhuma linha conectada</h3>
                      <p className="text-xs text-muted-foreground mt-1">Conecte um número WhatsApp pra começar a ligar.</p>
                   </div>
                </Card>
             )}
             {sessions.map((s) => {
                const online = s.paired && s.connected;
                return (
                   <Card key={s.id} className={`p-5 bg-glass shadow-soft ${online ? "border-emerald-500/30" : "border-border/50 opacity-75"}`}>
                      <div className="flex justify-between items-start mb-4">
                         <div className={`p-2 rounded-lg ${online ? "bg-emerald-500/10" : "bg-muted"}`}>
                            <Phone className={`w-5 h-5 ${online ? "text-emerald-500" : "text-muted-foreground"}`} />
                         </div>
                         <div className="flex gap-2">
                            {online ? (
                               <>
                                  <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Conectada</Badge>
                                  <Badge className="bg-indigo-500/10 text-indigo-500 border-indigo-500/20">Outbound</Badge>
                               </>
                            ) : (
                               <Badge variant="outline" className="text-muted-foreground">{s.paired ? "Reconectando" : "Desconectada"}</Badge>
                            )}
                         </div>
                      </div>
                      <h3 className="font-bold text-lg text-foreground">{s.jid ? fmtPhone(s.jid) : (s.name || "Linha WhatsApp")}</h3>
                      <p className="text-xs text-muted-foreground mt-1">{s.name || "WhatsApp"}{s.recording ? " • gravando" : ""}</p>
                      <div className="mt-4 flex gap-2">
                         <Button
                            size="sm"
                            variant={online ? "outline" : "default"}
                            disabled={busyLine === s.id}
                            onClick={() => toggleLine(s.id, online)}
                            className="gap-2 text-xs"
                            title={online ? "Deslogar esta linha (desconecta o WhatsApp; use pra reparear)" : "Reconectar / ler QR"}
                         >
                            {busyLine === s.id ? (
                               <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : online ? (
                               <LogOut className="h-3.5 w-3.5" />
                            ) : (
                               <QrCode className="h-3.5 w-3.5" />
                            )}
                            {online ? "Deslogar" : "Reconectar"}
                         </Button>
                      </div>
                   </Card>
                );
             })}
             <Card
                onClick={() => { createSession("WhatsApp").then(() => setView("calls")).catch(logError("createSession")); }}
                className="p-5 border border-dashed border-border/50 bg-transparent flex flex-col items-center justify-center text-center cursor-pointer hover:bg-muted/10 transition-colors"
             >
                <div className="p-3 rounded-full bg-primary/10 text-primary mb-3"><Phone className="w-6 h-6" /></div>
                <h3 className="font-bold text-sm">Conectar nova linha WhatsApp</h3>
                <p className="text-xs text-muted-foreground mt-1">Gera um QR / código pra parear outro número.</p>
             </Card>
          </div>
          
          <Card className="p-6 bg-glass border-border/50 shadow-soft">
             <div className="flex items-start justify-between gap-4 flex-col sm:flex-row">
                <div>
                   <h3 className="font-bold text-lg mb-1 flex items-center gap-2"><BrainCircuit className="w-5 h-5 text-indigo-500" /> Configuração de Voz</h3>
                   <p className="text-sm text-muted-foreground max-w-xl">
                      A voz (motor TTS, voz do agente, transcrição), a detecção de interrupção (barge-in)
                      e a gravação de chamadas são definidas nas Configurações. É lá que as mudanças valem
                      de verdade nas ligações.
                   </p>
                </div>
                <Button className="gap-2 shrink-0" onClick={() => setView("settings")}>
                   <BrainCircuit className="w-4 h-4" /> Abrir Configurações de Voz
                </Button>
             </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
