import { useState, useMemo } from "react";
import { Search, Phone, Users, PhoneForwarded, Filter, Building2, Hash, Send, ListPlus, SortAsc, Star, Download, Tag, Trash2, SlidersHorizontal, MoreHorizontal, X, FileText, Calendar } from "lucide-react";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useSessions } from "@/stores/sessions";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getSessionContacts } from "@/services/contacts";
import { createContactList, getContactStats, listContactLists, appendToContactList, type ContactStat } from "@/services/broadcast";
import { apiGet, apiPost, apiPut } from "@/lib/api";
import { apiUrl, authHeaders } from "@/lib/auth";
import { setView } from "@/stores/navigation";
import { useMassCallStore } from "@/stores/masscall";
import { useMassMessageStore } from "@/stores/massmsg";
import type { Contact } from "@/types/contacts";
import { cn } from "@/lib/utils";

type FilterType = "all" | "saved" | "unsaved" | "business" | "contacted" | "interested";
type SortType = "name" | "phone" | "ddd" | "score";

const scoreColor = (s: number) =>
  s >= 70 ? "text-emerald-500" : s >= 40 ? "text-amber-500" : "text-muted-foreground";

export const ContactsPage = () => {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<FilterType>("all");
  const [dddFilter, setDddFilter] = useState("");
  const [sort, setSort] = useState<SortType>("name");
  const [showExport, setShowExport] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  // Filtros avançados (aplicados na lista via useMemo). Só campos com lastro real em
  // ContactStat: score (engajamento) e status da última ligação (answered/interested/calls).
  const [advScoreMin, setAdvScoreMin] = useState("");
  const [advScoreMax, setAdvScoreMax] = useState("");
  const [advAnswered, setAdvAnswered] = useState(false);
  const [advInterested, setAdvInterested] = useState(false);
  const [advNoAnswer, setAdvNoAnswer] = useState(false);
  const [viewContact, setViewContact] = useState<Contact | null>(null);
  const sessions = useSessions((s) => s.sessions);
  const pairedSession = sessions.find((s) => s.paired);

  const { data: contacts = [], isLoading } = useQuery({
    queryKey: ["contacts", pairedSession?.id],
    queryFn: () => (pairedSession ? getSessionContacts(pairedSession.id) : Promise.resolve([])),
    enabled: !!pairedSession,
    staleTime: 60_000,
  });

  // Histórico/score por contato (de todas as campanhas já disparadas)
  const { data: stats = {} } = useQuery({
    queryKey: ["contact-stats"],
    queryFn: () => getContactStats(),
    staleTime: 30_000,
  });
  const statOf = (c: Contact): ContactStat | undefined => stats[c.phone];

  const filtered = useMemo(() => {
    let list = contacts;

    // Type filter
    if (filter === "saved") list = list.filter((c) => c.name !== "");
    if (filter === "unsaved") list = list.filter((c) => c.name === "" && !c.business_name);
    if (filter === "business") list = list.filter((c) => c.business_name !== "");
    if (filter === "contacted") list = list.filter((c) => (stats[c.phone]?.calls ?? 0) > 0);
    if (filter === "interested") list = list.filter((c) => stats[c.phone]?.interested);

    // Filtros avançados (drawer)
    const min = advScoreMin.trim() === "" ? null : Number(advScoreMin);
    const max = advScoreMax.trim() === "" ? null : Number(advScoreMax);
    if (min !== null && !Number.isNaN(min)) list = list.filter((c) => (stats[c.phone]?.score ?? 0) >= min);
    if (max !== null && !Number.isNaN(max)) list = list.filter((c) => (stats[c.phone]?.score ?? 0) <= max);
    if (advAnswered) list = list.filter((c) => (stats[c.phone]?.answered ?? 0) > 0);
    if (advInterested) list = list.filter((c) => stats[c.phone]?.interested);
    if (advNoAnswer) list = list.filter((c) => {
      const st = stats[c.phone];
      return st ? st.calls > 0 && st.answered === 0 : false;
    });

    // DDD filter (area code)
    if (dddFilter.trim()) {
      const ddd = dddFilter.trim();
      list = list.filter((c) => c.phone.startsWith("55" + ddd) || c.phone.startsWith(ddd));
    }

    // Text search
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.push_name.toLowerCase().includes(q) ||
          c.business_name.toLowerCase().includes(q) ||
          c.phone.includes(q),
      );
    }

    // Sort
    const byName = (c: Contact) => (c.name || c.push_name || c.business_name || c.phone).toLowerCase();
    list = [...list].sort((a, b) => {
      if (sort === "phone") return a.phone.localeCompare(b.phone);
      if (sort === "ddd") return a.phone.slice(2, 4).localeCompare(b.phone.slice(2, 4)) || byName(a).localeCompare(byName(b));
      if (sort === "score") return (stats[b.phone]?.score ?? -1) - (stats[a.phone]?.score ?? -1);
      return byName(a).localeCompare(byName(b));
    });

    return list;
  }, [contacts, search, filter, dddFilter, sort, stats, advScoreMin, advScoreMax, advAnswered, advInterested, advNoAnswer]);

  const selectedPhones = () => contacts.filter((c) => selected.has(c.jid)).map((c) => c.phone);
  const selectedJids = () => Array.from(selected);

  // Perfil 360 REAL do contato aberto (lead + notas + timeline de /api/contacts/{jid}/profile).
  const { data: profile360, isLoading: profileLoading, isError: profileError } = useQuery({
    queryKey: ["contact-profile", viewContact?.jid],
    queryFn: () => apiGet<any>(`/api/contacts/${encodeURIComponent(viewContact!.jid)}/profile`),
    enabled: !!viewContact,
  });

  // Salva a lista filtrada (resultado dos filtros avançados) como uma nova lista/segmento real.
  const saveFilteredAsSegment = async () => {
    const phones = filtered.map((c) => c.phone);
    if (phones.length === 0) {
      toast.info("Nenhum contato para salvar.");
      return;
    }
    const name = window.prompt("Nome do segmento:", `Segmento (${phones.length})`);
    if (!name || !name.trim()) return;
    try {
      await createContactList(name.trim(), phones);
      qc.invalidateQueries({ queryKey: ["contact-lists"] });
      toast.success(`Segmento "${name.trim()}" salvo com ${phones.length} contato(s).`);
      setShowAdvancedFilters(false);
    } catch (e) {
      toast.error("Falha ao salvar segmento: " + (e as Error).message);
    }
  };

  // Exporta os contatos selecionados como CSV (backend gera o arquivo).
  const exportCSV = async () => {
    try {
      const res = await fetch(apiUrl("/api/contacts/export"), {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ jids: selectedJids() }),
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "contatos.csv"; a.click();
      URL.revokeObjectURL(url);
      toast.success("CSV exportado.");
    } catch {
      toast.error("Falha ao exportar CSV.");
    }
  };

  // Aplica uma tag em massa (escolhe entre as tags existentes).
  const bulkTag = async () => {
    try {
      const tags = await apiGet<{ tags?: { id: string; name: string }[] } | { id: string; name: string }[]>("/api/contacts/tags");
      const list = Array.isArray(tags) ? tags : (tags.tags ?? []);
      if (list.length === 0) { toast.error("Crie uma tag primeiro em Tags."); return; }
      const name = window.prompt("Aplicar qual tag? " + list.map((t) => t.name).join(", "), list[0].name);
      if (!name) return;
      const tag = list.find((t) => t.name.toLowerCase() === name.toLowerCase());
      if (!tag) { toast.error("Tag não encontrada."); return; }
      await apiPost("/api/contacts/tags/bulk", { jids: selectedJids(), tag_id: tag.id });
      toast.success(`Tag "${tag.name}" aplicada a ${selected.size} contatos.`);
    } catch {
      toast.error("Falha ao aplicar tag.");
    }
  };

  // Exclui (soft delete) os contatos selecionados.
  const bulkDelete = async () => {
    if (!window.confirm(`Excluir ${selected.size} contatos selecionados?`)) return;
    try {
      const res = await fetch(apiUrl("/api/contacts/bulk"), {
        method: "DELETE",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ jids: selectedJids() }),
      });
      if (!res.ok) throw new Error();
      toast.success("Contatos removidos.");
      clearSelection();
      qc.invalidateQueries({ queryKey: ["contacts", pairedSession?.id] });
    } catch {
      toast.error("Falha ao excluir.");
    }
  };

  const toggle = (jid: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(jid)) next.delete(jid);
      else next.add(jid);
      return next;
    });
  };

  const selectAll = () => {
    if (selected.size === filtered.length && filtered.length > 0) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map((c) => c.jid)));
    }
  };

  const selectFiltered = () => {
    setSelected(new Set(filtered.map((c) => c.jid)));
  };

  const clearSelection = () => setSelected(new Set());

  const startMassCall = () => {
    const selectedContacts = contacts.filter((c) => selected.has(c.jid));
    useMassCallStore.getState().setContacts(selectedContacts);
    setView("mass-call");
  };

  const startMassMessage = () => {
    const selectedContacts = contacts.filter((c) => selected.has(c.jid));
    useMassMessageStore.getState().setContacts(selectedContacts);
    setView("mass-message");
  };

  const displayName = (c: Contact) => c.name || c.push_name || c.business_name || c.phone;

  if (!pairedSession) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <Users className="h-10 w-10 mb-3" />
        <p>Nenhuma sessão WhatsApp conectada.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 pb-20">
      {/* Header */}
      {/* Header and Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Users className="h-5 w-5 text-primary" />
          Carteira de Contatos
          {!isLoading && <Badge variant="secondary" className="bg-primary/10 text-primary">{contacts.length}</Badge>}
        </h2>
        <div className="flex items-center gap-2">
           <div className="relative w-full sm:w-64">
             <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
             <Input
               placeholder="Buscar contatos..."
               value={search}
               onChange={(e) => setSearch(e.target.value)}
               className="pl-9 h-9 bg-glass border-border/50 focus:border-primary/50 transition-colors"
             />
           </div>
           <Button variant="outline" size="sm" className="h-9 gap-2 border-border/50 bg-glass hover:bg-muted/50" onClick={() => setShowAdvancedFilters(true)}>
             <SlidersHorizontal className="h-4 w-4" /> Filtros Avançados
           </Button>
           <Button size="sm" className="h-9 gap-2">
             <Download className="h-4 w-4" /> Importar
           </Button>
        </div>
      </div>

      {/* Filters row */}
      <div className="flex flex-wrap items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        {([
          ["all", "Todos"],
          ["saved", "Salvos"],
          ["unsaved", "Não salvos"],
          ["business", "Empresas"],
          ["contacted", "Já ligados"],
          ["interested", "Interessados"],
        ] as [FilterType, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              filter === key
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            {label}
          </button>
        ))}
        <span className="text-muted-foreground">|</span>
        <div className="flex items-center gap-1">
          <Hash className="h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="DDD"
            value={dddFilter}
            onChange={(e) => setDddFilter(e.target.value.replace(/\D/g, "").slice(0, 2))}
            className="h-7 w-16 text-xs"
          />
        </div>
        <span className="text-muted-foreground">|</span>
        <div className="flex items-center gap-1">
          <SortAsc className="h-3.5 w-3.5 text-muted-foreground" />
          {([
            ["name", "Nome"],
            ["phone", "Número"],
            ["ddd", "DDD"],
            ["score", "Score"],
          ] as [SortType, string][]).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSort(key)}
              className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                sort === key ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Selection toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <button onClick={selectAll} className="underline hover:text-foreground">
            {selected.size === filtered.length && filtered.length > 0 ? "Desmarcar todos" : "Selecionar todos"}
          </button>
          {filtered.length !== contacts.length && (
            <>
              <span>·</span>
              <button onClick={selectFiltered} className="underline hover:text-foreground">
                Selecionar filtrados ({filtered.length})
              </button>
            </>
          )}
          {selected.size > 0 && (
            <>
              <span>·</span>
              <button onClick={clearSelection} className="underline hover:text-foreground text-destructive">
                Limpar seleção
              </button>
            </>
          )}
        </div>
        <span className="text-sm text-muted-foreground">{filtered.length} de {contacts.length}</span>
      </div>

      {/* Rich Data Table */}
      {isLoading ? (
        <div className="py-20 text-center text-muted-foreground flex flex-col items-center justify-center">
           <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
           Carregando contatos...
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-20 text-center text-muted-foreground bg-glass border border-border/50 rounded-xl">
           <Users className="h-10 w-10 mx-auto mb-3 opacity-20" />
           Nenhum contato encontrado.
        </div>
      ) : (
        <div className="bg-glass border border-border/50 rounded-xl overflow-hidden shadow-soft">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase bg-muted/30 border-b border-border/50">
                <tr>
                  <th scope="col" className="p-4 w-10">
                    <input type="checkbox" className="h-4 w-4 rounded border-input bg-background" checked={selected.size === filtered.length && filtered.length > 0} onChange={selectAll} />
                  </th>
                  <th scope="col" className="px-4 py-3 font-semibold">Contato</th>
                  <th scope="col" className="px-4 py-3 font-semibold">Telefone</th>
                  <th scope="col" className="px-4 py-3 font-semibold text-center">Score</th>
                  <th scope="col" className="px-4 py-3 font-semibold">Tags / Origem</th>
                  <th scope="col" className="px-4 py-3 font-semibold text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => {
                   const s = statOf(c);
                   const isSelected = selected.has(c.jid);
                   return (
                    <tr 
                      key={c.jid} 
                      onClick={() => setViewContact(c)}
                      className={`border-b border-border/20 last:border-0 hover:bg-muted/40 transition-colors cursor-pointer group ${isSelected ? 'bg-primary/5' : ''}`}
                    >
                      <td className="p-4 w-10" onClick={(e) => e.stopPropagation()}>
                        <input type="checkbox" checked={isSelected} onChange={() => toggle(c.jid)} className="h-4 w-4 rounded border-input bg-background" />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs shrink-0">
                            {displayName(c).charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-foreground">{displayName(c)}</p>
                            {c.business_name && <p className="text-[0.65rem] text-muted-foreground flex items-center gap-1 mt-0.5"><Building2 className="w-3 h-3"/> Empresa</p>}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">+{c.phone}</td>
                      <td className="px-4 py-3 text-center">
                        {s && s.calls > 0 ? (
                           <div className="flex flex-col items-center justify-center" title="Score de engajamento">
                              <span className={`font-bold ${scoreColor(s.score)}`}>{s.score}</span>
                              <div className="w-12 bg-muted h-1 rounded-full overflow-hidden mt-1">
                                 <div className={`h-full rounded-full ${scoreColor(s.score).replace('text-', 'bg-')}`} style={{width: `${s.score}%`}}></div>
                              </div>
                           </div>
                        ) : (
                           <span className="text-muted-foreground/40">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5 flex-wrap">
                           {c.name && !c.business_name && <Badge variant="outline" className="text-[0.6rem] bg-primary/5 text-primary border-primary/20">Salvo</Badge>}
                           {s?.interested && <Badge variant="outline" className="text-[0.6rem] bg-emerald-500/10 text-emerald-500 border-emerald-500/20"><Star className="w-2.5 h-2.5 mr-1" /> Lead Quente</Badge>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={e => e.stopPropagation()}>
                           <Button variant="ghost" size="icon" className="h-8 w-8 text-sky-500 hover:text-sky-400 hover:bg-sky-500/10" title="Chamar no WhatsApp">
                             <Send className="h-4 w-4" />
                           </Button>
                           <Button variant="ghost" size="icon" className="h-8 w-8 text-primary hover:text-primary hover:bg-primary/10" title="Ligar via IA" onClick={() => {
                              useMassCallStore.getState().setContacts([c]);
                              setView("mass-call");
                           }}>
                             <Phone className="h-4 w-4" />
                           </Button>
                           <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" title="Mais opções">
                             <MoreHorizontal className="h-4 w-4" />
                           </Button>
                        </div>
                      </td>
                    </tr>
                   )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Fixed bottom bar - mass actions */}
      {selected.size > 0 && (
        <div className="fixed bottom-0 left-0 right-0 z-40 border-t bg-background/95 backdrop-blur p-4 flex items-center justify-between shadow-[0_-10px_40px_rgba(0,0,0,0.2)] animate-in slide-in-from-bottom-10">
          <div className="flex items-center gap-3">
            <div className="bg-primary/20 text-primary font-bold w-8 h-8 rounded-full flex items-center justify-center border border-primary/30">
              {selected.size}
            </div>
            <span className="font-medium text-sm hidden sm:inline">Selecionados</span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto">
            <Button onClick={exportCSV} size="sm" variant="outline" className="gap-2 bg-glass">
              <Download className="h-4 w-4" />
              <span className="hidden sm:inline">Exportar CSV</span>
            </Button>
            <Button onClick={() => setShowExport(true)} size="sm" variant="outline" className="gap-2 bg-glass">
              <ListPlus className="h-4 w-4 text-emerald-500" />
              <span className="hidden sm:inline">Lista IA</span>
            </Button>
            <Button onClick={bulkTag} size="sm" variant="outline" className="gap-2 bg-glass">
              <Tag className="h-4 w-4 text-amber-500" />
              <span className="hidden sm:inline">Tag</span>
            </Button>
            <Button onClick={startMassMessage} size="sm" variant="outline" className="gap-2 bg-glass border-sky-500/30 hover:bg-sky-500/10 text-sky-500">
              <Send className="h-4 w-4" />
              <span className="hidden sm:inline">WhatsApp</span>
            </Button>
            <Button onClick={startMassCall} size="sm" className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow">
              <PhoneForwarded className="h-4 w-4" />
              <span className="hidden sm:inline">Disparo de Voz</span>
            </Button>
            <Button onClick={bulkDelete} size="sm" variant="outline" className="gap-2 bg-glass border-destructive/30 hover:bg-destructive/10 text-destructive ml-2">
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {showExport && (
        <ExportListModal
          phones={selectedPhones()}
          onClose={() => setShowExport(false)}
          onDone={() => {
            setShowExport(false);
            qc.invalidateQueries({ queryKey: ["contact-lists"] });
          }}
        />
      )}

      {/* Advanced Filters Drawer */}
      {showAdvancedFilters && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm" onClick={() => setShowAdvancedFilters(false)}>
           <div className="w-[400px] max-w-full h-full bg-background border-l border-border/50 p-6 flex flex-col shadow-2xl animate-in slide-in-from-right-full" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-8">
                 <h3 className="text-lg font-bold flex items-center gap-2"><SlidersHorizontal className="h-5 w-5" /> Filtros Avançados</h3>
                 <Button variant="ghost" size="icon" onClick={() => setShowAdvancedFilters(false)}><X className="h-5 w-5" /></Button>
              </div>

              <div className="space-y-6 flex-1 overflow-y-auto">
                 <div>
                    <label className="text-xs font-semibold uppercase text-muted-foreground mb-2 block">Data de Criação</label>
                    <select className="w-full bg-glass border border-border/50 rounded-md p-2 text-sm text-foreground">
                       <option>Qualquer data</option>
                       <option>Últimas 24h (1 dia)</option>
                       <option>Últimos 7 dias</option>
                       <option>Últimos 30 dias</option>
                       <option>Mais de 30 dias</option>
                    </select>
                 </div>
                 <div>
                    <label className="text-xs font-semibold uppercase text-muted-foreground mb-2 block">Engajamento (Score)</label>
                    <div className="flex items-center gap-2">
                       <Input type="number" placeholder="Min" className="bg-glass" value={advScoreMin} onChange={(e) => setAdvScoreMin(e.target.value)} />
                       <span className="text-muted-foreground">até</span>
                       <Input type="number" placeholder="Max" className="bg-glass" value={advScoreMax} onChange={(e) => setAdvScoreMax(e.target.value)} />
                    </div>
                 </div>
                 <div>
                    <label className="text-xs font-semibold uppercase text-muted-foreground mb-2 block">Status da Última Ligação</label>
                    <div className="space-y-2">
                       <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="rounded border-input" checked={advAnswered} onChange={(e) => setAdvAnswered(e.target.checked)} /> Atendida (Conversou)</label>
                       <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="rounded border-input" checked={advInterested} onChange={(e) => setAdvInterested(e.target.checked)} /> Demonstrou Interesse</label>
                       <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="rounded border-input" checked={advNoAnswer} onChange={(e) => setAdvNoAnswer(e.target.checked)} /> Ligou mas não atendeu</label>
                    </div>
                 </div>
                 <div>
                    <label className="text-xs font-semibold uppercase text-muted-foreground mb-2 block">Origem / Campanha</label>
                    <select className="w-full bg-glass border border-border/50 rounded-md p-2 text-sm text-foreground">
                       <option>Todas as Origens</option>
                       <option>Lista: Black Friday</option>
                       <option>Lista: Base Fria</option>
                    </select>
                 </div>
                 <p className="text-xs text-muted-foreground">{filtered.length} contato(s) correspondem aos filtros atuais.</p>
              </div>

              <div className="pt-6 mt-6 border-t border-border/50 flex flex-col gap-2">
                 <Button className="w-full" onClick={() => setShowAdvancedFilters(false)}>Ver {filtered.length} Resultado(s)</Button>
                 <Button
                    variant="outline"
                    className="w-full border-primary/20 text-primary hover:bg-primary/10"
                    disabled={filtered.length === 0}
                    onClick={saveFilteredAsSegment}
                 >
                    Salvar como Segmento ({filtered.length})
                 </Button>
                 <Button
                    variant="ghost"
                    className="w-full text-muted-foreground"
                    onClick={() => { setAdvScoreMin(""); setAdvScoreMax(""); setAdvAnswered(false); setAdvInterested(false); setAdvNoAnswer(false); }}
                 >
                    Limpar Filtros
                 </Button>
              </div>
           </div>
        </div>
      )}

      {/* Slide-over Contact Profile (CRM 360) */}
      {viewContact && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm" onClick={() => setViewContact(null)}>
           <div className="w-full max-w-md h-full bg-background border-l border-border/50 flex flex-col shadow-2xl animate-in slide-in-from-right-full" onClick={e => e.stopPropagation()}>
              
              <div className="p-6 pb-0 flex items-center justify-between">
                 <Button variant="ghost" size="icon" onClick={() => setViewContact(null)} className="rounded-full bg-muted/50"><X className="h-5 w-5" /></Button>
                 <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" className="h-8 gap-1"><Phone className="h-3 w-3" /> Ligar</Button>
                    <Button variant="outline" size="sm" className="h-8 gap-1"><Send className="h-3 w-3" /> Msg</Button>
                 </div>
              </div>

              <div className="p-6 flex flex-col items-center text-center border-b border-border/20">
                 <div className="w-20 h-20 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-3xl mb-4 border border-primary/20 shadow-glow">
                    {displayName(viewContact).charAt(0).toUpperCase()}
                 </div>
                 <h2 className="text-2xl font-bold">{displayName(viewContact)}</h2>
                 <p className="text-muted-foreground text-sm mt-1">+{viewContact.phone}</p>
                 <div className="flex gap-2 mt-4 flex-wrap justify-center">
                    {profile360?.lead?.stage && <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">{profile360.lead.stage}</Badge>}
                    {(profile360?.tags ?? []).map((tg: any) => <Badge key={tg.id} variant="outline">{tg.name}</Badge>)}
                    {!profile360?.lead?.stage && (profile360?.tags ?? []).length === 0 && <Badge variant="outline" className="text-muted-foreground">Sem classificação</Badge>}
                 </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-8">
                 {/* CRM Stats */}
                 <div className="grid grid-cols-2 gap-4">
                    <div className="bg-glass border border-border/50 rounded-xl p-3 flex flex-col items-center justify-center">
                       <span className="text-[0.65rem] uppercase font-bold text-muted-foreground mb-1">Score de Lead</span>
                       {/* Sem lead não há nota: antes mostrava o número de ligações como se fosse a nota. */}
                       <span className="text-2xl font-bold text-primary">{profile360?.lead?.score ?? "—"}</span>
                    </div>
                    <div className="bg-glass border border-border/50 rounded-xl p-3 flex flex-col items-center justify-center">
                       <span className="text-[0.65rem] uppercase font-bold text-muted-foreground mb-1">Ligações</span>
                       <span className="text-sm font-bold">{statOf(viewContact)?.calls ?? 0}</span>
                    </div>
                 </div>

                 {/* Timeline REAL */}
                 <div>
                    <h3 className="text-sm font-bold flex items-center gap-2 mb-4"><Calendar className="h-4 w-4" /> Histórico de Interações</h3>
                    {/* Sem histórico real: estado vazio honesto. Antes apareciam dois eventos inventados
                        (um atendimento com interesse e uma tentativa não atendida) como se fossem reais
                        (auditoria do mês 2, F33). Carregando/erro também caíam nos exemplos. */}
                    {profileLoading ? (
                       <p className="text-sm text-muted-foreground">Carregando histórico…</p>
                    ) : profileError ? (
                       <p className="text-sm text-muted-foreground">Não consegui carregar o histórico.</p>
                    ) : (profile360?.timeline ?? []).length === 0 ? (
                       <p className="text-sm text-muted-foreground">
                          Nenhuma interação registrada ainda.
                          {(statOf(viewContact)?.calls ?? 0) > 0 && " Ligações sem conversa (não atendidas ou sem fala do cliente) não aparecem aqui."}
                       </p>
                    ) : (
                       <div className="space-y-4 pl-2 border-l-2 border-border/50 ml-2">
                          {(profile360.timeline as any[]).map((ev, i) => (
                             <div key={i} className="relative pl-6">
                                <div className={cn("absolute -left-[21px] top-1 w-3 h-3 rounded-full", ev.type === "transcript" ? "bg-emerald-500" : ev.type === "call" ? "bg-blue-500" : "bg-amber-500")}></div>
                                <p className="text-sm font-medium">{ev.text || ev.type}</p>
                                <p className="text-xs text-muted-foreground mt-0.5">{ev.meta || ""} {ev.at ? "• " + new Date(ev.at).toLocaleString("pt-BR") : ""}</p>
                             </div>
                          ))}
                       </div>
                    )}
                 </div>

                 {/* Notes REAL */}
                 <div>
                    <h3 className="text-sm font-bold flex items-center gap-2 mb-3"><FileText className="h-4 w-4" /> Notas do Vendedor</h3>
                    <textarea
                      id="contact-notes-360"
                      className="w-full bg-glass border border-border/50 rounded-lg p-3 text-sm min-h-[100px] focus:ring-1 focus:ring-primary/50 outline-none"
                      placeholder="Adicione observações sobre o lead..."
                      defaultValue={profile360?.lead?.notes ?? ""}
                      key={viewContact.jid + (profile360?.lead?.notes ?? "")}
                    />
                    <Button
                      size="sm" className="mt-2 gap-2"
                      onClick={async () => {
                        const el = document.getElementById("contact-notes-360") as HTMLTextAreaElement | null;
                        try {
                          await apiPut(`/api/contacts/${encodeURIComponent(viewContact.jid)}/notes`, { notes: el?.value || "" });
                          toast.success("Nota salva.");
                        } catch { toast.error("Falha ao salvar nota."); }
                      }}
                    >
                      <FileText className="h-4 w-4" /> Salvar Nota
                    </Button>
                 </div>
              </div>
           </div>
        </div>
      )}
    </div>
  );
};

function ExportListModal({ phones, onClose, onDone }: { phones: string[]; onClose: () => void; onDone: () => void }) {
  const [mode, setMode] = useState<"new" | "existing">("new");
  const [name, setName] = useState("");
  const [targetId, setTargetId] = useState("");
  const [busy, setBusy] = useState(false);

  const { data: lists = [] } = useQuery({ queryKey: ["contact-lists"], queryFn: () => listContactLists() });

  const submit = async () => {
    setBusy(true);
    try {
      if (mode === "new") {
        if (!name.trim()) return toast.error("Dê um nome à lista");
        await createContactList(name.trim(), phones);
        toast.success(`Lista "${name}" criada com ${phones.length} contatos`);
      } else {
        if (!targetId) return toast.error("Escolha uma lista");
        const l = await appendToContactList(targetId, phones);
        toast.success(`Adicionados à lista (${l.count} no total)`);
      }
      onDone();
    } catch (e: any) {
      toast.error("Erro ao exportar", { description: e.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <Card className="w-full max-w-md p-5 space-y-4" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <ListPlus className="h-5 w-5" /> Exportar {phones.length} contatos
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setMode("new")}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium ${mode === "new" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
          >
            Nova lista
          </button>
          <button
            onClick={() => setMode("existing")}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium ${mode === "existing" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
          >
            Lista existente
          </button>
        </div>
        {mode === "new" ? (
          <Input placeholder="Nome da nova lista" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
        ) : (
          <select
            className="w-full rounded-md border bg-background p-2 text-sm"
            value={targetId}
            onChange={(e) => setTargetId(e.target.value)}
          >
            <option value="">Escolha uma lista...</option>
            {lists.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name} ({l.count})
              </option>
            ))}
          </select>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={submit} disabled={busy}>{mode === "new" ? "Criar lista" : "Adicionar"}</Button>
        </div>
      </Card>
    </div>
  );
}
