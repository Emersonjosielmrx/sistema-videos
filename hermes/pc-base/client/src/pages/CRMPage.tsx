import { useEffect, useState, useCallback } from "react";
import { KanbanSquare, Plus, Trash2, Phone, Users, Megaphone, ListChecks, Sparkles, FileText, Inbox, MoreVertical, ListPlus, Layers, Minimize2, Maximize2, ChevronsLeft, ArrowUpDown, Zap, Flame, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList } from "@/components/ui/tabs";
import { HideableTab } from "@/components/ui/HideableTab";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { listContactLists, type ContactList } from "@/services/broadcast";
import { AvatarInitial } from "@/components/shared/AvatarInitial";
import { toast } from "sonner";
import { apiGet, apiPost, apiDelete, apiPut } from "@/lib/api";
import { ContactsPage } from "@/pages/ContactsPage";
import { CampaignsPage } from "@/pages/CampaignsPage";
import { ListsPage } from "@/pages/ListsPage";
import { TagsPage } from "@/pages/TagsPage";
import { BlocksPage } from "@/pages/BlocksPage";
import { FollowUpPage } from "@/pages/FollowUpPage";
import { SplitPaneCRM } from "@/components/crm/SplitPaneCRM";
import { LayoutPanelLeft, Tags, Ban, Clock, LineChart, Search, ShieldCheck, Send } from "lucide-react"
import { MassCallPage } from "@/pages/MassCallPage"
import { MassMessagePage } from "@/pages/MassMessagePage"
import { PromisesManagerTab } from "@/components/settings/PromisesManagerTab";
import { cn } from "@/lib/utils";
import { CRMAnalytics } from "@/components/analytics/CRMAnalytics";
import { LeadCaptureTab } from "@/components/settings/LeadCaptureTab";
import { CollectedDataTab } from "@/components/crm/CollectedDataTab";
import { WhatsAppExtractorTab } from "@/components/crm/WhatsAppExtractorTab";
import { useMassCallStore } from "@/stores/masscall";
import { useMassMessageStore } from "@/stores/massmsg";
import { setView } from "@/stores/navigation";
import type { Contact } from "@/types/contacts";

// CRMPage — central de gestão de clientes. Agrupa em sub-abas tudo relacionado a
// contatos (pedido do dono 2026-07-16): o Kanban do funil + as telas de Contatos,
// Campanhas e Listas, que antes eram itens soltos no menu do topo.
//
// A sub-aba "Funil" é o Kanban: o dono CRIA etapas (colunas) e ARRASTA os contatos
// entre elas com drag nativo HTML5 (sem lib externa). Backend: /api/crm/board,
// /api/crm/stages, /api/crm/move. Cada card = um lead (contact_leads); mover grava o stage.

type Stage = { id: string; name: string; color: string; position: number; prompt?: string };
type Lead = { jid: string; phone: string; score: number; notes: string; name?: string; source?: string; updated_at?: string };

