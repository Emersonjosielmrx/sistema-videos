import { useState, useEffect, useRef, useCallback } from "react";
import { Database, Upload, Trash2, Settings2, Search, ArrowLeft, FileText, Globe, Bot, History, Loader2, AlertTriangle, RefreshCcw, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { apiGet, apiPost, apiUpload, apiDelete, apiErrorMessage } from "@/lib/api";

// Central de Conhecimento (RAG) — tudo aqui vem do servidor:
//   GET    /api/rag/documents?agent_id=<id|global>   lista as fontes da base
//   POST   /api/rag/documents?agent_id=<id|global>   sobe um arquivo (multipart "file")
//   DELETE /api/rag/documents/{id}                   apaga a fonte
//   POST   /api/rag/search {agent_id, query, top_k}  testa o que a IA encontraria
// A base "global" (agent_id = "global") vale para TODOS os agentes.
// Antes esta tela mostrava bases e trechos de exemplo (MOCK_DATASETS/mockChunks) e
// criar/apagar só mexia na memória do navegador.

const GLOBAL_ID = "global";

type Profile = { id: string; name: string };
type RagDoc = { id: string; agent_id?: string; name: string; source: string; chunks: number; created_at: string };
type RagHit = { id: string; document_id: string; content: string; score?: number };
type Base = { agentId: string; name: string; isGlobal: boolean };

const GLOBAL_BASE: Base = { agentId: GLOBAL_ID, name: "Base Global", isGlobal: true };

const docsPath = (agentId: string) => `/api/rag/documents?agent_id=${encodeURIComponent(agentId)}`;

const fmtDate = (iso: string) => {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? "" : d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
};

export function GlobalRagManager() {
  const [agents, setAgents] = useState<Profile[]>([]);
  const [agentsState, setAgentsState] = useState<"loading" | "ok" | "error">("loading");
  const [globalCount, setGlobalCount] = useState<number | null>(null);
  const [globalCountErr, setGlobalCountErr] = useState(false);
  const [activeBase, setActiveBase] = useState<Base | null>(null);

  const loadAgents = useCallback(() => {
    setAgentsState("loading");
    apiGet<{ profiles: Profile[] }>("/api/agent-profiles")
      .then((r) => { setAgents(r.profiles ?? []); setAgentsState("ok"); })
      .catch(() => setAgentsState("error"));
  }, []);

  const loadGlobalCount = useCallback(() => {
    setGlobalCountErr(false);
    apiGet<{ documents: RagDoc[] | null }>(docsPath(GLOBAL_ID))
      .then((r) => setGlobalCount((r.documents ?? []).length))
      .catch(() => { setGlobalCount(null); setGlobalCountErr(true); });
  }, []);

  useEffect(() => { loadAgents(); loadGlobalCount(); }, [loadAgents, loadGlobalCount]);

  if (activeBase) {
    return (
      <RagBaseDetail
        base={activeBase}
        onBack={() => { setActiveBase(null); loadGlobalCount(); }}
      />
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in">
      <div>
        <h2 className="text-2xl font-bold text-sky-500 flex items-center gap-2"><Database className="w-6 h-6" /> Central de Conhecimento (RAG)</h2>
        <p className="text-sm text-muted-foreground mt-1">Documentos que a IA consulta para responder. Suba arquivos de texto ou PDF com preços, regras e perguntas frequentes.</p>
      </div>

      <Tabs defaultValue="global" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="global" className="flex items-center gap-2"><Globe className="w-4 h-4" /> Base Global (todos os agentes)</TabsTrigger>
          <TabsTrigger value="agents" className="flex items-center gap-2"><Bot className="w-4 h-4" /> Bases por agente</TabsTrigger>
        </TabsList>

        <TabsContent value="global" className="m-0">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <button
              type="button"
              className="text-left bg-card/30 border border-border/50 hover:border-sky-500/50 hover:bg-sky-500/5 transition-all p-5 rounded-2xl"
              onClick={() => setActiveBase(GLOBAL_BASE)}
            >
              <div className="p-2 bg-sky-500/10 rounded-lg text-sky-500 w-max mb-3"><Globe className="w-6 h-6" /></div>
              <h3 className="font-bold text-base text-foreground mb-1">Base Global</h3>
              <p className="text-xs text-muted-foreground mb-4">Conhecimento compartilhado por todos os agentes (ex.: políticas da empresa, tabela de preços).</p>
              <div className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
                <FileText className="w-3.5 h-3.5" />
                {globalCountErr ? "Não consegui contar os documentos" : globalCount === null ? "Carregando…" : `${globalCount} ${globalCount === 1 ? "documento" : "documentos"}`}
              </div>
            </button>
          </div>
        </TabsContent>

        <TabsContent value="agents" className="m-0">
          {agentsState === "loading" && (
            <div className="p-8 text-center text-muted-foreground text-sm border border-dashed border-border/50 rounded-2xl flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> Carregando agentes…
            </div>
          )}
          {agentsState === "error" && (
            <div className="p-8 text-center text-sm border border-dashed border-destructive/40 rounded-2xl space-y-3">
              <p className="text-destructive flex items-center justify-center gap-2"><AlertTriangle className="w-4 h-4" /> Não consegui carregar seus agentes.</p>
              <Button variant="outline" size="sm" onClick={loadAgents}><RefreshCcw className="w-3.5 h-3.5 mr-1.5" /> Tentar de novo</Button>
            </div>
          )}
          {agentsState === "ok" && agents.length === 0 && (
            <div className="p-8 text-center text-muted-foreground text-sm border border-dashed border-border/50 rounded-2xl">
              Você ainda não tem agentes. Crie um agente para dar a ele uma base de conhecimento própria.
            </div>
          )}
          {agentsState === "ok" && agents.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {agents.map((agent) => (
                <button
                  type="button"
                  key={agent.id}
                  className="text-left bg-card/30 border border-border/50 hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all p-5 rounded-2xl"
                  onClick={() => setActiveBase({ agentId: agent.id, name: agent.name, isGlobal: false })}
                >
                  <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-500 w-max mb-3"><Bot className="w-6 h-6" /></div>
                  <h3 className="font-bold text-base text-foreground mb-1">{agent.name}</h3>
                  <p className="text-xs text-muted-foreground mb-4">Documentos que só este agente consulta.</p>
                  <div className="flex items-center gap-2 text-xs font-medium text-emerald-500"><Settings2 className="w-3.5 h-3.5" /> Abrir base do agente</div>
                </button>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function RagBaseDetail({ base, onBack }: { base: Base; onBack: () => void }) {
  const [docs, setDocs] = useState<RagDoc[]>([]);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [errMsg, setErrMsg] = useState("");
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Testar busca (o que a IA encontraria para uma pergunta)
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [hits, setHits] = useState<RagHit[] | null>(null);

  const load = useCallback(() => {
    setState("loading");
    apiGet<{ documents: RagDoc[] | null }>(docsPath(base.agentId))
      .then((r) => { setDocs(r.documents ?? []); setState("ok"); })
      .catch((e) => { setErrMsg(apiErrorMessage(e, "Não consegui carregar os documentos.")); setState("error"); });
  }, [base.agentId]);

  useEffect(() => { load(); }, [load]);

  const upload = async (file: File) => {
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await apiUpload<{ id: string; chunks: number }>(docsPath(base.agentId), form);
      toast.success(`"${file.name}" indexado (${r.chunks} trechos).`);
      load();
    } catch (e) {
      toast.error("Não consegui indexar o arquivo", { description: apiErrorMessage(e, "Tente de novo em instantes.") });
    } finally {
      setUploading(false);
    }
  };

  const onFilePicked = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file) upload(file);
  };

  const remove = async (doc: RagDoc) => {
    if (!window.confirm(`Apagar "${doc.name}" da base? A IA deixa de usar este conteúdo.`)) return;
    setDeletingId(doc.id);
    try {
      await apiDelete(`/api/rag/documents/${encodeURIComponent(doc.id)}`);
      setDocs((prev) => prev.filter((d) => d.id !== doc.id));
      toast.success("Documento apagado.");
    } catch (e) {
      toast.error("Não consegui apagar", { description: apiErrorMessage(e, "Tente de novo em instantes.") });
    } finally {
      setDeletingId(null);
    }
  };

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const r = await apiPost<{ chunks: RagHit[] | null }>("/api/rag/search", { agent_id: base.agentId, query: query.trim(), top_k: 4 });
      setHits(r.chunks ?? []);
    } catch (e) {
      setHits(null);
      toast.error("Não consegui testar a busca", { description: apiErrorMessage(e, "Tente de novo em instantes.") });
    } finally {
      setSearching(false);
    }
  };

  const accent = base.isGlobal ? "text-sky-500" : "text-emerald-500";

  return (
    <div className="bg-card/10 border border-border/30 rounded-2xl p-6 space-y-6 animate-in slide-in-from-right-4 fade-in">
      <input ref={fileInputRef} type="file" accept=".pdf,.txt,.md,.csv,.json,text/plain" className="hidden" onChange={onFilePicked} />
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 pb-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={onBack} className="hover:bg-muted/50" aria-label="Voltar"><ArrowLeft className="w-5 h-5" /></Button>
          <div className={`p-2 rounded-lg hidden sm:block ${base.isGlobal ? "bg-sky-500/10 text-sky-500" : "bg-emerald-500/10 text-emerald-500"}`}>
            {base.isGlobal ? <Globe className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
          </div>
          <div>
            <h3 className="text-xl font-bold text-foreground">{base.isGlobal ? "Base Global" : `Base de ${base.name}`}</h3>
            <p className="text-xs text-muted-foreground mt-0.5">{base.isGlobal ? "Vale para todos os agentes." : "Só este agente consulta estes documentos."}</p>
          </div>
        </div>
        <Button onClick={() => fileInputRef.current?.click()} disabled={uploading} className={base.isGlobal ? "bg-sky-500 hover:bg-sky-600 text-white" : ""}>
          {uploading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Enviando…</> : <><Upload className="w-4 h-4 mr-2" /> Adicionar documento</>}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Documentos da base */}
        <div className="space-y-3">
          <h4 className="text-sm font-bold flex items-center gap-2"><FileText className={`w-4 h-4 ${accent}`} /> Documentos</h4>
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f && !uploading) upload(f); }}
            className="space-y-2"
          >
            {state === "loading" && (
              <p className="text-xs text-muted-foreground flex items-center gap-2 p-4"><Loader2 className="w-3.5 h-3.5 animate-spin" /> Carregando documentos…</p>
            )}
            {state === "error" && (
              <div className="p-4 border border-dashed border-destructive/40 rounded-xl space-y-2 text-center">
                <p className="text-xs text-destructive flex items-center justify-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> {errMsg}</p>
                <Button variant="outline" size="sm" onClick={load}><RefreshCcw className="w-3.5 h-3.5 mr-1.5" /> Tentar de novo</Button>
              </div>
            )}
            {state === "ok" && docs.length === 0 && (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full text-center p-6 border-2 border-dashed border-border/60 hover:border-primary/50 rounded-xl bg-muted/10 transition-colors"
              >
                <Upload className="w-6 h-6 text-muted-foreground mx-auto mb-2 opacity-60" />
                <p className="text-sm font-medium text-foreground">Nenhum documento ainda</p>
                <p className="text-xs text-muted-foreground mt-1">Arraste um arquivo aqui ou clique. PDF, TXT, MD, CSV ou JSON (até 8 MB).</p>
              </button>
            )}
            {state === "ok" && docs.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between gap-2 p-3 bg-card/50 border border-border/50 rounded-xl">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="p-1.5 bg-background rounded-lg border border-border/50 shrink-0">
                    {doc.source === "conversations" ? <History className="w-4 h-4 text-emerald-500" /> : <FileText className={`w-4 h-4 ${accent}`} />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold truncate" title={doc.name}>{doc.name}</p>
                    <p className="text-[10px] text-muted-foreground flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-500" /> {doc.chunks} trechos{fmtDate(doc.created_at) ? ` · ${fmtDate(doc.created_at)}` : ""}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive shrink-0"
                  onClick={() => remove(doc)} disabled={deletingId === doc.id} aria-label={`Apagar ${doc.name}`}
                >
                  {deletingId === doc.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                </Button>
              </div>
            ))}
          </div>
        </div>

        {/* Testar a busca */}
        <div className="space-y-3">
          <h4 className="text-sm font-bold flex items-center gap-2"><Search className="w-4 h-4 text-amber-500" /> Testar o que a IA encontra</h4>
          <p className="text-xs text-muted-foreground">Escreva uma pergunta de cliente e veja quais trechos desta base a IA usaria para responder.</p>
          <div className="flex gap-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") search(); }}
              placeholder="Ex.: qual o prazo de devolução?"
              className="h-10 text-sm bg-background/80"
            />
            <Button variant="outline" className="h-10" onClick={search} disabled={searching || !query.trim()}>
              {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : "Testar"}
            </Button>
          </div>
          {hits !== null && (
            hits.length === 0 ? (
              <p className="text-xs text-muted-foreground p-3 border border-dashed border-border/50 rounded-xl">Nada encontrado nesta base para essa pergunta.</p>
            ) : (
              <div className="space-y-2">
                {hits.map((h, i) => (
                  <div key={h.id || i} className="p-3 bg-card/50 border border-border/50 rounded-xl">
                    {typeof h.score === "number" && (
                      <p className="text-[10px] font-mono text-muted-foreground mb-1">Semelhança: {Math.round(h.score * 100)}%</p>
                    )}
                    <p className="text-xs whitespace-pre-wrap line-clamp-6">{h.content}</p>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
