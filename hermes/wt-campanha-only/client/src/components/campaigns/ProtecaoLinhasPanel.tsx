import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Ban, CheckCircle2, OctagonX, RefreshCw, ShieldCheck, WifiOff, type LucideIcon } from "lucide-react";
import { apiGet } from "@/lib/api";
import { Card } from "@/components/ui/card";

// Proteção das linhas (plano do mês, item P4). Dados: GET /api/linhas/protecao
// (cmd/server/line_protection.go). Mostra, por linha da conta, o aquecimento (o teto de
// ligações por dia sobe com os dias de uso), quanto já ligou hoje, os últimos 7 dias, se
// há campanha rodando com falhas seguidas e os últimos acontecimentos (parada por risco,
// bloqueio, desconexão). Só mostra; quem decide parar é a dona.

interface Acontecimento {
  quando: string;
  tipo: string;
  texto: string;
}

interface Linha {
  session_id: string;
  nome: string;
  numero: string;
  status: string;
  situacao: string;
  dia_de_uso: number;
  nunca_usada: boolean;
  teto_hoje: number;
  ligacoes_hoje: number;
  proximo_teto: number;
  dias_para_proximo: number;
  ultimos_7_dias: number[];
  campanhas_agora: number;
  falhas_seguidas: number;
  acontecimentos: Acontecimento[];
}

interface Dados {
  teto_maximo: number;
  falhas_para_parar: number;
  linhas: Linha[];
}

// Cada situação tem ícone + nome (nunca só a cor).
const SITUACAO: Record<string, { nome: string; icone: LucideIcon; texto: string }> = {
  ok: { nome: "Tudo certo", icone: CheckCircle2, texto: "text-emerald-700 dark:text-emerald-400" },
  perto: { nome: "Perto do teto", icone: AlertTriangle, texto: "text-amber-700 dark:text-amber-400" },
  acima: { nome: "Acima do teto", icone: AlertTriangle, texto: "text-orange-700 dark:text-orange-400" },
  parada: { nome: "Parada por risco", icone: OctagonX, texto: "text-red-700 dark:text-red-400" },
  bloqueada: { nome: "Bloqueada", icone: Ban, texto: "text-red-700 dark:text-red-400" },
  desconectada: { nome: "Desconectada", icone: WifiOff, texto: "text-muted-foreground" },
  sem_numero: { nome: "Sem número", icone: WifiOff, texto: "text-muted-foreground" },
};

const diaCurto = (diasAtras: number) => {
  const d = new Date();
  d.setDate(d.getDate() - diasAtras);
  return diasAtras === 0 ? "hoje" : d.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "2-digit" });
};

const quandoFoi = (iso: string) => {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (min < 60) return `há ${Math.max(1, min)} min`;
  if (min < 48 * 60) return `há ${Math.round(min / 60)} h`;
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
};

