// Centraliza tratamento de erros "esperados" que eram silenciados com
// `.catch(() => {})`. P1-001: nunca engolir erro de API silenciosamente —
// pelo menos logar no console para debug. Casos onde o silêncio é
// justificável (AbortError, autoplay bloqueado, etc.) usam `silentIf()`.
//
// Use:
//   import { silentIf, logError } from "@/lib/log";
//   apiGet(...).catch(silentIf("AbortError"))    // silencia só AbortError
//   apiGet(...).catch(logError("/api/foo"))       // nunca engole, só loga

export function silentIf(...expectedNames: string[]) {
  return (err: unknown) => {
    const name = (err as { name?: string })?.name;
    if (expectedNames.includes(name ?? "")) return;
    console.warn("[non-fatal]", err);
  };
}

// Para casos onde QUEREMOS engolir tudo (ex.: service worker opcional,
// autoplay browser policy, sinkId não suportado). Loga no console.warn
// apenas em dev para não poluir prod.
export function silentAll() {
  const isDev = (import.meta as { env?: { DEV?: boolean } }).env?.DEV;
  if (isDev) {
    return (err: unknown) => console.warn("[silent]", err);
  }
  return () => {};
}

// Loga erro e repassa (não engole). Útil quando o caller vai fazer toast.error
// mas também quer rastrar no console.
export function logError(context: string) {
  return (err: unknown) => {
    console.warn(`[${context}]`, err);
  };
}
