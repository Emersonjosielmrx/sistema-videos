import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tag, Plus, Trash2, Sparkles, Activity, LineChart, Settings, BrainCircuit, Users, Search, Filter, Zap, CheckCircle2, History, X } from "lucide-react";
import { Field } from "@/components/ui/field";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { TagsAnalytics } from "@/components/analytics/TagsAnalytics";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import { toast } from "sonner";

// Colors available (fora do componente — estáveis)
const colors = [
  { name: "Verde (Sucesso)", cls: "bg-emerald-500", text: "text-emerald-500", bgLight: "bg-emerald-500/10", border: "border-emerald-500/20", hex: "#10b981" },
  { name: "Azul (Info)", cls: "bg-sky-500", text: "text-sky-500", bgLight: "bg-sky-500/10", border: "border-sky-500/20", hex: "#0ea5e9" },
  { name: "Vermelho (Risco)", cls: "bg-destructive", text: "text-destructive", bgLight: "bg-destructive/10", border: "border-destructive/20", hex: "#ef4444" },
  { name: "Laranja (Atenção)", cls: "bg-amber-500", text: "text-amber-500", bgLight: "bg-amber-500/10", border: "border-amber-500/20", hex: "#f59e0b" },
  { name: "Roxo (Especial)", cls: "bg-purple-500", text: "text-purple-500", bgLight: "bg-purple-500/10", border: "border-purple-500/20", hex: "#8b5cf6" },
  { name: "Cinza (Padrão)", cls: "bg-muted-foreground", text: "text-muted-foreground", bgLight: "bg-muted", border: "border-border/50", hex: "#6b7280" }
];

type ApiTag = { id: string; name: string; color: string; created_at: string };

function colorRefFromHex(hex: string) {
  return colors.find((c) => c.hex === hex) || colors[0];
}

