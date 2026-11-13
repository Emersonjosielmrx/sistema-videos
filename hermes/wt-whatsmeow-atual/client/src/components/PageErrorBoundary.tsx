import { Component, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { sanitize } from "./ErrorBoundary";

// Rede de proteção POR TELA (fica dentro do menu/cabeçalho). Se uma tela quebrar — ou o
// arquivo dela não carregar —, o resto do painel continua de pé e a pessoa pode tentar
// de novo, recarregar ou voltar ao Painel. O ErrorBoundary de main.tsx segue como última
// linha de defesa para erros fora das telas.

type Props = { children: ReactNode; onHome: () => void };
type State = { error: Error | null };

export class PageErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: unknown) {
    console.error("[PageErrorBoundary] tela quebrou:", error, info);
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <div className="flex items-center justify-center py-16 px-4">
        <div className="max-w-md w-full text-center space-y-4 rounded-2xl border border-border/50 bg-card/40 p-6">
          <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto" />
          <h2 className="text-lg font-semibold">Esta tela não abriu</h2>
          <p className="text-sm text-muted-foreground">
            Algo deu errado ao abrir esta parte do painel. O resto continua funcionando.
          </p>
          <pre className="text-left text-xs bg-muted/30 border border-border/50 rounded-lg p-3 overflow-auto max-h-32 whitespace-pre-wrap text-muted-foreground">
            {sanitize(error.message || String(error))}
          </pre>
          <div className="flex flex-wrap gap-2 justify-center">
            <button
              onClick={() => this.setState({ error: null })}
              className="px-4 py-2 rounded-lg border border-border/60 hover:bg-muted/50 text-sm"
            >
              Tentar de novo
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-lg border border-border/60 hover:bg-muted/50 text-sm"
            >
              Recarregar a página
            </button>
            <button
              onClick={() => { this.props.onHome(); this.setState({ error: null }); }}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold"
            >
              Voltar ao Painel
            </button>
          </div>
        </div>
      </div>
    );
  }
}