// Últimos 7 dias: barras finas de uma série só (a altura é o número de ligações do dia).
function Ultimos7Dias({ dias, teto }: { dias: number[]; teto: number }) {
  const maior = Math.max(teto, ...dias, 1);
  const descricao = dias.map((n, i) => `${diaCurto(dias.length - 1 - i)}: ${n}`).join(", ");
  return (
    <div>
      <div className="text-[11px] text-muted-foreground mb-1">Últimos 7 dias</div>
      <div className="flex items-end gap-[2px] h-8" role="img" aria-label={`Ligações por dia, últimos 7 dias: ${descricao}`}>
        {dias.map((n, i) => (
          <div key={i} className="flex-1 h-full flex items-end" title={`${diaCurto(dias.length - 1 - i)}: ${n} ligação(ões)`}>
            <div
              className={`w-full rounded-t-[3px] ${i === dias.length - 1 ? "bg-primary" : "bg-primary/40"}`}
              style={{ height: n > 0 ? `${Math.max(8, (n / maior) * 100)}%` : "2px" }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function LinhaCard({ l, falhasParaParar }: { l: Linha; falhasParaParar: number }) {
  const s = SITUACAO[l.status] ?? SITUACAO.ok;
  const Icone = s.icone;
  const pct = l.teto_hoje > 0 ? Math.min(100, (l.ligacoes_hoje / l.teto_hoje) * 100) : 0;
  const acima = l.ligacoes_hoje - l.teto_hoje;
  // A barra fala só do uso de hoje (a situação da linha já está no selo acima).
  const barra = pct >= 100 ? "bg-orange-500" : pct >= 80 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="p-4 space-y-3">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <div className="font-medium truncate">{l.nome || "Linha"}</div>
          {l.numero && <div className="text-xs text-muted-foreground font-mono">{l.numero}</div>}
        </div>
        <span className={`inline-flex items-center gap-1.5 text-sm font-medium ${s.texto}`}>
          <Icone className="w-4 h-4" /> {s.nome}
        </span>
      </div>
      <p className="text-xs text-muted-foreground">{l.situacao}</p>

      <div className="grid gap-4 sm:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div className="space-y-2">
          <div className="flex items-baseline justify-between text-sm">
            <span>
              Hoje: <b>{l.ligacoes_hoje}</b> de {l.teto_hoje} ligações
            </span>
            {acima > 0 && <span className="text-xs text-orange-700 dark:text-orange-400">+{acima} acima</span>}
          </div>
          <div
            className="h-1.5 rounded-full bg-muted overflow-hidden"
            role="meter"
            aria-valuemin={0}
            aria-valuemax={l.teto_hoje}
            aria-valuenow={l.ligacoes_hoje}
            aria-label="Ligações de hoje em relação ao teto"
          >
            <div className={`h-full rounded-full ${barra}`} style={{ width: `${pct}%` }} />
          </div>
          <p className="text-xs text-muted-foreground">
            {l.nunca_usada
              ? "Linha ainda sem ligações: começa com o teto mais baixo."
              : `Dia ${l.dia_de_uso} de uso.`}{" "}
            {l.proximo_teto > 0
              ? `O teto sobe para ${l.proximo_teto} em ${l.dias_para_proximo} dia(s) de uso.`
              : "Já está no teto máximo."}
          </p>
          {l.campanhas_agora > 0 && (
            <p className="text-xs">
              Campanha rodando agora · falhas seguidas: <b>{l.falhas_seguidas}</b> de {falhasParaParar}
              <span className="text-muted-foreground"> (para sozinha se chegar em {falhasParaParar})</span>
            </p>
          )}
        </div>
        <Ultimos7Dias dias={l.ultimos_7_dias} teto={l.teto_hoje} />
      </div>

      {l.acontecimentos.length > 0 && (
        <div className="space-y-1">
          <div className="text-[11px] text-muted-foreground">Últimos acontecimentos</div>
          {l.acontecimentos.slice(0, 4).map((a, i) => (
            <div key={i} className="text-xs flex gap-2">
              <span className="text-muted-foreground whitespace-nowrap">{quandoFoi(a.quando)}</span>
              <span className="min-w-0">{a.texto}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function ProtecaoLinhasPanel() {
  const [dados, setDados] = useState<Dados | null>(null);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      setDados(await apiGet<Dados>("/api/linhas/protecao"));
      setErro("");
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não consegui carregar.");
    } finally {
      setCarregando(false);
    }
  }, []);
  useEffect(() => {
    carregar();
    const t = setInterval(carregar, 60000);
    return () => clearInterval(t);
  }, [carregar]);

  const atencao = dados?.linhas.filter((l) => l.status !== "ok").length ?? 0;

  return (
    <Card className="overflow-hidden">
      <div className="px-4 py-3 flex items-start justify-between gap-3 border-b border-border/50">
        <div className="flex gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-500 mt-0.5 shrink-0" />
          <div>
            <h3 className="font-semibold">Proteção das linhas</h3>
            <p className="text-xs text-muted-foreground">
              Linha nova começa com 20 ligações por dia e o teto sobe com o uso. Se {dados?.falhas_para_parar ?? 8} ligações
              seguidas falharem, a campanha para sozinha para proteger o número.
              {dados && dados.linhas.length > 0 && (atencao > 0 ? ` ${atencao} linha(s) pedem atenção.` : " Tudo certo nas linhas.")}
            </p>
          </div>
        </div>
        <button onClick={carregar} className="p-1.5 rounded-lg border border-border/50 shrink-0" title="Atualizar">
          <RefreshCw className={`w-4 h-4 ${carregando ? "animate-spin" : ""}`} />
        </button>
      </div>
      {erro && <p className="p-4 text-sm text-red-600">{erro}</p>}
      {!dados && !erro && <p className="p-4 text-sm text-muted-foreground">Carregando…</p>}
      {dados && dados.linhas.length === 0 && (
        <p className="p-4 text-sm text-muted-foreground">Nenhuma linha de WhatsApp nesta conta ainda.</p>
      )}
      {dados && dados.linhas.length > 0 && (
        <div className="divide-y divide-border/40">
          {dados.linhas.map((l) => (
            <LinhaCard key={l.session_id} l={l} falhasParaParar={dados.falhas_para_parar} />
          ))}
        </div>
      )}
    </Card>
  );
}
