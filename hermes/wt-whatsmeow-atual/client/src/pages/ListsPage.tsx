import { useState, useRef } from "react";
import { ListChecks, Trash2, PhoneForwarded, Users, Plus, Activity, BarChart2, Filter, FileUp, Sparkles, Send, Search, ShieldCheck, Download, MoreVertical, Copy } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listContactLists, deleteContactList, createContactList, type ContactList } from "@/services/broadcast";
import { downloadCSV, csvTelefone } from "@/lib/csv";
import { useSessions } from "@/stores/sessions";
import { useMassCallStore } from "@/stores/masscall";
import { useMassMessageStore } from "@/stores/massmsg";
import { setView } from "@/stores/navigation";
import type { Contact } from "@/types/contacts";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// parsePhones extrai números de um texto colado OU de um arquivo (txt/csv). Aceita
// números separados por vírgula, ponto-e-vírgula, espaço ou quebra de linha. Só
// mantém dígitos de cada token; descarta tokens com menos de 10 dígitos (inválidos).
function parsePhones(raw: string): string[] {
  const tokens = raw.split(/[\s,;]+/);
  const out: string[] = [];
  const seen = new Set<string>();
  for (const t of tokens) {
    const d = t.replace(/\D/g, "");
    if (d.length >= 10 && d.length <= 13 && !seen.has(d)) {
      seen.add(d);
      out.push(d);
    }
  }
  return out;
}

const fmtDate = (s: string) => {
  try {
    return new Date(s).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return s;
  }
};

