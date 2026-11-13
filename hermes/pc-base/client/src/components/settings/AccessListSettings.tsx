import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { getAccessList, setAccessMode, addAccessEntry, removeAccessEntry } from "@/services/security";
import type { AccessEntry } from "@/types/security";

const modeOptions = [
  { value: "none", label: "Desativado" },
  { value: "whitelist", label: "So permitidos" },
  { value: "blacklist", label: "Bloquear listados" },
];

export function AccessListSettings() {
  const [mode, setMode] = useState("none");
  const [entries, setEntries] = useState<AccessEntry[]>([]);
  const [phone, setPhone] = useState("");
  const [label, setLabel] = useState("");
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const data = await getAccessList();
      setMode(data.mode || "disabled");
      setEntries(data.entries || []);
    } catch (e) {
      toast.error("Erro ao carregar lista de acesso");
    }
  };

  useEffect(() => { load(); }, []);

  const handleModeChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newMode = e.target.value;
    try {
      await setAccessMode(newMode);
      setMode(newMode);
      toast.success("Modo atualizado");
    } catch {
      toast.error("Erro ao alterar modo");
    }
  };

  const handleAdd = async () => {
    if (!phone.trim()) return;
    setLoading(true);
    try {
      const jid = phone.replace(/\D/g, "") + "@s.whatsapp.net";
      await addAccessEntry(jid, phone.trim(), label.trim());
      setPhone("");
      setLabel("");
      await load();
      toast.success("Contato adicionado");
    } catch {
      toast.error("Erro ao adicionar contato");
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (jid: string) => {
    try {
      await removeAccessEntry(jid);
      setEntries((prev) => prev.filter((e) => e.jid !== jid));
      toast.success("Contato removido");
    } catch {
      toast.error("Erro ao remover contato");
    }
  };

  return (
    <Card className="mt-4 space-y-5 p-4">
      <Field
        label="Modo da lista de acesso"
        hint="Desativado = todos podem usar. Lista de permitidos = só os numeros listados podem usar. Lista de bloqueio = todos podem exceto os listados."
      >
        <select className="w-full rounded-md border bg-background px-3 py-2 text-sm" value={mode} onChange={handleModeChange}>
          {modeOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </Field>

      <div className="flex items-end gap-2">
        <Field label="Telefone" hint="Numero com codigo do pais. Ex: +55 11 99999-9999. Apenas digitos sao usados.">
          <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+55 11 99999-9999" />
        </Field>
        <Field label="Rotulo" hint="Nome ou descricao para identificar este contato na lista.">
          <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Nome ou descricao" />
        </Field>
        <Button onClick={handleAdd} disabled={loading || !phone.trim()}>Adicionar</Button>
      </div>

      <div className="space-y-2">
        {entries.length === 0 && (
          <p className="text-sm text-muted-foreground">Nenhum contato na lista.</p>
        )}
        {entries.map((entry) => (
          <div key={entry.jid} className="flex items-center justify-between rounded-md border px-3 py-2">
            <div>
              <span className="text-sm font-medium">{entry.phone}</span>
              {entry.label && <span className="ml-2 text-sm text-muted-foreground">({entry.label})</span>}
            </div>
            <Button variant="ghost" size="sm" onClick={() => handleRemove(entry.jid)} title="Remover">✕</Button>
          </div>
        ))}
      </div>
    </Card>
  );
}
