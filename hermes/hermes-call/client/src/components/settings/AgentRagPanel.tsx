import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { UploadCloud, History, FileText, Trash2, Loader2 } from "lucide-react";
import { apiGet, apiDelete } from "@/lib/api";
import { logError } from "@/lib/log";
import { apiUrl, authHeaders } from "@/lib/auth";
import { getClientId } from "@/lib/client-id";

// AgentRagPanel — base de conhecimento (RAG) de um agente de texto. Sobe documentos
// (txt/md/csv), lista/apaga, e "destila" o histórico de conversas pra treinar o agente.
// Backend: /api/rag/documents (upload multipart + list + delete) e
// /api/rag/ingest-conversations.

type RagDoc = {
  id: string;
  name: string;
  source: string; // upload | conversations
  chunks: number;
  created_at: string;
};

export function AgentRagPanel({ agentId }: { agentId: string }) {
  const [docs, setDocs] = useState<RagDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const reload = () => {
    apiGet<{ documents: RagDoc[] }>(`/api/rag/documents?agent_id=${encodeURIComponent(agentId)}`)
      .then((r) => setDocs(r.documents ?? []))
      .catch(logError("AgentRagPanel"))
      .finally(() => setLoading(false));
  };
  useEffect(() => { reload(); }, [agentId]);

  const upload = async (file: File) => {
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(apiUrl(`/api/rag/documents?agent_id=${encodeURIComponent(agentId)}`), {
        method: "POST",
        headers: { "X-Client-Id": getClientId(), ...authHeaders() }, // sem Content-Type: browser define o boundary
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { toast.error(data.error || "Falha no upload"); return; }
      toast.success(`Indexado: ${data.chunks} trechos`);
      reload();
    } catch (e) {
      toast.error("Falha no upload", { description: (e as Error).message });
    } finally {
      setUploading(false);
    }
  };

  const ingestHistory = async () => {
    setIngesting(true);
    try {
      const res = await fetch(apiUrl(`/api/rag/ingest-conversations`), {
        method: "POST",
        headers: { "X-Client-Id": getClientId(), "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ agent_id: agentId }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) { toast.error(data.error || "Falha ao treinar"); return; }
      toast.success(data.chunks > 0 ? `Treinado com ${data.chunks} trechos das conversas` : "Nenhuma conversa pra indexar ainda");
      reload();
    } catch (e) {
      toast.error("Falha ao treinar", { description: (e as Error).message });
    } finally {
      setIngesting(false);
    }
  };

  const del = async (id: string) => {
    try {
      await apiDelete(`/api/rag/documents/${id}`);
      reload();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-4">
        <h5 className="font-bold flex items-center gap-2"><FileText className="h-4 w-4 text-amber-500" /> Arquivos (TXT, MD, CSV)</h5>
        <div
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) upload(f); }}
          className="border-2 border-dashed border-border/60 hover:border-primary/50 transition-colors rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer bg-muted/10 hover:bg-muted/30"
        >
          {uploading ? <Loader2 className="h-6 w-6 text-primary mb-2 animate-spin" /> : <UploadCloud className="h-6 w-6 text-muted-foreground mb-2" />}
          <p className="text-sm font-medium text-foreground">{uploading ? "Enviando…" : "Arraste um arquivo ou clique"}</p>
          <p className="text-xs text-muted-foreground mt-1">TXT, MD, CSV (máx 8MB)</p>
        </div>
        <input
          type="file" className="hidden" ref={fileRef}
          accept=".txt,.md,.csv,.json,text/plain"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ""; }}
        />
      </div>

      {/* Lista de fontes indexadas */}
      <div className="space-y-2">
        {loading ? (
          <p className="text-xs text-muted-foreground">Carregando base…</p>
        ) : docs.length === 0 ? (
          <p className="text-xs text-muted-foreground">Nenhum documento indexado ainda.</p>
        ) : (
          docs.map((d) => (
            <div key={d.id} className="flex items-center justify-between bg-muted/30 p-2 rounded-lg border border-border/50">
              <div className="flex items-center gap-2 min-w-0">
                {d.source === "conversations" ? <History className="h-4 w-4 text-emerald-500 shrink-0" /> : <FileText className="h-4 w-4 text-amber-500 shrink-0" />}
                <span className="text-xs truncate">{d.name}</span>
                <Badge variant="outline" className="text-[0.65rem] bg-emerald-500/10 text-emerald-500 border-emerald-500/20 shrink-0">{d.chunks} trechos</Badge>
              </div>
              <button onClick={() => del(d.id)} className="text-muted-foreground hover:text-destructive shrink-0" aria-label="Remover">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Destilar histórico do CRM/conversas */}
      <div className="border-t border-border/50 pt-5 mt-5">
        <h5 className="font-bold flex items-center gap-2 mb-2"><History className="h-4 w-4 text-emerald-500" /> Destilar Histórico</h5>
        <p className="text-sm text-muted-foreground mb-3">A IA lê as transcrições das ligações/conversas para aprender o tom e as respostas frequentes da sua equipe.</p>
        <Button variant="secondary" className="rounded-xl w-full mb-4" onClick={ingestHistory} disabled={ingesting}>
          {ingesting ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Treinando…</> : "Treinar Manualmente Agora"}
        </Button>
        {/* Ainda não existe no servidor: antes este botão aparecia LIGADO (só na tela). */}
        <div className="flex items-start gap-3 bg-muted/20 p-3 rounded-xl border border-border/50 mt-4 opacity-70" title="Em breve">
           <Switch checked={false} disabled id="auto-evolve" />
           <div className="flex-1">
              <Label htmlFor="auto-evolve" className="text-sm font-bold flex items-center gap-1.5 text-muted-foreground">
                <History className="w-3.5 h-3.5" /> Auto-Evolução (Shadowing)
                <span className="text-[10px] font-bold uppercase text-amber-500 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded">em breve</span>
              </Label>
              <p className="text-[0.65rem] text-muted-foreground mt-0.5 leading-tight">Quando uma reunião for classificada como "Sucesso", a IA extrairá automaticamente os melhores argumentos do humano e os aprenderá para a próxima ligação.</p>
           </div>
        </div>
      </div>
    </div>
  );
}
