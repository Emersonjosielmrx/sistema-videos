import { useEffect, useState } from "react";
import { PhoneCall, Mic } from "lucide-react";
import { Dialer } from "@/components/domain/call/Dialer";
import { CallCard } from "@/components/domain/call/CallCard";
import { OtherCallsList } from "@/components/domain/call/OtherCallsList";
import { HistoryDrawer } from "@/components/domain/history/HistoryDrawer";
import { EmptyState } from "@/components/shared/EmptyState";
import { isMine, useCalls } from "@/stores/calls";
import { Card } from "@/components/ui/card";
import { Bot, Sparkles } from "lucide-react";

export const CallsPage = ({ sid }: { sid: string }) => {
  const calls = useCalls((s) => s.calls);
  const [, force] = useState(0);

  useEffect(() => {
    const t = setInterval(() => force((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const sessionCalls = calls.filter((c) => c.sessionId === sid && c.status !== "ended");
  const mine = sessionCalls.filter(isMine);
  const others = sessionCalls.filter((c) => !isMine(c));

  if (!sid) {
    return (
      <EmptyState
        icon={<PhoneCall className="h-6 w-6" />}
        title="Selecione uma Linha"
        description="Clique em uma linha no menu lateral esquerdo para realizar ou visualizar ligações ativas."
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Cabeçalho Compacto Telefonia */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-500/10 via-background to-background border border-indigo-500/20 p-4 shadow-glow flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
          <PhoneCall className="w-16 h-16 text-indigo-500" />
        </div>
        <div className="relative z-10 flex items-center gap-3">
          <div className="hidden sm:flex items-center justify-center p-2 bg-indigo-500/10 rounded-xl border border-indigo-500/20 shadow-glow shrink-0">
            <PhoneCall className="w-6 h-6 text-indigo-500" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-indigo-500 to-indigo-400 drop-shadow-sm">
                Central de Caixa de Entrada
              </h2>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Gerencie suas chamadas ativas e disque para novos números.
            </p>
          </div>
        </div>
        <div className="relative z-10 flex items-center gap-3 shrink-0">
          <HistoryDrawer sid={sid} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Dialer sid={sid} />
          <h2 className="text-sm font-medium text-muted-foreground mt-2">
            {mine.length} {mine.length === 1 ? "chamada ativa" : "chamadas ativas"}
          </h2>
          {mine.length > 0 ? (
            <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
              {mine.map((c) => (
                <CallCard key={c.callId} call={c} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<PhoneCall className="h-6 w-6" />}
              title="Nenhuma chamada ativa"
              description="Disque um número acima para iniciar uma chamada."
            />
          )}
          <OtherCallsList calls={others} />
        </div>

        {/* Copiloto de Ligação (Sussurro) */}
        <div className="lg:col-span-1 space-y-4">
          <Card className="p-4 bg-gradient-to-br from-violet-500/10 to-indigo-500/10 border-violet-500/20 shadow-glow sticky top-4">
            <div className="flex items-center gap-2 mb-4">
              <div className="bg-violet-500/20 p-2 rounded-lg border border-violet-500/30">
                <Bot className="h-5 w-5 text-violet-400" />
              </div>
              <div>
                <h3 className="font-bold text-violet-100 flex items-center gap-1">Copiloto AI (Sussurro) <Sparkles className="h-3 w-3 text-violet-400" /></h3>
                <p className="text-[10px] text-muted-foreground">Em breve</p>
              </div>
            </div>
            
            {/* Copiloto em tempo real ainda não existe no backend. Antes esta área mostrava
                sugestões FIXAS ("João", "a esposa decide") como se fossem da ligação. */}
            <div className="h-40 flex flex-col items-center justify-center text-center opacity-60">
              <Mic className="h-8 w-8 mb-2 text-violet-400" />
              <p className="text-xs">Em breve: sugestões da IA durante a ligação.</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
