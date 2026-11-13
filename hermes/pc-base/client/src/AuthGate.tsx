import { Suspense, useCallback, useEffect, useState } from "react";
import { App } from "./App";
import { lazyNamed } from "@/lib/lazy";
import { checkAuth, clearAuth, consumeOAuthToken } from "@/lib/auth";
import { PaymentWaiting } from "./components/billing/PaymentWaiting";
import { PAID_PLANS, checkBilling, subscribePlan, openInvoice, billingErrorMessage, getBilling, hasDocOnFile, applyCoupon } from "@/services/billing";
import { cpfCnpjError, formatCpfCnpj, normalizeCpfCnpj } from "@/lib/cpf-cnpj";
// Login e cadastro só são baixados quando aparecem (quem já está logado não precisa deles).
const LoginScreen = lazyNamed(() => import("./components/auth/LoginScreen"), "LoginScreen");
const RegisterScreen = lazyNamed(() => import("./components/auth/RegisterScreen"), "RegisterScreen");

type AuthView = "checking" | "landing" | "login" | "register" | "trial_expired" | "payment_required" | "offline" | "ok";

export const AuthGate = () => {
  const [state, setState] = useState<AuthView>("checking");

  const run = useCallback(() => {
    // FIX P0-001 (2026-07-25): bypass de auth pelas portas 5173/5174 REMOVIDO.
    // O bloco abaixo (window.location.port === "5173" || "5174") liberava
    // dashboard sem token em produção — proxy/CDN que reescrevesse pra uma
    // dessas portas burlava o login. Era um TEMPORARY que ficou. Para dev
    // local, basta rodar `npm run dev` (porta 5173) com o backend local
    // servindo /api/auth/login normalmente — checkAuth() faz o resto.
    // Retorno do login Google sem 2FA (?token=): guarda o token antes de conferir a sessão.
    consumeOAuthToken();
    checkAuth().then((result) => {
      const urlParams = new URLSearchParams(window.location.search);
      const action = urlParams.get("action");

      if (result === true) {
        setState("ok");
      } else if (result === "trial_expired" || result === "payment_required") {
        setState(result);
      } else if (result === "offline") {
        // Servidor fora ou sem rede: NÃO desloga; mostra aviso e tenta de novo.
        setState("offline");
      } else {
        // Login Google com 2FA: o servidor volta com ?2fa_challenge=<id> e o painel pede o código.
        if (urlParams.get("2fa_challenge")) setState("login");
        else if (action === "login") setState("login");
        else if (action === "register") setState("register");
        else setState("landing");
      }
    });
  }, []);

  useEffect(() => { run(); }, [run]);

  // Sem servidor: tenta de novo a cada 10 s enquanto o aviso estiver na tela.
  useEffect(() => {
    if (state !== "offline") return;
    const id = window.setInterval(run, 10_000);
    return () => window.clearInterval(id);
  }, [state, run]);

  if (state === "checking") return null;
  if (state === "offline")
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center space-y-4">
          <div className="text-4xl">📡</div>
          <h1 className="text-xl font-bold text-white">Não consegui falar com o servidor</h1>
          <p className="text-sm text-slate-400">
            Pode ser a sua internet ou uma instabilidade rápida do Hermes. Você continua conectado;
            vamos tentar de novo sozinhos a cada 10 segundos.
          </p>
          <button
            onClick={() => { setState("checking"); run(); }}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold"
          >
            Tentar de novo agora
          </button>
        </div>
      </div>
    );
  if (state === "landing") {
    window.location.href = "/landing/index.html";
    return null;
  }
  if (state === "login")
    return (
      <Suspense fallback={null}>
        <LoginScreen
          onSuccess={() => setState("ok")}
          onRegister={() => setState("register")}
          onTrialExpired={() => setState("trial_expired")}
        />
      </Suspense>
    );
  if (state === "register")
    return (
      <Suspense fallback={null}>
        <RegisterScreen
          onSuccess={() => setState("ok")}
          onLogin={() => setState("login")}
        />
      </Suspense>
    );
  if (state === "trial_expired" || state === "payment_required")
    return <TrialExpired paymentRequired={state === "payment_required"} onLogout={() => { clearAuth(); setState("landing"); }} />;
  return <App />;
};

