import { apiGet, apiPost, apiErrorMessage, apiErrorStatus, apiErrorBody } from "@/lib/api";

// Cobrança (Asaas) — rotas do servidor:
//   GET  /api/billing               situação da assinatura
//   POST /api/billing/subscribe     {plan, cpf_cnpj} → {invoice_url?}
//   POST /api/billing/check         consulta o pagamento agora → {status, invoice_url?}
//   POST /api/billing/coupon        {coupon} → {ok, applied, effect:"trial_extended", trial_until, message}
//                                   erro: {error: coupon_required|invalid_coupon|coupon_not_applicable|coupon_already_used, message}
//   POST /api/billing/change-plan   {plan} → {invoice_url?, plan, previous_plan, applied_now, effective?, message} | {unchanged}
//                                   applied_now:false + effective "on_payment" (vale quando o pagamento
//                                   confirmar) ou "next_cycle" (vale no próximo ciclo).
//   POST /api/billing/cancel        → {ok}                         (novo)
// As chaves de plano são as mesmas da assinatura: "basic" (Start), "pro", "scale".

export type BillingInfo = {
  plan_code?: string;
  plan_name?: string;
  plan_value?: string;
  status?: string; // active | pending | overdue | cancelled | ...
  invoice_url?: string;
  coupon?: string;
  has_asaas?: boolean; // já tem assinatura no Asaas (logo, já tem cliente com CPF/CNPJ)
  has_customer?: boolean; // já tem cliente no Asaas (CPF/CNPJ guardado), se o servidor informar
  member_since?: string;
};

export const PAID_PLANS = [
  { id: "basic", name: "Start", price: "R$199/mês" },
  { id: "pro", name: "Pro", price: "R$399/mês" },
  { id: "scale", name: "Scale", price: "R$599/mês" },
];

export const getBilling = () => apiGet<BillingInfo>("/api/billing");

// O servidor já tem o CPF/CNPJ desta conta (não precisa pedir de novo para assinar).
export const hasDocOnFile = (b?: BillingInfo | null): boolean => !!(b?.has_customer || b?.has_asaas);

export const checkBilling = () => apiPost<{ status?: string; invoice_url?: string }>("/api/billing/check", {});

export const subscribePlan = (plan: string, cpfCnpj: string) =>
  apiPost<{ invoice_url?: string; status?: string }>("/api/billing/subscribe", { plan, cpf_cnpj: cpfCnpj });

export type ChangePlanResult = {
  ok?: boolean;
  invoice_url?: string; // cobrança nova (abre em outra aba)
  plan?: string; // plano novo
  previous_plan?: string;
  status?: string; // assinatura nova volta "pending" (falta pagar)
  applied_now?: boolean; // true = já valeu; false = ainda NÃO valeu (ver effective)
  effective?: "on_payment" | "next_cycle" | string; // quando a troca passa a valer
  unchanged?: boolean; // já estava neste plano
  message?: string;
  error?: string;
};

export const changePlan = (plan: string) => apiPost<ChangePlanResult>("/api/billing/change-plan", { plan });

export const cancelSubscription = () => apiPost<{ ok?: boolean; error?: string }>("/api/billing/cancel", {});

// Abre a página de pagamento numa NOVA aba (o painel continua aberto e fica conferindo
// o pagamento). Antes o painel trocava a própria página pelo checkout e a pessoa saía do app.
export const openInvoice = (url: string) => {
  window.open(url, "_blank", "noopener,noreferrer");
};

// Cupom: o servidor diz o que aconteceu (ex.: "Teste estendido até 09/10").
// Só repetimos o que ele respondeu — nunca afirmamos "aplicado" por conta própria.
const COUPON_ERRORS: Record<string, string> = {
  coupon_required: "Digite o cupom.",
  invalid_coupon: "Cupom inválido ou expirado.",
  coupon_not_applicable: "Este cupom não vale para a sua conta.",
  coupon_already_used: "Este cupom já foi usado.",
};

const fmtDay = (iso?: string) => {
  const d = iso ? new Date(iso) : null;
  return d && !isNaN(d.getTime()) ? d.toLocaleDateString("pt-BR") : "";
};

export async function applyCoupon(code: string): Promise<{ accepted: boolean; message: string }> {
  try {
    const r = await apiPost<{ ok?: boolean; applied?: boolean; effect?: string; trial_until?: string; message?: string; error?: string }>(
      "/api/billing/coupon",
      { coupon: code.trim() },
    );
    const accepted = r.ok !== false && r.applied !== false;
    const until = fmtDay(r.trial_until);
    const message =
      (typeof r.message === "string" && r.message.trim()) ||
      (r.effect === "trial_extended" && until ? `Teste grátis estendido até ${until}.` : "") ||
      (r.applied === true ? "Cupom aplicado." : r.applied === false ? "Cupom registrado, mas o servidor não informou nenhum efeito." : "Cupom aceito.");
    return { accepted, message };
  } catch (e) {
    const body = apiErrorBody(e);
    const msg = typeof body?.message === "string" && body.message.trim() ? body.message.trim() : "";
    if (msg) return { accepted: false, message: msg };
    const code = typeof body?.error === "string" ? body.error : "";
    if (COUPON_ERRORS[code]) return { accepted: false, message: COUPON_ERRORS[code] };
    if (code.includes(" ")) return { accepted: false, message: code }; // texto legível em "error"
    if (apiErrorStatus(e) === null) return { accepted: false, message: "Não consegui falar com o servidor para validar o cupom." };
    return { accepted: false, message: "Não consegui validar o cupom agora." };
  }
}

// Texto amigável para falhas de cobrança.
export function billingErrorMessage(e: unknown, fallback = "Não consegui gerar a cobrança. Tente de novo."): string {
  const status = apiErrorStatus(e);
  if (status === 503) return "Pagamento online indisponível no momento. Fale com o suporte pelo WhatsApp.";
  if (status === 404 || status === 405) return "Esta opção ainda não está disponível. Fale com o suporte pelo WhatsApp.";
  const msg = apiErrorMessage(e, "");
  return msg && msg.includes(" ") ? msg : fallback;
}
