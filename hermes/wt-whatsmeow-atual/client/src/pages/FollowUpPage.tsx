import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Timer, Plus, Trash2, ArrowRight, CheckCircle2, Clock, CalendarDays, LineChart, Settings, Phone, MessageSquare, Mic, AlertCircle, Play } from "lucide-react";
import { Field } from "@/components/ui/field";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { FollowUpAnalytics } from "@/components/analytics/FollowUpAnalytics";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import { toast } from "sonner";

export type FollowUpStep = {
  id: string;
  delay_hours: number;
  channel: "voice" | "whatsapp_text" | "whatsapp_audio";
  message: string;
};

export type FollowUpSequence = {
  id: string;
  name: string;
  trigger_type: "tag" | "call_status" | "pipeline_stage";
  trigger_value: string;
  business_hours_only: boolean;
  stop_on_reply: boolean;
  active: boolean;
  steps: FollowUpStep[];
};

export function FollowUpPage() {
  const [viewMode, setViewMode] = useState<"dashboard" | "analytics">("dashboard");
  const [sequences, setSequences] = useState<FollowUpSequence[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Builder State
  const [isBuilding, setIsBuilding] = useState(false);
  const [newSeq, setNewSeq] = useState<Partial<FollowUpSequence>>({
     name: "", trigger_type: "tag", trigger_value: "", business_hours_only: true, stop_on_reply: true, steps: []
  });

  const loadRules = async () => {
    setLoading(true);
    try {
      const data = await apiGet<{ rules: FollowUpSequence[] }>("/api/followup/sequences");
      setSequences(data?.rules ?? []);
    } catch (e) {
      toast.error("Falha ao carregar as réguas de follow-up.");
      setSequences([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadRules(); }, []);

  const handleAddStep = () => {
    setNewSeq(prev => ({
      ...prev,
      steps: [...(prev.steps || []), { id: Date.now().toString(), delay_hours: 24, channel: "whatsapp_text", message: "" }]
    }));
  };

  const handleCreate = async () => {
    if (!newSeq.name || !newSeq.trigger_value || !(newSeq.steps?.length)) {
      toast.error("Preencha o nome, o gatilho e adicione pelo menos uma etapa.");
      return;
    }
    try {
      await apiPost("/api/followup/sequences", newSeq);
      toast.success("Sequência ativada com sucesso!");
      setIsBuilding(false);
      setNewSeq({ name: "", trigger_type: "tag", trigger_value: "", business_hours_only: true, stop_on_reply: true, steps: [] });
      loadRules();
    } catch (e: any) {
      toast.error("Falha ao salvar a sequência: " + (e?.message || "erro desconhecido"));
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remover esta sequência?")) return;
    try {
      await apiDelete(`/api/followup/sequences/${id}`);
      toast.success("Sequência removida");
      loadRules();
    } catch (e: any) {
      toast.error("Falha ao remover a sequência: " + (e?.message || "erro desconhecido"));
    }
  };

  const ChannelIcon = ({ type }: { type: string }) => {
    if (type === "voice") return <Phone className="w-4 h-4 text-primary" />;
    if (type === "whatsapp_audio") return <Mic className="w-4 h-4 text-sky-500" />;
    return <MessageSquare className="w-4 h-4 text-emerald-500" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 mb-2">
        <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
          <Timer className="h-6 w-6 text-primary" /> Follow-Up e Réguas
        </h2>
        <div className="flex items-center bg-muted/50 rounded-lg p-1 border border-border/50">
          <button 
            onClick={() => setViewMode("dashboard")} 
            className={cn("flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors", viewMode === "dashboard" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground")}
          >
            <Settings className="h-4 w-4" /> Configuração
          </button>
          <button 
            onClick={() => setViewMode("analytics")} 
            className={cn("flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors", viewMode === "analytics" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground")}
          >
            <LineChart className="h-4 w-4" /> Analytics
          </button>
        </div>
      </div>

      {viewMode === "analytics" ? (
        <FollowUpAnalytics />
      ) : (
        <>
          {/* Dashboard (Metrics) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="h-10 w-10 rounded-full bg-amber-500/10 flex items-center justify-center">
              <Clock className="h-5 w-5 text-amber-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">0</p>
              <p className="text-xs text-muted-foreground">Follow-ups pendentes hoje</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="h-10 w-10 rounded-full bg-emerald-500/10 flex items-center justify-center">
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">0</p>
              <p className="text-xs text-muted-foreground">Concluídos na semana</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <CalendarDays className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">0</p>
              <p className="text-xs text-muted-foreground">Regras Ativas</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-between mt-8 mb-4">
         <div>
           <h3 className="text-lg font-bold">Sequências Ativas</h3>
           <p className="text-sm text-muted-foreground">Suas réguas de relacionamento rodando no piloto automático.</p>
         </div>
         <Button onClick={() => setIsBuilding(true)} className="gap-2 shadow-glow"><Plus className="w-4 h-4"/> Nova Sequência</Button>
      </div>

      {isBuilding && (
        <Card className="border-primary/50 shadow-[0_0_30px_rgba(16,185,129,0.1)] animate-in slide-in-from-top-4 mb-8 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
          <CardHeader className="bg-muted/30 border-b border-border/50 pb-4">
            <div className="flex justify-between items-start">
               <div>
                 <CardTitle>Criador de Sequência Híbrida</CardTitle>
                 <CardDescription>Crie uma cadência multi-etapa usando Voz e WhatsApp.</CardDescription>
               </div>
               <Button variant="ghost" onClick={() => setIsBuilding(false)} className="text-muted-foreground">Cancelar</Button>
            </div>
          </CardHeader>
          <CardContent className="pt-6 space-y-8">
             {/* Trigger Setup */}
             <div className="space-y-4">
               <h4 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2"><ArrowRight className="w-4 h-4"/> 1. Gatilho Inicial</h4>
               <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                 <Field label="Nome da Sequência">
                   <Input placeholder="Ex: Lead Frio" value={newSeq.name} onChange={e => setNewSeq({...newSeq, name: e.target.value})} className="bg-glass" />
                 </Field>
                 <Field label="Tipo de Gatilho">
                   <select className="w-full bg-glass border border-border/50 rounded-md p-2.5 text-sm text-foreground" value={newSeq.trigger_type} onChange={e => setNewSeq({...newSeq, trigger_type: e.target.value as any})}>
                      <option value="tag">Adição de Tag</option>
                      <option value="call_status">Status da Ligação (Ex: Caixa Postal)</option>
                      <option value="pipeline_stage">Mudança no Funil</option>
                   </select>
                 </Field>
                 <Field label="Valor do Gatilho">
                   <Input placeholder={newSeq.trigger_type === 'tag' ? "Nome da tag..." : "Valor esperado..."} value={newSeq.trigger_value} onChange={e => setNewSeq({...newSeq, trigger_value: e.target.value})} className="bg-glass" />
                 </Field>
               </div>
               <div className="flex gap-6 mt-2 p-3 bg-muted/20 rounded-lg border border-border/50">
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input type="checkbox" className="rounded border-input text-primary focus:ring-primary" checked={newSeq.business_hours_only} onChange={e => setNewSeq({...newSeq, business_hours_only: e.target.checked})} />
                    Respeitar Horário Comercial (09h às 18h)
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input type="checkbox" className="rounded border-input text-primary focus:ring-primary" checked={newSeq.stop_on_reply} onChange={e => setNewSeq({...newSeq, stop_on_reply: e.target.checked})} />
                    Parar se o lead responder/atender
                  </label>
               </div>
             </div>

             {/* Timeline Builder */}
             <div className="space-y-4">
               <h4 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2"><Timer className="w-4 h-4"/> 2. Cadência (Linha do Tempo)</h4>
               
               <div className="pl-4 border-l-2 border-border/50 space-y-6 ml-2 relative">
                 {newSeq.steps?.map((step, idx) => (
                   <div key={step.id} className="relative pl-6">
                      <div className="absolute -left-[29px] top-4 w-6 h-6 rounded-full bg-background border-2 border-primary flex items-center justify-center text-[10px] font-bold text-primary">
                        {idx + 1}
                      </div>
                      <div className="bg-glass border border-border/50 rounded-xl p-4 space-y-4 shadow-sm group">
                         <div className="flex justify-between items-center">
                            <div className="flex items-center gap-3">
                               <span className="text-sm font-medium">Espera:</span>
                               <Input type="number" className="w-20 h-8 bg-background" value={step.delay_hours} onChange={e => {
                                  const steps = [...newSeq.steps!]; steps[idx].delay_hours = Number(e.target.value); setNewSeq({...newSeq, steps});
                               }} />
                               <span className="text-sm text-muted-foreground">horas depois</span>
                            </div>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => {
                               const steps = newSeq.steps!.filter((_, i) => i !== idx); setNewSeq({...newSeq, steps});
                            }}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                         </div>
                         <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="md:col-span-1">
                               <Field label="Canal">
                                 <select className="w-full bg-background border border-border/50 rounded-md p-2 text-sm text-foreground" value={step.channel} onChange={e => {
                                    const steps = [...newSeq.steps!]; steps[idx].channel = e.target.value as any; setNewSeq({...newSeq, steps});
                                 }}>
                                    <option value="whatsapp_text">WhatsApp Texto</option>
                                    <option value="whatsapp_audio">WhatsApp Áudio</option>
                                    <option value="voice">Ligação (Voz IA)</option>
                                 </select>
                               </Field>
                            </div>
                            <div className="md:col-span-3">
                               <Field label={step.channel === 'voice' ? "Prompt / Objetivo da Ligação" : "Mensagem (Use {{nome}} para personalizar)"}>
                                 <Input className="bg-background" value={step.message} onChange={e => {
                                    const steps = [...newSeq.steps!]; steps[idx].message = e.target.value; setNewSeq({...newSeq, steps});
                                 }} placeholder={step.channel === 'voice' ? "Ex: Ligar para confirmar se recebeu o e-mail..." : "Ex: Oi {{nome}}, tudo bem?"} />
                               </Field>
                            </div>
                         </div>
                      </div>
                   </div>
                 ))}

                 <div className="relative pl-6 pt-2">
                    <Button variant="outline" onClick={handleAddStep} className="gap-2 border-dashed border-primary/50 text-primary hover:bg-primary/10 w-full justify-start h-12">
                      <Plus className="w-4 h-4" /> Adicionar Etapa na Sequência
                    </Button>
                 </div>
               </div>
             </div>

             <div className="pt-4 flex items-center justify-between border-t border-border/50">
                <Button variant="outline" className="gap-2 text-muted-foreground"><Play className="w-4 h-4"/> Disparar Teste</Button>
                <Button onClick={handleCreate} size="lg" className="shadow-glow">Salvar e Ativar Sequência</Button>
             </div>
          </CardContent>
        </Card>
      )}

      {/* Active Sequences List */}
      <div className="grid gap-4">
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">Carregando cadências...</div>
        ) : sequences.length === 0 ? (
          <div className="p-10 text-center bg-glass rounded-xl border border-border/50 text-muted-foreground flex flex-col items-center gap-3">
             <LineChart className="h-10 w-10 opacity-20" />
             <p className="font-medium">Nenhuma sequência configurada.</p>
             <p className="text-sm opacity-60 max-w-sm">Crie gatilhos para recuperar leads perdidos e fazer acompanhamento automático.</p>
          </div>
        ) : (
          sequences.map(seq => (
            <Card key={seq.id} className="overflow-hidden bg-glass border-border/50">
              <div className="flex flex-col md:flex-row border-b border-border/20">
                <div className="p-5 flex-1 bg-muted/10">
                   <div className="flex items-center gap-3 mb-2">
                     <h3 className="text-lg font-bold">{seq.name}</h3>
                     <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Ativa</Badge>
                   </div>
                   <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mt-4">
                      <span className="flex items-center gap-1.5 bg-background px-2.5 py-1 rounded-md border border-border/50">
                         <AlertCircle className="w-3.5 h-3.5" /> 
                         Gatilho: <strong className="text-foreground">{seq.trigger_type === 'tag' ? 'Tag' : seq.trigger_type} = {seq.trigger_value}</strong>
                      </span>
                      {seq.business_hours_only && (
                        <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> Apenas Horário Comercial</span>
                      )}
                      {seq.stop_on_reply && (
                        <span className="flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5" /> Para se responder</span>
                      )}
                   </div>
                </div>
                <div className="p-5 flex flex-col justify-center items-end bg-background/50 md:border-l border-border/20 gap-2">
                   <div className="text-right">
                     <p className="text-2xl font-bold text-primary">{seq.steps.length}</p>
                     <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Etapas</p>
                   </div>
                   <div className="flex items-center gap-2 mt-2">
                     <Button variant="outline" size="sm">Pausar</Button>
                     <Button variant="ghost" size="sm" className="text-destructive hover:bg-destructive/10" onClick={() => handleDelete(seq.id)}>Excluir</Button>
                   </div>
                </div>
              </div>
              
              {/* Visual Timeline Preview */}
              <div className="p-5 bg-background flex items-center gap-2 overflow-x-auto custom-scrollbar">
                 <div className="shrink-0 flex flex-col items-center gap-2 text-muted-foreground">
                    <div className="w-8 h-8 rounded-full border border-border/50 flex items-center justify-center bg-muted/30"><AlertCircle className="w-4 h-4"/></div>
                    <span className="text-[10px] font-bold uppercase">Gatilho</span>
                 </div>
                 
                 {seq.steps.map((step, idx) => (
                    <div key={step.id} className="flex items-center shrink-0">
                       <div className="w-16 h-[2px] bg-border/50 relative mx-1">
                          <span className="absolute -top-4 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground font-medium">{step.delay_hours}h</span>
                       </div>
                       <div className="flex flex-col items-center gap-2">
                          <div className={cn("w-10 h-10 rounded-full flex items-center justify-center border shadow-sm", 
                             step.channel === 'voice' ? "bg-primary/10 border-primary/20" : 
                             step.channel === 'whatsapp_audio' ? "bg-sky-500/10 border-sky-500/20" : "bg-emerald-500/10 border-emerald-500/20"
                          )}>
                             <ChannelIcon type={step.channel} />
                          </div>
                          <span className="text-[10px] font-bold uppercase">{idx + 1}º Contato</span>
                       </div>
                    </div>
                 ))}
                 
                 <div className="flex items-center shrink-0">
                    <div className="w-8 h-[2px] bg-border/50 mx-1"></div>
                    <div className="shrink-0 flex flex-col items-center gap-2 opacity-50">
                       <div className="w-8 h-8 rounded-full border border-dashed border-border/50 flex items-center justify-center bg-muted/10"><CheckCircle2 className="w-4 h-4"/></div>
                       <span className="text-[10px] font-bold uppercase">Fim</span>
                    </div>
                 </div>
              </div>
            </Card>
          ))
        )}
      </div>
        </>
      )}
    </div>
  );
}