// Tela de teste vencido / cobrança vencida COM assinatura dentro do app. Antes o botão
// "Ver planos" levava pro domínio de testes (fora do ar) — quem vencia não tinha como pagar.
function TrialExpired({ onLogout, paymentRequired }: { onLogout: () => void; paymentRequired?: boolean }) {
  const [plan, setPlan] = useState("basic");
  const [doc, setDoc] = useState("");
  const [docErr, setDocErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  // Cobrança aberta em outra aba: a tela fica conferindo o pagamento (PaymentWaiting).
  const [invoiceUrl, setInvoiceUrl] = useState("");
  // O servidor já tem o CPF/CNPJ (cliente no Asaas)? Então não pedimos de novo.
  const [docOnFile, setDocOnFile] = useState(false);
  // Cupom (estende o teste): só no teste vencido.
  const [coupon, setCoupon] = useState("");
  const [couponMsg, setCouponMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [couponBusy, setCouponBusy] = useState(false);

  useEffect(() => {
    getBilling().then((b) => setDocOnFile(hasDocOnFile(b))).catch(() => setDocOnFile(false));
  }, []);

  const aplicarCupom = async () => {
    if (!coupon.trim()) return;
    setCouponBusy(true);
    const r = await applyCoupon(coupon);
    setCouponMsg({ ok: r.accepted, text: r.message });
    setCouponBusy(false);
  };

  const assinar = async () => {
    setMsg("");
    if (!docOnFile) {
      const err = cpfCnpjError(doc);
      setDocErr(err || "");
      if (err) return;
    }
    setBusy(true);
    try {
      const r = await subscribePlan(plan, docOnFile ? "" : normalizeCpfCnpj(doc));
      if (r.invoice_url) {
        // Antes: window.location.href = invoice_url (a pessoa saía do app sem volta).
        openInvoice(r.invoice_url);
        setInvoiceUrl(r.invoice_url);
        return;
      }
      setMsg("Assinatura criada. Aguarde a confirmação do pagamento.");
    } catch (e) {
      setMsg(billingErrorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const jaPaguei = async () => {
    setBusy(true);
    setMsg("");
    try {
      const r = await checkBilling();
      if (r.status === "active") {
        location.reload();
        return;
      }
      setMsg("Pagamento ainda não confirmado. PIX leva alguns minutos; boleto, até 3 dias úteis.");
    } catch {
      setMsg("Não consegui verificar agora. Tente de novo em instantes.");
    } finally {
      setBusy(false);
    }
  };

  const planos = PAID_PLANS.map((p) => ({ id: p.id, nome: p.name, preco: p.price }));

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="w-16 h-16 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto">
          <span className="text-3xl">⏱</span>
        </div>
        <h1 className="text-2xl font-bold text-white">{paymentRequired ? "Assinatura com pagamento pendente" : "Período de teste expirado"}</h1>
        <p className="text-slate-400">
          {paymentRequired
            ? "Regularize o pagamento da sua assinatura para continuar usando o Hermes Call."
            : "Seu período de teste grátis acabou. Para continuar usando o Hermes Call, escolha um plano ou use um cupom."}
        </p>
        {invoiceUrl ? (
          <>
            <PaymentWaiting tone="dark" invoiceUrl={invoiceUrl} onPaid={() => location.reload()} />
            <button
              onClick={onLogout}
              className="block w-full py-3 text-sm font-medium border border-white/10 hover:border-white/20 rounded-lg transition-colors text-slate-400 hover:text-white"
            >
              Sair
            </button>
          </>
        ) : (
        <>
        <div className="grid grid-cols-3 gap-2">
          {planos.map((p) => (
            <button
              key={p.id}
              onClick={() => setPlan(p.id)}
              className={
                "rounded-lg border p-3 text-sm transition-colors " +
                (plan === p.id ? "border-emerald-500 bg-emerald-500/10 text-white" : "border-white/10 text-slate-400 hover:border-white/30")
              }
            >
              <div className="font-semibold">{p.nome}</div>
              <div className="text-xs">{p.preco}</div>
            </button>
          ))}
        </div>
        {docOnFile ? (
          <p className="text-xs text-slate-400">Seu CPF/CNPJ já está cadastrado; não precisa informar de novo.</p>
        ) : (
        <div className="text-left space-y-1">
          <input
            value={doc}
            onChange={(e) => { setDoc(formatCpfCnpj(e.target.value)); setDocErr(""); }}
            onBlur={() => { if (doc) setDocErr(cpfCnpjError(doc) || ""); }}
            placeholder="CPF ou CNPJ"
            autoCapitalize="characters"
            aria-invalid={!!docErr}
            className={"w-full rounded-lg border bg-slate-900 px-3 py-3 text-sm text-white placeholder:text-slate-500 " + (docErr ? "border-red-500/70" : "border-white/10")}
          />
          {docErr && <p className="text-xs text-red-400">{docErr}</p>}
        </div>
        )}
        {msg && <p className="text-sm text-amber-400">{msg}</p>}
        <div className="space-y-3">
          <button
            onClick={assinar}
            disabled={busy}
            className="block w-full py-3 text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 rounded-lg transition-colors text-white"
          >
            {busy ? "Aguarde..." : "Assinar e pagar"}
          </button>
          <button
            onClick={jaPaguei}
            disabled={busy}
            className="block w-full py-3 text-sm font-medium border border-emerald-500/30 hover:border-emerald-500/60 rounded-lg transition-colors text-emerald-400"
          >
            Já paguei — verificar
          </button>
          {!paymentRequired && (
            <div className="text-left space-y-2 border-t border-white/10 pt-3">
              <label htmlFor="trial-coupon" className="text-xs text-slate-400">Tem um cupom? Ele pode estender o seu teste.</label>
              <div className="flex gap-2">
                <input
                  id="trial-coupon"
                  value={coupon}
                  onChange={(e) => { setCoupon(e.target.value.toUpperCase()); setCouponMsg(null); }}
                  placeholder="CUPOM"
                  className="flex-1 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 uppercase"
                />
                <button
                  onClick={aplicarCupom}
                  disabled={couponBusy || !coupon.trim()}
                  className="px-4 py-2 text-sm font-medium border border-white/20 hover:border-white/40 rounded-lg text-white disabled:opacity-50"
                >
                  {couponBusy ? "Aguarde..." : "Aplicar"}
                </button>
              </div>
              {couponMsg && (
                <div className={"text-sm " + (couponMsg.ok ? "text-emerald-400" : "text-amber-400")}>
                  <p>{couponMsg.text}</p>
                  {couponMsg.ok && (
                    <button onClick={() => location.reload()} className="mt-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold">
                      Entrar no painel
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
          <button
            onClick={onLogout}
            className="block w-full py-3 text-sm font-medium border border-white/10 hover:border-white/20 rounded-lg transition-colors text-slate-400 hover:text-white"
          >
            Sair
          </button>
        </div>
        </>
        )}
      </div>
    </div>
  );
}
