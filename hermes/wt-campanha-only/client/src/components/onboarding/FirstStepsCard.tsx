import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Circle, Loader2, X, QrCode, Bot, PhoneCall, CreditCard, Rocket } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { apiGet } from "@/lib/api";
import { getUser } from "@/lib/auth";
import { normalizePhone } from "@/lib/phone";
import { useSessions, setActiveSession } from "@/stores/sessions";
import { setView, openSettingsTab } from "@/stores/navigation";
import { useMassCallStore } from "@/stores/masscall";
import { createSession } from "@/services/sessions";
import { currentUserId } from "./onboarding-state";

// "Primeiros passos" — o caminho principal para começar, com o estado REAL de cada etapa:
//   1. Conectar a linha do WhatsApp (QR)     → alguma linha pareada (lista de sessões)
//   2. Criar ou escolher um agente            → GET /api/agent-profiles tem algum agente
//   3. Ligação de teste para o próprio número → GET /api/transcripts com o número do cadastro
//                                               (sem número no cadastro: qualquer ligação)
//   4. Assinar um plano                       → GET /api/billing status "active" (ou plano pago)
// Some sozinho quando tudo estiver feito e pode ser dispensado. É o caminho ÚNICO do 1º acesso:
// o tour de boas-vindas não abre mais sozinho por cima (05/10); abre pelo link "Ver o tour do
// painel" daqui. Os assistentes de Configurações continuam existindo para quem quiser detalhe.

const dismissKey = () => `hermes.firststeps.dismissed.${currentUserId()}`;

type Check = boolean | null; // null = ainda verificando (erro na consulta conta como "não feito")

const ownNumber = (): string => {
  const raw = String(getUser()?.whatsapp || "");
  const d = raw.replace(/\D/g, "");
  return d.length >= 10 ? normalizePhone(d) : "";
};

// Compara pelos 8 últimos dígitos (o WhatsApp às vezes guarda o celular sem o 9 extra).
const sameNumber = (a: string, b: string) => {
  const x = a.replace(/\D/g, "");
  const y = b.replace(/\D/g, "");
  return x.length >= 8 && y.length >= 8 && x.slice(-8) === y.slice(-8);
};

