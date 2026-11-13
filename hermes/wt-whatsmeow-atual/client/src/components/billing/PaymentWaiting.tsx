import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, ExternalLink, CheckCircle2 } from "lucide-react";
import { checkBilling } from "@/services/billing";

// Espera do pagamento: a página de pagamento abre em OUTRA aba e, enquanto esta tela
// estiver aberta, consultamos /api/billing/check a cada 10 s (e na hora em que a pessoa
// volta para esta aba). Quando o servidor disser "active", chamamos onPaid().
// O botão "Já paguei — verificar" continua disponível para conferir na hora.

const POLL_MS = 10_000;

export function useBillingPoll(enabled: boolean, onPaid: () => void) {
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [checking, setChecking] = useState(false);
  const [failed, setFailed] = useState(false);
  const onPaidRef = useRef(onPaid);
  onPaidRef.current = onPaid;
  const doneRef = useRef(false);
  const busyRef = useRef(false);

  // true = pago; false = ainda não; null = já havia uma conferência em andamento.
  const check = useCallback(async (): Promise<boolean | null> => {
    if (doneRef.current) return true;
    if (busyRef.current) return null;
    busyRef.current = true;
    setChecking(true);
    try {
      const r = await checkBilling();
      setFailed(false);
      setLastCheck(new Date());
      if (r.status === "active") {
        doneRef.current = true;
        onPaidRef.current();
        return true;
      }
      return false;
    } catch {
      setFailed(true);
      return false;
    } finally {
      busyRef.current = false;
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    const id = window.setInterval(() => {
      if (document.visibilityState === "visible") check();
    }, POLL_MS);
    const onBack = () => { if (document.visibilityState === "visible") check(); };
    document.addEventListener("visibilitychange", onBack);
    window.addEventListener("focus", onBack);
    return () => {
      window.clearInterval(id);
      document.removeEventListener("visibilitychange", onBack);
      window.removeEventListener("focus", onBack);
    };
  }, [enabled, check]);

  return { check, checking, lastCheck, failed };
}

type Props = {
  invoiceUrl: string;
  onPaid: () => void;
  // Texto/ação extra (ex.: "Entrar no painel e pagar depois").
  secondaryLabel?: string;
  onSecondary?: () => void;
  // Visual escuro (telas de login/teste vencido) ou do tema do painel.
  tone?: "dark" | "theme";
};

export function PaymentWaiting({ invoiceUrl, onPaid, secondaryLabel, onSecondary, tone = "theme" }: Props) {
  const [paid, setPaid] = useState(false);
  const [msg, setMsg] = useState("");
  const { check, checking, lastCheck, failed } = useBillingPoll(!paid, () => {
    setPaid(true);
    onPaid();
  });

  const verifyNow = async () => {
    setMsg("");
    const ok = await check();
    if (ok === false) setMsg("Pagamento ainda não confirmado. PIX costuma levar alguns minutos; boleto, até 3 dias úteis.");
  };

  const dark = tone === "dark";
  const muted = dark ? "text-slate-400" : "text-muted-foreground";
  const box = dark ? "border-white/10 bg-slate-900/60" : "border-border/50 bg-background/50";

  if (paid) {
    return (
      <div className={`rounded-xl border p-5 text-center space-y-2 ${box}`}>
        <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
        <p className={`font-semibold ${dark ? "text-white" : ""}`}>Pagamento confirmado!</p>
        <p className={`text-sm ${muted}`}>Entrando no painel…</p>
      </div>
    );
  }

  return (
    <div className={`rounded-xl border p-5 space-y-4 text-left ${box}`}>
      <div className="flex items-start gap-3">
        <Loader2 className="h-5 w-5 text-emerald-500 animate-spin shrink-0 mt-0.5" />
        <div>
          <p className={`font-semibold text-sm ${dark ? "text-white" : ""}`}>Aguardando a confirmação do pagamento</p>
          <p className={`text-xs mt-1 ${muted}`}>
            A página de pagamento abriu em outra aba. Pode pagar lá e voltar: esta tela confere sozinha a cada 10 segundos.
          </p>
        </div>
      </div>
      <a
        href={invoiceUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 w-full py-2.5 text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white transition-colors"
      >
        <ExternalLink className="h-4 w-4" /> Abrir a página de pagamento
      </a>
      <button
        type="button"
        onClick={verifyNow}
        disabled={checking}
        className={`block w-full py-2.5 text-sm font-medium border rounded-lg transition-colors disabled:opacity-60 ${dark ? "border-emerald-500/30 hover:border-emerald-500/60 text-emerald-400" : "border-emerald-500/40 hover:border-emerald-500/70 text-emerald-600 dark:text-emerald-400"}`}
      >
        {checking ? "Verificando…" : "Já paguei — verificar"}
      </button>
      {onSecondary && secondaryLabel && (
        <button type="button" onClick={onSecondary} className={`block w-full py-2 text-xs underline-offset-2 hover:underline ${muted}`}>
          {secondaryLabel}
        </button>
      )}
      {msg && <p className="text-xs text-amber-500">{msg}</p>}
      <p className={`text-[11px] ${muted}`}>
        {failed
          ? "Não consegui consultar agora; vou tentar de novo em instantes."
          : lastCheck
            ? `Última conferência: ${lastCheck.toLocaleTimeString("pt-BR")}`
            : "Primeira conferência em alguns segundos."}
      </p>
    </div>
  );
}
