import { useState } from 'react'
import { Loader2, Phone, Check, Zap, Bot, CheckCircle2, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { register, RegisterError } from '@/lib/auth'
import { applyCoupon, openInvoice } from '@/services/billing'
import { cpfCnpjError, formatCpfCnpj, normalizeCpfCnpj } from '@/lib/cpf-cnpj'
import { PaymentWaiting } from '@/components/billing/PaymentWaiting'

interface RegisterScreenProps {
  onSuccess: () => void
  onLogin: () => void
}

const plans = [
  {
    id: 'basic',
    name: 'Start',
    price: 'R$199/mês',
    subtitle: 'Para começar com 1 canal',
    trial: null,
    features: [
      '1 Instância WhatsApp',
      'Até 3 Agentes de IA',
      'Escolha 1 canal: Texto OU Voz',
      'RAG Básica',
      'Integração Simples via API',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 'R$399/mês',
    subtitle: 'Texto + Ligação',
    trial: null,
    features: [
      'Tudo do Start',
      '3 Instâncias WhatsApp',
      'Agentes Ilimitados (Texto + Voz)',
      'RAG & Memória Avançada',
      'Chatbots Arena (A/B)',
    ],
  },
  {
    id: 'scale',
    name: 'Scale',
    price: 'R$599/mês',
    subtitle: 'IA em Reuniões + Automações',
    trial: null,
    features: [
      'Tudo do Pro',
      'IA em Reuniões (Meet)',
      '50 mil tokens de IA/mês',
      'Análise de Sentimento em tempo real',
      'Webhooks & API Dedicada',
    ],
  },
  {
    id: 'trial',
    name: 'Teste Grátis',
    price: 'R$0',
    subtitle: '10 horas pra experimentar',
    trial: 'Grátis 10h',
    features: [
      'Acesso ao painel por 10h',
      'Teste voz e texto',
      'Sem cartão de crédito',
      'Escolhe o plano quando o teste acabar',
    ],
  },
]

export function RegisterScreen({ onSuccess, onLogin }: RegisterScreenProps) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [whatsapp, setWhatsapp] = useState('')
  const [company, setCompany] = useState('')
  const [selectedPlan, setSelectedPlan] = useState('basic')
  const [cpfCnpj, setCpfCnpj] = useState('')
  const [cpfError, setCpfError] = useState('')
  const [coupon, setCoupon] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  // Depois de criar a conta: resultado mostrado NA TELA (antes era alert() ou um erro que
  // sumia porque a tela trocava na hora).
  const [done, setDone] = useState<
    | { kind: 'coupon'; ok: boolean; text: string }
    | { kind: 'payment'; invoiceUrl: string }
    | { kind: 'no_payment'; text: string }
    | null
  >(null)

  const hasCoupon = coupon.trim() !== ''
  const isPaidPlan = selectedPlan !== 'trial' && selectedPlan !== 'enterprise'
  // CPF/CNPJ é obrigatório quando vai gerar cobrança (plano pago sem cupom).
  const needsDoc = isPaidPlan && !hasCoupon

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (password.length < 6) {
      setError('A senha deve ter no mínimo 6 caracteres.')
      return
    }

    if (password !== confirmPassword) {
      setError('As senhas não coincidem.')
      return
    }

    if (needsDoc) {
      const docErr = cpfCnpjError(cpfCnpj)
      setCpfError(docErr || '')
      if (docErr) return
    }

    setLoading(true)
    try {
      const res = await register({
        name,
        email,
        password,
        whatsapp: whatsapp || undefined,
        company: company || undefined,
        plan: hasCoupon ? 'trial' : selectedPlan,
        cpf_cnpj: needsDoc ? normalizeCpfCnpj(cpfCnpj) : undefined,
      })

      // Com cupom: a conta nasce no teste grátis e o cupom pode ESTENDER o teste.
      // Mostramos exatamente o que o servidor respondeu (nada de "aplicado" por conta própria).
      if (hasCoupon) {
        const r = await applyCoupon(coupon)
        setDone({ kind: 'coupon', ok: r.accepted, text: r.accepted ? r.message : `${r.message} Sua conta foi criada no teste grátis de 10h.` })
        return
      }

      // Plano pago: a cobrança abre em OUTRA aba e esta tela confere o pagamento a cada 10 s.
      // Antes: window.location.href = invoice_url (a pessoa saía do app sem volta).
      if (res.payment_required && res.invoice_url) {
        openInvoice(res.invoice_url)
        setDone({ kind: 'payment', invoiceUrl: res.invoice_url })
        return
      }
      // Plano pago sem cobrança gerada (gateway indisponível etc.): a conta entra no teste
      // de 10h e o cliente assina depois (tela de teste vencido ou Configurações › Assinatura).
      const unavailable = (res as { payment_unavailable?: string }).payment_unavailable
      if (unavailable) {
        setDone({ kind: 'no_payment', text: unavailable })
        return
      }
      onSuccess()
    } catch (err: any) {
      const m = String(err?.message || '')
      // Servidor recusou o CPF/CNPJ: erro embaixo do próprio campo.
      if (err instanceof RegisterError && err.field === 'cpf_cnpj') {
        const txt = err.serverMessage || (err.code.includes(' ') ? err.code : '')
        setCpfError(txt || 'CPF/CNPJ recusado pelo servidor. Confira os caracteres.')
        return
      }
      if (err instanceof RegisterError && err.status === 429) {
        setError(err.serverMessage || 'Muitas tentativas de cadastro. Aguarde alguns minutos e tente de novo.')
        return
      }
      if (/already registered/i.test(m)) setError('Este e-mail já tem conta. Faça login ou use "Esqueci minha senha".')
      else if (m === 'Failed to fetch') setError('Não foi possível conectar ao servidor. Verifique sua internet e tente novamente.')
      else setError(m || 'Erro ao criar conta. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  // Tela de resultado (cupom / pagamento / cobrança indisponível), no lugar do formulário.
  const resultPanel = done && (
    <div className="space-y-4">
      {done.kind === 'coupon' && (
        <div className={`rounded-xl border p-4 text-sm flex items-start gap-2 ${done.ok ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500' : 'border-amber-500/30 bg-amber-500/10 text-amber-500'}`}>
          {done.ok ? <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" /> : <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />}
          <div>
            <p className="font-semibold">Conta criada!</p>
            <p className="mt-1">Cupom: {done.text}</p>
          </div>
        </div>
      )}
      {done.kind === 'payment' && (
        <>
          <p className="text-sm text-muted-foreground">Conta criada! Falta só o pagamento do plano. Enquanto isso, você já pode usar o teste grátis.</p>
          <PaymentWaiting
            invoiceUrl={done.invoiceUrl}
            onPaid={onSuccess}
            secondaryLabel="Entrar no painel agora e pagar depois"
            onSecondary={onSuccess}
          />
        </>
      )}
      {done.kind === 'no_payment' && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-500 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Conta criada no teste grátis de 10h.</p>
            <p className="mt-1">Não consegui gerar a cobrança agora: {done.text}</p>
            <p className="mt-1 text-muted-foreground">Você pode assinar depois em Configurações › Faturamento.</p>
          </div>
        </div>
      )}
      {done.kind !== 'payment' && (
        <Button type="button" onClick={onSuccess} className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow h-11 rounded-xl">
          Entrar no painel
        </Button>
      )}
    </div>
  )

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
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
        <div className="relative w-full max-w-lg rounded-2xl border border-border/50 bg-glass backdrop-blur-xl p-8 shadow-glow my-8 shrink-0">
        <div className="mb-8 flex flex-col items-center text-center gap-3">
          <div className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            <Zap className="mr-1.5 h-3.5 w-3.5" /> Comece agora
          </div>
          <div className="flex items-center gap-3 mt-2">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-glow text-primary-foreground">
              <Bot className="h-6 w-6" />
            </span>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground mt-2">Criar sua conta</h1>
            <p className="text-sm text-muted-foreground mt-1">Hermes — Inteligência Artificial</p>
          </div>
        </div>

        {resultPanel || (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-muted-foreground">
              Nome
            </Label>
            <Input
              id="name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Seu nome completo"
              className="border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-primary"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email" className="text-muted-foreground">
              E-mail
            </Label>
            <Input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              className="border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-primary"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-muted-foreground">
              Senha
            </Label>
            <Input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mínimo 6 caracteres"
              className="border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-primary"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-muted-foreground">
              Confirmar senha
            </Label>
            <Input
              id="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repita a senha"
              className="border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-primary"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="whatsapp" className="text-muted-foreground">
              WhatsApp{' '}
              <span className="text-muted-foreground/50">(opcional)</span>
            </Label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/50" />
              <Input
                id="whatsapp"
                type="tel"
                value={whatsapp}
                onChange={(e) => setWhatsapp(e.target.value)}
                placeholder="+55 11 99999-9999"
                className="border-border/50 bg-background/50 pl-10 text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-primary"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="company" className="text-muted-foreground">
              Empresa{' '}
              <span className="text-muted-foreground/50">(opcional)</span>
            </Label>
            <Input
              id="company"
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Nome da empresa"
              className="border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-primary"
            />
          </div>

          {/* Plan selection */}
          <div className="space-y-3 pt-2">
            <Label className="text-muted-foreground">Escolha seu plano</Label>
            <div className="grid grid-cols-2 gap-3">
              {plans.map((plan) => (
                <button
                  key={plan.id}
                  type="button"
                  onClick={() => setSelectedPlan(plan.id)}
                  className={`relative rounded-xl border p-4 text-left transition-all ${
                    selectedPlan === plan.id
                      ? 'border-primary bg-primary/10'
                      : 'border-border/50 bg-background/50 hover:border-primary/30'
                  }`}
                >
                  {selectedPlan === plan.id && (
                    <Check className="absolute right-2 top-2 h-4 w-4 text-primary" />
                  )}
                  <p className="font-semibold text-foreground">{plan.name}</p>
                  <p className="text-sm font-medium text-primary">{plan.price}</p>
                  {plan.subtitle && (
                    <p className="text-xs text-muted-foreground">{plan.subtitle}</p>
                  )}
                  <ul className="mt-2 space-y-1">
                    {plan.features.map((feat) => (
                      <li key={feat} className="text-xs text-muted-foreground">{feat}</li>
                    ))}
                  </ul>
                </button>
              ))}
            </div>
          </div>

          {/* CPF/CNPJ: obrigatório no plano pago (gera a cobrança), com validação dos dígitos. */}
          {needsDoc && (
            <div className="space-y-2">
              <Label htmlFor="cpf" className="text-muted-foreground">CPF ou CNPJ</Label>
              <Input
                id="cpf"
                type="text"
                autoCapitalize="characters"
                aria-required="true"
                value={cpfCnpj}
                onChange={(e) => { setCpfCnpj(formatCpfCnpj(e.target.value)); setCpfError('') }}
                onBlur={() => { if (cpfCnpj) setCpfError(cpfCnpjError(cpfCnpj) || '') }}
                placeholder="000.000.000-00 ou 00.000.000/0000-00"
                aria-invalid={!!cpfError}
                aria-describedby="cpf-help"
                className={`bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-primary ${cpfError ? 'border-destructive' : 'border-border/50'}`}
              />
              {cpfError
                ? <p id="cpf-help" className="text-xs text-destructive">{cpfError}</p>
                : <p id="cpf-help" className="text-[11px] text-muted-foreground/70">Necessário para gerar a cobrança do plano.</p>}
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="coupon" className="text-muted-foreground">
              Cupom <span className="text-muted-foreground/50">(opcional)</span>
            </Label>
            <Input
              id="coupon"
              type="text"
              value={coupon}
              onChange={(e) => setCoupon(e.target.value.toUpperCase())}
              placeholder="Tem um cupom? Digite aqui"
              className="border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus-visible:ring-primary uppercase"
            />
            {hasCoupon && (
              <p className="text-[11px] text-muted-foreground/80">
                Com cupom a conta começa no teste grátis{isPaidPlan ? ' (você assina o plano depois)' : ''}. O efeito do cupom aparece depois de criar a conta.
              </p>
            )}
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <Button
            type="submit"
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow h-11 rounded-xl mt-4"
            disabled={loading}
          >
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : needsDoc ? "Criar conta e pagar" : "Criar conta"}
          </Button>

          <div className="text-center text-sm text-muted-foreground pt-4 pb-2">
            Já tem uma conta?{" "}
            <button
              type="button"
              onClick={onLogin}
              className="font-medium text-primary hover:text-primary/80 hover:underline transition-colors"
            >
              Fazer login
            </button>
          </div>
        </form>
        )}
      </div>
      </div>
    </div>
  )
}
