// O "extras" do agente (campos avançados) vem como OBJETO em /api/agents e como TEXTO JSON em
// /api/agent-profiles. Ler sempre por aqui: `perfil.extras.x` direto num texto dá undefined e a
// tela salva os padrões por cima do que estava gravado (auditoria do mês 2, F15).
export function parseExtras(raw: unknown): Record<string, any> {
  if (raw && typeof raw === "object" && !Array.isArray(raw)) return raw as Record<string, any>;
  if (typeof raw === "string" && raw.trim()) {
    try {
      const v = JSON.parse(raw);
      return v && typeof v === "object" && !Array.isArray(v) ? v : {};
    } catch {
      return {};
    }
  }
  return {};
}

// Lista (automations etc.) que pode vir como array ou como texto JSON.
export function parseList(raw: unknown): any[] {
  if (Array.isArray(raw)) return raw;
  if (typeof raw === "string" && raw.trim()) {
    try {
      const v = JSON.parse(raw);
      return Array.isArray(v) ? v : [];
    } catch {
      return [];
    }
  }
  return [];
}
