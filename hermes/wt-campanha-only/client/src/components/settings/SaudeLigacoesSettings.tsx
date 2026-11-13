import { useCallback, useEffect, useState } from "react";
import { Activity, PhoneIncoming, PhoneOutgoing, RefreshCw } from "lucide-react";
import { apiGet } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Saúde das ligações (só a dona da plataforma). Dados: GET /api/admin/saude-ligacoes
// (cmd/server/call_health.go). Cada ligação com áudio guarda a qualidade do som nos dois
// sentidos e o tempo de cada resposta da IA. Serve pra saber se a ligação piorou sem
// abrir o registro do servidor.

interface Qualidade {
  rx_perda_pct: number;
  rx_fora_ordem: number;
  rx_buracos: number;
  rx_jitter_ms: number;
  tx_buracos: number;
  tx_maior_buraco_ms: number;
}

interface Voz {
  turnos: number;
  latencia_media_ms: number;
  latencia_max_ms: number;
  interrupcoes: number;
  esperas_longas: number;
  transcricoes_antecipadas: number;
}

interface Ligacao {
  call_id: string;
  direcao: string;
  numero: string;
  terminou_em: string;
  duracao_s: number;
  resultado: string;
  qualidade: Qualidade;
  voz?: Voz;
}

interface Resumo {
  ligacoes: number;
  com_cortes: number;
  pct_com_cortes: number;
  latencia_media_ms: number;
  latencia_p90_ms: number;
  respostas_medidas: number;
  interrupcoes: number;
  esperas_longas: number;
  perda_media_pct: number;
  buracos_no_envio: number;
  transcricoes_antecipadas: number;
}

interface Dados {
  dias: number;
  resumo: Resumo;
  ligacoes: Ligacao[];
}

const segundos = (ms: number) => (ms / 1000).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " s";

// Meta do plano: até 2,5 s do fim da fala do cliente até a voz da IA.
const corDaLatencia = (ms: number) => (ms === 0 ? "text-muted-foreground" : ms <= 2500 ? "text-emerald-600" : ms <= 3500 ? "text-amber-600" : "text-red-600");

function Numero({ titulo, valor, detalhe, cor }: { titulo: string; valor: string; detalhe?: string; cor?: string }) {
  return (
    <Card className="bg-glass border-border/50 shadow-soft p-4">
      <div className="text-xs text-muted-foreground">{titulo}</div>
      <div className={`text-2xl font-bold mt-1 ${cor ?? ""}`}>{valor}</div>
      {detalhe && <div className="text-xs text-muted-foreground mt-1">{detalhe}</div>}
    </Card>
  );
}

