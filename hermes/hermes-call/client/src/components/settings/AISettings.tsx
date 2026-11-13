import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { ToggleField } from "@/components/ui/field";
import { CredentialSelect } from "@/components/settings/CredentialSelect";
import { updateAI, updateBudget, getAICost, type BudgetConfig } from "@/services/settings";
import { fetchAIModels, fetchDefaultPrompts, testAIKey } from "@/services/aimodels";
import { t } from "@/lib/i18n";
import { logError } from "@/lib/log";
import type { AISettings as AICfg } from "@/types/settings";
import { ShieldAlert, Zap, CheckCircle2, BrainCircuit } from "lucide-react";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { LLM_PROVIDERS as providers } from "@/constants/ai-providers";

export function AISettings({ initial, onSaved }: { initial: AICfg; onSaved: () => void }) {
  // Se o provider vier vazio, o <select> mostra a 1ª opção mas o estado fica ""
  // (busca/teste iriam com provider vazio → 400). Defaulta pra anthropic.
  const [cfg, setCfg] = useState<AICfg>({ ...initial, provider: initial.provider || "anthropic" });
  const [saving, setSaving] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testing, setTesting] = useState(false);
  // Circuit Breaker Financeiro — estado real (backend: /api/settings/budget + /api/ai-cost).
  const [budget, setBudget] = useState<BudgetConfig>({ enabled: false, monthly_brl: 0, hard_limit: true, warn_at_pct: 80 });
  const [monthSpent, setMonthSpent] = useState(0);
  const [savingBudget, setSavingBudget] = useState(false);
  // Proxies/custom nem sempre expõem o endpoint de listar modelos, então lá
  // o usuário digita o nome do modelo à mão (não bloqueia com o "Buscar").
  const isCustom = cfg.provider === "custom";

  useEffect(() => {
    if (!cfg.system_message) {
      fetchDefaultPrompts().then((p) => setCfg((c) => (c.system_message ? c : { ...c, system_message: p.ai }))).catch(logError("fetchDefaultPrompts"));
    }
    getAICost().then((c) => {
      setMonthSpent(c.month_brl || 0);
      setBudget({
        enabled: c.budget_enabled,
        monthly_brl: c.budget_monthly || 0,
        hard_limit: c.budget_hard,
        warn_at_pct: c.budget_warn_pct || 80,
      });
    }).catch(logError("AISettings"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const saveBudget = async () => {
    setSavingBudget(true);
    try {
      await updateBudget(budget);
      toast.success("Orçamento salvo");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingBudget(false);
    }
  };

  const loadModels = async () => {
    if (!cfg.api_key && !cfg.credential_id) {
      toast.error("Preencha a API Key ou selecione uma credencial primeiro");
      return;
    }
    setLoadingModels(true);
    try {
      const list = await fetchAIModels(cfg.provider, cfg.api_key, cfg.api_base_url, cfg.credential_id);
      setModels(list);
      toast.success(`${list.length} modelos encontrados`);
    } catch (e) {
      toast.error("Erro ao buscar modelos", { description: (e as Error).message });
    } finally {
      setLoadingModels(false);
    }
  };

  const testKey = async () => {
    if (!cfg.api_key) {
      toast.error("Preencha a API Key primeiro");
      return;
    }
    setTesting(true);
    try {
      const r = await testAIKey(cfg.provider, cfg.api_key, cfg.api_base_url, cfg.model);
      if (r.ok) toast.success("Chave OK! A IA respondeu.");
      else toast.error("Chave não funcionou", { description: r.error });
    } catch (e) {
      toast.error("Erro ao testar", { description: (e as Error).message });
    } finally {
      setTesting(false);
    }
  };

  const save = async () => {
    setSaving(true);
    try {
      await updateAI(cfg);
      toast.success(t("saved_success"));
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 mt-4 pb-20">
      
      {/* Principal Settings */}
      <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
        <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-sm">Cérebro Principal (IA Padrão)</h3>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant="outline" className={cn("gap-1.5 px-2", cfg.enabled ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-muted text-muted-foreground")}>
               <div className={cn("w-2 h-2 rounded-full", cfg.enabled ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground")}></div>
               {cfg.enabled ? "Cérebro Ativo" : "Desligado"}
            </Badge>
          </div>
        </div>

        <div className={cn("p-6 space-y-6 transition-opacity", !cfg.enabled && "opacity-50")}>
          <div className="flex items-center justify-between p-4 bg-background/50 rounded-xl border border-border/50">
            <div>
               <p className="font-semibold">Ativação da Inteligência</p>
               <p className="text-xs text-muted-foreground mt-0.5">Liga/desliga a IA padrão. Quando desligada, o sistema não usa IA para processar mensagens automaticamente.</p>
            </div>
            <ToggleField label="" checked={cfg.enabled} onChange={(v) => setCfg({ ...cfg, enabled: v })} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm font-semibold">Provedor de IA (Provider)</label>
              <Select options={[...providers]} value={cfg.provider} onChange={(e) => setCfg({ ...cfg, provider: e.target.value })} />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold">Credencial Vinculada</label>
              <CredentialSelect
                type="llm"
                value={cfg.credential_id ?? ""}
                onChange={(id, cred) =>
                  setCfg({
                    ...cfg,
                    credential_id: id,
                    ...(id ? { api_key: "", provider: cred?.provider || cfg.provider, api_base_url: cred?.base_url || "" } : {}),
                  })
                }
              />
            </div>
          </div>

          {/* Chave/Base URL manuais — só aparecem quando NÃO há credencial selecionada. */}
          {!cfg.credential_id && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-semibold">API Key Manual</label>
                <Input type="password" value={cfg.api_key} onChange={(e) => setCfg({ ...cfg, api_key: e.target.value })} placeholder="sk-..." className="bg-background" />
              </div>

              <div className="space-y-1">
                <label className="text-sm font-semibold">Base URL (opcional)</label>
                <Input value={cfg.api_base_url} onChange={(e) => setCfg({ ...cfg, api_base_url: e.target.value })} placeholder="deixe vazio para usar o padrão" className="bg-background" />
              </div>
            </div>
          )}

          <div className="space-y-1">
            <label className="text-sm font-semibold">Modelo de Linguagem (LLM)</label>
            <p className="text-xs text-muted-foreground mb-2">
              {isCustom ? "Proxy/custom não lista modelos automaticamente — digite o nome exato do modelo (ex: kr/claude-haiku-4.5)." : "Nome do modelo de IA. Clique em 'Buscar modelos' para listar."}
            </p>
            <div className="flex gap-2">
              {models.length > 0 && !isCustom ? (
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:ring-2 focus:ring-primary/50"
                  value={cfg.model}
                  onChange={(e) => setCfg({ ...cfg, model: e.target.value })}
                >
                  <option value="">Selecione um modelo...</option>
                  {models.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              ) : (
                <Input className="flex-1 bg-background" value={cfg.model} onChange={(e) => setCfg({ ...cfg, model: e.target.value })} placeholder={isCustom ? "digite o nome do modelo" : "clique em 'Buscar' ou digite"} />
              )}
              {!isCustom && (
                <Button type="button" variant="secondary" onClick={loadModels} disabled={loadingModels} className="shrink-0">
                  {loadingModels ? "Buscando..." : "Listar"}
                </Button>
              )}
            </div>
          </div>

          <div className="space-y-1 mt-4">
            <label className="text-sm font-semibold">System Prompt Global (Personalidade Base)</label>
            <p className="text-xs text-muted-foreground mt-1">
              Este prompt define como seus <strong>Funcionários IA</strong> (vendas, suporte, atendimento) conversam com os <strong>clientes finais</strong>. Configure aqui o tom de voz, regras de negócio e comportamento padrão que todos os bots de atendimento herdarão.
            </p>
            <Textarea rows={8} value={cfg.system_message} onChange={(e) => setCfg({ ...cfg, system_message: e.target.value })} placeholder="Você é o Hermes..." className="bg-[#0D1117] text-[#C9D1D9] border-border/50 font-mono text-sm resize-none focus:ring-primary/50 mt-2" />
          </div>
          
          <div className="pt-4 border-t border-border/50 flex items-center justify-between">
             <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Zap className="w-4 h-4 text-amber-500" /> Teste a conexão antes de salvar.
             </div>
             <div className="flex items-center gap-2">
                <Button type="button" variant="outline" onClick={testKey} disabled={testing} className="gap-2">
                  {testing ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-foreground"></span> : <CheckCircle2 className="w-4 h-4" />}
                  {testing ? "Diagnosticando..." : "Diagnóstico de Rede"}
                </Button>
                <Button onClick={save} disabled={saving} className="gap-2 shadow-glow">
                  <Zap className="w-4 h-4"/> Salvar Motor Base
                </Button>
             </div>
          </div>
        </div>
      </Card>

      {/* CONTROLE DE GASTO DA IA. (05/10: saíram daqui "Fallback em Cascata" e "Roteador Semântico",
          que só diziam "em desenvolvimento" — P3 do plano do mês.) */}
      <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
        <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-500" />
            <h3 className="font-bold text-sm">Controle de gasto da IA</h3>
          </div>
          <Badge variant="outline" className="text-[10px] bg-amber-500/10 text-amber-500 border-amber-500/20">Teto mensal</Badge>
        </div>
        
        <div className="p-6 space-y-6">
          <Accordion type="multiple" className="space-y-4">
            <AccordionItem value="circuit" className="border border-border/50 rounded-xl bg-card/50 px-4 data-[state=open]:bg-background transition-all shadow-sm">
              <AccordionTrigger className="hover:no-underline py-4">
                <div className="flex items-center gap-3">
                  <ShieldAlert className="w-5 h-5 text-rose-500" />
                  <div className="text-left">
                    <p className="text-sm font-bold">Circuit Breaker Financeiro (Capping)</p>
                    <p className="text-xs text-muted-foreground font-normal mt-0.5">Desativa IA pesada ou transborda se o custo diário estourar.</p>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="pb-4 space-y-6 pt-2">
                 <ToggleField
                   label="Ativar controle de orçamento"
                   hint="Monitora o gasto estimado de IA do mês (por tokens) e avisa/bloqueia ao atingir o teto."
                   checked={budget.enabled}
                   onChange={(v) => setBudget({ ...budget, enabled: v })}
                 />
                 <div className="space-y-3">
                   <div className="flex justify-between items-center">
                     <label className="text-sm font-bold">Teto de gasto mensal (estimado)</label>
                     <div className="text-right">
                       <span className="text-rose-500 font-mono font-bold">R$ {budget.monthly_brl.toFixed(2)}</span>
                       <p className="text-[11px] text-muted-foreground font-mono">gasto no mês: R$ {monthSpent.toFixed(2)}</p>
                     </div>
                   </div>
                   <Input
                     type="number" min={0} step={10}
                     value={budget.monthly_brl || ""}
                     onChange={(e) => setBudget({ ...budget, monthly_brl: parseFloat(e.target.value) || 0 })}
                     placeholder="Ex: 300 (0 = sem teto)"
                     disabled={!budget.enabled}
                   />
                   {budget.enabled && budget.monthly_brl > 0 && (
                     <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                       <div
                         className={`h-full ${monthSpent >= budget.monthly_brl ? "bg-rose-500" : monthSpent >= budget.monthly_brl * (budget.warn_at_pct / 100) ? "bg-amber-500" : "bg-emerald-500"}`}
                         style={{ width: `${Math.min(100, (monthSpent / budget.monthly_brl) * 100)}%` }}
                       />
                     </div>
                   )}
                 </div>
                 <div className="grid grid-cols-2 gap-3">
                   <div className="space-y-2">
                     <label className="text-xs font-bold text-muted-foreground">Avisar ao atingir (% do teto)</label>
                     <Input
                       type="number" min={1} max={100}
                       value={budget.warn_at_pct}
                       onChange={(e) => setBudget({ ...budget, warn_at_pct: parseInt(e.target.value) || 80 })}
                       disabled={!budget.enabled}
                     />
                   </div>
                   <div className="space-y-2">
                     <label className="text-xs font-bold text-muted-foreground">Ação ao estourar o teto</label>
                     <select
                       className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50"
                       value={budget.hard_limit ? "block" : "warn"}
                       onChange={(e) => setBudget({ ...budget, hard_limit: e.target.value === "block" })}
                       disabled={!budget.enabled}
                     >
                       <option value="block">Bloquear chamadas de IA (hard limit)</option>
                       <option value="warn">Só avisar o dono (não bloqueia)</option>
                     </select>
                   </div>
                 </div>
                 <Button variant="outline" size="sm" onClick={saveBudget} disabled={savingBudget}>
                   {savingBudget ? t("loading") : "Salvar orçamento"}
                 </Button>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </Card>

      <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
        <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-500" />
            <h3 className="font-bold text-sm">Permissões de Execução</h3>
          </div>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div onClick={() => setCfg({ ...cfg, allow_send_message: !cfg.allow_send_message })} className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-2 ${cfg.allow_send_message ? "border-emerald-500 bg-emerald-500/10 shadow-glow" : "border-border/50 bg-background/50"}`}>
              <CheckCircle2 className={`w-6 h-6 ${cfg.allow_send_message ? "text-emerald-500" : "text-muted"}`} />
              <div className="text-xs font-bold">Mensagens de Texto</div>
            </div>
            
            <div onClick={() => setCfg({ ...cfg, allow_send_audio: !cfg.allow_send_audio })} className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-2 ${cfg.allow_send_audio ? "border-emerald-500 bg-emerald-500/10 shadow-glow" : "border-border/50 bg-background/50"}`}>
              <CheckCircle2 className={`w-6 h-6 ${cfg.allow_send_audio ? "text-emerald-500" : "text-muted"}`} />
              <div className="text-xs font-bold">Áudios (Voz Sintética TTS)</div>
            </div>
            
            <div onClick={() => setCfg({ ...cfg, allow_send_link: !cfg.allow_send_link })} className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-2 ${cfg.allow_send_link ? "border-emerald-500 bg-emerald-500/10 shadow-glow" : "border-border/50 bg-background/50"}`}>
              <CheckCircle2 className={`w-6 h-6 ${cfg.allow_send_link ? "text-emerald-500" : "text-muted"}`} />
              <div className="text-xs font-bold">Links (com preview)</div>
            </div>
          </div>
          <p className="text-[10px] text-muted-foreground text-center mt-2">Mesmo com as chaves ligadas, o gate do administrador ainda supervisiona operações sensíveis (ex: banir clientes).</p>
        </div>
      </Card>

    </div>
  );
}
