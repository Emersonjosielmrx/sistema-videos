import { useEffect, useState } from "react";
import { toast } from "sonner";
import { KeyRound, Plus, Trash2, Pencil, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Card } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { getCredentials, createCredential, updateCredential, deleteCredential } from "@/services/settings";
import type { Credential } from "@/types/settings";

// CredentialsSettings — aba única de credenciais (estilo n8n). O usuário cadastra
// suas chaves de API uma vez (Nome + Tipo + Provedor + Chave + Base URL) e depois
// apenas as SELECIONA nas outras abas (IA Padrão, IA da Ligação, Voz). Assim a mesma
// chave pode ser reusada em funções diferentes sem digitá-la de novo.
//
// Tipos: "llm" (IA/LLM), "stt" (Transcrição), "tts" (Voz). O backend guarda a chave
// mascarada ao listar (nunca volta em texto puro) — por isso, ao editar, só reenviamos
// a chave se o usuário digitar uma nova.

// Tipos de credencial que o backend entende. O `label` é o que o dono vê.
const CRED_TYPES = [
  { value: "llm", label: "IA / LLM (texto)" },
  { value: "stt", label: "Transcrição / STT (voz → texto)" },
  { value: "tts", label: "Voz / TTS (texto → voz)" },
  { value: "pay", label: "Pagamentos (Stripe, Asaas, MP)" },
];

// Provedores sugeridos por tipo (ajuda o dono a não errar o nome). É só sugestão —
// o campo aceita qualquer provedor compatível.
const PROVIDERS_BY_TYPE: Record<string, { value: string; label: string }[]> = {
  llm: [
    { value: "anthropic", label: "Anthropic (Claude)" },
    { value: "openai", label: "OpenAI" },
    { value: "gemini", label: "Google Gemini" },
    { value: "groq", label: "Groq" },
    { value: "custom", label: "Custom / Proxy (compatível OpenAI)" },
  ],
  stt: [
    { value: "groq", label: "Groq (Whisper)" },
    { value: "openai", label: "OpenAI (Whisper)" },
    { value: "custom", label: "Custom / Servidor próprio" },
  ],
  tts: [
    { value: "elevenlabs", label: "ElevenLabs" },
    { value: "gemini", label: "Google Gemini TTS" },
    { value: "openai", label: "OpenAI TTS" },
    { value: "custom", label: "Custom / Proxy" },
  ],
  pay: [
    { value: "asaas", label: "Asaas" },
    { value: "stripe", label: "Stripe" },
    { value: "mercadopago", label: "Mercado Pago" },
    { value: "custom", label: "Custom / Outro Gateway" },
  ],
};

function typeLabel(t: string) {
  return CRED_TYPES.find((x) => x.value === t)?.label ?? t;
}

// Estado inicial do formulário (novo cadastro).
const emptyForm = { id: "", name: "", type: "llm", provider: "anthropic", api_key: "", base_url: "" };

