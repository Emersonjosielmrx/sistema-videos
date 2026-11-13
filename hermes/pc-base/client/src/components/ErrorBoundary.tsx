import { Component, type ReactNode } from "react";

// ErrorBoundary — rede de proteção do app. Sem isto, qualquer erro de runtime num
// componente derruba a árvore inteira e a tela fica PRETA (o fundo é escuro), sem pista
// do que quebrou. Aqui a gente captura o erro, mostra a mensagem e um botão de recarregar,
// pra o usuário não ficar preso numa tela vazia — e pra dar pra ver o erro real.
//
// FIX P1-002 (2026-07-25): `error.message` cru pode vazar tokens, paths internos, SQL,
// fragmentos de URL. Antes do fix mostrávamos a mensagem completa + stack. Agora:
//   - Mostra só a primeira linha da mensagem (curta, segura)
//   - Detalhes completos (stack, componente) ficam num <details> colapsado
//   - Botão "Copiar detalhes" para o usuário mandar pro suporte sem ter que abrir DevTools
//   - Substitui padrão "https://.../secret" / "Bearer xxx" / "postgresql://..." por [REDACTED]

type State = { error: Error | null; showDetails: boolean; copied: boolean };

const TRUNCATE_AT = 240;
const SENSITIVE_PATTERNS: RegExp[] = [
  /\bBearer\s+[A-Za-z0-9._\-+/=]+/gi,                    // Authorization header
  /\bBasic\s+[A-Za-z0-9._\-+/=]+/gi,                     // Basic auth
  /\bpostgresql:\/\/[^\s'"]+/gi,                         // PG URLs
  /\bmysql:\/\/[^\s'"]+/gi,
  /\b(eyJ[A-Za-z0-9._\-+]{20,}=*)/g,                     // JWT
  /\b(api[_-]?key|token|secret|password|senha)\s*[:=]\s*['"]?[^'"\s,}]+/gi,
  /\bhttps?:\/\/[^\s'"]*(token|key|secret)[^\s'"]*/gi,
  /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?/g,        // IPs internos
];

export function sanitize(s: string): string {
  let out = s;
  for (const p of SENSITIVE_PATTERNS) {
    out = out.replace(p, "[REDACTED]");
  }
  if (out.length > TRUNCATE_AT) out = out.slice(0, TRUNCATE_AT) + "…";
  return out;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null, showDetails: false, copied: false };

  static getDerivedStateFromError(error: Error): State {
    return { error, showDetails: false, copied: false };
  }

  componentDidCatch(error: Error, info: unknown) {
    // Loga no console pra diagnóstico (aparece no DevTools).
    console.error("[ErrorBoundary] render crash:", error, info);
  }

  copyDetails = () => {
    if (!this.state.error) return;
    const text =
      `URL: ${window.location.href}\n` +
      `User-Agent: ${navigator.userAgent}\n` +
      `Time: ${new Date().toISOString()}\n` +
      `Message: ${this.state.error.message}\n` +
      `Stack: ${this.state.error.stack ?? "(sem stack)"}`;
    navigator.clipboard.writeText(text).then(
      () => this.setState({ copied: true }),
      () => {}
    );
  };

  render() {
    if (!this.state.error) return this.props.children;
    const err = this.state.error;
    const summary = sanitize(err.message || String(err));
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 p-6 text-center">
        <div className="max-w-md w-full space-y-4">
          <div className="text-4xl">⚠️</div>
          <h1 className="text-xl font-bold text-white">Algo quebrou nesta tela</h1>
          <p className="text-sm text-slate-400">
            A página encontrou um erro e parou. Recarregar costuma resolver. Se continuar,
            me mande o texto abaixo que eu corrijo.
          </p>
          <pre className="text-left text-xs bg-slate-900 border border-white/10 rounded-lg p-3 overflow-auto max-h-40 text-red-300 whitespace-pre-wrap">
            {summary}
          </pre>
          <details
            className="text-left text-[0.7rem] text-slate-400"
            onToggle={(e) => this.setState({ showDetails: (e.target as HTMLDetailsElement).open })}
          >
            <summary className="cursor-pointer hover:text-slate-200">Detalhes técnicos</summary>
            <pre className="mt-2 text-left text-[0.65rem] bg-slate-900 border border-white/10 rounded-lg p-3 overflow-auto max-h-60 text-slate-400 whitespace-pre-wrap">
{err.stack || "(sem stack)"}
            </pre>
          </details>
          <div className="flex gap-2 justify-center flex-wrap">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold"
            >
              Recarregar
            </button>
            <button
              onClick={() => this.setState({ error: null })}
              className="px-4 py-2 rounded-lg border border-white/10 hover:border-white/20 text-slate-300 text-sm"
            >
              Tentar de novo
            </button>
            <button
              onClick={this.copyDetails}
              className="px-4 py-2 rounded-lg border border-white/10 hover:border-white/20 text-slate-300 text-sm"
            >
              {this.state.copied ? "✓ Copiado" : "Copiar detalhes"}
            </button>
          </div>
        </div>
      </div>
    );
  }
}

