// config.ts — parametros centrais da suite de QA do Hermes Call.
// Tudo que muda de ambiente fica aqui. NAO commitar segredos reais.

export const BASE_URL =
  process.env.HERMES_QA_URL || "https://hermescall.inovareinteligenciaartificial.com";

// Proxy OmniRoute (OpenAI-compat, sem auth) — usado pra verificacao semantica com visao.
// Documentado em README.md. Se cair, ver secao "Dependencias externas" do README.
export const VISION = {
  baseUrl: process.env.HERMES_QA_VISION_URL || "http://157.173.207.22:20128/v1",
  model: process.env.HERMES_QA_VISION_MODEL || "antigravity/gemini-2.5-flash",
  fallbackModels: ["antigravity/gemini-3.1-pro-low", "auto/pro-vision"],
  enabled: process.env.HERMES_QA_VISION !== "0", // HERMES_QA_VISION=0 desliga a IA (so mecanico)
};

// Planos que a suite provisiona e testa (espelha plan_features.go do backend).
// tabs = abas que o plano DEVE mostrar; o teste confirma que aparecem exatamente essas.
export const PLANS: Record<string, { label: string; tabs: string[] }> = {
  trial:       { label: "Teste Gratis 10h", tabs: ["cost", "crm", "chat", "manager_chat", "specialized", "agenda", "catalog", "calls", "meeting-ai"] },
  start_texto: { label: "Start (Texto)",    tabs: ["cost", "crm", "chat", "manager_chat", "specialized"] },
  start_voz:   { label: "Start (Voz)",      tabs: ["cost", "crm", "calls"] },
  pro:         { label: "Pro",              tabs: ["cost", "crm", "chat", "manager_chat", "specialized", "agenda", "catalog", "calls"] },
  scale:       { label: "Scale",            tabs: ["cost", "crm", "chat", "manager_chat", "specialized", "agenda", "catalog", "calls", "meeting-ai"] },
  enterprise:  { label: "Enterprise",       tabs: ["cost", "crm", "chat", "manager_chat", "specialized", "agenda", "catalog", "calls", "meeting-ai"] },
};

// Rotulos visiveis na sidebar (view -> texto EXATO com acento), pra clicar como o cliente ve.
export const TAB_LABELS: Record<string, string> = {
  cost: "Visão Geral",
  crm: "Gestão de Leads",
  chat: "Chat",
  manager_chat: "Funcionário Gestor",
  specialized: "Funcionários IA",
  agenda: "Agenda",
  catalog: "Vitrine de Produtos",
  calls: "Central de Telefonia",
  "meeting-ai": "Meet com IA",
  settings: "Configurações",
  help: "Ajuda",
};
