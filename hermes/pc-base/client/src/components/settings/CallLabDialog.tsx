import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { PhoneCall, Play, Mic, Gauge, AlertTriangle, CheckCircle2, Lightbulb } from "lucide-react";
import { apiGet, apiPost } from "@/lib/api";

// Laboratório de Ligações (POST /api/agents/{id}/call-lab): o agente de LIGAÇÃO conversa
// por escrito com uma IA cliente — mesmo prompt, modelo e regras da ligação — e uma IA juiz
// avalia. Opcional: teste de pronúncia (falas do vendedor → voz real → transcrição).

type Pron = { ouvido: string; diferencas: string[] | null; ms_voz: number; erro?: string };
type Turno = { cliente: string; vendedor: string; falado: string; ms_ia: number; ms_primeira_frase?: number; pronuncia?: Pron };
type Juiz = {
  nota: number; disse_preco: boolean; respostas_curtas: boolean; inventou_algo: boolean;
  problemas: string[] | null; sugestoes_prompt: string[] | null; resumo: string;
};
type Resultado = {
  agente: string; persona: string; modo: string; modelo: string; abertura: string[] | null;
  turnos: Turno[] | null; avaliacao?: Juiz; ms_ia_medio: number; encerrou: string;
  pronuncia: boolean; palavras_ruins?: string[] | null;
};
type Cred = { id: string; name: string; provider: string; type: string };

const PERSONAS: { id: string; label: string }[] = [
  { id: "curioso", label: "Curioso (quem fala, como funciona, preço, teste)" },
  { id: "preco", label: "Quer o preço logo e pede desconto" },
  { id: "desconfiado", label: "Desconfiado (é golpe? de onde tirou meu número?)" },
  { id: "apressado", label: "Apressado (resume! ameaça desligar)" },
  { id: "sem_interesse", label: "Sem interesse (tenta encerrar)" },
  { id: "atendimento", label: "Cliente que LIGA pra empresa (agente que atende)" },
];

const s = (v: unknown) => (typeof v === "string" ? v : v == null ? "" : String(v));