export function SaudeLigacoesSettings() {
  const [dias, setDias] = useState(7);
  const [dados, setDados] = useState<Dados | null>(null);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro("");
    try {
      setDados(await apiGet<Dados>(`/api/admin/saude-ligacoes?dias=${dias}`));
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não consegui carregar.");
    } finally {
      setCarregando(false);
    }
  }, [dias]);
  useEffect(() => { carregar(); }, [carregar]);

  const r = dados?.resumo;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex gap-3">
          <Activity className="w-5 h-5 text-emerald-500 mt-1 shrink-0" />
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Saúde das ligações</h2>
            <p className="text-muted-foreground text-sm mt-1 max-w-2xl">
              Cada ligação atendida guarda a qualidade do som e quanto a IA demorou pra responder. A meta é responder em até
              2,5 s depois que o cliente para de falar.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {[1, 7, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDias(d)}
              className={`text-xs px-3 py-1.5 rounded-lg border ${dias === d ? "bg-primary text-primary-foreground border-primary" : "border-border/50"}`}
            >
              {d === 1 ? "Hoje" : `${d} dias`}
            </button>
          ))}
          <button onClick={carregar} className="p-1.5 rounded-lg border border-border/50" title="Atualizar">
            <RefreshCw className={`w-4 h-4 ${carregando ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {!dados && !erro && <p className="text-sm text-muted-foreground">Carregando…</p>}

      {r && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Numero titulo="Ligações com áudio" valor={String(r.ligacoes)} />
          <Numero
            titulo="Com cortes no som"
            valor={`${r.pct_com_cortes.toLocaleString("pt-BR")}%`}
            detalhe={`${r.com_cortes} de ${r.ligacoes}`}
            cor={r.pct_com_cortes > 20 ? "text-red-600" : r.pct_com_cortes > 5 ? "text-amber-600" : "text-emerald-600"}
          />
          <Numero
            titulo="Tempo médio de resposta"
            valor={r.respostas_medidas ? segundos(r.latencia_media_ms) : "—"}
            detalhe={r.respostas_medidas ? `9 em cada 10 até ${segundos(r.latencia_p90_ms)}` : "nenhuma resposta medida"}
            cor={corDaLatencia(r.latencia_media_ms)}
          />
          <Numero
            titulo="IA demorou e disse “um instante”"
            valor={String(r.esperas_longas)}
            detalhe={`${r.interrupcoes} interrupções do cliente`}
            cor={r.esperas_longas > 0 ? "text-amber-600" : undefined}
          />
        </div>
      )}

      {r && r.ligacoes > 0 && (
        <Card className="bg-glass border-border/50 shadow-soft p-4 text-xs text-muted-foreground space-y-1">
          <p>
            <b>De onde vêm os cortes:</b> perda média de {r.perda_media_pct.toLocaleString("pt-BR")}% no que chega do cliente
            (rede dele) e {r.buracos_no_envio} buraco(s) no que o servidor manda (problema nosso, se for maior que zero).
          </p>
          <p>Transcrições adiantadas aproveitadas (deixam a resposta mais rápida): {r.transcricoes_antecipadas}.</p>
        </Card>
      )}

      {dados && dados.ligacoes.length > 0 && (
        <Card className="bg-glass border-border/50 shadow-soft overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-muted-foreground border-b border-border/50">
              <tr>
                <th className="text-left p-3">Quando</th>
                <th className="text-left p-3">Número</th>
                <th className="text-right p-3">Duração</th>
                <th className="text-left p-3">Som</th>
                <th className="text-right p-3">Resposta (média / pior)</th>
                <th className="text-right p-3">Interrupções</th>
              </tr>
            </thead>
            <tbody>
              {dados.ligacoes.map((l) => (
                <tr key={l.call_id} className="border-b border-border/30 last:border-0">
                  <td className="p-3 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5">
                      {l.direcao === "entrada" ? <PhoneIncoming className="w-3.5 h-3.5" /> : <PhoneOutgoing className="w-3.5 h-3.5" />}
                      {new Date(l.terminou_em).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-xs">{l.numero}</td>
                  <td className="p-3 text-right">{Math.floor(l.duracao_s / 60)}:{String(l.duracao_s % 60).padStart(2, "0")}</td>
                  <td className="p-3">
                    <Badge
                      variant="outline"
                      className={`whitespace-nowrap ${l.resultado === "boa" ? "text-emerald-600 border-emerald-600/40" : "text-red-600 border-red-600/40"}`}
                      title={`perda ${l.qualidade.rx_perda_pct}% · fora de ordem ${l.qualidade.rx_fora_ordem} · buracos no envio ${l.qualidade.tx_buracos}`}
                    >
                      {l.resultado}
                    </Badge>
                  </td>
                  <td className={`p-3 text-right whitespace-nowrap ${corDaLatencia(l.voz?.latencia_media_ms ?? 0)}`}>
                    {l.voz && l.voz.turnos > 0 ? `${segundos(l.voz.latencia_media_ms)} / ${segundos(l.voz.latencia_max_ms)}` : "—"}
                  </td>
                  <td className="p-3 text-right">{l.voz?.interrupcoes ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {dados && dados.ligacoes.length === 0 && (
        <p className="text-sm text-muted-foreground">Nenhuma ligação com áudio no período.</p>
      )}
    </div>
  );
}