export function FirstStepsCard() {
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(dismissKey()) === "1");
  const sessions = useSessions((s) => s.sessions);
  const [hasAgent, setHasAgent] = useState<Check>(null);
  const [testCalled, setTestCalled] = useState<Check>(null);
  const [subscribed, setSubscribed] = useState<Check>(null);
  const [connecting, setConnecting] = useState(false);
  const myNumber = ownNumber();

  const lineConnected = sessions.some((s) => s.paired);

  const refresh = useCallback(() => {
    apiGet<{ profiles?: unknown[] }>("/api/agent-profiles")
      .then((r) => setHasAgent((r.profiles ?? []).length > 0))
      .catch(() => setHasAgent(false));

    const q = myNumber ? `?q=${encodeURIComponent(myNumber.slice(-8))}&limit=20` : "?limit=1";
    apiGet<{ transcripts?: { number?: string }[] }>(`/api/transcripts${q}`)
      .then((r) => {
        const list = r.transcripts ?? [];
        setTestCalled(myNumber ? list.some((t) => sameNumber(String(t.number || ""), myNumber)) : list.length > 0);
      })
      .catch(() => setTestCalled(false));

    const plan = String(getUser()?.plan || "");
    apiGet<{ status?: string }>("/api/billing")
      .then((b) => setSubscribed(b.status === "active" || (!!plan && plan !== "trial")))
      .catch(() => setSubscribed(!!plan && plan !== "trial"));
  }, [myNumber]);

  useEffect(() => {
    if (dismissed) return;
    refresh();
    // Quando a pessoa volta para a aba (depois de fazer um passo em outro lugar), reconfere.
    const onFocus = () => { if (document.visibilityState === "visible") refresh(); };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onFocus);
    return () => {
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onFocus);
    };
  }, [dismissed, refresh]);

  const connectLine = async () => {
    const unpaired = sessions.find((s) => !s.paired);
    if (unpaired) {
      setActiveSession(unpaired.id);
      setView("calls");
      return;
    }
    setConnecting(true);
    try {
      const { id } = await createSession("WhatsApp");
      setActiveSession(id);
      setView("calls");
    } catch (e) {
      toast.error("Não consegui criar a linha", { description: (e as Error).message });
    } finally {
      setConnecting(false);
    }
  };

  const testCall = () => {
    if (myNumber) {
      useMassCallStore.getState().setContacts([
        { jid: `${myNumber}@s.whatsapp.net`, phone: myNumber, name: "Eu (ligação de teste)", push_name: "", business_name: "", is_group: false },
      ]);
      toast.info("Seu número já está na lista. Escolha o áudio e inicie a ligação.");
    } else {
      toast.info("Adicione o seu número na lista e inicie a ligação.");
    }
    setView("mass-call");
  };

  const steps = [
    {
      key: "line", icon: QrCode, done: lineConnected as Check,
      title: "Conectar a linha do WhatsApp",
      desc: "Leia o QR Code com o WhatsApp do número que vai fazer as ligações.",
      action: { label: connecting ? "Abrindo…" : "Conectar WhatsApp", onClick: connectLine, disabled: connecting },
    },
    {
      key: "agent", icon: Bot, done: hasAgent,
      title: "Criar ou escolher o agente",
      desc: "O agente é a IA que fala nas ligações: roteiro, voz e o que ela sabe da sua empresa.",
      action: { label: "Criar agente", onClick: () => setView("specialized") },
    },
    {
      key: "test", icon: PhoneCall, done: testCalled,
      title: "Fazer uma ligação de teste para você",
      desc: myNumber
        ? "Ligue para o seu próprio número e ouça como a IA atende."
        : "Ligue para o seu próprio número e ouça como a IA atende. (Seu WhatsApp não está no cadastro: conta qualquer ligação atendida.)",
      action: { label: "Ligar para mim", onClick: testCall, disabled: !lineConnected, hint: !lineConnected ? "Conecte a linha primeiro." : "" },
    },
    {
      key: "plan", icon: CreditCard, done: subscribed,
      title: "Assinar um plano",
      desc: "Mantém tudo funcionando depois do período de teste.",
      action: { label: "Ver planos", onClick: () => openSettingsTab("finance") },
    },
  ];

  const doneCount = steps.filter((s) => s.done === true).length;
  if (dismissed || doneCount === steps.length) return null;

  const dismiss = () => {
    localStorage.setItem(dismissKey(), "1");
    setDismissed(true);
  };

  return (
    <Card className="p-5 bg-glass border border-primary/30 shadow-soft">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <h3 className="font-bold flex items-center gap-2"><Rocket className="h-5 w-5 text-primary" /> Primeiros passos</h3>
          <p className="text-xs text-muted-foreground mt-1">
            {doneCount} de {steps.length} feitos. Siga a ordem para a IA começar a ligar.{" "}
            <button type="button" onClick={() => window.dispatchEvent(new Event("hermes:abrir-tour"))} className="underline hover:text-foreground">
              Ver o tour do painel
            </button>
          </p>
        </div>
        <button type="button" onClick={dismiss} className="text-muted-foreground hover:text-foreground p-1 rounded-md hover:bg-muted/50" title="Dispensar" aria-label="Dispensar primeiros passos">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="h-1.5 w-full rounded-full bg-muted/40 mb-4 overflow-hidden">
        <div className="h-full bg-primary transition-all" style={{ width: `${(doneCount / steps.length) * 100}%` }} />
      </div>
      <ol className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        {steps.map((s, i) => (
          <li key={s.key} className={`rounded-xl border p-4 flex flex-col gap-2 ${s.done ? "border-emerald-500/30 bg-emerald-500/5" : "border-border/50 bg-background/40"}`}>
            <div className="flex items-center gap-2">
              {s.done === true ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
              ) : s.done === null && s.key !== "line" ? (
                <Loader2 className="h-5 w-5 text-muted-foreground animate-spin shrink-0" />
              ) : (
                <Circle className="h-5 w-5 text-muted-foreground shrink-0" />
              )}
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">Passo {i + 1}</span>
              <s.icon className="h-4 w-4 text-primary ml-auto" />
            </div>
            <p className="font-semibold text-sm">{s.title}</p>
            <p className="text-xs text-muted-foreground flex-1">{s.desc}</p>
            {s.done === true ? (
              <p className="text-xs font-medium text-emerald-500">Feito</p>
            ) : (
              <>
                <Button size="sm" variant={i === doneCount ? "default" : "outline"} onClick={s.action.onClick} disabled={s.action.disabled} className="w-full">
                  {s.action.label}
                </Button>
                {"hint" in s.action && s.action.hint && <p className="text-[11px] text-muted-foreground">{s.action.hint}</p>}
              </>
            )}
          </li>
        ))}
      </ol>
    </Card>
  );
}