export function CallLabDialog({ agentId, open, onOpenChange }: { agentId: string; open: boolean; onOpenChange: (o: boolean) => void }) {
  const [persona, setPersona] = useState("curioso");
  const [turnos, setTurnos] = useState(6);
  const [pronuncia, setPronuncia] = useState(false);
  const [modelo, setModelo] = useState("");
  const [chave, setChave] = useState("");
  const [creds, setCreds] = useState<Cred[]>([]);
  const [rodando, setRodando] = useState(false);
  const [res, setRes] = useState<Resultado | null>(null);

  useEffect(() => {
    if (!open) return;
    apiGet<{ credentials: Cred[] }>("/api/credentials")
      .then((r) => setCreds((r.credentials || []).filter((c) => c.type === "llm" || ["gemini", "openai", "groq", "anthropic"].includes(c.provider))))
      .catch(() => setCreds([]));
  }, [open]);

  const rodar = async () => {
    setRodando(true);
    setRes(null);
    try {
      const r = await apiPost<Resultado>(`/api/agents/${agentId}/call-lab`, {
        persona, turnos, pronuncia, modo: persona === "atendimento" ? "atendimento" : "vendas", modelo, chave,
      });
      setRes(r);
    } catch (e) {
      toast.error("O teste não rodou: " + s((e as Error).message).slice(0, 200));
    } finally {
      setRodando(false);
    }
  };

  const j = res?.avaliacao;
  const nota = j?.nota ?? 0;
  const corNota = nota >= 8 ? "text-emerald-500" : nota >= 6 ? "text-amber-500" : "text-red-500";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><PhoneCall className="h-5 w-5 text-indigo-500" /> Laboratório de ligação</DialogTitle>
          <DialogDescription>
            Uma IA faz o papel do cliente e conversa por escrito com este agente de ligação — com o mesmo prompt, o mesmo modelo
            e as mesmas regras da ligação de verdade. Ninguém recebe ligação nem mensagem; as ações só são simuladas.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 sm:grid-cols-2 text-sm">
          <label className="space-y-1">
            <span className="font-medium">Cliente</span>
            <select className="w-full rounded-md border bg-background px-2 py-2" value={persona} onChange={(e) => setPersona(e.target.value)}>
              {PERSONAS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
          </label>
          <label className="space-y-1">
            <span className="font-medium">Turnos de conversa ({turnos})</span>
            <input type="range" min={2} max={12} value={turnos} onChange={(e) => setTurnos(Number(e.target.value))} className="w-full" />
          </label>
          <label className="space-y-1">
            <span className="font-medium">Modelo (vazio = o da ligação)</span>
            <Input placeholder="ex.: gemini-3.5-flash-lite" value={modelo} onChange={(e) => setModelo(e.target.value)} />
          </label>
          <label className="space-y-1">
            <span className="font-medium">Chave (vazio = a da ligação)</span>
            <select className="w-full rounded-md border bg-background px-2 py-2" value={chave} onChange={(e) => setChave(e.target.value)}>
              <option value="">— a da ligação —</option>
              {creds.map((c) => <option key={c.id} value={c.name}>{c.name} ({c.provider})</option>)}
            </select>
          </label>
          <label className="flex items-center gap-2 sm:col-span-2">
            <input type="checkbox" checked={pronuncia} onChange={(e) => setPronuncia(e.target.checked)} />
            <Mic className="h-4 w-4" /> Testar a pronúncia (as falas do vendedor viram áudio na voz da ligação e são transcritas — gasta crédito de voz)
          </label>
        </div>

        <div className="flex justify-end">
          <Button onClick={rodar} disabled={rodando} className="gap-2">
            <Play className="h-4 w-4" /> {rodando ? "Conversando… (até 2 min)" : "Rodar teste"}
          </Button>
        </div>

        {res && (
          <ScrollArea className="flex-1 min-h-0 border rounded-md">
            <div className="p-3 space-y-3 text-sm">
              {j && (
                <div className="rounded-md border p-3 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`text-2xl font-bold ${corNota}`}>{nota}/10</span>
                    <Badge variant={j.disse_preco ? "default" : "destructive"}>{j.disse_preco ? "disse o preço" : "não disse o preço"}</Badge>
                    <Badge variant={j.respostas_curtas ? "default" : "destructive"}>{j.respostas_curtas ? "respostas curtas" : "respostas longas"}</Badge>
                    <Badge variant={j.inventou_algo ? "destructive" : "default"}>{j.inventou_algo ? "inventou algo" : "não inventou"}</Badge>
                    <Badge variant="outline" className="gap-1"><Gauge className="h-3 w-3" /> IA {res.ms_ia_medio} ms/resposta</Badge>
                    <Badge variant="outline">{s(res.modelo)}</Badge>
                  </div>
                  {s(j.resumo) && <p className="text-muted-foreground">{s(j.resumo)}</p>}
                  {(j.problemas || []).length > 0 && (
                    <ul className="space-y-1">{(j.problemas || []).map((p, i) => <li key={i} className="flex gap-2"><AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />{s(p)}</li>)}</ul>
                  )}
                  {(j.sugestoes_prompt || []).length > 0 && (
                    <ul className="space-y-1">{(j.sugestoes_prompt || []).map((p, i) => <li key={i} className="flex gap-2"><Lightbulb className="h-4 w-4 text-indigo-500 shrink-0" />{s(p)}</li>)}</ul>
                  )}
                  {(res.palavras_ruins || []).length > 0 && (
                    <p><b>Palavras que a voz pode estar falando errado:</b> {(res.palavras_ruins || []).join(", ")}</p>
                  )}
                </div>
              )}
              {(res.abertura || []).map((a, i) => (
                <div key={"a" + i} className="text-muted-foreground italic">🎙️ {s(a)}</div>
              ))}
              {(res.turnos || []).map((t, i) => (
                <div key={i} className="space-y-1">
                  <div><b>Cliente:</b> {s(t.cliente)}</div>
                  <div className="rounded-md bg-indigo-500/10 p-2">
                    <b>Agente:</b> {s(t.vendedor)} <span className="text-xs text-muted-foreground">(1ª frase em {t.ms_primeira_frase ?? t.ms_ia} ms)</span>
                    {s(t.falado) && s(t.falado) !== s(t.vendedor) && <div className="text-xs text-muted-foreground mt-1">🔊 falado: {s(t.falado)}</div>}
                    {t.pronuncia && (
                      <div className="text-xs mt-1">
                        {t.pronuncia.erro ? <span className="text-red-500">pronúncia: {s(t.pronuncia.erro)}</span> : (
                          (t.pronuncia.diferencas || []).length === 0
                            ? <span className="text-emerald-600 flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> pronúncia ok</span>
                            : <span className="text-amber-600">ouvido: "{s(t.pronuncia.ouvido)}" — confere: {(t.pronuncia.diferencas || []).join(", ")}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div className="text-xs text-muted-foreground">Fim: {s(res.encerrou)} · cliente: {s(res.persona)}</div>
            </div>
          </ScrollArea>
        )}
      </DialogContent>
    </Dialog>
  );
}
