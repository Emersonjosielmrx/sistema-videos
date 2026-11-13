import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiGet, apiPost, apiPut } from "@/lib/api";
import { RefreshCw, DollarSign, Bot, Phone, ShieldAlert } from "lucide-react";
import { Field, ToggleField } from "@/components/ui/field";

interface CostRow {
  lane: string;
  in_tokens: number;
  out_tokens: number;
  cost_brl: number;
  updated_at: string;
}

interface CostSummary {
  rows: CostRow[];
  total_brl: number;
  month_brl?: number;
  budget_enabled?: boolean;
  budget_monthly?: number;
  budget_hard?: boolean;
  budget_warn_pct?: number;
}

const laneLabels: Record<string, { label: string; icon: React.ElementType; desc: string; hint: string }> = {
  main: { label: "IA principal (chat/Telegram)", icon: Bot,
    desc: "Tokens de entrada e saída para a IA padrão.", hint: "Credencial usada para o agente responder clientes no WhatsApp, no Telegram e analisar gravações." },
  call: { label: "IA da ligação (rápida)", icon: Phone,
    desc: "Tokens de entrada e saída para a IA da ligação.", hint: "Credencial separada, mais rápida, usada só durante chamadas de voz em tempo real." },
};

function formatBRL(n: number): string {
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatTokens(n: number): string {
  if (n < 1000) return String(n);
  if (n < 1_000_000) return `${(n / 1000).toFixed(1)}k`;
  return `${(n / 1_000_000).toFixed(2)}M`;
}

export function CostPage({ hideTotalAndLimits }: { hideTotalAndLimits?: boolean }) {
  const [data, setData] = useState<CostSummary | null>(null);
  const [loading, setLoading] = useState(false);

  // Controle de orçamento (hard limit).
  const [budgetEnabled, setBudgetEnabled] = useState(false);
  const [budgetMonthly, setBudgetMonthly] = useState("");
  const [budgetHard, setBudgetHard] = useState(true);
  const [budgetWarnPct, setBudgetWarnPct] = useState("80");
  const [savingBudget, setSavingBudget] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await apiGet<CostSummary>("/api/ai-cost");
      setData(res);
      setBudgetEnabled(res.budget_enabled ?? false);
      setBudgetMonthly(res.budget_monthly ? String(res.budget_monthly) : "");
      setBudgetHard(res.budget_hard ?? true);
      setBudgetWarnPct(String(res.budget_warn_pct || 80));
    } catch (e) {
      console.error("Erro ao carregar custos:", e);
      // Removed toast to prevent spam
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const saveBudget = async () => {
    setSavingBudget(true);
    try {
      await apiPut("/api/settings/budget", {
        enabled: budgetEnabled,
        monthly_brl: parseFloat(budgetMonthly) || 0,
        hard_limit: budgetHard,
        warn_at_pct: parseInt(budgetWarnPct) || 80,
      });
      toast.success("Controle de custos salvo");
      load();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingBudget(false);
    }
  };

  const reset = async () => {
    if (!confirm("Zerar o contador de custo? (os valores voltarão a R$ 0,00)")) return;
    try {
      await apiPost("/api/ai-cost/reset", {});
      toast.success("Contador zerado");
      load();
    } catch {
      toast.error("Erro ao zerar contador");
    }
  };

  const rows = data?.rows ?? [];
  const total = data?.total_brl ?? 0;

  return (
    <div className={`flex h-full flex-col gap-4 ${hideTotalAndLimits ? 'p-0 pt-2' : 'p-6'}`}>
      {!hideTotalAndLimits && (
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-background to-background border border-primary/20 p-4 shadow-glow flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
          <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
            <DollarSign className="w-16 h-16 text-primary" />
          </div>
          <div className="relative z-10 flex items-center gap-3">
            <div className="hidden sm:flex items-center justify-center p-2 bg-primary/10 rounded-xl border border-primary/20 shadow-glow shrink-0">
              <DollarSign className="w-6 h-6 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-primary/50 drop-shadow-sm">
                  Custos de IA
                </h2>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Quanto cada credencial de IA gastou, em reais (R$). Atualizado em tempo real.
              </p>
            </div>
          </div>
          <div className="relative z-10 flex items-center gap-2 shrink-0">
            <Button variant="outline" size="sm" onClick={load} disabled={loading} className="rounded-xl bg-background shadow-sm">
              <RefreshCw className={loading ? "h-4 w-4 animate-spin mr-2" : "h-4 w-4 mr-2"} /> Atualizar
            </Button>
            <Button variant="outline" size="sm" onClick={reset} className="rounded-xl text-destructive hover:bg-destructive/10 border-destructive/20 shadow-sm">Zerar</Button>
          </div>
        </div>
      )}

      {!hideTotalAndLimits && (
        <Card className="p-6 bg-gradient-to-br from-primary/10 to-primary/5 rounded-2xl border-primary/20 shadow-glow relative overflow-hidden group">
          <div className="absolute right-[-20px] top-[-20px] opacity-10 group-hover:scale-110 transition-transform duration-500 pointer-events-none">
             <DollarSign className="w-32 h-32 text-primary" />
          </div>
          <div className="text-sm font-semibold text-muted-foreground relative z-10">Total acumulado da conta</div>
          <div className="text-5xl font-black text-primary relative z-10 drop-shadow-sm my-1">{formatBRL(total)}</div>
          <div className="text-xs text-muted-foreground relative z-10 font-medium">Soma de todas as faixas e módulos rodando em segundo plano.</div>
        </Card>
      )}

      {/* Controle rígido de custos (hard limit) */}
      {!hideTotalAndLimits && (
        <Card className="p-6 space-y-4 border-amber-500/30 bg-gradient-to-br from-amber-500/10 to-background rounded-2xl shadow-glow">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-amber-500/20 rounded-xl">
              <ShieldAlert className="h-5 w-5 text-amber-500 drop-shadow-sm" />
            </div>
            <h3 className="text-lg font-bold">Controle e Teto de Gastos (Hard Limit)</h3>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed max-w-3xl">
            Define um teto de gasto estimado de IA por mês. Com o bloqueio ligado, ao atingir o teto o sistema
            <strong className="text-foreground"> pausa as chamadas de IA</strong> até o próximo mês — evitando prejuízos imprevisíveis.
          </p>

          {/* Barra de progresso do gasto do mês vs. teto */}
          {budgetEnabled && parseFloat(budgetMonthly) > 0 && (() => {
            const month = data?.month_brl ?? 0;
            const limit = parseFloat(budgetMonthly) || 0;
            const pct = limit > 0 ? Math.min(100, Math.round((month / limit) * 100)) : 0;
            const barColor = pct >= 100 ? "bg-red-500" : pct >= (parseInt(budgetWarnPct) || 80) ? "bg-amber-500" : "bg-primary";
            return (
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Gasto do mês</span>
                  <span className="font-medium">{formatBRL(month)} / {formatBRL(limit)} ({pct}%)</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div className={`h-full ${barColor} transition-all`} style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })()}

          <ToggleField
            label="Ativar limite de gasto mensal"
            hint="Liga o controle de orçamento. Desligado, não há teto (gasto livre)."
            checked={budgetEnabled}
            onChange={setBudgetEnabled}
          />

          {budgetEnabled && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Field label="Teto mensal (R$)" hint="Gasto estimado máximo de IA por mês, em reais.">
                <Input
                  type="number"
                  min="0"
                  step="1"
                  value={budgetMonthly}
                  onChange={(e) => setBudgetMonthly(e.target.value)}
                  placeholder="Ex.: 200"
                  className="rounded-xl border-border/50 bg-background"
                />
              </Field>
              <Field label="Avisar em (% do teto)" hint="A que % do limite você recebe o aviso no Telegram. Padrão: 80%.">
                <Input
                  type="number"
                  min="1"
                  max="100"
                  value={budgetWarnPct}
                  onChange={(e) => setBudgetWarnPct(e.target.value)}
                  placeholder="80"
                  className="rounded-xl border-border/50 bg-background"
                />
              </Field>
              <div className="sm:col-span-2">
                <ToggleField
                  label="Bloquear ao atingir o teto (hard limit)"
                  hint="Ligado: ao chegar no teto, a IA para de responder até o mês virar. Desligado: só avisa, mas continua gastando."
                  checked={budgetHard}
                  onChange={setBudgetHard}
                />
              </div>
            </div>
          )}

          <div className="pt-2">
            <Button size="sm" onClick={saveBudget} disabled={savingBudget} className="rounded-xl px-6 shadow-glow">
              {savingBudget ? "Salvando…" : "Salvar controle de custos"}
            </Button>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {["main", "call"].map((lane) => {
          const row = rows.find((r) => r.lane === lane);
          const meta = laneLabels[lane];
          const Icon = meta.icon;
          return (
            <Card key={lane} className="p-5 space-y-4 rounded-2xl shadow-soft hover:shadow-glow transition-all hover:-translate-y-1 border-border/50 group bg-card">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-xl group-hover:bg-primary/20 transition-colors">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-bold">{meta.label}</h3>
                </div>
                <div className="text-2xl font-black text-foreground drop-shadow-sm">{formatBRL(row?.cost_brl ?? 0)}</div>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{meta.hint}</p>
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border/50">
                <div className="bg-muted/30 p-3 rounded-xl border border-border/30">
                  <div className="text-[10px] uppercase font-bold text-muted-foreground">Entrada (Tokens)</div>
                  <div className="text-sm font-mono font-bold mt-0.5">{formatTokens(row?.in_tokens ?? 0)}</div>
                </div>
                <div className="bg-muted/30 p-3 rounded-xl border border-border/30">
                  <div className="text-[10px] uppercase font-bold text-muted-foreground">Saída (Tokens)</div>
                  <div className="text-sm font-mono font-bold mt-0.5">{formatTokens(row?.out_tokens ?? 0)}</div>
                </div>
              </div>
              {row?.updated_at && (
                <div className="text-[10px] font-semibold text-muted-foreground/60 text-right uppercase tracking-wider">
                  Última atulização: {new Date(row.updated_at).toLocaleString("pt-BR")}
                </div>
              )}
            </Card>
          );
        })}
      </div>

    </div>
  );
}
