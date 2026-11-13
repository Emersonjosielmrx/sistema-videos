import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Users, DollarSign, TrendingUp, Moon, Zap, Layers } from "lucide-react";
import { apiGet } from "@/lib/api";
import { logError } from "@/lib/log";

// ROIPanel — mostra o VALOR que a automação gera: tempo economizado, salários de
// atendentes economizados, plantão (fora do horário), agilidade, multiatendimento.
// Baseado no volume real de ligações (transcrições). Os parâmetros de cálculo são
// FIXOS (definidos por nós, não pelo cliente) — o cliente não configura isso.

type Transcript = { number: string; interested: boolean; created_at: string };

// Parâmetros FIXOS do cálculo (definidos por nós). Não expostos ao cliente.
const SALARIO_ATENDENTE = 2500;   // salário-base de referência de um atendente (R$)
const ENCARGOS_PCT = 0.70;        // 70% de encargos (FGTS, 13º, férias, impostos)
const MIN_POR_ATENDIMENTO = 6;    // minutos que um humano levaria por atendimento
const HORAS_MES = 176;            // horas úteis/mês (base do valor-hora)
const RESP_IA_SEG = 2;            // a IA responde em ~2s (base da agilidade)
const MULTI_SIMULTANEO = 30;      // ligações simultâneas que a IA aguenta (1 humano = 1)

function brl(n: number) {
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function ROIPanel() {
  const [totalCalls, setTotalCalls] = useState(0);
  const [interested, setInterested] = useState(0);
  const [afterHours, setAfterHours] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiGet<{ transcripts: Transcript[] }>("/api/transcripts?limit=200")
      .then((r) => {
        const list = r.transcripts ?? [];
        setTotalCalls(list.length);
        setInterested(list.filter((t) => t.interested).length);
        // Plantão: ligações fora do horário comercial (antes das 8h / depois das 18h / fim de semana).
        setAfterHours(list.filter((t) => {
          const d = new Date(t.created_at);
          const h = d.getHours();
          const wd = d.getDay();
          return h < 8 || h >= 18 || wd === 0 || wd === 6;
        }).length);
      })
      .catch(logError("ROIPanel"))
      .finally(() => setLoading(false));
  }, []);

  // Cálculos de ROI (parâmetros fixos acima).
  const minutosTotais = totalCalls * MIN_POR_ATENDIMENTO;      // tempo humano equivalente
  const horaBase = SALARIO_ATENDENTE / HORAS_MES;             // valor/hora
  const custoBase = (minutosTotais / 60) * horaBase;          // custo mão de obra
  const custoEncargos = custoBase * ENCARGOS_PCT;             // + encargos
  const economiaTotal = custoBase + custoEncargos;            // total economizado em salários
  // Atendentes que precisaria contratar pra esse volume (8h/dia, 22 dias).
  // Agilidade: quanto a IA responde mais rápido que um humano por atendimento.
  const agilidadeSeg = Math.max(0, MIN_POR_ATENDIMENTO * 60 - RESP_IA_SEG);
  // Custo por conversa (só o gasto de IA é irrisório; aqui mostramos o valor economizado por conversa).
  const economiaPorConversa = totalCalls > 0 ? economiaTotal / totalCalls : 0;



  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Quanto a automação já gerou de valor — em tempo e em salários — com base nas
        <strong className="text-foreground"> {totalCalls} ligações</strong> registradas.
      </p>

      {/* Métricas (5) - Exclusivas, sem duplicar o Dashboard */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <RoiCard icon={Moon} tint="text-amber-500" label="Atendimentos em plantão"
          value={loading ? "…" : String(afterHours)} sub="fora do horário comercial" />
        <RoiCard icon={Zap} tint="text-yellow-500" label="Agilidade de resposta"
          value={loading ? "…" : `${agilidadeSeg}s mais rápido`} sub="IA responde em ~2s" />
        <RoiCard icon={Layers} tint="text-sky-500" label="Multiatendimento"
          value={loading ? "…" : `${MULTI_SIMULTANEO}x`} sub="ligações ao mesmo tempo" />
        <RoiCard icon={DollarSign} tint="text-emerald-500" label="Valor por conversa"
          value={loading ? "…" : brl(economiaPorConversa)} sub="economia média por atendimento" />
        <RoiCard icon={Users} tint="text-pink-500" label="Ligações atendidas"
          value={loading ? "…" : String(totalCalls)} sub="conversas registradas pela IA" />
      </div>

      {/* Interesse gerado */}
      <Card>
        <CardContent className="p-4 flex items-center gap-3">
          <TrendingUp className="h-5 w-5 text-green-500" />
          <div>
            <p className="text-sm">
              <strong className="text-green-500">{interested}</strong> de {totalCalls} ligações geraram
              interesse{totalCalls > 0 && <> ({Math.round((interested / totalCalls) * 100)}% de conversão)</>}.
            </p>
            <p className="text-xs text-muted-foreground">A IA qualifica leads enquanto você foca no que fecha.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function RoiCard({ icon: Icon, tint, label, value, sub }: { icon: React.ElementType; tint: string; label: string; value: string; sub: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <Icon className={`h-4 w-4 ${tint}`} />
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
        <p className={`mt-1 text-2xl font-bold ${tint}`}>{value}</p>
        {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  );
}
