import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Rocket, Clock, MessageSquare, Save, Settings, Megaphone, Target, PenTool, Flame, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { apiPost } from "@/lib/api";

// Converte o "timing" do wizard em horas (o backend de sequências guarda delay_hours).
const timingToHours = (t: string): number => {
  switch (t) {
    case "15m": return 0; // < 1h: o cron trata 0 como "assim que possível na próxima passada"
    case "2h": return 2;
    case "24h": return 24;
    case "7d": return 24 * 7;
    case "30d": return 24 * 30;
    default: return 24;
  }
};

// Mapeia o evento do wizard pro gatilho do backend (trigger_type + trigger_value).
const eventToTrigger = (ev: string): { type: string; value: string } => {
  switch (ev) {
    case "no_response": return { type: "call_status", value: "no_answer" };
    case "abandoned_cart": return { type: "tag", value: "carrinho_abandonado" };
    case "post_sale": return { type: "pipeline_stage", value: "pos_venda" };
    case "time_based": return { type: "tag", value: "followup" };
    default: return { type: "tag", value: "followup" };
  }
};

export const EasyFollowUpWizard = () => {
  const [activeTab, setActiveTab] = useState<"templates" | "triggers" | "advanced">("templates");
  const [saving, setSaving] = useState(false);

  const [state, setState] = useState({
    enabled: true,
    timing: "24h",
    triggerEvent: "no_response",
    messageTemplate: "Oi! Tudo bem? Fiquei aguardando seu retorno. Conseguimos dar sequência hoje?",
    stopOnReply: true,
    smartDelay: true,
    escalatePressure: false,
  });

  const updateState = (key: keyof typeof state, value: any) => {
    setState(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    if (!state.messageTemplate.trim()) { toast.error("Escreva a mensagem do follow-up primeiro."); return; }
    setSaving(true);
    const trig = eventToTrigger(state.triggerEvent);
    const baseHours = timingToHours(state.timing);
    // Monta as etapas: a 1ª sempre; se "escalonamento de pressão" estiver ligado,
    // adiciona uma 2ª etapa mais agressiva/urgente algum tempo depois.
    const steps: { delay_hours: number; channel: string; message: string }[] = [
      { delay_hours: baseHours, channel: "whatsapp_text", message: state.messageTemplate },
    ];
    if (state.escalatePressure) {
      steps.push({
        delay_hours: baseHours + 24,
        channel: "whatsapp_text",
        message: "Última chance! Não quero que você perca essa condição. Consigo segurar sua vaga só até hoje — posso confirmar?",
      });
    }
    const seq = {
      name: `Follow-Up Fácil (${state.timing}, ${state.triggerEvent})`,
      trigger_type: trig.type,
      trigger_value: trig.value,
      business_hours_only: state.smartDelay,
      stop_on_reply: state.stopOnReply,
      active: state.enabled,
      steps,
    };
    try {
      await apiPost("/api/followup/sequences", seq);
      toast.success("Follow-Up Automático ativado! Confira na aba Follow-Up.");
    } catch (e) {
      toast.error("Erro ao salvar", { description: (e as Error).message });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20 shadow-[0_0_30px_rgba(245,158,11,0.15)] relative overflow-hidden">
        <div className="absolute -right-10 -top-10 opacity-10 pointer-events-none">
          <Clock className="w-40 h-40 text-amber-500" />
        </div>
        <div className="flex items-center gap-4 relative z-10">
          <div className="bg-amber-500/20 p-3 rounded-xl border border-amber-500/30">
            <Megaphone className="h-8 w-8 text-amber-500" />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-orange-400 drop-shadow-sm">
              Follow-Up & Retargeting Fácil
            </h2>
            <p className="text-sm text-amber-500/80 font-medium">Recupere leads perdidos automaticamente sem esforço.</p>
          </div>
        </div>
        <div className="flex items-center gap-3 relative z-10">
           <span className="text-sm font-semibold text-muted-foreground">Status do Motor</span>
           <Switch checked={state.enabled} onCheckedChange={c => updateState("enabled", c)} className="data-[state=checked]:bg-amber-500" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1 bg-black/20 backdrop-blur-md rounded-xl border border-border/50">
        <button 
          onClick={() => setActiveTab("templates")}
          className={cn("flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2", activeTab === "templates" ? "bg-amber-500/20 text-amber-400 shadow-sm border border-amber-500/30" : "text-muted-foreground hover:bg-white/5")}
        >
          <MessageSquare className="h-4 w-4" /> 1. A Mensagem
        </button>
        <button 
          onClick={() => setActiveTab("triggers")}
          className={cn("flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2", activeTab === "triggers" ? "bg-amber-500/20 text-amber-400 shadow-sm border border-amber-500/30" : "text-muted-foreground hover:bg-white/5")}
        >
          <Target className="h-4 w-4" /> 2. O Gatilho
        </button>
        <button 
          onClick={() => setActiveTab("advanced")}
          className={cn("flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2", activeTab === "advanced" ? "bg-amber-500/20 text-amber-400 shadow-sm border border-amber-500/30" : "text-muted-foreground hover:bg-white/5")}
        >
          <Settings className="h-4 w-4" /> 3. Regras (Avançado)
        </button>
      </div>

      {/* Content */}
      <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft">
        
        {activeTab === "templates" && (
          <div className="space-y-6 animate-in slide-in-from-left-4">
            <div>
              <h3 className="text-xl font-bold mb-1 flex items-center gap-2"><PenTool className="h-5 w-5 text-amber-500"/> O que o Agente vai dizer?</h3>
              <p className="text-muted-foreground text-sm">Crie a mensagem que será enviada para "acordar" o cliente.</p>
            </div>
            
            <div className="space-y-3">
              <label className="text-sm font-medium">Template Base (Spintax suportado)</label>
              <Textarea 
                value={state.messageTemplate}
                onChange={e => updateState("messageTemplate", e.target.value)}
                className="min-h-[120px] bg-background/50 border-amber-500/30 focus-visible:ring-amber-500"
                placeholder="Oi {{nome}}! Fiquei aguardando seu retorno..."
              />
              <p className="text-xs text-muted-foreground flex items-center gap-1"><Rocket className="h-3 w-3" /> Dica: Use <b>{'{nome}'}</b> para puxar o nome do contato.</p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              <Button variant="outline" className="text-xs h-8 border-dashed" onClick={() => updateState("messageTemplate", "Oi {nome}! Sumiu? Queria saber se conseguimos fechar aquela proposta hoje.")}>Use: Retenção Agressiva</Button>
              <Button variant="outline" className="text-xs h-8 border-dashed" onClick={() => updateState("messageTemplate", "Tudo bem por aí? Vi que não nos falamos mais. Posso te ajudar em algo que ficou pendente?")}>Use: Consultivo Suave</Button>
            </div>
          </div>
        )}

        {activeTab === "triggers" && (
          <div className="space-y-6 animate-in slide-in-from-left-4">
            <div>
              <h3 className="text-xl font-bold mb-1 flex items-center gap-2"><Clock className="h-5 w-5 text-amber-500"/> Quando disparar?</h3>
              <p className="text-muted-foreground text-sm">Defina o comportamento temporal para ativar este disparo.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium">Condição (Evento)</label>
                <select className="flex h-12 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm focus-visible:ring-amber-500" value={state.triggerEvent} onChange={e => updateState("triggerEvent", e.target.value)}>
                  <option value="no_response">Cliente ignorou a última mensagem (Vácuo)</option>
                  <option value="abandoned_cart">Abandono de Carrinho (API)</option>
                  <option value="post_sale">Pós-venda (Pesquisa de Satisfação)</option>
                  <option value="time_based">Apenas por Tempo (Máquina do Tempo)</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Esperar quanto tempo?</label>
                <select className="flex h-12 w-full rounded-md border border-input bg-background/50 px-3 py-1 text-sm focus-visible:ring-amber-500" value={state.timing} onChange={e => updateState("timing", e.target.value)}>
                  <option value="15m">15 minutos (Agressivo)</option>
                  <option value="2h">2 horas</option>
                  <option value="24h">24 horas (Recomendado)</option>
                  <option value="7d">7 dias (Re-engajamento)</option>
                  <option value="30d">30 dias (Máquina do Tempo)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {activeTab === "advanced" && (
          <div className="space-y-6 animate-in slide-in-from-left-4">
            <div>
              <h3 className="text-xl font-bold mb-1 flex items-center gap-2"><Settings className="h-5 w-5 text-amber-500"/> Regras de Ouro</h3>
              <p className="text-muted-foreground text-sm">Proteções para o bot não virar um spammer.</p>
            </div>
            
            <div className="p-4 bg-background/40 border border-border/50 rounded-xl space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-sm">Parar se o cliente responder</h4>
                  <p className="text-xs text-muted-foreground">Se o cliente mandar qualquer mensagem, este follow-up é abortado.</p>
                </div>
                <Switch checked={state.stopOnReply} onCheckedChange={c => updateState("stopOnReply", c)} className="data-[state=checked]:bg-emerald-500" />
              </div>
              
              <div className="h-px w-full bg-border/50" />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-sm flex items-center gap-1">Horário Inteligente (Smart Delay) <Sparkles className="h-3 w-3 text-amber-500"/></h4>
                  <p className="text-xs text-muted-foreground">Se o prazo cair de madrugada, o bot espera até as 09:00 da manhã para enviar.</p>
                </div>
                <Switch checked={state.smartDelay} onCheckedChange={c => updateState("smartDelay", c)} className="data-[state=checked]:bg-amber-500" />
              </div>

              <div className="h-px w-full bg-border/50" />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-sm flex items-center gap-1">Escalonamento de Pressão (Ghosting) <Flame className="h-3 w-3 text-destructive"/></h4>
                  <p className="text-xs text-muted-foreground">Se o cliente continuar no vácuo, a IA aumenta sozinha o nível de agressividade e gera gatilhos de escassez extrema (Urgência).</p>
                </div>
                <Switch checked={state.escalatePressure} onCheckedChange={c => updateState("escalatePressure", c)} className="data-[state=checked]:bg-destructive" />
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 pt-6 border-t border-border/50 flex justify-end">
          <Button onClick={handleSave} disabled={saving} className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white shadow-glow border-none gap-2 h-12 px-8 disabled:opacity-60">
            <Save className="h-4 w-4" /> {saving ? "Salvando..." : "Salvar Automação"}
          </Button>
        </div>

      </Card>
    </div>
  );
};
