import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ShieldAlert, Ban, AlertTriangle, UserX, LineChart, Shield, ShieldCheck, Clock, BrainCircuit, Search, Filter, CalendarClock, Lock, Unlock, Sparkles } from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { BlocksAnalytics } from "@/components/analytics/BlocksAnalytics";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import { toast } from "sonner";

type BlacklistItem = { id?: string; phone_number: string; reason: string; created_at: string; expires_at?: string | null };

export function BlocksPage() {
  const [viewMode, setViewMode] = useState<"dashboard" | "analytics">("dashboard");
  const [showAdd, setShowAdd] = useState(false);

  // Form State
  const [blockTarget, setBlockTarget] = useState("");
  const [blockCategory, setBlockCategory] = useState("optout");
  const [blockDuration, setBlockDuration] = useState("forever");
  const [saving, setSaving] = useState(false);

  const categories: Record<string, { label: string; color: string; icon: any }> = {
    optout: { label: "Opt-out / DNC", color: "text-amber-500 bg-amber-500/10 border-amber-500/20", icon: AlertTriangle },
    hardbounce: { label: "Número Inválido", color: "text-sky-500 bg-sky-500/10 border-sky-500/20", icon: UserX },
    spam: { label: "Anti-Spam / Procon", color: "text-destructive bg-destructive/10 border-destructive/20", icon: ShieldAlert },
    quarantine: { label: "Quarentena", color: "text-purple-500 bg-purple-500/10 border-purple-500/20", icon: Clock },
  };

  // Blacklist REAL de /api/followup/blacklist
  const [raw, setRaw] = useState<BlacklistItem[]>([]);
  const loadBlacklist = async () => {
    try {
      const r = await apiGet<{ blacklist: BlacklistItem[] }>("/api/followup/blacklist");
      setRaw(r.blacklist ?? []);
    } catch {
      setRaw([]);
    }
  };
  useEffect(() => { loadBlacklist(); }, []);

  const fmtDate = (s: string) => { try { return new Date(s).toLocaleDateString("pt-BR"); } catch { return s; } };

  const blocklist = raw.map((b, i) => ({
    id: b.id || String(i),
    target: b.phone_number,
    category: /spam|procon/i.test(b.reason) ? "spam" : /inv|bounce/i.test(b.reason) ? "hardbounce" : /quar/i.test(b.reason) ? "quarantine" : "optout",
    type: "number",
    origin: "Manual",
    saved: 0,
    date: fmtDate(b.created_at),
    expires: b.expires_at ? fmtDate(b.expires_at) : "Nunca",
    reason: b.reason,
  }));

  const handleAddBlock = async () => {
    if (!blockTarget.trim()) { toast.error("Informe o número a bloquear."); return; }
    setSaving(true);
    try {
      await apiPost("/api/followup/blacklist", { phone: blockTarget.trim(), reason: categories[blockCategory]?.label || "", duration: blockDuration });
      toast.success("Bloqueio adicionado.");
      setBlockTarget(""); setShowAdd(false);
      await loadBlacklist();
    } catch {
      toast.error("Falha ao adicionar bloqueio.");
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveBlock = async (phone: string) => {
    // Desbloquear devolve o número às campanhas/follow-ups — confirma antes (clique acidental).
    if (!confirm(`Desbloquear ${phone}? Ele volta a receber campanhas e follow-ups.`)) return;
    try {
      await apiDelete(`/api/followup/blacklist?phone=${encodeURIComponent(phone)}`);
      toast.success("Bloqueio removido.");
      await loadBlacklist();
    } catch {
      toast.error("Falha ao remover.");
    }
  };

  const defenseLog: { id: number; time: string; target: string; action: string; reason: string }[] = [];

  return (
    <div className="space-y-6 pb-20">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" /> Motor de Supressão
          </h2>
          <p className="text-sm text-muted-foreground mt-1">Proteja sua operação contra spam, multas e custos desnecessários.</p>
        </div>
        <div className="flex items-center gap-2">
           <Button variant="outline" className="gap-2 bg-glass shadow-sm" onClick={() => setViewMode(viewMode === "analytics" ? "dashboard" : "analytics")}>
             <LineChart className="h-4 w-4" /> {viewMode === "analytics" ? "Voltar ao Gerenciador" : "Ver Relatórios"}
           </Button>
           <Button className="gap-2 shadow-glow" onClick={() => setShowAdd(!showAdd)} variant={showAdd ? "secondary" : "default"}>
             {showAdd ? "Cancelar" : <><Lock className="h-4 w-4" /> Novo Bloqueio</>}
           </Button>
        </div>
      </div>

      {viewMode === "analytics" ? (
        <BlocksAnalytics />
      ) : (
        <>
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Card className="bg-glass border-border/50 shadow-soft">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-destructive/10 border border-destructive/20 flex items-center justify-center">
                  <ShieldAlert className="h-5 w-5 text-destructive" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{blocklist.length.toLocaleString("pt-BR")}</p>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Itens na Lista Negra</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-glass border-border/50 shadow-soft">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <ShieldCheck className="h-5 w-5 text-emerald-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{blocklist.filter((b) => b.category === "optout").length}</p>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Opt-out / DNC</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-glass border-border/50 shadow-soft">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
                  <Clock className="h-5 w-5 text-purple-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{blocklist.filter((b) => b.category === "quarantine").length}</p>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Em Quarentena</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-emerald-500/20 to-transparent border-emerald-500/30 shadow-soft">
              <CardContent className="p-4 flex flex-col justify-center h-full">
                 <p className="text-sm font-bold text-emerald-500 flex items-center gap-1.5"><Sparkles className="w-4 h-4"/> {blocklist.filter((b) => b.category === "spam").length} Anti-Spam</p>
                 <p className="text-xs text-muted-foreground mt-1">Contatos bloqueados por Procon/Spam.</p>
              </CardContent>
            </Card>
          </div>

          {/* Settings / Rules Toggles */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
             <Card className="bg-glass border-border/50 shadow-soft">
                <CardHeader className="pb-3">
                   <CardTitle className="text-sm flex items-center gap-2"><BrainCircuit className="w-4 h-4 text-primary"/> Supressão Inteligente (IA)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                   <p className="text-xs text-muted-foreground">
                     Regras automáticas de supressão (bloquear quem pede "não ligue mais" / auto-quarentena
                     após falhas repetidas) ainda estão em desenvolvimento. Por enquanto, use o bloqueio
                     manual ao lado para adicionar contatos ou tags à lista de bloqueio.
                   </p>
                </CardContent>
             </Card>
             
             {/* Form Creation Area (Conditionally Rendered or always there) */}
             {showAdd && (
                <Card className="border-destructive/50 shadow-[0_0_30px_rgba(239,68,68,0.1)] animate-in fade-in zoom-in-95">
                  <div className="p-4 space-y-4">
                     <div>
                       <label className="text-sm font-medium mb-1.5 block">Alvo do Bloqueio</label>
                       <Input placeholder="Telefone (+55...) ou nome exato da Tag" value={blockTarget} onChange={e => setBlockTarget(e.target.value)} className="bg-background" />
                     </div>
                     <div className="grid grid-cols-2 gap-4">
                       <div>
                         <label className="text-sm font-medium mb-1.5 block">Categoria</label>
                         <select className="w-full bg-background border border-border/50 rounded-md p-2 text-sm" value={blockCategory} onChange={e => setBlockCategory(e.target.value)}>
                            <option value="optout">Opt-out / DNC</option>
                            <option value="hardbounce">Hard Bounce (Inexistente)</option>
                            <option value="spam">Anti-Spam / Procon</option>
                            <option value="quarantine">Quarentena / Pausa</option>
                         </select>
                       </div>
                       <div>
                         <label className="text-sm font-medium mb-1.5 block">Duração</label>
                         <select className="w-full bg-background border border-border/50 rounded-md p-2 text-sm" value={blockDuration} onChange={e => setBlockDuration(e.target.value)}>
                            <option value="forever">Para Sempre</option>
                            <option value="7days">7 Dias</option>
                            <option value="30days">30 Dias</option>
                         </select>
                       </div>
                     </div>
                     <Button className="w-full gap-2" variant="destructive" disabled={saving} onClick={handleAddBlock}><Ban className="w-4 h-4"/> Adicionar à Lista Negra</Button>
                  </div>
                </Card>
             )}
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 mt-6">
             {/* Left Area: Suppression Table */}
             <div className="xl:col-span-3 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4 bg-muted/20 p-2 rounded-lg border border-border/50">
                   <div className="relative w-full md:w-72">
                     <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                     <Input placeholder="Buscar na lista negra..." className="pl-9 bg-background h-9" />
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
                          <th className="px-5 py-4 font-semibold">Alvo (Contato/Tag)</th>
                          <th className="px-5 py-4 font-semibold">Motivo / Categoria</th>
                          <th className="px-5 py-4 font-semibold">Origem</th>
                          <th className="px-5 py-4 font-semibold text-center">Tentativas Evitadas</th>
                          <th className="px-5 py-4 font-semibold text-right">Ações</th>
                        </tr>
                      </thead>
                      <tbody>
                        {blocklist.map((b) => {
                          const CatIcon = categories[b.category].icon;
                          return (
                          <tr key={b.id} className="border-b border-border/20 last:border-0 hover:bg-muted/40 transition-colors group">
                            <td className="px-5 py-4">
                               <p className="font-bold font-mono">{b.target}</p>
                               <div className="flex items-center gap-2 mt-1">
                                 <Badge variant="outline" className="text-[9px] h-4 bg-muted text-muted-foreground px-1 uppercase tracking-wider">{b.type}</Badge>
                                 <span className="text-[10px] text-muted-foreground flex items-center gap-1"><CalendarClock className="w-3 h-3"/> {b.date}</span>
                               </div>
                            </td>
                            <td className="px-5 py-4">
                               <Badge variant="outline" className={cn("gap-1.5 px-2.5 py-1 rounded-sm", categories[b.category].color)}>
                                  <CatIcon className="w-3 h-3" />
                                  {categories[b.category].label}
                               </Badge>
                               {b.expires !== "Nunca" && (
                                 <p className="text-[10px] text-purple-500 mt-1 font-medium flex items-center gap-1"><Clock className="w-3 h-3"/> Expira {b.expires}</p>
                               )}
                            </td>
                            <td className="px-5 py-4">
                               <span className="text-xs text-muted-foreground">{b.origin}</span>
                            </td>
                            <td className="px-5 py-4 text-center">
                               <Badge variant="secondary" className="bg-muted text-foreground">{b.saved}</Badge>
                            </td>
                            <td className="px-5 py-4 text-right">
                               <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <Button variant="ghost" size="icon" onClick={() => handleRemoveBlock(b.target)} className="h-8 w-8 text-emerald-500 hover:text-emerald-500 hover:bg-emerald-500/10" title="Desbloquear / Remover da lista"><Unlock className="h-4 w-4" /></Button>
                               </div>
                            </td>
                          </tr>
                        )})}
                      </tbody>
                    </table>
                  </div>
                </div>
             </div>

             {/* Right Area: Defense Log */}
             <div className="xl:col-span-1">
                <Card className="bg-glass border-border/50 shadow-soft h-full flex flex-col overflow-hidden">
                   <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
                      <h3 className="font-bold text-sm flex items-center gap-2"><Shield className="w-4 h-4"/> Log de Defesa</h3>
                   </div>
                   <div className="p-4 flex-1 space-y-5 overflow-y-auto custom-scrollbar max-h-[600px]">
                      {defenseLog.length === 0 ? (
                        <div className="text-center text-xs text-muted-foreground py-10">
                          Sem eventos de defesa registrados. O histórico de bloqueios automáticos está
                          em desenvolvimento.
                        </div>
                      ) : defenseLog.map((log) => (
                        <div key={log.id} className="relative pl-6">
                           <div className="absolute left-0 top-1 w-2 h-2 rounded-full ring-4 ring-background bg-destructive"></div>
                           <div className="absolute left-[3px] top-4 w-[1px] h-full bg-border/50 -z-10"></div>

                           <div className="space-y-1">
                             <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold text-muted-foreground">{log.time}</span>
                             </div>
                             <p className="text-xs font-bold text-foreground">
                               {log.action}
                             </p>
                             <p className="text-[11px] text-muted-foreground font-mono truncate" title={log.target}>{log.target}</p>
                             <div className="bg-destructive/5 border border-destructive/20 rounded p-2 mt-1">
                                <p className="text-[10px] text-destructive font-medium">{log.reason}</p>
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