export const ListsPage = () => {
  const qc = useQueryClient();
  const sessions = useSessions((s) => s.sessions);
  const pairedSession = sessions.find((s) => s.paired);
  const [busy, setBusy] = useState<string | null>(null);

  // Criar lista UI State
  const [showCreate, setShowCreate] = useState(false);
  const [createMode, setCreateMode] = useState<"static" | "smart">("static");
  const [newName, setNewName] = useState("");
  const [rawPhones, setRawPhones] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [creating, setCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const onFile = async (f: File | undefined) => {
    if (!f) return;
    const text = await f.text();
    setRawPhones((prev) => (prev ? prev + "\n" : "") + text);
    toast.success(`Arquivo "${f.name}" carregado`);
  };

  const onCreate = async () => {
    const phones = parsePhones(rawPhones);
    if (!newName.trim()) { toast.error("Dê um nome à lista"); return; }
    if (phones.length === 0) { toast.error("Nenhum número válido encontrado"); return; }
    setCreating(true);
    try {
      await createContactList(newName.trim(), phones);
      toast.success(`Lista criada com ${phones.length} números`);
      setNewName(""); setRawPhones(""); setShowCreate(false);
      qc.invalidateQueries({ queryKey: ["contact-lists"] });
    } catch (e: any) {
      toast.error("Erro ao criar", { description: e.message });
    } finally {
      setCreating(false);
    }
  };

  const { data: lists = [], isLoading } = useQuery({
    queryKey: ["contact-lists"],
    queryFn: () => listContactLists(),
  });

  const onDelete = async (l: ContactList) => {
    if (!window.confirm(`Excluir a lista "${l.name}"?`)) return;
    setBusy(l.id);
    try {
      await deleteContactList(l.id);
      toast.success("Lista excluída");
      qc.invalidateQueries({ queryKey: ["contact-lists"] });
    } catch (e: any) {
      toast.error("Erro ao excluir", { description: e.message });
    } finally {
      setBusy(null);
    }
  };

  const callList = (l: ContactList) => {
    const contacts: Contact[] = l.phones.map((p) => ({
      jid: `${p}@s.whatsapp.net`,
      phone: p,
      name: "",
      push_name: "",
      business_name: "",
      is_group: false,
    }));
    useMassCallStore.getState().setContacts(contacts);
    setView("mass-call");
  };

  // Disparo de campanha de MENSAGEM (WhatsApp): mesma ideia do callList, mas leva pro
  // fluxo de mensagem em massa em vez de ligacao. Antes o botao Send nao tinha onClick.
  const messageList = (l: ContactList) => {
    const contacts: Contact[] = l.phones.map((p) => ({
      jid: `${p}@s.whatsapp.net`,
      phone: p,
      name: "",
      push_name: "",
      business_name: "",
      is_group: false,
    }));
    useMassMessageStore.getState().setContacts(contacts);
    setView("mass-message");
  };

  // Planilha pela lib/csv: telefone como texto (sem virar 5,59E+12) e ";"/BOM para o Excel.
  const baixarListaCSV = (l: ContactList) => {
    downloadCSV(`${l.name.replace(/[^a-zA-Z0-9_-]/g, "_")}.csv`, ["telefone"], l.phones.map((p) => [csvTelefone(p)]));
    toast.success(`Lista "${l.name}" baixada (${l.count} números)`);
  };

  const duplicateList = async (l: ContactList) => {
    setBusy(l.id);
    try {
      await createContactList(`${l.name} (cópia)`, l.phones);
      toast.success(`Lista duplicada como "${l.name} (cópia)"`);
      qc.invalidateQueries({ queryKey: ["contact-lists"] });
    } catch (e: any) {
      toast.error("Erro ao duplicar", { description: e.message });
    } finally {
      setBusy(null);
    }
  };

  // A API só devolve dados básicos da lista (id/nome/contagem/criação). Métricas de
  // "saúde" e "conversão" ainda não existem no backend — antes eram FALSIFICADAS com
  // Math.random() e exibidas como reais, enganando a dona. Não inventamos números:
  // marcamos como indisponíveis até haver telemetria real por lista.
  const enrichedLists = lists.map(l => ({
    ...l,
    type: l.name.toLowerCase().includes('dinâmica') ? 'smart' : 'static',
  }));

  const filteredLists = enrichedLists.filter(l => l.name.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Users className="h-6 w-6 text-primary" /> Audiências e Segmentação
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Crie listas estáticas ou dinâmicas para hiper-segmentar seus disparos.
          </p>
        </div>
        <div className="flex items-center gap-2">
           <Button variant="outline" disabled className="gap-2 bg-glass shadow-sm opacity-50 cursor-not-allowed" title="Listas dinâmicas por regra ainda não disponíveis">
             <Sparkles className="h-4 w-4 text-amber-500" /> Lista Dinâmica
             <Badge variant="muted" className="ml-1 h-4 text-[0.55rem] px-1">Em breve</Badge>
           </Button>
           <Button className="gap-2 shadow-glow" onClick={() => { setShowCreate(true); setCreateMode("static"); }}>
             <Plus className="h-4 w-4" /> Nova Lista
           </Button>
        </div>
      </div>

      {/* Creation Builder */}
      {showCreate && (
        <Card className="border-primary/50 shadow-[0_0_30px_rgba(16,185,129,0.1)] animate-in slide-in-from-top-4 overflow-hidden relative">
          <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
          <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
             <div className="flex items-center gap-2">
                <Button variant={createMode === "static" ? "default" : "ghost"} size="sm" onClick={() => setCreateMode("static")}>Lista Estática (CSV/Colar)</Button>
                <Button variant={createMode === "smart" ? "default" : "ghost"} size="sm" disabled onClick={() => setCreateMode("smart")} className="gap-2 opacity-50 cursor-not-allowed" title="Listas dinâmicas por regra ainda não disponíveis"><Sparkles className="w-3.5 h-3.5"/> Lista Dinâmica (Regras) <Badge variant="muted" className="ml-1 h-4 text-[0.55rem] px-1">Em breve</Badge></Button>
             </div>
             <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}>Cancelar</Button>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
               <div className="space-y-4">
                 <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Nome da Lista (ex: VIPs Inativos)" className="text-lg font-medium h-12 bg-glass" />
                 
                 {createMode === "smart" ? (
                   <div className="p-6 bg-glass border border-border/50 rounded-xl space-y-4 border-dashed">
                      <div className="flex items-center gap-3 text-muted-foreground mb-4">
                        <Filter className="w-5 h-5"/>
                        <p className="text-sm font-medium">Defina as regras para popular automaticamente:</p>
                      </div>
                      <Badge variant="muted" className="gap-1 mb-1"><Sparkles className="w-3 h-3" /> Em breve</Badge>
                      <select disabled className="w-full bg-background border border-border/50 rounded-md p-3 text-sm text-foreground opacity-50 cursor-not-allowed">
                         <option>Leads que possuem a Tag: Carrinho Abandonado</option>
                         <option>Leads inativos há mais de 30 dias</option>
                         <option>Leads que não atenderam a última campanha</option>
                      </select>
                      <Button variant="outline" disabled className="w-full gap-2 border-dashed opacity-50 cursor-not-allowed"><Plus className="w-4 h-4"/> Adicionar Regra (AND)</Button>
                   </div>
                 ) : (
                   <Textarea
                     value={rawPhones}
                     onChange={(e) => setRawPhones(e.target.value)}
                     rows={8}
                     className="bg-glass resize-none"
                     placeholder="Cole os números aqui (um por linha, ou separados por vírgula). Ex: 5511999999999"
                   />
                 )}
               </div>

               {createMode === "static" && (
                 <div 
                   className={cn(
                     "border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-8 text-center transition-all bg-muted/10",
                     isDragging ? "border-primary bg-primary/5" : "border-border/50 hover:border-primary/50"
                   )}
                   onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                   onDragLeave={() => setIsDragging(false)}
                   onDrop={(e) => {
                     e.preventDefault(); setIsDragging(false);
                     onFile(e.dataTransfer.files?.[0]);
                   }}
                 >
                   <div className="w-16 h-16 rounded-full bg-background flex items-center justify-center shadow-sm mb-4 border border-border/50 text-muted-foreground">
                     <FileUp className="w-8 h-8" />
                   </div>
                   <h3 className="font-bold text-lg">Arraste seu CSV para cá</h3>
                   <p className="text-sm text-muted-foreground mt-2 max-w-[200px] mb-6">Suporta arquivos .txt e .csv com milhares de contatos.</p>
                   
                   <input ref={fileRef} type="file" accept=".txt,.csv,text/plain" className="hidden" onChange={(e) => onFile(e.target.files?.[0])} />
                   <Button variant="secondary" onClick={() => fileRef.current?.click()} className="w-full max-w-[200px]">Procurar Arquivo</Button>
                 </div>
               )}
            </div>

            <div className="mt-8 flex items-center justify-between border-t border-border/50 pt-4">
               {createMode === "static" ? (
                 <div className="flex items-center gap-2 text-sm text-muted-foreground">
                   <ShieldCheck className="w-4 h-4 text-emerald-500" />
                   <strong className="text-foreground">{parsePhones(rawPhones).length}</strong> contatos válidos detectados e higienizados.
                 </div>
               ) : (
                 <div className="flex items-center gap-2 text-sm text-muted-foreground">
                   <Activity className="w-4 h-4 text-amber-500" />
                   Atualização automática por regra ainda não disponível (em breve).
                 </div>
               )}
               <Button size="lg" onClick={onCreate} disabled={creating} className="shadow-glow">
                 {creating ? "Processando…" : "Criar Audiência"}
               </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Main Table Area */}
      <div className="space-y-4">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-muted/20 p-2 rounded-lg border border-border/50">
           <div className="relative w-full md:w-72">
             <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
             <Input placeholder="Buscar audiência..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="pl-9 bg-background h-9" />
           </div>
           <div className="flex items-center gap-2">
             <Button variant="outline" size="sm" className="gap-2 bg-background"><Filter className="w-4 h-4"/> Filtros</Button>
           </div>
        </div>

        {/* Data Table */}
        {isLoading ? (
          <div className="py-10 text-center text-muted-foreground flex flex-col items-center gap-2">
             <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div> Carregando audiências...
          </div>
        ) : filteredLists.length === 0 ? (
          <div className="py-16 text-center text-muted-foreground bg-glass rounded-xl border border-border/50 shadow-soft">
            <Users className="mx-auto h-12 w-12 mb-4 opacity-20" />
            <h3 className="font-bold text-lg text-foreground mb-1">Nenhuma lista encontrada</h3>
            <p className="text-sm">Importe um CSV ou crie uma Segmentação Dinâmica para começar.</p>
          </div>
        ) : (
          <div className="bg-glass border border-border/50 rounded-xl overflow-hidden shadow-soft">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-muted-foreground uppercase bg-muted/30 border-b border-border/50">
                  <tr>
                    <th className="px-5 py-4 font-semibold">Nome da Audiência</th>
                    <th className="px-5 py-4 font-semibold">Tamanho</th>
                    <th className="px-5 py-4 font-semibold">Saúde / Validade</th>
                    <th className="px-5 py-4 font-semibold">Desempenho</th>
                    <th className="px-5 py-4 font-semibold text-right">Ações Rápidas</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLists.map((l) => (
                    <tr key={l.id} className="border-b border-border/20 last:border-0 hover:bg-muted/40 transition-colors group cursor-pointer">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                           <div className={cn("w-8 h-8 rounded-full flex items-center justify-center border shadow-sm", l.type === 'smart' ? "bg-amber-500/10 border-amber-500/20 text-amber-500" : "bg-primary/10 border-primary/20 text-primary")}>
                             {l.type === 'smart' ? <Sparkles className="w-4 h-4"/> : <ListChecks className="w-4 h-4"/>}
                           </div>
                           <div>
                             <p className="font-bold">{l.name}</p>
                             <div className="flex items-center gap-2 mt-0.5">
                               {l.type === 'smart' ? 
                                 <Badge variant="outline" className="text-[10px] h-4 bg-amber-500/5 text-amber-500 border-amber-500/20 px-1">Dinâmica</Badge> : 
                                 <Badge variant="outline" className="text-[10px] h-4 bg-muted text-muted-foreground border-border/50 px-1">Estática</Badge>
                               }
                               <span className="text-[10px] text-muted-foreground">Criada {fmtDate(l.created_at)}</span>
                             </div>
                           </div>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                         <div className="flex flex-col">
                           <span className="font-bold text-foreground text-base">{l.count.toLocaleString()}</span>
                           <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Leads</span>
                         </div>
                      </td>
                      <td className="px-5 py-4">
                         <span className="text-xs text-muted-foreground">—</span>
                      </td>
                      <td className="px-5 py-4">
                         <div className="flex flex-col">
                           <span className="font-medium text-muted-foreground flex items-center gap-1"><BarChart2 className="w-3.5 h-3.5"/> Sem dados</span>
                         </div>
                      </td>
                      <td className="px-5 py-4 text-right">
                         <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-sky-500 hover:text-sky-400 hover:bg-sky-500/10" onClick={() => messageList(l)} disabled={!pairedSession} title={!pairedSession ? "Conecte WhatsApp para disparar mensagens" : "Disparar Campanha WhatsApp (Mensagem)"}><Send className="h-4 w-4" /></Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-primary hover:text-primary hover:bg-primary/10" onClick={() => callList(l)} disabled={!pairedSession} title={!pairedSession ? "Conecte WhatsApp para ligar via IA" : "Disparar Ligações IA (Voz)"}><PhoneForwarded className="h-4 w-4" /></Button>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted/50" title="Opções"><MoreVertical className="h-4 w-4" /></Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-48">
                                <DropdownMenuItem onClick={() => baixarListaCSV(l)} className="gap-2 cursor-pointer">
                                  <Download className="h-4 w-4" /> Baixar CSV
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => duplicateList(l)} disabled={busy === l.id} className="gap-2 cursor-pointer">
                                  <Copy className="h-4 w-4" /> Duplicar Lista
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => onDelete(l)} disabled={busy === l.id} className="gap-2 cursor-pointer text-destructive focus:text-destructive">
                                  <Trash2 className="h-4 w-4" /> Excluir
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                         </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