// "há 5 min", "há 3 h", "há 2 dias" a partir da data real de atualização do lead.
function fmtAgo(iso?: string): string {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  if (isNaN(t)) return "";
  const min = Math.max(0, Math.round((Date.now() - t) / 60000));
  if (min < 1) return "agora";
  if (min < 60) return `há ${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `há ${h} h`;
  const d = Math.round(h / 24);
  return `há ${d} ${d === 1 ? "dia" : "dias"}`;
}
type Board = { stages: Stage[]; leads: Record<string, Lead[]> };

// CRMPage — casca com sub-abas. Centraliza Funil + Contatos + Campanhas + Listas.
export function CRMPage() {
  const [funnelView, setFunnelView] = useState<"kanban" | "split" | "list">("split");
  const [activeTab, setActiveTab] = useState("funnel");
  const [stageFilter, setStageFilter] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);

  const getTabTitle = () => {
    switch(activeTab) {
      case "funnel": return "Funil de Vendas";
      case "analytics": return "Analytics CRM";
      case "contacts": return "Meus Contatos";
      case "followup": return "Follow Up";
      case "campaigns": return "Campanhas";
      case "capture": return "Scraping de Leads";
      case "garimpo": return "Garimpo WhatsApp";
      case "lists": return "Listas";
      case "tags": return "Tags";
      case "blocks": return "Bloqueios";
      default: return "Gestão de Leads";
    }
  };

  const getTabDesc = () => {
    switch(activeTab) {
      case "funnel": return "Acompanhe o funil ou peça para a IA negociar por você.";
      case "analytics": return "Métricas e resultados das negociações.";
      case "contacts": return "Base de clientes e carteira de leads.";
      case "followup": return "Retornos agendados e lembretes.";
      case "campaigns": return "Disparos em massa e engajamento.";
      case "capture": return "Busca e extração de novos leads na internet.";
      case "garimpo": return "Extraia contatos e conversas do WhatsApp para virar campanha.";
      case "lists": return "Listas de transmissão e contatos.";
      case "tags": return "Etiquetas de segmentação.";
      case "blocks": return "Gestão de contatos bloqueados.";
      case "collected": return "Dados estruturados e formulários preenchidos pela IA.";
      default: return "";
    }
  };

  return (
    <div className="space-y-4">
      {/* Cabeçalho Compacto CRM */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-500/10 via-background to-background border border-emerald-500/20 p-4 shadow-glow flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
          <KanbanSquare className="w-16 h-16 text-emerald-500" />
        </div>
        <div className="relative z-10 flex items-center gap-3">
          <div className="hidden sm:flex items-center justify-center p-2 bg-emerald-500/10 rounded-xl border border-emerald-500/20 shadow-glow shrink-0">
            <img src="/inovareLogo.png" alt="Inovare Logo" className="w-8 h-8 object-contain drop-shadow-[0_0_8px_rgba(16,185,129,0.3)] rounded-full" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-emerald-500 to-emerald-400 drop-shadow-sm">
                {getTabTitle()}
              </h2>
              <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Hermes Call Inovare
              </Badge>
              <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Piloto Automático
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {getTabDesc()}
            </p>
          </div>
        </div>
        <div className="relative z-10 flex items-center gap-3 shrink-0">

          <div className="flex items-center bg-muted/50 rounded-lg p-1 border border-border/50 hidden md:flex">
            {activeTab === "funnel" && (
              <>
                <button 
                  onClick={() => setFunnelView("split")} 
                  className={cn("flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors", funnelView === "split" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground")}
                >
                  <LayoutPanelLeft className="h-4 w-4" /> Dividido
                </button>
                <button
                  onClick={() => setFunnelView("kanban")}
                  className={cn("flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors", funnelView === "kanban" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground")}
                >
                  <KanbanSquare className="h-4 w-4" /> Kanban
                </button>
                <button
                  onClick={() => setFunnelView("list")}
                  className={cn("flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors", funnelView === "list" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground")}
                >
                  <ListChecks className="h-4 w-4" /> Lista
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      <Tabs defaultValue="funnel" value={activeTab} onValueChange={setActiveTab} className="flex flex-col md:flex-row gap-6 w-full">
        <div className="w-full md:w-56 shrink-0 overflow-x-auto pb-2 custom-scrollbar">
          <TabsList className="flex flex-row md:flex-col h-auto bg-transparent items-center md:items-stretch p-0 space-x-2 md:space-x-0 md:space-y-1 w-max md:w-full">
            <HideableTab value="funnel" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <KanbanSquare className="h-4 w-4 mr-2" /> Funil
            </HideableTab>
            <HideableTab value="analytics" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <LineChart className="h-4 w-4 mr-2" /> Analytics
            </HideableTab>
            <HideableTab value="contacts" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Users className="h-4 w-4 mr-2" /> Contatos
            </HideableTab>
            <HideableTab value="followup" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Clock className="h-4 w-4 mr-2" /> Follow Up
            </HideableTab>
            <HideableTab value="campaigns" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Megaphone className="h-4 w-4 mr-2" /> Campanhas
            </HideableTab>
            <HideableTab value="capture" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Search className="h-4 w-4 mr-2" /> Captação
            </HideableTab>
            <HideableTab value="garimpo" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Inbox className="h-4 w-4 mr-2" /> Garimpo
            </HideableTab>
            <HideableTab value="collected" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <FileText className="h-4 w-4 mr-2" /> Formulários IA
            </HideableTab>
            <HideableTab value="lists" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <ListChecks className="h-4 w-4 mr-2" /> Listas
            </HideableTab>
            <HideableTab value="tags" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Tags className="h-4 w-4 mr-2" /> Tags
            </HideableTab>
            <HideableTab value="blocks" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Ban className="h-4 w-4 mr-2" /> Bloqueios
            </HideableTab>
            <HideableTab value="masscall" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Phone className="h-4 w-4 mr-2" /> Chamada em Massa
            </HideableTab>
            <HideableTab value="massmsg" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <Send className="h-4 w-4 mr-2" /> Mensagem em Massa
            </HideableTab>
            <HideableTab value="promises" className="justify-start px-4 py-2.5 rounded-xl text-sm font-medium transition-all data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow hover:bg-muted/50 border border-transparent data-[state=active]:border-primary/20">
              <ShieldCheck className="h-4 w-4 mr-2" /> Promessas
            </HideableTab>
          </TabsList>
        </div>

        <div className="flex-1 min-w-0">
          <TabsContent value="funnel" className="m-0 focus-visible:outline-none">
            {funnelView === "kanban" ? <CRMBoard stageFilter={stageFilter} sourceFilter={sourceFilter} onClearFilters={() => { setStageFilter(null); setSourceFilter(null); }} /> : funnelView === "list" ? <CRMListTable stageFilter={stageFilter} sourceFilter={sourceFilter} onClearFilters={() => { setStageFilter(null); setSourceFilter(null); }} /> : <SplitPaneCRM />}
          </TabsContent>
          <TabsContent value="analytics" className="m-0 focus-visible:outline-none">
            <CRMAnalytics onFilterClick={(type, value) => {
              if (type === "stage") { setStageFilter(value); setSourceFilter(null); }
              else { setSourceFilter(value); setStageFilter(null); }
              setActiveTab("funnel");
            }} />
          </TabsContent>
          <TabsContent value="contacts" className="m-0 focus-visible:outline-none">
            <ContactsPage />
          </TabsContent>
          <TabsContent value="followup" className="m-0 focus-visible:outline-none">
            <FollowUpPage />
          </TabsContent>
          <TabsContent value="campaigns" className="m-0 focus-visible:outline-none">
            <CampaignsPage />
          </TabsContent>
          <TabsContent value="capture" className="m-0 focus-visible:outline-none">
            <LeadCaptureTab onExported={() => setActiveTab("lists")} />
          </TabsContent>
          <TabsContent value="garimpo" className="m-0 focus-visible:outline-none">
            <WhatsAppExtractorTab />
          </TabsContent>
          <TabsContent value="collected" className="m-0 focus-visible:outline-none">
            <CollectedDataTab />
          </TabsContent>
          <TabsContent value="lists" className="m-0 focus-visible:outline-none">
            <ListsPage />
          </TabsContent>
          <TabsContent value="tags" className="m-0 focus-visible:outline-none">
            <TagsPage />
          </TabsContent>
          <TabsContent value="blocks" className="m-0 focus-visible:outline-none">
            <BlocksPage />
          </TabsContent>
          <TabsContent value="masscall" className="m-0 focus-visible:outline-none">
            <MassCallPage />
          </TabsContent>
          <TabsContent value="massmsg" className="m-0 focus-visible:outline-none">
            <MassMessagePage />
          </TabsContent>
          <TabsContent value="promises" className="m-0 focus-visible:outline-none">
            <PromisesManagerTab />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

// CRMBoard — o Kanban do funil (antigo corpo da CRMPage).
function CRMBoard({ stageFilter, sourceFilter, onClearFilters }: { stageFilter?: string | null; sourceFilter?: string | null; onClearFilters?: () => void }) {
  const [board, setBoard] = useState<Board>({ stages: [], leads: {} });
  const [loading, setLoading] = useState(true);
  const [newStage, setNewStage] = useState("");
  const [dragJid, setDragJid] = useState<string | null>(null);
  const [selected, setSelected] = useState<string[]>([]);       // seleção múltipla de leads (checkboxes)
  const toggleSelected = (jid: string) =>
    setSelected((cur) => (cur.includes(jid) ? cur.filter((j) => j !== jid) : [...cur, jid]));
  const [bulkBusy, setBulkBusy] = useState(false);              // "Mover para..." em andamento
  // Edição do prompt de uma etapa (instruções que o agente segue com leads nela).
  const [editStage, setEditStage] = useState<Stage | null>(null);
  const [editPrompt, setEditPrompt] = useState("");
  const [savingPrompt, setSavingPrompt] = useState(false);

  // Ações por etapa (Criar Lista / Adicionar a Lista Existente / Virar Campanha).
  // Backend: POST /api/crm/stage-action {stage, action, list_name|list_id}.
  const [actionStage, setActionStage] = useState("");           // etapa-alvo da ação atual
  const [newListOpen, setNewListOpen] = useState(false);        // dialog "Criar Nova Lista"
  const [newListName, setNewListName] = useState("");
  const [appendOpen, setAppendOpen] = useState(false);          // dialog "Adicionar a Lista Existente"
  const [existingLists, setExistingLists] = useState<ContactList[]>([]);
  const [selectedListId, setSelectedListId] = useState("");

  // Toolbar de organização do kanban (state local, sem backend — fiel à golden).
  const [boardSearch, setBoardSearch] = useState("");           // busca "Spotlight" de leads
  const [groupBy, setGroupBy] = useState<"etapa" | "origem">("etapa"); // Agrupar colunas
  const [compact, setCompact] = useState(false);                // Visão Compacta
  const [collapsed, setCollapsed] = useState<string[]>([]);     // etapas recolhidas (Recolher coluna)
  const toggleCollapse = (id: string) =>
    setCollapsed((cur) => (cur.includes(id) ? cur.filter((c) => c !== id) : [...cur, id]));
  const [profileLead, setProfileLead] = useState<Lead | null>(null); // drawer "Ver Perfil"

  const reload = useCallback(() => {
    apiGet<Board>("/api/crm/board")
      .then((b) => setBoard({ stages: b.stages ?? [], leads: b.leads ?? {} }))
      .catch((e) => toast.error("Erro ao carregar CRM", { description: (e as Error).message }))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => { reload(); }, [reload]);

  // Lead que saiu do quadro (apagado ou mudado por outra tela) sai da seleção, para a
  // contagem "N leads selecionados" não ficar presa em quem não existe mais.
  useEffect(() => {
    const noQuadro = new Set(Object.values(board.leads).flat().map((l) => l.jid));
    setSelected((cur) => {
      const next = cur.filter((j) => noQuadro.has(j));
      return next.length === cur.length ? cur : next;
    });
  }, [board]);

  // "Mover para...": move os leads marcados para a etapa, um a um, pela mesma rota do arrastar
  // (/api/crm/move), para valerem os mesmos efeitos (aviso, webhook, pausa da IA em
  // "Atendimento Humano"). Antes o botão não fazia nada (auditoria do mês 2, F32).
  const moveSelected = async (stageName: string) => {
    const jids = [...selected];
    if (jids.length === 0 || bulkBusy) return;
    setBulkBusy(true);
    const falharam: string[] = [];
    for (const jid of jids) {
      try {
        await apiPost("/api/crm/move", { jid, stage: stageName });
      } catch {
        falharam.push(jid);
      }
    }
    setBulkBusy(false);
    setSelected(falharam); // os que falharam continuam marcados, para tentar de novo
    reload();
    const movidos = jids.length - falharam.length;
    if (falharam.length === 0) {
      toast.success(`${movidos} ${movidos === 1 ? "lead movido" : "leads movidos"} para "${stageName}"`);
    } else {
      toast.warning(`${movidos} movido(s) para "${stageName}"; ${falharam.length} não (continuam marcados, tente de novo).`);
    }
  };

  // "Disparo em Massa": leva os leads marcados para a Ligação em massa ou a Mensagem em massa,
  // as mesmas telas que a aba Listas usa. Nada é disparado daqui: a dona confere e dispara lá.
  const bulkDispatch = (tipo: "ligacao" | "mensagem") => {
    const todos = Object.values(board.leads).flat();
    const vistos = new Set<string>();
    const contacts: Contact[] = [];
    for (const jid of selected) {
      const l = todos.find((x) => x.jid === jid);
      if (!l) continue;
      const fone = (l.phone || (jid.endsWith("@s.whatsapp.net") ? jid.split("@")[0] : "")).replace(/\D/g, "");
      if (fone.length < 10 || vistos.has(fone)) continue;
      vistos.add(fone);
      contacts.push({ jid: `${fone}@s.whatsapp.net`, phone: fone, name: l.name ?? "", push_name: "", business_name: "", is_group: false });
    }
    if (contacts.length === 0) {
      toast.error("Nenhum dos leads marcados tem telefone para o disparo.");
      return;
    }
    if (tipo === "ligacao") {
      useMassCallStore.getState().setContacts(contacts);
      setView("mass-call");
    } else {
      useMassMessageStore.getState().setContacts(contacts);
      setView("mass-message");
    }
    toast.info(`${contacts.length} contato(s) levados para a ${tipo === "ligacao" ? "Ligação" : "Mensagem"} em massa. Confira e dispare por lá.`);
    setSelected([]);
  };

  // Criar Lista: copia os contatos da etapa para uma NOVA lista.
  const createListFromStage = async () => {
    if (!newListName.trim() || !actionStage) return;
    try {
      const r = await apiPost<{ count: number }>("/api/crm/stage-action", {
        stage: actionStage,
        action: "new_list",
        list_name: newListName,
      });
      toast.success(`Lista criada com ${r.count} leads!`);
      setNewListOpen(false);
      setNewListName("");
    } catch (e) { toast.error((e as Error).message); }
  };

  // Abre o dialog "Adicionar a Lista Existente" (carrega as listas primeiro).
  const openAppendDialog = async (stageName: string) => {
    setActionStage(stageName);
    try {
      const lists = await listContactLists();
      setExistingLists(lists || []);
      setAppendOpen(true);
    } catch {
      toast.error("Erro ao carregar listas");
    }
  };

  // Adiciona os contatos da etapa à lista selecionada.
  const appendStageToList = async () => {
    if (!selectedListId || !actionStage) return;
    try {
      const r = await apiPost<{ count: number }>("/api/crm/stage-action", {
        stage: actionStage,
        action: "append_list",
        list_id: selectedListId,
      });
      toast.success(`${r.count} leads adicionados à lista!`);
      setAppendOpen(false);
      setSelectedListId("");
    } catch (e) { toast.error((e as Error).message); }
  };

  // Vira Campanha: joga os contatos da etapa numa nova campanha de disparo.
  const stageToCampaign = async (stageName: string) => {
    try {
      toast.info("Processando fila de campanha...");
      const r = await apiPost<{ count: number }>("/api/crm/stage-action", {
        stage: stageName,
        action: "campaign",
      });
      toast.success(`Campanha criada com ${r.count} leads!`);
    } catch (e) { toast.error((e as Error).message); }
  };

  const addStage = async () => {
    if (!newStage.trim()) return;
    try {
      await apiPost("/api/crm/stages", { name: newStage.trim(), color: "#3b82f6" });
      setNewStage("");
      reload();
    } catch (e) { toast.error((e as Error).message); }
  };

  const delStage = async (id: string, name: string) => {
    if (!confirm(`Apagar a etapa "${name}"? Os contatos nela não são apagados.`)) return;
    try { await apiDelete(`/api/crm/stages/${id}`); reload(); }
    catch (e) { toast.error((e as Error).message); }
  };

  // Abre o editor de prompt de uma etapa.
  const openPromptEditor = (st: Stage) => {
    setEditStage(st);
    setEditPrompt(st.prompt ?? "");
  };

  // Salva o prompt da etapa (PUT mantém nome/cor e atualiza o prompt).
  const savePrompt = async () => {
    if (!editStage) return;
    setSavingPrompt(true);
    try {
      await apiPut(`/api/crm/stages/${editStage.id}`, {
        name: editStage.name,
        color: editStage.color,
        prompt: editPrompt,
      });
      toast.success("Prompt da etapa salvo");
      setEditStage(null);
      reload();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingPrompt(false);
    }
  };

  // Move um lead pra uma etapa (soltar o card na coluna).
  const drop = async (stageName: string) => {
    if (!dragJid) return;
    const jid = dragJid;
    setDragJid(null);
    // Otimista: reflete na UI já.
    setBoard((b) => {
      const leads: Record<string, Lead[]> = {};
      let moved: Lead | undefined;
      for (const [st, arr] of Object.entries(b.leads)) {
        leads[st] = arr.filter((l) => {
          if (l.jid === jid) { moved = l; return false; }
          return true;
        });
      }
      if (moved) leads[stageName] = [moved, ...(leads[stageName] ?? [])];
      return { ...b, leads };
    });
    try { await apiPost("/api/crm/move", { jid, stage: stageName }); }
    catch (e) { toast.error("Erro ao mover", { description: (e as Error).message }); reload(); }
  };

  if (loading) return <div className="p-6 text-muted-foreground">Carregando CRM…</div>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4 bg-muted/10 p-4 rounded-2xl border border-border/50">
        <div>
           <h3 className="text-sm font-bold text-foreground flex items-center gap-2"><KanbanSquare className="w-4 h-4 text-primary" /> Funil de contatos</h3>
           <p className="text-xs text-muted-foreground mt-1 max-w-lg">
             Crie etapas e arraste os contatos. Clique no <Sparkles className="mx-1 inline h-3 w-3 text-primary" /> de uma etapa para definir o <strong>prompt</strong>. A etapa "Atendimento Humano" pausa a IA.
           </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {selected.length > 0 && (
            <div className="flex items-center gap-2 bg-primary/10 border border-primary/20 p-1 px-3 rounded-xl animate-in fade-in mr-2">
              <span className="text-xs font-bold text-primary">{selected.length} {selected.length === 1 ? "lead selecionado" : "leads selecionados"}</span>
              <div className="w-px h-4 bg-primary/20 mx-1" />
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="ghost" disabled={bulkBusy || board.stages.length === 0} className="h-7 text-xs px-2 hover:bg-primary/20 text-primary">
                    {bulkBusy ? "Movendo…" : "Mover para..."}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-52 max-h-72 overflow-y-auto rounded-xl">
                  {board.stages.map((st) => (
                    <DropdownMenuItem key={st.id} onClick={() => moveSelected(st.name)}>
                      <span className="mr-2 h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: st.color }} /> {st.name}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="ghost" disabled={bulkBusy} className="h-7 text-xs px-2 hover:bg-primary/20 text-primary">Disparo em Massa</Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 rounded-xl">
                  <DropdownMenuItem onClick={() => bulkDispatch("ligacao")}>
                    <Phone className="mr-2 h-4 w-4" /> Ligação em massa (IA)
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => bulkDispatch("mensagem")}>
                    <Send className="mr-2 h-4 w-4" /> Mensagem em massa
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <button onClick={() => setSelected([])} title="Limpar seleção" className="text-primary/70 transition-colors hover:text-primary">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={boardSearch}
              onChange={(e) => setBoardSearch(e.target.value)}
              placeholder="Buscar leads (Spotlight)..."
              className="h-10 w-64 rounded-xl bg-background border-border/50 shadow-sm pl-9 transition-all focus:w-72"
            />
          </div>
          <div className="flex items-center gap-1 bg-background border border-border/50 rounded-xl p-1 shadow-sm mx-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setGroupBy(groupBy === "etapa" ? "origem" : "etapa")}
              title="Agrupar colunas"
              className={cn("px-2 h-8 rounded-lg", groupBy !== "etapa" && "bg-primary/10 text-primary")}
            >
              <Layers className="h-4 w-4 mr-1" /> {groupBy === "etapa" ? "Etapa" : "Origem"}
            </Button>
            <div className="w-px h-4 bg-border mx-1" />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCompact(!compact)}
              title="Visão Compacta"
              className={cn("px-2 h-8 rounded-lg", compact && "bg-muted")}
            >
              {compact ? <Maximize2 className="h-4 w-4 text-muted-foreground" /> : <Minimize2 className="h-4 w-4 text-muted-foreground" />}
            </Button>
          </div>
          <Input
            value={newStage}
            onChange={(e) => setNewStage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addStage()}
            placeholder="Nome da etapa…"
            className="h-10 w-48 rounded-xl bg-background border-border/50 shadow-sm"
          />
          <Button size="sm" className="gap-1 rounded-xl shadow-glow h-10 px-4" onClick={addStage}><Plus className="h-4 w-4" /> Nova Etapa</Button>
        </div>
      </div>

      {(stageFilter || sourceFilter) && (
        <div className="flex items-center gap-2 px-4 py-2 bg-primary/5 border border-primary/20 rounded-xl animate-in fade-in">
          <span className="text-xs text-muted-foreground">Filtro ativo:</span>
          {stageFilter && <Badge variant="secondary" className="gap-1">Etapa: {stageFilter} <X className="h-3 w-3 cursor-pointer" onClick={onClearFilters} /></Badge>}
          {sourceFilter && <Badge variant="secondary" className="gap-1">Origem: {sourceFilter} <X className="h-3 w-3 cursor-pointer" onClick={onClearFilters} /></Badge>}
          <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={onClearFilters}>Limpar</Button>
        </div>
      )}

      {/* Board: colunas roláveis na horizontal (responsivo mobile) */}
      <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
        {/* AGRUPAR POR ORIGEM (relato #6 da dona: "tanto faz clicar em Etapa ou Origem"):
            colunas somente-leitura por fonte do lead. Origem é o canal de entrada, então
            não há arrastar aqui; o agrupamento por Etapa (com arrastar) segue abaixo. */}
        {groupBy === "origem" && (() => {
          const q = boardSearch.trim().toLowerCase();
          const all = Object.values(board.leads).flat().filter(
            (l) => (!q || (l.name ?? "").toLowerCase().includes(q) || (l.phone ?? "").toLowerCase().includes(q))
              && (!sourceFilter || (l.source ?? "") === sourceFilter)
          );
          const bySource: Record<string, Lead[]> = {};
          for (const l of all) {
            const key = (l.source ?? "").trim() || "Sem origem";
            (bySource[key] ??= []).push(l);
          }
          const groups = Object.keys(bySource).sort((x, y) => bySource[y].length - bySource[x].length);
          if (groups.length === 0) {
            return (
              <div className="flex flex-col items-center justify-center h-32 w-full border-2 border-dashed border-border/50 rounded-xl bg-muted/5">
                <Inbox className="h-8 w-8 text-muted-foreground/30 mb-2" />
                <span className="text-xs text-muted-foreground font-medium">Nenhum lead para agrupar por origem</span>
              </div>
            );
          }
          return groups.map((src) => (
            <div key={src} className={cn("flex shrink-0 flex-col rounded-2xl border border-border/50 bg-glass shadow-soft overflow-hidden", compact ? "w-60" : "w-72")}>
              <div className="flex items-center justify-between border-b border-border/50 bg-muted/20 p-3" style={{ borderTopColor: "#6366f1", borderTopWidth: 4 }}>
                <span className="truncate text-[0.95rem] font-semibold flex items-center gap-1.5">
                  <Layers className="h-3.5 w-3.5 text-indigo-400 shrink-0" /> {src}
                </span>
                <span className="rounded-full bg-background px-2.5 py-0.5 text-xs font-medium text-muted-foreground shadow-sm">{bySource[src].length}</span>
              </div>
              <div className="flex flex-col gap-3 p-3 min-h-[100px] overflow-y-auto">
                {bySource[src].map((l) => (
                  <Card key={l.jid} className="p-3 text-sm border-border/60 hover:-translate-y-1 hover:shadow-glow transition-all duration-300 bg-background/80 hover:bg-card rounded-xl cursor-pointer" onClick={() => setProfileLead(l)}>
                    <div className="flex items-center gap-1.5 font-medium">
                      <AvatarInitial name={l.name || "Lead"} />
                      <div className="min-w-0">
                        <div className="truncate font-semibold">{l.name || "Lead"}</div>
                        <span className="text-xs text-muted-foreground flex items-center gap-1"><Phone className="h-3 w-3" /> {l.phone}</span>
                      </div>
                    </div>
                    {l.notes && <div className="mt-2 line-clamp-2 text-xs text-muted-foreground/80 font-medium leading-relaxed">{l.notes}</div>}
                  </Card>
                ))}
              </div>
            </div>
          ));
        })()}
        {groupBy === "etapa" && board.stages.filter((st) => !stageFilter || st.name === stageFilter).map((st) => {
          const q = boardSearch.trim().toLowerCase();
          const leads = (board.leads[st.name] ?? []).filter(
            (l) => (!q || (l.name ?? "").toLowerCase().includes(q) || (l.phone ?? "").toLowerCase().includes(q))
              && (!sourceFilter || (l.source ?? "") === sourceFilter)
          );
          // Coluna recolhida (Recolher coluna): faixa estreita clicável que reexpande.
          if (collapsed.includes(st.id)) {
            return (
              <div
                key={st.id}
                onClick={() => toggleCollapse(st.id)}
                title={`Expandir etapa: ${st.name}`}
                className="flex w-12 shrink-0 flex-col items-center rounded-2xl border border-border/50 bg-glass shadow-soft overflow-hidden transition-all cursor-pointer hover:bg-muted/20 hover:border-primary/50 group/col"
              >
                <div className="w-full h-1.5" style={{ backgroundColor: st.color }} />
                <div className="py-4 px-2 flex flex-col items-center gap-6 h-full mt-2">
                  <span className="rounded-full bg-background px-2 py-0.5 text-[10px] font-medium text-muted-foreground shadow-sm border border-border/50 group-hover/col:text-primary">{leads.length}</span>
                  <span className="text-[0.85rem] font-semibold tracking-wider text-muted-foreground group-hover/col:text-primary transition-colors whitespace-nowrap" style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}>{st.name}</span>
                </div>
              </div>
            );
          }
          return (
            <div
              key={st.id}
              className={cn("flex shrink-0 flex-col rounded-2xl border border-border/50 bg-glass shadow-soft overflow-hidden transition-all duration-300", compact ? "w-60" : "w-72")}
              onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("ring-2", "ring-primary/50", "bg-primary/5"); }}
              onDragLeave={(e) => { e.currentTarget.classList.remove("ring-2", "ring-primary/50", "bg-primary/5"); }}
              onDrop={(e) => { e.currentTarget.classList.remove("ring-2", "ring-primary/50", "bg-primary/5"); drop(st.name); }}
            >
              <div className="flex items-center justify-between border-b border-border/50 bg-muted/20 p-3" style={{ borderTopColor: st.color, borderTopWidth: 4 }}>
                <span className="truncate text-[0.95rem] font-semibold flex items-center gap-1.5">
                  <button
                    onClick={() => toggleCollapse(st.id)}
                    title="Recolher coluna"
                    className="text-muted-foreground hover:text-primary transition-colors shrink-0 p-0.5 rounded hover:bg-background shadow-sm opacity-50 hover:opacity-100"
                  >
                    <ChevronsLeft className="h-3.5 w-3.5" />
                  </button>
                  {st.name}
                  {st.prompt && <span title="Possui automação configurada" className="inline-flex"><Zap className="h-3.5 w-3.5 text-amber-500 fill-amber-500 opacity-80" /></span>}
                </span>
                <div className="flex items-center gap-1.5">
                  <span className="rounded-full bg-background px-2.5 py-0.5 text-xs font-medium text-muted-foreground shadow-sm">{leads.length}</span>
                  <button className="text-muted-foreground hover:text-primary transition-colors p-1 rounded-md hover:bg-background shadow-sm" title="Ordenar coluna">
                    <ArrowUpDown className="h-3.5 w-3.5" />
                  </button>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button className="text-muted-foreground hover:text-primary transition-colors" title="Ações da etapa">
                        <MoreVertical className="h-4 w-4" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48 rounded-xl">
                      <DropdownMenuItem onClick={() => { setActionStage(st.name); setNewListOpen(true); }}>
                        <ListPlus className="mr-2 h-4 w-4" /> Criar lista
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => openAppendDialog(st.name)}>
                        <Users className="mr-2 h-4 w-4" /> Adicionar a lista…
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => stageToCampaign(st.name)}>
                        <Megaphone className="mr-2 h-4 w-4 text-emerald-500" /> Virar campanha
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                  <button
                    onClick={() => openPromptEditor(st)}
                    title={st.prompt ? "Editar prompt da etapa (definido)" : "Definir prompt da etapa"}
                    className={st.prompt ? "text-primary hover:text-primary/70 transition-colors drop-shadow-sm" : "text-muted-foreground hover:text-primary transition-colors"}
                  >
                    <Sparkles className="h-4 w-4" />
                  </button>
                  <button onClick={() => delStage(st.id, st.name)} className="text-muted-foreground hover:text-destructive transition-colors ml-1">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              {/* Removido: "Valor no Funil" (R$ 1.250 inventado por lead) — o CRM não guarda valor de negócio. */}
              <div className="flex flex-col gap-3 p-3 min-h-[100px] overflow-y-auto">
                {leads.map((l) => (
                  <Card
                    key={l.jid}
                    draggable
                    onDragStart={() => setDragJid(l.jid)}
                    className="relative cursor-grab p-3 active:cursor-grabbing border-border/60 hover:-translate-y-1 hover:shadow-glow transition-all duration-300 bg-background/80 hover:bg-card group rounded-xl"
                  >
                    {/* Removido: selo "Ana está visualizando este lead" (presença inventada). */}
                    <div className="absolute -left-2 -top-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                      <input
                        type="checkbox"
                        checked={selected.includes(l.jid)}
                        onChange={() => toggleSelected(l.jid)}
                        className="w-4 h-4 rounded border-border/50 bg-background cursor-pointer"
                      />
                    </div>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2.5 font-medium text-[0.95rem]">
                        <AvatarInitial name={l.name || "Desconhecido"} />
                        <div className="flex flex-col">
                          <span>{l.name || "Lead"}</span>
                          <span className="text-[0.65rem] text-muted-foreground flex items-center gap-0.5"><Phone className="h-2.5 w-2.5"/> {l.phone}</span>
                        </div>
                      </div>
                      {/* Nota real do lead (0-100), só quando o servidor tem uma. Antes eram bolinhas fixas. */}
                      {l.score > 0 && (
                        <span
                          className={`mt-1 text-[0.6rem] font-bold px-1.5 py-0.5 rounded border ${l.score >= 70 ? "text-emerald-500 bg-emerald-500/10 border-emerald-500/20" : l.score >= 40 ? "text-amber-500 bg-amber-500/10 border-amber-500/20" : "text-muted-foreground bg-muted/30 border-border/50"}`}
                          title="Nota do lead (0 a 100)"
                        >
                          {l.score}
                        </span>
                      )}
                    </div>
                    {l.notes && <div className="mt-2 line-clamp-2 text-xs text-muted-foreground/80 font-medium leading-relaxed">{l.notes}</div>}
                    
                    {/* Botões de Ação Rápida */}
                    <div className="mt-3 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                       <span className="text-[0.65rem] text-muted-foreground">{l.updated_at ? `Atualizado ${fmtAgo(l.updated_at)}` : ""}</span>
                       <Button size="sm" variant="secondary" onClick={() => setProfileLead(l)} className="h-6 text-[10px] px-2 rounded-full hover:bg-primary hover:text-primary-foreground font-bold">
                         Ver Perfil
                       </Button>
                    </div>
                  </Card>
                ))}
                {leads.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-32 border-2 border-dashed border-border/50 rounded-xl bg-muted/5">
                    <Inbox className="h-8 w-8 text-muted-foreground/30 mb-2" />
                    <span className="text-xs text-muted-foreground font-medium">Nenhum lead nesta etapa</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {/* Coluna "sem etapa" (leads com stage vazio/órfão) — só no modo Etapa */}
        {groupBy === "etapa" && (board.leads[""]?.length ?? 0) > 0 && (
          <div className="flex w-72 shrink-0 flex-col rounded-2xl border border-dashed border-border/60 bg-muted/10 overflow-hidden"
            onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("ring-2", "ring-muted-foreground/50", "bg-muted/20"); }}
            onDragLeave={(e) => { e.currentTarget.classList.remove("ring-2", "ring-muted-foreground/50", "bg-muted/20"); }}
            onDrop={(e) => { e.currentTarget.classList.remove("ring-2", "ring-muted-foreground/50", "bg-muted/20"); drop(""); }}>
            <div className="border-b border-border/50 bg-muted/5 p-3 text-sm font-semibold text-muted-foreground">Sem etapa</div>
            <div className="flex flex-col gap-3 p-3 min-h-[100px]">
              {board.leads[""].map((l) => (
                <Card key={l.jid} draggable onDragStart={() => setDragJid(l.jid)} className="cursor-grab p-3 text-sm active:cursor-grabbing hover:-translate-y-1 transition-all duration-300 rounded-xl hover:shadow-glow border-border/60 group">
                  <div className="flex items-center gap-1.5 font-medium"><Phone className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary transition-colors" /> {l.phone}</div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Drawer "Ver Perfil" do lead (só dados reais). */}
      {profileLead && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm" onClick={() => setProfileLead(null)}>
          <div className="w-full max-w-md h-full bg-background border-l border-border/50 flex flex-col shadow-2xl animate-in slide-in-from-right-full overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 pb-0 flex items-center justify-between">
              <Button variant="ghost" size="icon" onClick={() => setProfileLead(null)} className="rounded-full bg-muted/50"><X className="h-5 w-5" /></Button>
            </div>
            <div className="p-6 space-y-6">
              <div className="flex items-center gap-3">
                <AvatarInitial name={profileLead.name || "Lead"} />
                <div>
                  <h3 className="text-lg font-bold">{profileLead.name || "Lead"}</h3>
                  <span className="text-sm text-muted-foreground flex items-center gap-1"><Phone className="h-3 w-3" /> {profileLead.phone}</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {/* Antes: "Quente (Atrasado)" e "R$ 1.250,00" fixos para todo lead. */}
                <div className="bg-muted/10 border border-border/50 p-3 rounded-xl">
                  <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Nota do lead</span>
                  <div className="font-bold text-amber-500 flex items-center gap-1 mt-1"><Flame className="w-4 h-4" /> {profileLead.score > 0 ? `${profileLead.score} / 100` : "Sem nota ainda"}</div>
                </div>
                <div className="bg-muted/10 border border-border/50 p-3 rounded-xl">
                  <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Origem</span>
                  <div className="font-bold mt-1">{profileLead.source || "—"}</div>
                  {profileLead.updated_at && <div className="text-[11px] text-muted-foreground mt-0.5">Atualizado {fmtAgo(profileLead.updated_at)}</div>}
                </div>
              </div>
              {profileLead.notes && (
                <div className="bg-muted/10 border border-border/50 p-3 rounded-xl">
                  <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Anotações da IA</span>
                  <p className="text-sm mt-1 text-muted-foreground leading-relaxed">{profileLead.notes}</p>
                </div>
              )}
              <div className="bg-muted/10 border border-border/50 p-3 rounded-xl">
                <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">JID (Sistema)</span>
                <p className="font-mono text-xs break-all mt-1">{profileLead.jid}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Criar Nova Lista a partir da etapa */}
      <Dialog open={newListOpen} onOpenChange={setNewListOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Criar Nova Lista</DialogTitle>
            <DialogDescription>
              Todos os contatos da etapa "{actionStage}" serão copiados para esta nova lista.
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder="Nome da lista..."
            value={newListName}
            onChange={(e) => setNewListName(e.target.value)}
          />
          <DialogFooter>
            <Button variant="ghost" onClick={() => setNewListOpen(false)}>Cancelar</Button>
            <Button onClick={createListFromStage}>Criar Lista</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Adicionar contatos da etapa a uma lista existente */}
      <Dialog open={appendOpen} onOpenChange={setAppendOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Adicionar a Lista Existente</DialogTitle>
            <DialogDescription>
              Os contatos da etapa "{actionStage}" serão adicionados à lista selecionada.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-2 max-h-[40vh] overflow-y-auto">
            {existingLists.length === 0 && (
              <p className="text-sm text-muted-foreground">Nenhuma lista encontrada.</p>
            )}
            {existingLists.map((l) => (
              <Button
                key={l.id}
                variant={selectedListId === l.id ? "default" : "outline"}
                className="justify-start font-normal"
                onClick={() => setSelectedListId(l.id)}
              >
                <ListChecks className="w-4 h-4 mr-2" /> {l.name}
              </Button>
            ))}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAppendOpen(false)}>Cancelar</Button>
            <Button onClick={appendStageToList} disabled={!selectedListId}>Adicionar Contatos</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Editor do prompt da etapa */}
      <Dialog open={!!editStage} onOpenChange={(o) => !o && setEditStage(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" /> Prompt da etapa — {editStage?.name}
            </DialogTitle>
            <DialogDescription>
              Instruções que o agente segue quando o lead está nesta etapa. Use para dizer
              como conduzir o contato para a próxima etapa (o que oferecer, tom, próximo passo).
              Deixe vazio para o agente usar só o prompt padrão.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            rows={6}
            value={editPrompt}
            onChange={(e) => setEditPrompt(e.target.value)}
            placeholder="Ex.: O lead demonstrou interesse. Seja direto: envie condições e formas de pagamento e chame para fechar."
            className="rounded-xl border-border/50 bg-muted/10 p-4"
          />
          <DialogFooter className="pt-2">
            <Button variant="ghost" onClick={() => setEditStage(null)} className="rounded-xl">Cancelar</Button>
            <Button onClick={savePrompt} disabled={savingPrompt} className="rounded-xl shadow-glow px-6">{savingPrompt ? "Salvando…" : "Salvar prompt"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// CRMListTable — visão "Lista" do funil (fiel à golden CPe). Achata todos os leads
// de todas as etapas numa tabela plana. Usa o mesmo /api/crm/board das outras visões.
type FlatLead = Lead & { stageName: string; updated_at?: string };
function CRMListTable({ stageFilter, sourceFilter, onClearFilters }: { stageFilter?: string | null; sourceFilter?: string | null; onClearFilters?: () => void }) {
  const [board, setBoard] = useState<Board>({ stages: [], leads: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<Board>("/api/crm/board")
      .then((b) => setBoard({ stages: b.stages ?? [], leads: b.leads ?? {} }))
      .catch((e) => toast.error("Erro ao carregar CRM", { description: (e as Error).message }))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-muted-foreground">Carregando Tabela…</div>;

  const rows: FlatLead[] = board.stages
    .filter((st) => !stageFilter || st.name === stageFilter)
    .flatMap((st) =>
      (board.leads[st.name] ?? [])
        .filter((l) => !sourceFilter || (l.source ?? "") === sourceFilter)
        .map((l) => ({ ...l, stageName: st.name }))
    );

  return (
    <div className="bg-card/50 rounded-2xl border border-border/50 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold">Leads por Etapa</h3>
        {(stageFilter || sourceFilter) && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Filtro:</span>
            {stageFilter && <Badge variant="secondary" className="gap-1">Etapa: {stageFilter} <X className="h-3 w-3 cursor-pointer" onClick={onClearFilters} /></Badge>}
            {sourceFilter && <Badge variant="secondary" className="gap-1">Origem: {sourceFilter} <X className="h-3 w-3 cursor-pointer" onClick={onClearFilters} /></Badge>}
            <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={onClearFilters}>Limpar</Button>
          </div>
        )}
      </div>
      <div className="rounded-xl border border-border/50 overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/20">
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Telefone</TableHead>
              <TableHead>Etapa (Funil)</TableHead>
              <TableHead>Últ. Atualização</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((l, i) => (
              <TableRow key={l.jid || i}>
                <TableCell className="font-medium">{l.name || l.phone}</TableCell>
                <TableCell className="text-muted-foreground">{l.phone}</TableCell>
                <TableCell>
                  <Badge variant="outline">{l.stageName}</Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">{l.updated_at || "—"}</TableCell>
              </TableRow>
            ))}
            {rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                  Nenhum lead encontrado no funil.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
