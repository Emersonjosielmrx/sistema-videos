import { useEffect, useState, useCallback } from "react";
import { Search, Phone, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { apiGet, apiPost } from "@/lib/api";
import { downloadCSV, csvTelefone } from "@/lib/csv";
import { cn } from "@/lib/utils";

// TranscriptsPage — histórico BUSCÁVEL de ligações (transcrição + resumo + classificação).
// Antes o resumo só ia pro Telegram e sumia; aqui fica pesquisável por número/texto.
// Backend: GET /api/transcripts?q=&limit=

type Transcript = {
  id: string;
  campaign_id: string;
  number: string;
  transcript: string;
  resumo: string;
  classificacao: string;
  interested: boolean;
  created_at: string;
};

const CLASSIF_LABEL: Record<string, string> = {
  interessado: "🔥 Interessado",
  sem_interesse: "❄️ Sem interesse",
  pediu_retorno: "📅 Pediu retorno",
  numero_errado: "❌ Número errado",
  caixa_postal: "📵 Caixa postal",
  indefinido: "❓ Indefinido",
};

export function TranscriptsPage() {
  const [list, setList] = useState<Transcript[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const selectAll = () => {
    if (selectedIds.length === list.length && list.length > 0) setSelectedIds([]);
    else setSelectedIds(list.map(t => t.id));
  };

  const deleteSelected = async () => {
    if (!selectedIds.length) return;
    if (!confirm(`Tem certeza que deseja apagar ${selectedIds.length} ligações/campanhas selecionadas?`)) return;
    // FIX P0-005 (2026-07-25): antes era false-success total (comentário TODO
    // + toast verde sem persistir). Agora chama POST /api/transcripts/batch-delete
    // que existe no server (cmd/server/transcript_store.go:DeleteBatch +
    // cost_api.go:handleDeleteTranscriptsBatch). Só mostra sucesso se o backend
    // confirmar (N === selectedIds.length ou parcial com aviso).
    try {
      const r = await apiPost<{ deleted: number }>("/api/transcripts/batch-delete", { ids: selectedIds });
      if (r.deleted === selectedIds.length) {
        toast.success(`${r.deleted} registros apagados com sucesso.`);
      } else if (r.deleted > 0) {
        toast.success(`${r.deleted} de ${selectedIds.length} apagados.`);
      } else {
        toast.error("Nenhum registro foi apagado. Atualize a página e tente de novo.");
        return;
      }
      setList(prev => prev.filter(t => !selectedIds.includes(t.id)));
      setSelectedIds([]);
    } catch (e: any) {
      toast.error(`Erro ao apagar: ${e?.message || "desconhecido"}`);
    }
  };

  const load = useCallback((query: string) => {
    setLoading(true);
    apiGet<{ transcripts: Transcript[] }>(`/api/transcripts?q=${encodeURIComponent(query)}`)
      .then((r) => setList(r.transcripts ?? []))
      .catch((e) => toast.error("Erro ao carregar ligações", { description: (e as Error).message }))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(""); }, [load]);

  // "Exportar CSV": baixa o que está na tela (a busca atual; as marcadas, se houver) pela
  // lib/csv — o que o cliente falou pode começar com = + - @ e vira texto, não fórmula.
  // Antes o botão não fazia nada.
  const exportarCSV = () => {
    const linhas = selectedIds.length > 0 ? list.filter((t) => selectedIds.includes(t.id)) : list;
    if (linhas.length === 0) return;
    downloadCSV(
      `ligacoes_${new Date().toISOString().slice(0, 10)}.csv`,
      ["data", "telefone", "classificacao", "interessado", "resumo", "transcricao"],
      linhas.map((t) => [
        t.created_at ? new Date(t.created_at).toLocaleString("pt-BR") : "",
        csvTelefone(t.number),
        CLASSIF_LABEL[t.classificacao]?.replace(/^\S+\s/, "") ?? t.classificacao,
        t.interested ? "sim" : "não",
        t.resumo,
        t.transcript,
      ]),
    );
    toast.success(`${linhas.length} ligação(ões) exportada(s).`);
  };

  // Busca com debounce leve.
  useEffect(() => {
    const t = setTimeout(() => load(q.trim()), 350);
    return () => clearTimeout(t);
  }, [q, load]);

  return (
    <div className="space-y-4">
      {/* Cabeçalho Compacto Telefonia */}
      <div className="sticky top-0 z-10 relative overflow-hidden rounded-2xl bg-gradient-to-br from-sky-500/10 via-background to-background border border-sky-500/20 p-4 shadow-glow flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
          <Phone className="w-16 h-16 text-sky-500" />
        </div>
        <div className="relative z-10 flex items-center gap-3">
          <div className="p-2 bg-sky-500/10 rounded-xl border border-sky-500/20 shadow-glow hidden sm:block">
            <Phone className="h-6 w-6 text-sky-500" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-sky-500 to-sky-400 drop-shadow-sm">
                Central de Telefonia
              </h2>
              <Badge className="bg-sky-500/10 text-sky-500 border-sky-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Inteligência em Ação
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Acesse o histórico completo das ligações e métricas de sentimento.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar histórico..."
              className="pl-8 bg-muted/20"
            />
          </div>
          {selectedIds.length > 0 && (
            <Button variant="destructive" size="sm" className="gap-1.5 h-9" onClick={deleteSelected}>
              <Trash2 className="h-4 w-4" /> Apagar ({selectedIds.length})
            </Button>
          )}
          <Button variant="outline" size="sm" className="hidden sm:flex gap-1.5 h-9" onClick={exportarCSV} disabled={list.length === 0}>
            Exportar <span className="text-[0.65rem] text-muted-foreground ml-1">CSV</span>
          </Button>
        </div>
      </div>
      <p className="text-sm text-muted-foreground">
        Tudo que os clientes falaram nas ligações, com resumo e classificação da IA. Busque por número
        ou por qualquer palavra dita na conversa.
      </p>

      {loading ? (
        <div className="space-y-4 pt-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex flex-col gap-3 p-4 rounded-2xl border border-border/30 bg-card/50">
               <div className="flex justify-between">
                 <Skeleton className="h-5 w-32 rounded-md" />
                 <Skeleton className="h-4 w-24 rounded-md" />
               </div>
               <Skeleton className="h-16 w-full rounded-xl" />
            </div>
          ))}
        </div>
      ) : list.length === 0 ? (
        <div className="space-y-3 pt-2 opacity-75">
          <p className="text-sm text-muted-foreground mb-4">
            {q ? "Nenhuma ligação encontrada para essa busca." : "Nenhuma ligação registrada ainda. Veja abaixo um exemplo de como cada ligação vai aparecer:"}
          </p>
          {/* Exemplo FICTÍCIO só no estado vazio sem busca (antes aparecia também após uma busca sem resultado). */}
          {!q && (
          <Card className="p-5 flex flex-col gap-4 bg-glass border-dashed border-border/50 relative">
            <span className="absolute -top-2 left-4 text-[10px] font-bold uppercase tracking-wider bg-amber-500/15 text-amber-500 border border-amber-500/30 rounded px-1.5 py-0.5">Exemplo</span>
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/30 pb-3">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <Phone className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-bold">+55 (11) 98765-4321</h3>
                  <p className="text-xs text-muted-foreground">Campanha: Inovare Vendas • Ontem às 14:30</p>
                </div>
              </div>
              <div className="flex gap-2">
                <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-500">🔥 Interessado</span>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-1">Resumo da IA:</p>
              <p className="text-sm text-muted-foreground">Cliente demonstrou alto interesse na plataforma de agentes. Solicitou envio do link de pagamento para o plano Pro. Agendou retorno para amanhã às 10h.</p>
            </div>
            <div className="bg-black/20 p-3 rounded-lg max-h-32 overflow-y-auto text-xs font-mono text-muted-foreground">
              [IA]: Olá, falo com o João?<br/>
              [Cliente]: Sim, quem é?<br/>
              [IA]: Aqui é da Inovare, vi que você preencheu nosso formulário...
            </div>
          </Card>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex justify-between items-center px-2 py-1">
            <label className="flex items-center gap-2 text-sm cursor-pointer hover:text-primary transition-colors w-fit">
              <input type="checkbox" className="rounded text-primary focus:ring-primary h-4 w-4 cursor-pointer" checked={list.length > 0 && selectedIds.length === list.length} onChange={selectAll} />
              <span className="text-muted-foreground font-semibold">Selecionar todas as campanhas da busca</span>
            </label>
            {selectedIds.length > 0 && (
              <span className="text-xs text-muted-foreground font-medium bg-muted px-2 py-1 rounded-md">{selectedIds.length} selecionadas</span>
            )}
          </div>
          {list.map((t) => (
            <Card key={t.id} className={cn("p-4 flex gap-3 transition-all", selectedIds.includes(t.id) && "border-primary/50 bg-primary/5 shadow-[0_0_15px_rgba(16,185,129,0.1)]")}>
              <div className="pt-1 shrink-0">
                <input type="checkbox" className="rounded text-primary focus:ring-primary h-4 w-4 cursor-pointer" checked={selectedIds.includes(t.id)} onChange={() => toggleSelect(t.id)} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 font-medium">
                    <Phone className="h-4 w-4 opacity-60" /> {t.number}
                    {t.interested && <span className="text-xs text-green-500">• interessado</span>}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span>{CLASSIF_LABEL[t.classificacao] ?? t.classificacao}</span>
                    <span>{new Date(t.created_at).toLocaleString("pt-BR")}</span>
                  </div>
                </div>
                {t.resumo && <p className="mt-3 text-[0.9rem] bg-muted/30 p-3 rounded-xl border border-border/50 text-foreground/90">{t.resumo}</p>}
              {t.transcript && (
                <details className="mt-3 group">
                  <summary className="cursor-pointer text-xs font-semibold text-primary hover:text-primary/80 list-none flex items-center gap-1">
                    <span className="group-open:hidden">►</span>
                    <span className="hidden group-open:inline">▼</span>
                    Ver transcrição completa
                  </summary>
                  <div className="mt-3 space-y-3 p-4 rounded-2xl bg-card border border-border/50 shadow-inner max-h-96 overflow-y-auto custom-scrollbar">
                    {t.transcript.split('\n').map((line, i) => {
                      if (!line.trim()) return null;
                      
                      // Heurística simples para identificar quem está falando (Agente/IA vs Cliente/User)
                      const isClient = /^(cliente|user|humano|usuário)\s*:/i.test(line);
                      const isAgent = /^(ia|agente|bot|hermes|assistant)\s*:/i.test(line);
                      const cleanLine = line.replace(/^(cliente|user|humano|usuário|ia|agente|bot|hermes|assistant)\s*:\s*/i, '');
                      
                      // Se não identificar, usa padrão
                      if (!isClient && !isAgent) {
                         return <p key={i} className="text-xs text-muted-foreground">{line}</p>;
                      }

                      return (
                        <div key={i} className={cn("flex w-full", isClient ? "justify-end" : "justify-start")}>
                          <div className={cn(
                            "max-w-[80%] rounded-2xl px-4 py-2.5 text-[0.85rem] shadow-sm relative",
                            isClient 
                              ? "bg-primary text-primary-foreground rounded-br-none" 
                              : "bg-muted text-foreground rounded-bl-none border border-border/50"
                          )}>
                            <span className="block text-[0.6rem] font-bold uppercase mb-1 opacity-70">
                              {isClient ? "Cliente" : "IA"}
                            </span>
                            {cleanLine}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </details>
              )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
