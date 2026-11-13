import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getRecordings, deleteRecording } from "@/services/security";
import { getApiBase, getApiKey } from "@/lib/auth";
import type { CallRecording } from "@/types/security";

function formatDuration(sec: number): string {
  const totalSec = Math.floor(sec);
  const min = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${min}m ${s}s`;
}

// URL autenticada do audio (o <audio> nao manda header, entao passa apiKey na query)
// FIX P0-006 (2026-07-25): JWT em URL é visível para proxies. <audio> não
// suporta custom headers. TODO longo prazo: cookie httpOnly. Por agora, log
// explícito para deixar evidência do problema.
function audioUrl(id: string): string {
  const apiKey = getApiKey();
  if (apiKey && typeof console !== "undefined") {
    console.warn("[SECURITY P0-006] JWT em URL (audioUrl) — visível para proxies.");
  }
  return `${getApiBase()}/api/recordings/${id}/audio?apiKey=${encodeURIComponent(apiKey)}`;
}

const PAGE_SIZE = 20;

export function RecordingsPage() {
  const [recordings, setRecordings] = useState<CallRecording[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);

  const load = async (p: number) => {
    setLoading(true);
    try {
      const data = await getRecordings(PAGE_SIZE, p * PAGE_SIZE);
      setRecordings(data.recordings || []);
      setTotal(data.total || 0);
    } catch {
      toast.error("Erro ao carregar gravações");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(page); }, [page]);

  const handleDelete = async (id: string) => {
    try {
      await deleteRecording(id);
      toast.success("Gravação excluída");
      await load(page);
    } catch {
      toast.error("Erro ao excluir gravação");
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="flex h-full flex-col gap-4 p-6">
      <h2 className="text-xl font-semibold">Gravações de Chamadas</h2>

      <Card className="flex-1 overflow-auto p-0">
        {loading ? (
          <div className="flex items-center justify-center gap-3 p-10 text-sm text-muted-foreground">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-primary" />
            Carregando gravações...
          </div>
        ) : recordings.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">Nenhuma gravação encontrada.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Contato</th>
                <th className="px-4 py-2 text-left font-medium">Direção</th>
                <th className="px-4 py-2 text-left font-medium">Duração</th>
                <th className="px-4 py-2 text-left font-medium">Data</th>
                <th className="px-4 py-2 text-left font-medium">Áudio</th>
                <th className="px-4 py-2 text-left font-medium">Ações</th>
              </tr>
            </thead>
            <tbody>
              {recordings.map((rec) => (
                <tr key={rec.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="px-4 py-2 font-mono">{rec.remote_jid?.split("@")[0] || "—"}</td>
                  <td className="px-4 py-2">{rec.direction === "inbound" ? "Recebida" : "Realizada"}</td>
                  <td className="px-4 py-2">{formatDuration(rec.duration_sec)}</td>
                  <td className="px-4 py-2">{new Date(rec.created_at).toLocaleString("pt-BR")}</td>
                  <td className="px-4 py-2">
                    <audio controls preload="none" src={audioUrl(rec.id)} className="h-8 max-w-[220px]" />
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap">
                    <a href={audioUrl(rec.id)} download className="text-primary hover:underline text-xs mr-3">Baixar</a>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(rec.id)}>Excluir</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            Página {page + 1} de {totalPages} ({total} gravações)
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>
              Anterior
            </Button>
            <Button variant="outline" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>
              Próxima
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
