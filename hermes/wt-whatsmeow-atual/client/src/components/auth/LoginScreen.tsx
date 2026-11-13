import { useState } from "react";
import { Loader2, Zap, Bot, ArrowLeft, ShieldCheck, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { requestPasswordReset, resetPassword, loginSecondFactor, setSession } from "@/lib/auth";

// Passos da tela:
//   login  → e-mail + senha (POST /api/auth/login)
//   2fa    → quando o servidor responde {"2fa_required":true,"challenge"}: código de 6 dígitos
//            (POST /api/auth/login/2fa {challenge, code}, que responde igual ao login)
//   forgot → "Esqueci minha senha": e-mail (POST /api/auth/forgot); o código vai pro WhatsApp
//   reset  → código + nova senha (POST /api/auth/reset) → volta ao login com aviso de sucesso
type Step = "login" | "2fa" | "forgot" | "reset";

const SUPPORT_WA = "https://wa.me/5591984698653?text=";
const NETWORK_ERR = "Não foi possível conectar ao servidor. Verifique sua internet e tente novamente.";
const UNAVAILABLE = "Este recurso ainda não está disponível no servidor. Use o suporte no WhatsApp abaixo.";

// Login Google com 2FA ligado: o servidor redireciona para o painel com ?2fa_challenge=<id>.
const urlChallenge = (): string => {
  try { return new URLSearchParams(window.location.search).get("2fa_challenge") || ""; } catch { return ""; }
};
// Tira o ?2fa_challenge da barra de endereço (desafio usado/vencido não deve ser reaproveitado).
const clearUrlChallenge = () => {
  try {
    const u = new URL(window.location.href);
    if (!u.searchParams.has("2fa_challenge")) return;
    u.searchParams.delete("2fa_challenge");
    window.history.replaceState(null, "", u.pathname + (u.search ? u.search : "") + u.hash);
  } catch { /* sem history */ }
};

// Mensagem do servidor só se for texto legível (não códigos como "invalid_code").
const readable = (v: unknown): string => (typeof v === "string" && v.includes(" ") ? v : "");

export const LoginScreen = ({
  onRegister,
  onTrialExpired,
}: {
  onSuccess?: () => void;
  onRegister: () => void;
  onTrialExpired?: () => void;
}) => {
  const [step, setStep] = useState<Step>(() => (urlChallenge() ? "2fa" : "login"));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [info, setInfo] = useState(() => (urlChallenge() ? "Para concluir a entrada com o Google, digite o código do seu aplicativo autenticador." : ""));
  // 2FA (o desafio vem do login com senha ou do retorno do login Google)
  const [challenge, setChallenge] = useState(urlChallenge);
  const [code2fa, setCode2fa] = useState("");
  // Esqueci a senha
  const [resetCode, setResetCode] = useState("");
  const [newPass, setNewPass] = useState("");
  const [newPass2, setNewPass2] = useState("");

  const goTo = (next: Step) => {
    setErr("");
    setInfo("");
    setStep(next);
  };

  // Login concluído (com ou sem 2FA): guarda a sessão e abre o painel.
  const finishLogin = (data: any) => {
    setSession(data.token, data.user);
    // P1-2 fix: navigate para uma rota limpa (sem ?action=login) pra que o
    // AuthGate monte <App /> em URL canonica. Antes só chamava onSuccess() que
    // setava state="ok" mas a URL continuava com ?action=login e o refresh
    // mostrava a tela de login de novo.
    window.location.assign("/dashboard");
  };

  // Erros de login (vale para a senha e para o código 2FA).
  const handleLoginError = (status: number, data: any, fallback: string) => {
    if (data?.error === "trial_expired") {
      if (data.token) setSession(data.token, data.user);
      if (onTrialExpired) onTrialExpired();
      // Usa a mensagem explicativa do backend (ex: "Seu período de teste de
      // 10 horas expirou..."), não um texto genérico.
      else setErr(data.message || "Seu período de teste expirou. Faça upgrade para continuar.");
      return;
    }
    if (data?.error === "invalid credentials" || data?.error === "invalid_credentials") {
      setErr("E-mail ou senha incorretos.");
      return;
    }
    if (status === 429) {
      setErr(data?.message || "Muitas tentativas. Aguarde alguns minutos e tente novamente.");
      return;
    }
    setErr(data?.message || readable(data?.error) || fallback);
  };

  const submitLogin = async () => {
    setBusy(true);
    setErr("");
    setInfo("");
    try {
      const r = await fetch(window.location.origin + "/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        handleLoginError(r.status, data, "Não consegui entrar. Tente de novo.");
        return;
      }
      // Conta com verificação em duas etapas: pede o código antes de liberar.
      if (data?.["2fa_required"] && data?.challenge) {
        setChallenge(String(data.challenge));
        setCode2fa("");
        goTo("2fa");
        return;
      }
      finishLogin(data);
    } catch (e: any) {
      // "Failed to fetch" = erro de REDE (requisição não chegou ao servidor), não é
      // credencial nem trial. Traduz pra algo que a pessoa entenda e possa agir.
      const isNetwork = e?.message === "Failed to fetch" || e?.name === "TypeError";
      setErr(isNetwork ? NETWORK_ERR : (e?.message || "Erro ao fazer login"));
    } finally {
      setBusy(false);
    }
  };

  const submit2fa = async () => {
    const code = code2fa.replace(/\D/g, "");
    if (code.length !== 6) {
      setErr("Digite os 6 números do código.");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const res = await loginSecondFactor(challenge, code);
      if (res.ok && res.data?.token) {
        finishLogin(res.data);
        return;
      }
      if (res.status === 404) {
        setErr("A verificação em duas etapas está indisponível no momento. Tente de novo mais tarde.");
        return;
      }
      // Desafio vencido (401 challenge_expired): precisa entrar de novo com a senha.
      if (res.data?.error === "challenge_expired") {
        clearUrlChallenge();
        setChallenge("");
        setPassword("");
        setInfo("");
        setStep("login");
        setErr(res.data?.message || "O tempo para digitar o código acabou. Entre de novo com a senha.");
        return;
      }
      // 401 invalid_code (com message) e 429 (limite de tentativas) mostram a mensagem do servidor.
      handleLoginError(res.status, res.data, res.data?.error === "invalid_code" ? "Código inválido. Confira no aplicativo autenticador." : "Código inválido ou expirado. Entre de novo com a senha para receber outro.");
    } catch {
      setErr(NETWORK_ERR);
    } finally {
      setBusy(false);
    }
  };

  const submitForgot = async () => {
    if (!email.trim() || !email.includes("@")) {
      setErr("Digite o e-mail do cadastro.");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const res = await requestPasswordReset(email);
      if (res.ok) {
        setResetCode("");
        setNewPass("");
        setNewPass2("");
        setStep("reset");
        setInfo("Se este e-mail estiver cadastrado, enviamos um código de 6 dígitos para o WhatsApp do cadastro.");
        return;
      }
      if (res.status === 404) setErr(UNAVAILABLE);
      else if (res.status === 429) setErr(res.data?.message || readable(res.data?.error) || "Muitos pedidos. Aguarde alguns minutos e tente de novo.");
      else setErr(res.data?.message || readable(res.data?.error) || "Não consegui enviar o código agora. Tente de novo.");
    } catch {
      setErr(NETWORK_ERR);
    } finally {
      setBusy(false);
    }
  };

  const resendCode = async () => {
    setBusy(true);
    setErr("");
    try {
      const res = await requestPasswordReset(email);
      if (res.ok) setInfo("Pedimos um novo código. Ele chega no WhatsApp do cadastro em instantes.");
      else if (res.status === 429) setErr(res.data?.message || readable(res.data?.error) || "Muitos pedidos. Aguarde alguns minutos e tente de novo.");
      else setErr(res.data?.message || readable(res.data?.error) || "Não consegui reenviar o código agora.");
    } catch {
      setErr(NETWORK_ERR);
    } finally {
      setBusy(false);
    }
  };

  const submitReset = async () => {
    const code = resetCode.replace(/\D/g, "");
    if (code.length !== 6) {
      setErr("Digite os 6 números do código que chegou no WhatsApp.");
      return;
    }
    if (newPass.length < 6) {
      setErr("A nova senha deve ter no mínimo 6 caracteres.");
      return;
    }
    if (newPass !== newPass2) {
      setErr("As senhas não coincidem.");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const res = await resetPassword(email, code, newPass);
      if (res.ok) {
        setPassword("");
        setStep("login");
        setErr("");
        setInfo("Senha alterada! Entre com a nova senha.");
        return;
      }
      if (res.status === 404) setErr(UNAVAILABLE);
      else setErr(res.data?.message || readable(res.data?.error) || "Código inválido ou expirado. Peça um novo código.");
    } catch {
      setErr(NETWORK_ERR);
    } finally {
      setBusy(false);
    }
  };

  const inputCls = "border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-primary";
  const supportLink = (
    <a
      href={SUPPORT_WA + encodeURIComponent("Olá! Esqueci minha senha do Hermes Call. Meu e-mail de acesso é: " + (email || ""))}
      target="_blank"
      rel="noopener noreferrer"
      className="block text-center text-xs text-muted-foreground hover:text-primary"
    >
      Prefere falar com uma pessoa? Chamar o suporte no WhatsApp
    </a>
  );

  const titles: Record<Step, { title: string; sub: string }> = {
    login: { title: "Bem-vindo(a) de volta", sub: "Hermes — Inteligência Artificial" },
    "2fa": { title: "Verificação em duas etapas", sub: "Digite o código de 6 dígitos para entrar." },
    forgot: { title: "Recuperar senha", sub: "Vamos mandar um código para o WhatsApp do cadastro." },
    reset: { title: "Criar nova senha", sub: "Digite o código que chegou no WhatsApp e a nova senha." },
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4 md:p-8 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-6xl flex flex-col lg:flex-row items-center justify-center gap-12 lg:gap-24 relative z-10">

        {/* Left Side: Mockup (Apple Style) */}
        <div className="hidden lg:flex flex-1 flex-col items-center justify-center">
          <div className="relative w-full max-w-lg aspect-square animate-float">
             <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-transparent rounded-[3rem] blur-3xl" />
             <div className="absolute inset-4 rounded-[2rem] border border-white/10 bg-black/40 backdrop-blur-3xl shadow-2xl overflow-hidden flex flex-col">
                {/* Mockup Header */}
                <div className="h-12 border-b border-white/10 flex items-center px-6 gap-2">
                   <div className="w-3 h-3 rounded-full bg-red-500/80" />
                   <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                   <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                </div>
                {/* Mockup Body */}
                <div className="flex-1 p-6 flex flex-col gap-4">
                   <div className="h-8 w-1/3 bg-white/5 rounded-lg" />
                   <div className="flex gap-4">
                     <div className="h-32 w-full bg-primary/20 rounded-xl border border-primary/30 flex items-center justify-center">
                       <Bot className="h-12 w-12 text-primary opacity-50" />
                     </div>
                     <div className="h-32 w-full bg-white/5 rounded-xl border border-white/10" />
                   </div>
                   <div className="h-40 w-full bg-white/5 rounded-xl border border-white/10 mt-auto" />
                </div>
             </div>

             {/* Floating elements around */}
             <div className="absolute -right-8 top-1/4 w-24 h-24 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl animate-float" style={{ animationDelay: '1s' }}>
                <div className="w-full h-full flex items-center justify-center text-primary"><Bot className="h-10 w-10 drop-shadow-[0_0_10px_rgba(16,185,129,0.5)]" /></div>
             </div>
             <div className="absolute -left-4 bottom-1/4 w-20 h-20 rounded-full border border-white/10 bg-white/5 backdrop-blur-xl animate-float" style={{ animationDelay: '2s' }}>
                <div className="w-full h-full flex items-center justify-center text-sky-400"><Zap className="h-8 w-8 drop-shadow-[0_0_10px_rgba(56,189,248,0.5)]" /></div>
             </div>
          </div>
        </div>

        {/* Right Side: Form */}
        <div className="relative w-full max-w-md space-y-6 rounded-2xl border border-border/50 bg-glass p-8 shadow-glow backdrop-blur-xl shrink-0">
          <div className="flex flex-col items-center text-center gap-3">
          <div className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <Zap className="mr-1.5 h-3.5 w-3.5" /> Acesso Seguro
          </div>
          <div className="flex items-center gap-3 mt-2">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-glow">
              {step === "2fa" ? <ShieldCheck className="h-6 w-6" /> : step === "login" ? <Bot className="h-6 w-6" /> : <KeyRound className="h-6 w-6" />}
            </span>
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground mt-2">{titles[step].title}</h1>
            <p className="text-sm text-muted-foreground mt-1">{titles[step].sub}</p>
          </div>
        </div>

        {info && <p className="text-sm rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-500 px-3 py-2">{info}</p>}

        {step === "login" && (
        <div className="space-y-3">
          <div className="space-y-1">
            <Label className="text-muted-foreground">Email</Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              autoComplete="email"
              className={inputCls}
            />
          </div>
          <div className="space-y-1">
            <Label className="text-muted-foreground">Senha</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") submitLogin(); }}
              placeholder="sua senha"
              autoComplete="current-password"
              className={inputCls}
            />
          </div>
          <button
            type="button"
            onClick={() => goTo("forgot")}
            className="block ml-auto text-right text-xs text-muted-foreground hover:text-primary"
          >
            Esqueci minha senha
          </button>
          {err && <p className="text-sm text-destructive">{err}</p>}
          <Button
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow h-11 rounded-xl"
            onClick={submitLogin}
            disabled={busy}
          >
            {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Entrar"}
          </Button>
          <div className="text-center text-sm text-muted-foreground pt-2">
          Não tem uma conta?{" "}
          <button
            onClick={onRegister}
            className="font-medium text-primary hover:underline hover:text-primary/80 transition-colors"
          >
            Criar agora
          </button>
        </div>

          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-slate-400">Ou continuar com</span>
            </div>
          </div>

          <Button
            variant="outline"
            className="w-full border-white/10 bg-white/5 hover:bg-white/10 text-white"
            onClick={() => {
              toast.info("Login com Google em breve!", { description: "A integração com o Google Workspace está sendo finalizada." });
            }}
          >
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
              <path d="M1 1h22v22H1z" fill="none" />
            </svg>
            Google <span className="ml-1 text-[10px] text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded uppercase font-bold">Em breve</span>
          </Button>

        </div>
        )}

        {step === "2fa" && (
          <div className="space-y-3">
            <div className="space-y-1">
              <Label className="text-muted-foreground">Código de verificação</Label>
              <Input
                value={code2fa}
                onChange={(e) => setCode2fa(e.target.value.replace(/\D/g, "").slice(0, 6))}
                onKeyDown={(e) => { if (e.key === "Enter") submit2fa(); }}
                inputMode="numeric"
                autoComplete="one-time-code"
                autoFocus
                placeholder="000000"
                className={`${inputCls} text-center text-lg tracking-[0.5em] font-mono`}
              />
              <p className="text-[11px] text-muted-foreground">Use o código do seu aplicativo autenticador.</p>
            </div>
            {err && <p className="text-sm text-destructive">{err}</p>}
            <Button
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow h-11 rounded-xl"
              onClick={submit2fa}
              disabled={busy || code2fa.length !== 6}
            >
              {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Confirmar e entrar"}
            </Button>
            <button type="button" onClick={() => { clearUrlChallenge(); setChallenge(""); goTo("login"); }} className="flex items-center gap-1 mx-auto text-xs text-muted-foreground hover:text-primary">
              <ArrowLeft className="h-3 w-3" /> Voltar
            </button>
          </div>
        )}

        {step === "forgot" && (
          <div className="space-y-3">
            <div className="space-y-1">
              <Label className="text-muted-foreground">E-mail do cadastro</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") submitForgot(); }}
                placeholder="seu@email.com"
                autoComplete="email"
                autoFocus
                className={inputCls}
              />
              <p className="text-[11px] text-muted-foreground">O código de 6 dígitos chega pelo WhatsApp informado no cadastro.</p>
            </div>
            {err && <p className="text-sm text-destructive">{err}</p>}
            <Button
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow h-11 rounded-xl"
              onClick={submitForgot}
              disabled={busy}
            >
              {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Enviar código"}
            </Button>
            <button type="button" onClick={() => goTo("login")} className="flex items-center gap-1 mx-auto text-xs text-muted-foreground hover:text-primary">
              <ArrowLeft className="h-3 w-3" /> Voltar para o login
            </button>
            {supportLink}
          </div>
        )}

        {step === "reset" && (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground text-center">Conta: <strong className="text-foreground">{email}</strong></p>
            <div className="space-y-1">
              <Label className="text-muted-foreground">Código recebido no WhatsApp</Label>
              <Input
                value={resetCode}
                onChange={(e) => setResetCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                inputMode="numeric"
                autoComplete="one-time-code"
                autoFocus
                placeholder="000000"
                className={`${inputCls} text-center text-lg tracking-[0.5em] font-mono`}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-muted-foreground">Nova senha</Label>
              <Input
                type="password"
                value={newPass}
                onChange={(e) => setNewPass(e.target.value)}
                placeholder="Mínimo 6 caracteres"
                autoComplete="new-password"
                className={inputCls}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-muted-foreground">Repita a nova senha</Label>
              <Input
                type="password"
                value={newPass2}
                onChange={(e) => setNewPass2(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") submitReset(); }}
                placeholder="Repita a senha"
                autoComplete="new-password"
                className={inputCls}
              />
            </div>
            {err && <p className="text-sm text-destructive">{err}</p>}
            <Button
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow h-11 rounded-xl"
              onClick={submitReset}
              disabled={busy}
            >
              {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Salvar nova senha"}
            </Button>
            <div className="flex items-center justify-between text-xs">
              <button type="button" onClick={() => goTo("forgot")} className="flex items-center gap-1 text-muted-foreground hover:text-primary">
                <ArrowLeft className="h-3 w-3" /> Trocar e-mail
              </button>
              <button type="button" onClick={resendCode} disabled={busy} className="text-muted-foreground hover:text-primary disabled:opacity-50">
                Reenviar código
              </button>
            </div>
            {supportLink}
          </div>
        )}
        </div>
      </div>
    </div>
  );
};
