import { useState, useEffect, useCallback } from "react";
import { Search, MapPin, Activity, User } from "lucide-react";
import { Input } from "@/components/ui/input";
import { AvatarInitial } from "@/components/shared/AvatarInitial";
import { apiGet } from "@/lib/api";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

type Stage = { id: string; name: string; color: string; position: number; prompt?: string };
type Lead = { jid: string; phone: string; score: number; notes: string };
type Board = { stages: Stage[]; leads: Record<string, Lead[]> };

export function SplitPaneCRM() {
  const [board, setBoard] = useState<Board>({ stages: [], leads: {} });
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [selectedStageName, setSelectedStageName] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const reload = useCallback(() => {
    apiGet<Board>("/api/crm/board")
      .then((b) => setBoard({ stages: b.stages ?? [], leads: b.leads ?? {} }))
      .catch((e) => toast.error("Erro ao carregar CRM", { description: (e as Error).message }))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  // Flatten leads
  let allLeads: { lead: Lead; stageName: string; stageColor: string }[] = [];
  board.stages.forEach(st => {
    const leadsInStage = board.leads[st.name] ?? [];
    leadsInStage.forEach(l => {
      allLeads.push({ lead: l, stageName: st.name, stageColor: st.color });
    });
  });

  if (search) {
    allLeads = allLeads.filter(l => l.lead.phone.includes(search) || l.lead.notes?.toLowerCase().includes(search.toLowerCase()));
  }

  // Keyboard Navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!allLeads.length) return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      const currentIndex = selectedLead ? allLeads.findIndex(l => l.lead.jid === selectedLead.jid) : -1;
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const next = currentIndex + 1 < allLeads.length ? currentIndex + 1 : 0;
        setSelectedLead(allLeads[next].lead);
        setSelectedStageName(allLeads[next].stageName);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prev = currentIndex - 1 >= 0 ? currentIndex - 1 : allLeads.length - 1;
        setSelectedLead(allLeads[prev].lead);
        setSelectedStageName(allLeads[prev].stageName);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [allLeads, selectedLead]);

  if (loading) return <div className="p-6 text-muted-foreground animate-pulse">Carregando Leads...</div>;

  return (
    <div className="flex h-[calc(100vh-220px)] w-full rounded-2xl border border-border/50 bg-glass shadow-soft overflow-hidden">
      
      {/* Esquerda: Lista de Leads */}
      <div className="w-[30%] min-w-[300px] border-r border-border/50 flex flex-col bg-background/50">
        <div className="p-4 border-b border-border/50 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar leads (Spotlight)..."
              className="pl-9 h-9 bg-muted/50 border-border/30"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-2 overflow-x-auto custom-scrollbar pb-1">
            <span className="shrink-0 inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-[0.65rem] font-medium text-primary">Todos</span>
            <span className="shrink-0 inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[0.65rem] font-medium text-muted-foreground">Filtros Avançados...</span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
          {allLeads.map(({ lead, stageName, stageColor }) => {
            const isSelected = selectedLead?.jid === lead.jid;
            // Identificador visual de score / ddd simulado
            const ddd = lead.phone.replace(/\D/g, '').substring(2, 4);

            return (
              <button
                key={lead.jid}
                onClick={() => { setSelectedLead(lead); setSelectedStageName(stageName); }}
                className={cn(
                  "w-full text-left p-3 flex gap-3 rounded-xl transition-all border",
                  isSelected 
                    ? "bg-muted border-primary/20 shadow-sm" 
                    : "bg-transparent border-transparent hover:bg-muted/50"
                )}
              >
                <AvatarInitial name={lead.phone} className="h-9 w-9 shrink-0 shadow-sm" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold truncate">{lead.phone}</span>
                    {ddd && <span className="text-[0.6rem] font-medium text-muted-foreground bg-background px-1.5 rounded-sm border border-border/50">{ddd}</span>}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: stageColor }} />
                    <span className="text-xs text-muted-foreground truncate">{stageName}</span>
                  </div>
                </div>
              </button>
            )
          })}
          {allLeads.length === 0 && (
            <div className="p-6 text-center text-sm text-muted-foreground">Nenhum lead encontrado.</div>
          )}
        </div>
      </div>

      {/* Direita: Painel de Detalhes e Timeline */}
      <div className="flex-1 flex flex-col bg-card/10">
        {selectedLead ? (
          <>
            <div className="p-6 border-b border-border/50 bg-background/80 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-4">
                <AvatarInitial name={selectedLead.phone} className="h-14 w-14 shadow-md ring-2 ring-background" />
                <div>
                  <h3 className="text-xl font-bold">{selectedLead.phone}</h3>
                  <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
                    <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" /> Fuso BRT</span>
                    <span className="inline-flex items-center gap-1 bg-primary/10 text-primary px-2 py-0.5 rounded-full text-xs font-medium">Score: {selectedLead.score}</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                 <button className="px-3 py-1.5 text-sm font-medium border border-border/50 bg-glass hover:bg-muted rounded-lg transition-colors">
                   Ações
                 </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 flex flex-col md:flex-row gap-6">
              
              {/* Timeline */}
              <div className="flex-1 space-y-6">
                <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                  <Activity className="h-4 w-4" /> Timeline de Atividades
                </h4>
                
                <div className="relative border-l border-border/50 ml-3 pl-6 space-y-6">
                  {/* Etapa Atual */}
                  <div className="relative">
                    <span className="absolute -left-[30px] top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary ring-4 ring-background" />
                    <p className="text-xs text-muted-foreground mb-1">Status Atual</p>
                    <p className="text-sm font-medium">Movido para <span className="font-semibold text-primary">{selectedStageName}</span></p>
                  </div>
                  
                  {/* Anotações da IA (reais quando existem). Antes havia 2 blocos com
                      timestamps FIXOS ("Há 15 min", "Ontem") que apareciam pra qualquer
                      lead — removidos por serem mock enganoso. Sem endpoint de timeline
                      de atividade, mostramos só o que é real: as notes do lead. */}
                  {selectedLead.notes && (
                    <div className="relative opacity-90">
                      <span className="absolute -left-[30px] top-1 flex h-4 w-4 items-center justify-center rounded-full bg-muted border border-border/50 ring-4 ring-background" />
                      <p className="text-xs text-muted-foreground mb-1">Anotações da IA</p>
                      <div className="bg-glass border border-border/50 rounded-xl p-3 mt-1 text-sm">
                        <p className="text-muted-foreground text-xs">{selectedLead.notes}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Detalhes Extra */}
              <div className="w-full md:w-64 space-y-6 shrink-0">
                <div className="bg-muted/30 border border-border/50 rounded-xl p-4">
                   <h5 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">Informações</h5>
                   <div className="space-y-3 text-sm">
                     <div>
                       <span className="block text-xs text-muted-foreground">Telefone</span>
                       <span className="font-medium">{selectedLead.phone}</span>
                     </div>
                     <div>
                       <span className="block text-xs text-muted-foreground">JID (Sistema)</span>
                       <span className="font-mono text-xs break-all">{selectedLead.jid}</span>
                     </div>
                   </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground p-6">
            <User className="h-12 w-12 opacity-20 mb-4" />
            <p className="font-medium">Nenhum Lead Selecionado</p>
            <p className="text-sm mt-1">Selecione um lead na lista à esquerda ou use as setas do teclado para navegar.</p>
          </div>
        )}
      </div>

    </div>
  );
}
