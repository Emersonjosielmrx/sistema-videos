import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Crown, CheckCircle2, MessageCircle, Bot, UploadCloud, CreditCard, CreditCard as PayIcon, RefreshCw, Loader2, Ticket, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { logError } from "@/lib/log";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { PaymentWaiting } from "@/components/billing/PaymentWaiting";
import {
  PAID_PLANS as PLANS, getBilling, subscribePlan, changePlan, cancelSubscription, applyCoupon, openInvoice, billingErrorMessage, hasDocOnFile,
  type BillingInfo as Billing,
} from "@/services/billing";
import { cpfCnpjError, formatCpfCnpj, normalizeCpfCnpj } from "@/lib/cpf-cnpj";

// Confirmação antes de trocar de plano ou cancelar.
type Confirm = { kind: "change"; plan: string } | { kind: "cancel" } | null;

export function SubscriptionTab() {
  const [billing, setBilling] = useState<Billing | null>(null);
  const [costMonth, setCostMonth] = useState(0);
  const [subscribing, setSubscribing] = useState("");
  const [cpfCnpj, setCpfCnpj] = useState("");
  const [cpfError, setCpfError] = useState("");
  const [coupon, setCoupon] = useState("");
  const [showPlans, setShowPlans] = useState(false);
  const [confirm, setConfirm] = useState<Confirm>(null);
  const [working, setWorking] = useState(false);
  // Cobrança aberta em outra aba: conferimos o pagamento a cada 10 s (PaymentWaiting).
  const [waitingInvoice, setWaitingInvoice] = useState("");
  // Troca de plano que ainda NÃO valeu (applied_now:false): mensagem do servidor fica visível.
  const [pendingChange, setPendingChange] = useState<{ message: string; invoiceUrl?: string } | null>(null);

  const loadBilling = () => getBilling().then(setBilling).catch(logError("/api/billing"));

  // Já existe assinatura no Asaas (viva)? Então é TROCA de plano, não assinatura nova
  // (antes pedir Pro com o Start ativo só reaproveitava a cobrança do Start).
  const hasSubscription = !!billing?.has_asaas && billing?.status !== "cancelled";
  // O servidor já tem o CPF/CNPJ (cliente no Asaas): não pede de novo.
  const docOnFile = hasDocOnFile(billing);

  useEffect(() => {
    loadBilling();
    apiGet<{ total_brl?: number; month_brl?: number }>("/api/ai-cost")
      .then((r) => setCostMonth(r.month_brl ?? r.total_brl ?? 0))
      .catch(logError("/api/ai-cost"));
  }, []);

  const subscribe = async (plan: string) => {
    if (!docOnFile) {
      const err = cpfCnpjError(cpfCnpj);
      setCpfError(err || "");
      if (err) return;
    }
    setSubscribing(plan);
    try {
      const res = await subscribePlan(plan, docOnFile ? "" : normalizeCpfCnpj(cpfCnpj));
      await loadBilling();
      if (res.invoice_url) {
        openInvoice(res.invoice_url);
        setWaitingInvoice(res.invoice_url);
        setShowPlans(false);
      } else {
        toast.success("Assinatura criada. Aguarde a confirmação do pagamento.");
      }
    } catch (e) {
      toast.error(billingErrorMessage(e, "Falha ao gerar cobrança."));
    } finally {
      setSubscribing("");
    }
  };

  // Troca de plano (POST /api/billing/change-plan). Pode devolver uma cobrança nova.
  const doChangePlan = async (plan: string) => {
    setWorking(true);
    try {
      const res = await changePlan(plan);
      if (res.ok === false || (res.error && !res.invoice_url && !res.applied_now && !res.unchanged)) {
        toast.error("Não consegui trocar o plano", { description: res.message || res.error || "Tente de novo em instantes." });
        return;
      }
      const wasActive = billing?.status === "active";
      await loadBilling();
      setConfirm(null);
      setShowPlans(false);
      const newPlan = res.plan || plan;
      const name = PLANS.find((p) => p.id === newPlan)?.name || newPlan;
      if (res.unchanged) {
        toast.info(res.message || `Você já está no plano ${name}.`);
      } else if (res.applied_now === false) {
        // A troca ainda NÃO valeu: nunca dizer "plano alterado" aqui. Mostra o que o servidor disse.
        const msg = res.message || (res.effective === "next_cycle"
          ? `O plano ${name} passa a valer no próximo ciclo.`
          : `O plano ${name} passa a valer quando o pagamento do valor novo for confirmado.`);
        const payUrl = res.effective === "on_payment" ? res.invoice_url : undefined;
        if (payUrl) {
          openInvoice(payUrl);
          // Só confere sozinho se a conta não estava ativa: com a conta ativa, o status já é
          // "active" (do plano antigo) e a conferência diria "pago" antes da hora.
          if (!wasActive) setWaitingInvoice(payUrl);
        }
        setPendingChange({ message: msg, invoiceUrl: payUrl });
        toast.info(msg, { duration: 8000 });
      } else if (res.invoice_url && res.status !== "active") {
        // Assinatura NOVA (sem applied_now): há uma cobrança a pagar de fato.
        // Troca com cobrança: abre o pagamento em outra aba e confere a cada 10 s.
        openInvoice(res.invoice_url);
        setWaitingInvoice(res.invoice_url);
        toast.success(res.message || `Troca para ${name} pedida. Falta o pagamento.`);
      } else if (res.applied_now) {
        toast.success(res.message || `Plano trocado para ${name}.`);
      } else {
        toast.success(res.message || `Troca para ${name} registrada.`);
      }
    } catch (e) {
      toast.error("Não consegui trocar o plano", { description: billingErrorMessage(e, "Tente de novo em instantes.") });
    } finally {
      setWorking(false);
    }
  };

  // Cancelamento (POST /api/billing/cancel), sempre depois da confirmação.
  const doCancel = async () => {
    setWorking(true);
    try {
      const res = await cancelSubscription();
      if (!res.ok && res.error) {
        toast.error("Não consegui cancelar", { description: (res as { message?: string }).message || res.error });
        return;
      }
      setConfirm(null);
      setWaitingInvoice("");
      await loadBilling();
      toast.success("Assinatura cancelada. As próximas cobranças não serão geradas.");
    } catch (e) {
      toast.error("Não consegui cancelar", { description: billingErrorMessage(e, "Tente de novo ou fale com o suporte.") });
    } finally {
      setWorking(false);
    }
  };

  const onApplyCoupon = async () => {
    if (!coupon.trim()) return;
    const r = await applyCoupon(coupon);
    if (r.accepted) {
      toast.success(r.message);
      setCoupon("");
      loadBilling();
    } else {
      toast.error(r.message);
    }
  };

  const statusLabel = (s?: string) => {
    switch (s) {
      case "active": return { text: "Ativo", cls: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", dot: "bg-emerald-500" };
      case "overdue": return { text: "Vencido", cls: "bg-amber-500/10 text-amber-500 border-amber-500/20", dot: "bg-amber-500" };
      case "pending": return { text: "Aguardando pagamento", cls: "bg-amber-500/10 text-amber-500 border-amber-500/20", dot: "bg-amber-500" };
      case "cancelled": return { text: "Cancelado", cls: "bg-destructive/10 text-destructive border-destructive/20", dot: "bg-destructive" };
      default: return { text: "Pendente", cls: "bg-muted text-muted-foreground border-border/50", dot: "bg-muted-foreground" };
    }
  };
  const st = statusLabel(billing?.status);
  const planName = billing?.plan_name || "Plano";
  const planValue = billing?.plan_value || "—";

  return (
    <div className="max-w-4xl space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Card className="p-8 bg-glass border-border/50 shadow-soft relative overflow-hidden">
        {/* Glow de fundo */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none"></div>
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h3 className="text-xl font-bold flex items-center gap-2 tracking-tight text-amber-500">
              <Crown className="h-5 w-5" /> {planName.toUpperCase()}
            </h3>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-4xl font-bold">{planValue}</span>
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              Acesso completo à orquestração de Agentes IA, CRM e Disparos no WhatsApp.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
             <Badge className={`${st.cls} px-3 py-1 flex items-center gap-1.5 font-semibold text-sm`}>
                <div className={`w-2 h-2 rounded-full ${st.dot} animate-pulse`}></div>
                {st.text}
             </Badge>
             <span className="text-xs text-muted-foreground">
               {billing?.member_since ? `Membro desde ${new Date(billing.member_since).toLocaleDateString("pt-BR")}` : "—"}
             </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-t border-border/50 pt-8">
          
          <div className="space-y-4">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Incluído no Plano</h4>
            <div className="space-y-3">
              {[
                "Múltiplos Agentes Especializados",
                "Piloto Automático de Ligações (Voz)",
                "Integração Nativa WhatsApp",
                "CRM de Follow-up Inteligente",
                "Disparos em Massa (Texto/Áudio)",
                "Integração com n8n e Webhooks",
                "Transcrição e Resumo de Áudios",
                "Transbordo Humano Imediato"
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span className="text-sm font-medium">{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4">Uso do Período</h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                   <span className="text-sm text-muted-foreground">Custo de IA no mês</span>
                   <span className="text-sm font-bold">{costMonth.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</span>
                </div>
                <div className="flex justify-between items-center">
                   <span className="text-sm text-muted-foreground">Mensagens processadas</span>
                   <span className="text-sm font-bold">∞</span>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              {billing?.invoice_url && (
                <a href={billing.invoice_url} target="_blank" rel="noopener noreferrer" className="block">
                  <Button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white shadow-glow border-none gap-2 rounded-xl h-11">
                    <PayIcon className="h-4 w-4" /> Pagar agora
                  </Button>
                </a>
              )}
              <Button
                variant="outline"
                className="w-full border-primary/30 hover:border-primary/50 gap-2 rounded-xl h-11"
                onClick={() => setShowPlans((v) => !v)}
              >
                <RefreshCw className="h-4 w-4" /> {billing?.status === "active" ? "Trocar de plano" : "Escolher outro plano"}
              </Button>
              {hasSubscription && (
                <Button
                  variant="ghost"
                  className="w-full gap-2 rounded-xl h-11 text-destructive hover:text-destructive hover:bg-destructive/10"
                  onClick={() => setConfirm({ kind: "cancel" })}
                >
                  <XCircle className="h-4 w-4" /> Cancelar assinatura
                </Button>
              )}
              <a
                href={`https://wa.me/5591984698653?text=${encodeURIComponent("Olá! Quero gerenciar minha assinatura do Hermes Call.")}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block"
              >
                <Button variant="ghost" className="w-full gap-2 rounded-xl h-11 text-muted-foreground">
                  <MessageCircle className="h-4 w-4" /> Gerenciar via WhatsApp
                </Button>
              </a>
            </div>
          </div>
        </div>

        {pendingChange && (
          <div className="mt-8 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm flex items-start gap-3">
            <RefreshCw className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <div className="flex-1 space-y-2">
              <p className="font-semibold text-amber-500">Troca de plano pedida</p>
              <p className="text-foreground/90">{pendingChange.message}</p>
              {pendingChange.invoiceUrl && !waitingInvoice && (
                <a href={pendingChange.invoiceUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium hover:underline">
                  <PayIcon className="h-4 w-4" /> Abrir a página de pagamento
                </a>
              )}
            </div>
            <button type="button" onClick={() => setPendingChange(null)} className="text-muted-foreground hover:text-foreground" aria-label="Fechar aviso">
              <XCircle className="h-4 w-4" />
            </button>
          </div>
        )}

        {waitingInvoice && (
          <div className="mt-8 border-t border-border/50 pt-6">
            <PaymentWaiting
              invoiceUrl={waitingInvoice}
              onPaid={() => { setWaitingInvoice(""); setPendingChange(null); loadBilling(); toast.success("Pagamento confirmado! Plano ativo."); }}
              secondaryLabel="Fechar (confiro depois)"
              onSecondary={() => setWaitingInvoice("")}
            />
          </div>
        )}

        {showPlans && (
          <div className="mt-8 border-t border-border/50 pt-6 space-y-4">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
              {hasSubscription ? "Trocar para outro plano" : "Escolha o plano"}
            </h4>
            {!hasSubscription && !docOnFile && (
              <div className="space-y-1">
                <input
                  type="text"
                  autoCapitalize="characters"
                  value={cpfCnpj}
                  onChange={(e) => { setCpfCnpj(formatCpfCnpj(e.target.value)); setCpfError(""); }}
                  onBlur={() => { if (cpfCnpj) setCpfError(cpfCnpjError(cpfCnpj) || ""); }}
                  placeholder="CPF ou CNPJ"
                  aria-invalid={!!cpfError}
                  className={`w-full rounded-lg border bg-background/50 px-3 py-2 text-sm ${cpfError ? "border-destructive" : "border-border/50"}`}
                />
                {cpfError && <p className="text-xs text-destructive">{cpfError}</p>}
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {PLANS.map((p) => {
                const isCurrent = billing?.plan_code === p.id && (billing?.status === "active" || hasSubscription);
                return (
                  <div
                    key={p.id}
                    className={`rounded-xl border p-4 ${isCurrent ? "border-emerald-500 bg-emerald-500/10" : "border-border/50 bg-background/50"}`}
                  >
                    <p className="font-bold">{p.name}</p>
                    <p className="text-sm text-primary font-medium">{p.price}</p>
                    <Button
                      size="sm"
                      disabled={!!subscribing || working || isCurrent}
                      className="w-full mt-3 gap-1"
                      onClick={() => (hasSubscription ? setConfirm({ kind: "change", plan: p.id }) : subscribe(p.id))}
                    >
                      {subscribing === p.id ? <Loader2 className="h-3 w-3 animate-spin" /> : isCurrent ? "Plano atual" : hasSubscription ? "Trocar para este" : "Assinar"}
                    </Button>
                  </div>
                );
              })}
            </div>
            <div className="flex items-center gap-2 pt-2">
              <div className="relative flex-1">
                <Ticket className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  value={coupon}
                  onChange={(e) => setCoupon(e.target.value)}
                  placeholder="Tem um cupom? Digite aqui"
                  className="w-full rounded-lg border border-border/50 bg-background/50 pl-9 pr-3 py-2 text-sm"
                />
              </div>
              <Button variant="outline" size="sm" onClick={onApplyCoupon} disabled={!coupon.trim()}>
                Aplicar
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Cupons válidos estendem o seu período de teste. O resultado aparece depois de aplicar.</p>
          </div>
        )}
      </Card>

      <Card className="p-8 bg-glass border-border/50 shadow-soft">
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-6 flex items-center gap-2">
          Add-ons (Módulos Opcionais)
          <Badge variant="outline" className="text-[10px] bg-amber-500/10 text-amber-500 border-amber-500/20 normal-case tracking-normal">Em breve</Badge>
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-background/50 border border-border/50 p-5 rounded-2xl flex flex-col items-start hover:border-primary/50 transition-colors">
            <Bot className="h-6 w-6 text-fuchsia-500 mb-3" />
            <h5 className="font-bold mb-1">Modelo Opus (Ultra IA)</h5>
            <p className="text-xs text-muted-foreground mb-4">Acesso ao Claude 3.5 Sonnet / Opus para conversas altamente complexas.</p>
            <span className="text-xs font-bold text-primary mt-auto">+R$ 49/mês</span>
          </div>
          <div className="bg-background/50 border border-border/50 p-5 rounded-2xl flex flex-col items-start hover:border-primary/50 transition-colors">
            <UploadCloud className="h-6 w-6 text-sky-500 mb-3" />
            <h5 className="font-bold mb-1">Armazenamento em Nuvem</h5>
            <p className="text-xs text-muted-foreground mb-4">Guarde até 1TB de áudios gravados e transcritos a longo prazo.</p>
            <span className="text-xs font-bold text-primary mt-auto">+R$ 29/mês</span>
          </div>
          <div className="bg-background/50 border border-border/50 p-5 rounded-2xl flex flex-col items-start hover:border-primary/50 transition-colors">
            <CreditCard className="h-6 w-6 text-amber-500 mb-3" />
            <h5 className="font-bold mb-1">Links de Pagamento Asaas</h5>
            <p className="text-xs text-muted-foreground mb-4">Permita que sua IA feche vendas e emita cobranças pelo chat.</p>
            <span className="text-xs font-bold text-primary mt-auto">+R$ 39/mês</span>
          </div>
        </div>
      </Card>

      <Dialog open={!!confirm} onOpenChange={(o) => { if (!o && !working) setConfirm(null); }}>
        <DialogContent className="sm:max-w-md">
          {confirm?.kind === "cancel" ? (
            <DialogHeader>
              <DialogTitle>Cancelar a assinatura?</DialogTitle>
              <DialogDescription>
                As próximas cobranças do plano {planName} deixam de ser geradas. Para voltar depois, é só assinar de novo nesta tela.
              </DialogDescription>
            </DialogHeader>
          ) : confirm?.kind === "change" ? (
            <DialogHeader>
              <DialogTitle>Trocar para o plano {PLANS.find((p) => p.id === confirm.plan)?.name}?</DialogTitle>
              <DialogDescription>
                Novo valor: {PLANS.find((p) => p.id === confirm.plan)?.price}. Subir de plano passa a valer quando o pagamento do valor novo
                for confirmado (a página de pagamento abre em outra aba); descer de plano passa a valer no próximo ciclo.
              </DialogDescription>
            </DialogHeader>
          ) : null}
          <DialogFooter className="gap-2">
            <Button variant="ghost" onClick={() => setConfirm(null)} disabled={working}>Voltar</Button>
            {confirm?.kind === "cancel" ? (
              <Button variant="destructive" onClick={doCancel} disabled={working}>
                {working ? <Loader2 className="h-4 w-4 animate-spin" /> : "Sim, cancelar assinatura"}
              </Button>
            ) : confirm?.kind === "change" ? (
              <Button onClick={() => doChangePlan(confirm.plan)} disabled={working}>
                {working ? <Loader2 className="h-4 w-4 animate-spin" /> : "Confirmar troca"}
              </Button>
            ) : null}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