export function TagsPage() {
  const [viewMode, setViewMode] = useState<"dashboard" | "analytics">("dashboard");
  const [showCreate, setShowCreate] = useState(false);

  // Create Tag Form State
  const [newTagName, setNewTagName] = useState("");
  const [newTagColor, setNewTagColor] = useState("bg-emerald-500");
  const [newTagRule, setNewTagRule] = useState("");
  // Auto-tag por IA ainda não é persistido pelo backend (não há coluna de regra).
  // Mantido desabilitado ("Em breve") até existir suporte real.
  const [aiEnabled, setAiEnabled] = useState(false);
  const [saving, setSaving] = useState(false);

  // Tags REAIS de /api/contacts/tags
  const [apiTags, setApiTags] = useState<ApiTag[]>([]);

  const loadTags = async () => {
    try {
      const r = await apiGet<{ tags: ApiTag[] } | ApiTag[]>("/api/contacts/tags");
      const list = Array.isArray(r) ? r : (r.tags ?? []);
      setApiTags(list);
    } catch {
      setApiTags([]);
    }
  };
  useEffect(() => { loadTags(); }, []);

  // Adapta pro formato do render. Contagem de leads/gatilhos não existe no schema → 0/—.
  const tags = apiTags.map((t) => {
    const cls = t.color?.startsWith("bg-") ? t.color : "";
    const ref = cls ? (colors.find((c) => c.cls === cls) || colors[0]) : colorRefFromHex(t.color || "#10b981");
    return { id: t.id, name: t.name, colorRef: ref, leads: 0, aiActive: false, trigger: null as string | null, rule: "" };
  });

  const handleCreateTag = async () => {
    if (!newTagName.trim()) { toast.error("Dê um nome à tag."); return; }
    setSaving(true);
    try {
      const ref = colors.find((c) => c.cls === newTagColor) || colors[0];
      await apiPost("/api/contacts/tags", { name: newTagName.trim(), color: ref.hex });
      toast.success("Tag criada!");
      setNewTagName(""); setNewTagRule(""); setShowCreate(false);
      await loadTags();
    } catch {
      toast.error("Falha ao criar tag.");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteTag = async (id: string) => {
    try {
      await apiDelete(`/api/contacts/tags/${id}`);
      toast.success("Tag removida.");
      await loadTags();
    } catch {
      toast.error("Falha ao remover tag.");
    }
  };

  const auditLog: { id: number; time: string; phone: string; tag: string; color: any; reason: string }[] = [];

  return (
    <div className="space-y-6 pb-20">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <BrainCircuit className="h-6 w-6 text-primary" /> Motor Semântico & Tags
          </h2>
          <p className="text-sm text-muted-foreground mt-1">Classifique contatos automaticamente usando Inteligência Artificial.</p>
        </div>
        <div className="flex items-center gap-2">
           <Button variant="outline" className="gap-2 bg-glass shadow-sm" onClick={() => setViewMode(viewMode === "analytics" ? "dashboard" : "analytics")}>
             <LineChart className="h-4 w-4" /> {viewMode === "analytics" ? "Voltar ao Gerenciador" : "Ver Analytics"}
           </Button>
           <Button className="gap-2 shadow-glow" onClick={() => setShowCreate(true)}>
             <Plus className="h-4 w-4" /> Nova Regra (Tag)
           </Button>
        </div>
      </div>

      {viewMode === "analytics" ? (
        <TagsAnalytics />
      ) : (
        <>
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Card className="bg-glass border-border/50 shadow-soft">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <Tag className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{tags.length}</p>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Tags Criadas</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-glass border-border/50 shadow-soft">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <Activity className="h-5 w-5 text-emerald-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{tags.length}</p>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Tags Ativas</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-glass border-border/50 shadow-soft">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-sky-500/10 border border-sky-500/20 flex items-center justify-center">
                  <Sparkles className="h-5 w-5 text-sky-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{auditLog.length}</p>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Ações Recentes da IA</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-primary/20 to-transparent border-primary/30 shadow-soft">
              <CardContent className="p-4 flex flex-col justify-center h-full">
                 <p className="text-sm font-bold text-primary flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4"/> Tags automáticas</p>
                 <p className="text-xs text-muted-foreground mt-1">A IA aplica estas tags aos contatos conforme o contexto das conversas.</p>
              </CardContent>
            </Card>
          </div>

          {/* Creation Builder */}
          {showCreate && (
            <Card className="border-primary/50 shadow-[0_0_30px_rgba(16,185,129,0.1)] animate-in slide-in-from-top-4 overflow-hidden relative mt-8">
              <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
              <CardHeader className="bg-muted/30 border-b border-border/50 pb-4">
                <div className="flex justify-between items-start">
                   <div>
                     <CardTitle className="flex items-center gap-2"><BrainCircuit className="w-5 h-5 text-primary"/> Motor de Regra Inteligente</CardTitle>
                     <CardDescription>Crie a Tag e ensine a IA exatamente quando aplicá-la.</CardDescription>
                   </div>
                   <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}><X className="w-4 h-4"/></Button>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                 <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="space-y-4">
                       <Field label="Nome da Tag">
                         <Input placeholder="Ex: Risco de Churn" value={newTagName} onChange={e => setNewTagName(e.target.value)} className="bg-glass h-11" />
                       </Field>
                       
                       <div>
                         <label className="text-sm font-medium mb-2 block">Cor da Categoria</label>
                         <div className="flex flex-wrap gap-2">
                           {colors.map(c => (
                             <button 
                               key={c.cls} 
                               onClick={() => setNewTagColor(c.cls)}
                               className={cn(
                                 "w-8 h-8 rounded-full border-2 transition-transform hover:scale-110 flex items-center justify-center", 
                                 c.cls, 
                                 newTagColor === c.cls ? "border-white ring-2 ring-primary scale-110" : "border-transparent"
                               )} 
                               title={c.name} 
                             />
                           ))}
                         </div>
                       </div>
                    </div>

                    <div className="md:col-span-2 space-y-4">
                       <div className="flex items-center justify-between">
                          <label className="text-sm font-medium flex items-center gap-2">Prompt de Tagueamento (Regra da IA) <Badge variant="muted" className="h-4 text-[0.55rem] px-1">Em breve</Badge></label>
                          <label className="flex items-center gap-2 text-sm opacity-50 cursor-not-allowed" title="Auto-tagueamento por IA ainda não disponível">
                            <input type="checkbox" disabled className="rounded border-input text-primary focus:ring-primary cursor-not-allowed" checked={aiEnabled} onChange={e => setAiEnabled(e.target.checked)} />
                            Ativar Auto-Tagueamento IA
                          </label>
                       </div>
                       <textarea
                          className="w-full bg-glass border border-border/50 rounded-xl p-4 min-h-[120px] text-sm focus:outline-none opacity-50 cursor-not-allowed"
                          placeholder="Instrua a IA sobre quando aplicar esta tag.&#10;Ex: 'Se o cliente mencionar qualquer intenção de cancelamento, insatisfação com o serviço ou perguntar sobre quebra de contrato.'"
                          disabled
                          value={newTagRule}
                          onChange={e => setNewTagRule(e.target.value)}
                       />
                       <div className="flex items-start gap-2 bg-amber-500/10 border border-amber-500/20 p-3 rounded-lg text-xs text-amber-500">
                         <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
                         <p><strong>Em breve:</strong> o auto-tagueamento por IA ainda não é salvo nem aplicado. Por enquanto, criar a tag salva apenas o nome e a cor.</p>
                       </div>
                    </div>
                 </div>
                 
                 <div className="mt-6 pt-4 border-t border-border/50 flex justify-end">
                    <Button size="lg" className="shadow-glow gap-2" disabled={saving} onClick={handleCreateTag}>Salvar Tag <Sparkles className="w-4 h-4"/></Button>
                 </div>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 mt-6">
             {/* Left Area: Tags Management Table */}
             <div className="xl:col-span-3 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4 bg-muted/20 p-2 rounded-lg border border-border/50">
                   <div className="relative w-full md:w-72">
                     <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                     <Input placeholder="Buscar tags..." className="pl-9 bg-background h-9" />
                   </div>
                   <div className="flex items-center gap-2">
                     <Button variant="outline" size="sm" className="gap-2 bg-background"><Filter className="w-4 h-4"/> Categoria</Button>
                   </div>
                </div>

                <div className="bg-glass border border-border/50 rounded-xl overflow-hidden shadow-soft">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-muted-foreground uppercase bg-muted/30 border-b border-border/50">
                        <tr>
                          <th className="px-5 py-4 font-semibold">Identificação da Tag</th>
                          <th className="px-5 py-4 font-semibold text-center">Audiência</th>
                          <th className="px-5 py-4 font-semibold">Status Inteligência</th>
                          <th className="px-5 py-4 font-semibold">Gatilhos / Ações</th>
                          <th className="px-5 py-4 font-semibold text-right">Opções</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tags.map((t) => (
                          <tr key={t.id} className="border-b border-border/20 last:border-0 hover:bg-muted/40 transition-colors group">
                            <td className="px-5 py-4">
                               <Badge variant="outline" className={cn("gap-1.5 px-2.5 py-1", t.colorRef.bgLight, t.colorRef.text, t.colorRef.border)}>
                                  <div className={cn("w-1.5 h-1.5 rounded-full", t.colorRef.cls)}></div>
                                  {t.name}
                               </Badge>
                            </td>
                            <td className="px-5 py-4 text-center">
                               <p className="font-bold">{t.leads.toLocaleString()}</p>
                               <p className="text-[10px] text-muted-foreground">leads</p>
                            </td>
                            <td className="px-5 py-4">
                               {t.aiActive ? (
                                 <div className="flex flex-col gap-1">
                                    <span className="flex items-center gap-1.5 text-[11px] font-bold text-primary"><Sparkles className="w-3 h-3"/> Auto-Tagueamento ON</span>
                                    <span className="text-[10px] text-muted-foreground truncate max-w-[150px]" title={t.rule}>"{t.rule}"</span>
                                 </div>
                               ) : (
                                 <span className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground"><Settings className="w-3 h-3"/> Manual Apenas</span>
                               )}
                            </td>
                            <td className="px-5 py-4">
                               {t.trigger ? (
                                 <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/20 gap-1 rounded-sm"><Zap className="w-3 h-3"/> {t.trigger}</Badge>
                               ) : (
                                 <span className="text-xs text-muted-foreground">—</span>
                               )}
                            </td>
                            <td className="px-5 py-4 text-right">
                               <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <Button variant="ghost" size="icon" className="h-8 w-8 text-primary hover:text-primary hover:bg-primary/10" title="Ver leads"><Users className="h-4 w-4" /></Button>
                                  <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted/50" title="Editar"><Settings className="h-4 w-4" /></Button>
                                  <Button variant="ghost" size="icon" onClick={() => handleDeleteTag(t.id)} className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10" title="Excluir"><Trash2 className="h-4 w-4" /></Button>
                               </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
             </div>

             {/* Right Area: AI Audit Log Feed */}
             <div className="xl:col-span-1">
                <Card className="bg-glass border-border/50 shadow-soft h-full flex flex-col overflow-hidden">
                   <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
                      <h3 className="font-bold text-sm flex items-center gap-2"><History className="w-4 h-4"/> Auditoria da IA</h3>
                   </div>
                   <div className="p-4 flex-1 space-y-5 overflow-y-auto custom-scrollbar max-h-[600px]">
                      {auditLog.length === 0 ? (
                        <div className="text-center text-xs text-muted-foreground py-10">
                          Ainda não há registros de tags aplicadas automaticamente pela IA. O histórico
                          de auditoria por tag está em desenvolvimento.
                        </div>
                      ) : auditLog.map((log) => (
                        <div key={log.id} className="relative pl-6">
                           <div className={cn("absolute left-0 top-1 w-2 h-2 rounded-full ring-4 ring-background", log.color.cls)}></div>
                           <div className="absolute left-[3px] top-4 w-[1px] h-full bg-border/50 -z-10"></div>

                           <div className="space-y-1">
                             <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold text-muted-foreground">{log.time}</span>
                                <span className="text-[10px] text-muted-foreground">{log.phone}</span>
                             </div>
                             <p className="text-xs">
                               IA adicionou <Badge variant="outline" className={cn("px-1.5 py-0 text-[9px] h-4", log.color.bgLight, log.color.text, log.color.border)}>{log.tag}</Badge>
                             </p>
                             <div className="bg-muted/30 border border-border/50 rounded p-2 mt-1">
                                <p className="text-[10px] text-muted-foreground font-mono">Motivo: {log.reason}</p>
                             </div>
                           </div>
                        </div>
                      ))}
                   </div>
                </Card>
             </div>
          </div>
        </>
      )}
    </div>
  );
}
