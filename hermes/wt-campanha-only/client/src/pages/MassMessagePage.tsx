import { useState, useEffect } from "react";
import { ArrowLeft, Play, XCircle, Users, CheckCircle, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useMassMessageStore } from "@/stores/massmsg";
import { useSessions } from "@/stores/sessions";
import { setView } from "@/stores/navigation";
import { startMassMessage, getMassMessageStatus, cancelMassMessage } from "@/services/massmsg";
import type { MassMessageJob } from "@/types/massmsg";
import { toast } from "sonner";

export const MassMessagePage = () => {
  const contacts = useMassMessageStore((s) => s.contacts);
  const setContacts = useMassMessageStore((s) => s.setContacts);
  const clearContacts = useMassMessageStore((s) => s.clear);
  const [message, setMessage] = useState("");
  const [delay, setDelay] = useState(5);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<MassMessageJob | null>(null);
  // Entrada manual de números (pedido #10: faltava campo pra adicionar números/listas;
  // antes só dava pra vir da aba Contatos). Cola vários separados por vírgula/linha.
  const [manualNumbers, setManualNumbers] = useState("");

  const sessions = useSessions((s) => s.sessions);
  const activeSession = sessions.find((s) => s.paired);

  // Status em tempo real via polling (a cada 3s no efeito abaixo). O SSE antigo
  // apontava pra uma rota inexistente e sem auth, então foi removido.
  // Lista vazia NÃO expulsa mais pra "crm" (relato #10 da dona: "somem as sub-abas");
  // a tela mostra a entrada manual de números e um estado vazio.

  // Converte os números colados manualmente em Contacts e junta com os já selecionados.
  const addManualNumbers = () => {
    const parsed = manualNumbers
      .split(/[\s,;]+/)
      .map((n) => n.replace(/\D/g, ""))
      .filter((n) => n.length >= 10);
    if (parsed.length === 0) {
      toast.error("Nenhum número válido (use DDD, ex.: 11987654321)");
      return;
    }
    const existing = new Set(contacts.map((c) => c.phone));
    const novos = parsed
      .filter((p) => !existing.has(p))
      .map((p) => ({ jid: `${p}@s.whatsapp.net`, phone: p, name: "", push_name: "", business_name: "", is_group: false }));
    if (novos.length === 0) {
      toast.info("Todos os números já estavam na lista");
      return;
    }
    setContacts([...contacts, ...novos]);
    setManualNumbers("");
    toast.success(`${novos.length} número(s) adicionado(s)`);
  };

  useEffect(() => {
    if (jobId) {
      const fetchStatus = async () => {
        try {
          const res = await getMassMessageStatus(jobId);
          setJob(res);
          if (res.status === "completed" || res.status === "cancelled" || res.status === "failed") {
            clearInterval(interval);
          }
        } catch (e) {
          console.error(e);
        }
      };
      fetchStatus();
      const interval = setInterval(fetchStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [jobId]);

  const handleStart = async () => {
    if (!message.trim()) {
      toast.error("A mensagem não pode estar vazia");
      return;
    }
    if (!activeSession) {
      toast.error("Nenhuma sessão WhatsApp ativa");
      return;
    }
    try {
      const newJob = await startMassMessage({
        sessionId: activeSession.id,
        message,
        delay_between: delay,
        contacts,
      });
      setJobId(newJob.id);
      setJob(newJob);
      toast.success("Envio em massa iniciado!");
    } catch (e: any) {
      toast.error("Erro ao iniciar", { description: e.message });
    }
  };

  const handleCancel = async () => {
    if (!jobId) return;
    try {
      await cancelMassMessage(jobId);
      toast.info("Processo cancelado");
    } catch (e: any) {
      toast.error("Erro ao cancelar", { description: e.message });
    }
  };

  const handleClose = () => {
    clearContacts();
    setView("crm");
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-20">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={handleClose}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h2 className="text-xl font-semibold">Envio em Massa</h2>
      </div>

      {!jobId ? (
        <div className="grid gap-6 md:grid-cols-[1fr_300px]">
          <div className="space-y-6">
            <Card className="p-4 space-y-4">
              <div className="space-y-2">
                <Label>Mensagem</Label>
                <Textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Olá! Temos uma novidade para você..."
                  className="min-h-[150px] resize-y"
                />
              </div>

              <div className="space-y-2">
                <Label>Intervalo entre envios (segundos)</Label>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <Input
                    type="number"
                    min="2"
                    max="60"
                    value={delay}
                    onChange={(e) => setDelay(Number(e.target.value))}
                    className="w-24"
                  />
                  <span className="text-sm text-muted-foreground">
                    Recomendado: 5-10s para evitar bloqueios
                  </span>
                </div>
              </div>

              <Button
                size="lg"
                className="w-full gap-2"
                onClick={handleStart}
                disabled={!message.trim() || contacts.length === 0}
              >
                <Play className="h-5 w-5" />
                Iniciar Envio para {contacts.length} contatos
              </Button>
            </Card>
          </div>

          <div className="space-y-4">
            <h3 className="font-medium flex items-center gap-2">
              <Users className="w-4 h-4" />
              Alvos ({contacts.length})
            </h3>

            {/* Entrada manual de números (#10): antes só vinha da aba Contatos. */}
            <Card className="p-3 space-y-2">
              <Label className="text-xs">Adicionar números manualmente</Label>
              <Textarea
                value={manualNumbers}
                onChange={(e) => setManualNumbers(e.target.value)}
                placeholder="Cole números com DDD, separados por vírgula ou linha. Ex.: 11987654321, 21998765432"
                className="min-h-[70px] text-sm resize-y"
              />
              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="flex-1" onClick={addManualNumbers} disabled={!manualNumbers.trim()}>
                  Adicionar à lista
                </Button>
                {contacts.length > 0 && (
                  <Button size="sm" variant="ghost" className="text-destructive" onClick={clearContacts}>
                    Limpar
                  </Button>
                )}
              </div>
            </Card>

            {contacts.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">
                Nenhum alvo ainda. Adicione números acima ou selecione contatos na aba Contatos.
              </p>
            ) : (
              <div className="max-h-[400px] overflow-y-auto space-y-2">
                {contacts.map((c) => (
                  <div key={c.jid} className="p-2 border rounded text-sm bg-muted/50">
                    <div className="font-medium truncate">{c.name || c.push_name || c.phone}</div>
                    <div className="text-xs text-muted-foreground">+{c.phone}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <Card className="p-6 space-y-6">
          <div className="text-center space-y-2">
            <h3 className="text-xl font-medium">Status do Envio</h3>
            <p className="text-muted-foreground">
              {job?.status === "running" && "Enviando mensagens..."}
              {job?.status === "completed" && "Envio concluído!"}
              {job?.status === "cancelled" && "Envio cancelado."}
              {job?.status === "failed" && "Erro no envio."}
            </p>
          </div>

          {job && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progresso</span>
                <span>
                  {job.progress} / {job.total} (
                  {Math.round((job.progress / job.total) * 100)}%)
                </span>
              </div>
              <Progress value={(job.progress / job.total) * 100} />
            </div>
          )}

          <div className="max-h-[300px] overflow-y-auto space-y-2 border rounded-md p-4">
            {job?.results?.map((r, i) => (
              <div key={i} className="flex items-center justify-between text-sm p-2 bg-muted/50 rounded">
                <div>
                  <div className="font-medium">{r.name || "+" + r.phone}</div>
                </div>
                {r.status === "sent" ? (
                  <span className="flex items-center justify-center gap-1 text-green-500">
                    <CheckCircle className="w-4 h-4" /> Enviado
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-1 text-red-500" title={r.error}>
                    <XCircle className="w-4 h-4" /> Falhou
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-center gap-4">
            {job?.status === "running" ? (
              <Button variant="destructive" onClick={handleCancel}>
                Cancelar
              </Button>
            ) : (
              <Button onClick={handleClose}>Voltar aos Contatos</Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