export function CredentialsSettings() {
  const [list, setList] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [editing, setEditing] = useState(false); // true quando estamos editando uma credencial existente
  const [toDelete, setToDelete] = useState<Credential | null>(null);

  const reload = () => {
    setLoading(true);
    getCredentials()
      .then(setList)
      .catch((e) => toast.error("Erro ao carregar credenciais", { description: (e as Error).message }))
      .finally(() => setLoading(false));
  };
  useEffect(() => { reload(); }, []);

  // Ao trocar o tipo, ajusta o provider pro 1º sugerido daquele tipo (evita provider inválido).
  const changeType = (type: string) => {
    const first = PROVIDERS_BY_TYPE[type]?.[0]?.value ?? "custom";
    setForm((f) => ({ ...f, type, provider: first }));
  };

  const resetForm = () => { setForm({ ...emptyForm }); setEditing(false); };

  const startEdit = (c: Credential) => {
    // Não trazemos a chave (vem mascarada do backend) — deixamos vazia; só reenvia se digitar nova.
    setForm({ id: c.id, name: c.name, type: c.type, provider: c.provider, api_key: "", base_url: c.base_url });
    setEditing(true);
  };

  const save = async () => {
    if (!form.name.trim()) { toast.error("Dê um nome à credencial"); return; }
    if (!editing && !form.api_key.trim()) { toast.error("Cole a API Key"); return; }
    setSaving(true);
    try {
      const payload: Partial<Credential> = {
        name: form.name.trim(),
        type: form.type,
        provider: form.provider,
        base_url: form.base_url.trim(),
      };
      // Só manda a chave se o usuário digitou algo (no editar, vazio = mantém a atual).
      if (form.api_key.trim()) payload.api_key = form.api_key.trim();

      if (editing) {
        await updateCredential(form.id, payload);
        toast.success("Credencial atualizada");
      } else {
        await createCredential(payload);
        toast.success("Credencial criada");
      }
      resetForm();
      reload();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id: string) => {
    try {
      await deleteCredential(id);
      toast.success("Credencial removida");
      if (form.id === id) resetForm();
      reload();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const providerOptions = PROVIDERS_BY_TYPE[form.type] ?? PROVIDERS_BY_TYPE.llm;

  return (
    <div className="mt-4 space-y-4">
      <Card className="p-4 bg-primary/5 border-primary/20 shadow-glow">
        <div className="mb-1 flex items-center gap-2">
          <KeyRound className="h-4 w-4 text-primary" />
          <h4 className="text-sm font-semibold">Cadastro de chaves de IA</h4>
        </div>
        <p className="text-xs text-muted-foreground">
          Cadastre suas chaves de API (IA/LLM, transcrição, voz e **Pagamentos**) uma vez aqui. Depois é só
          {" "}<strong className="text-foreground">selecioná-las</strong> nas abas <strong className="text-foreground">IA Padrão</strong>,
          {" "}<strong className="text-foreground">IA da Ligação</strong> e <strong className="text-foreground">Voz &amp; Transcrição</strong>.
          As chaves de Pagamento (Asaas, Stripe) permitem que a IA faça cobranças e envie links do seu gateway via Follow-Up automático.
        </p>
      </Card>

      {/* Lista de credenciais salvas */}
      {loading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : list.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nenhuma credencial ainda. Crie a primeira no formulário abaixo.</p>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {list.map((c) => (
            <Card key={c.id} className="p-3 bg-background/50 border-primary/20 shadow-glow transition-all hover:-translate-y-1">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 font-medium">
                    <KeyRound className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                    <span className="truncate">{c.name}</span>
                  </div>
                  <div className="mt-0.5 text-xs text-muted-foreground">{typeLabel(c.type)} · {c.provider}</div>
                  <div className="mt-1 font-mono text-xs text-muted-foreground">{c.api_key || "••••"}</div>
                  {c.base_url && <div className="mt-0.5 truncate text-xs text-muted-foreground">{c.base_url}</div>}
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button variant="ghost" size="sm" onClick={() => startEdit(c)} aria-label={`Editar ${c.name}`}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setToDelete(c)} aria-label={`Excluir ${c.name}`}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Formulário criar / editar */}
      <Card className="space-y-3 p-4 bg-background/50 border-primary/20 shadow-glow">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold">{editing ? "✏️ Editar credencial" : "➕ Nova credencial"}</h4>
          {editing && (
            <Button variant="ghost" size="sm" onClick={resetForm} className="gap-1 text-muted-foreground">
              <X className="h-3.5 w-3.5" /> Cancelar
            </Button>
          )}
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Field label="Nome da credencial" hint="Um apelido pra você identificar (ex.: 'OpenAI Produção', 'ElevenLabs Voz PT').">
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Ex.: OpenAI Produção" />
          </Field>
          <Field label="Tipo" hint="Pra que serve essa chave: IA (texto), Transcrição (STT) ou Voz (TTS).">
            <Select options={CRED_TYPES} value={form.type} onChange={(e) => changeType(e.target.value)} />
          </Field>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Field label="Provedor" hint="Empresa/serviço da chave. Escolha um sugerido ou use 'Custom' para proxy.">
            <Select options={providerOptions} value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} />
          </Field>
          <Field label="Base URL (opcional)" hint="Deixe vazio para o endpoint padrão do provedor. Preencha só para proxy/custom.">
            <Input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} placeholder="https://..." />
          </Field>
        </div>

        <Field
          label="API Key"
          hint={editing
            ? "Deixe vazio para manter a chave atual. Digite uma nova só se quiser trocá-la."
            : "A chave secreta do provedor. Fica guardada no banco, mascarada no painel."}
        >
          <Input
            type="password"
            autoComplete="new-password"
            value={form.api_key}
            onChange={(e) => setForm({ ...form, api_key: e.target.value })}
            placeholder={editing ? "(mantém a atual se vazio)" : "sk-..."}
          />
        </Field>

        <Button onClick={save} disabled={saving} className="gap-1">
          {editing ? <Pencil className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {saving ? "Salvando…" : editing ? "Salvar alterações" : "Criar credencial"}
        </Button>
      </Card>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="Excluir credencial?"
        description={toDelete ? `"${toDelete.name}" será removida. As abas que a usam voltarão a exigir chave manual.` : undefined}
        confirmLabel="Excluir"
        destructive
        onConfirm={() => { if (toDelete) void remove(toDelete.id); }}
      />
    </div>
  );
}
