import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Field, ToggleField } from "@/components/ui/field";
import { updateAgentChat, createAgentGroup, agentChatSemRoteamento } from "@/services/settings";
import type { AgentChatSettings as AgentChatCfg } from "@/types/settings";

export function AgentChatSettings({ initial, onSaved }: { initial: AgentChatCfg; onSaved: () => void }) {
  const [cfg, setCfg] = useState<AgentChatCfg>(initial);
  const [saving, setSaving] = useState(false);
  const [creatingGroup, setCreatingGroup] = useState(false);
  const [groupName, setGroupName] = useState(cfg.group_name || "Hermes Call - Assistente IA");

  const save = async () => {
    setSaving(true);
    try {
      await updateAgentChat(agentChatSemRoteamento(cfg));
      toast.success("Configurações do agente salvas");
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateGroup = async () => {
    setCreatingGroup(true);
    try {
      const result = await createAgentGroup(groupName, cfg.welcome_msg || "👋 Olá! Sou o Hermes, seu assistente IA. Mande uma mensagem e eu respondo!");
      setCfg({ ...cfg, group_jid: result.group_jid, group_name: result.name });
      toast.success(`Grupo "${result.name}" criado com sucesso!`);
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCreatingGroup(false);
    }
  };

  return (
    <div className="space-y-4 mt-4">
      {/* Tutorial */}
      <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
        <h4 className="font-semibold text-sm mb-2">📖 Como configurar o atendimento automático</h4>
        <ol className="text-xs text-slate-400 space-y-1 list-decimal list-inside">
          <li>Conecte seu WhatsApp (menu Sessões → Escanear QR)</li>
          <li>Configure a IA (Settings → Inteligência Artificial → API key)</li>
          <li>Ative o Agente WhatsApp aqui embaixo</li>
          <li>Escolha o modo: Privado (responde PVs) ou Grupo (cria grupo dedicado)</li>
          <li>Pronto — o Hermes já começa a responder!</li>
        </ol>
        <p className="text-xs text-slate-500 mt-2">💡 Use o Telegram pra monitorar as conversas em tempo real</p>
      </Card>

      {/* Main config */}
      <Card className="p-4 space-y-4">
        <ToggleField
          label="Agente WhatsApp ativo"
          hint="Liga/desliga o atendimento automático por WhatsApp. Quando ativo, o Hermes responde clientes automaticamente."
          checked={cfg.enabled}
          onChange={(v) => setCfg({ ...cfg, enabled: v })}
        />

        <Field
          label="Modo de resposta"
          hint="Escolhe se o agente responde só em conversas privadas (PV) ou cria um grupo dedicado pro atendimento."
        >
          <div className="grid grid-cols-3 gap-3">
            <button
              type="button"
              onClick={() => setCfg({ ...cfg, mode: "private" })}
              title="O agente responde qualquer pessoa que mandar mensagem no seu WhatsApp privado"
              className={`rounded-lg border p-3 text-left text-sm transition-all ${
                cfg.mode === "private" || (!cfg.mode && cfg.mode !== "group" && cfg.mode !== "all")
                  ? "border-emerald-500 bg-emerald-600/10"
                  : "border-white/10 hover:border-white/20"
              }`}
            >
              <p className="font-medium">Só privado</p>
              <p className="text-xs text-slate-400 mt-1">Responde só em PV</p>
            </button>
            <button
              type="button"
              onClick={() => setCfg({ ...cfg, mode: "group" })}
              title="O agente só responde dentro de um grupo específico que você criar"
              className={`rounded-lg border p-3 text-left text-sm transition-all ${
                cfg.mode === "group"
                  ? "border-emerald-500 bg-emerald-600/10"
                  : "border-white/10 hover:border-white/20"
              }`}
            >
              <p className="font-medium">Só grupo</p>
              <p className="text-xs text-slate-400 mt-1">Responde só no grupo dedicado</p>
            </button>
            <button
              type="button"
              onClick={() => setCfg({ ...cfg, mode: "all" })}
              title="O agente responde em conversas privadas E em grupos"
              className={`rounded-lg border p-3 text-left text-sm transition-all ${
                cfg.mode === "all"
                  ? "border-emerald-500 bg-emerald-600/10"
                  : "border-white/10 hover:border-white/20"
              }`}
            >
              <p className="font-medium">Ambos</p>
              <p className="text-xs text-slate-400 mt-1">Responde no PV e em grupos</p>
            </button>
          </div>
        </Field>

        {/* Group creation */}
        {cfg.mode === "group" && (
          <div className="space-y-3 rounded-lg border border-white/10 p-3">
            {cfg.group_jid ? (
              <div className="text-sm">
                <p className="text-slate-300">Grupo ativo: <span className="font-medium text-emerald-400">{cfg.group_name}</span></p>
                <p className="text-xs text-slate-500 mt-0.5">{cfg.group_jid}</p>
              </div>
            ) : (
              <>
                <Field label="Nome do grupo" hint="Nome que aparece no WhatsApp quando o grupo for criado. Pode mudar depois.">
                <Input
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  placeholder="Hermes Call - Assistente IA"
                  className="border-white/10 bg-white/5 text-sm"
                />
              </Field>
                <Button size="sm" onClick={handleCreateGroup} disabled={creatingGroup}>
                  {creatingGroup ? "Criando..." : "Criar grupo"}
                </Button>
              </>
            )}
          </div>
        )}

        <Field
          label="Mensagem de boas-vindas"
          hint="Primeira mensagem que o agente envia quando alguém inicia uma conversa. Deixe vazio para não enviar saudação."
        >
          <Textarea
            value={cfg.welcome_msg}
            onChange={(e) => setCfg({ ...cfg, welcome_msg: e.target.value })}
            placeholder="👋 Olá! Sou o Hermes, seu assistente IA. Mande uma mensagem e eu respondo!"
            className="border-white/10 bg-white/5 text-sm min-h-[60px]"
          />
        </Field>

        <ToggleField
          label="Notificar no Telegram"
          hint="Receba um resumo no Telegram sempre que o agente IA responder uma mensagem no WhatsApp. Útil pra monitorar sem abrir o WhatsApp."
          checked={cfg.notify_telegram}
          onChange={(v) => setCfg({ ...cfg, notify_telegram: v })}
        />
      </Card>

      {/* OpenClaw */}
      <Card className="p-4 space-y-4">
        <ToggleField
          label="OpenClaw externo"
          hint="Conecta um agente IA externo (como OpenClaw) em vez de usar o agente local do Hermes. Útil se já tem um agente configurado em outro lugar."
          checked={cfg.openclaw.enabled}
          onChange={(v) => setCfg({ ...cfg, openclaw: { ...cfg.openclaw, enabled: v } })}
        />
        {cfg.openclaw.enabled && (
          <div className="space-y-3 ml-1">
            <Field label="URL do OpenClaw" hint="Endereço do servidor do OpenClaw. Exemplo: https://api.seu-claw.com">
              <Input
                value={cfg.openclaw.url}
                onChange={(e) => setCfg({ ...cfg, openclaw: { ...cfg.openclaw, url: e.target.value } })}
                placeholder="https://seu-openclaw.com"
                className="border-white/10 bg-white/5 text-sm"
              />
            </Field>
            <Field label="API Key do OpenClaw" hint="Chave de API do seu OpenClaw. Pode ser obtida no painel do OpenClaw.">
              <Input
                value={cfg.openclaw.api_key}
                onChange={(e) => setCfg({ ...cfg, openclaw: { ...cfg.openclaw, api_key: e.target.value } })}
                placeholder="sk-..."
                type="password"
                className="border-white/10 bg-white/5 text-sm"
              />
            </Field>
          </div>
        )}
      </Card>

      <Button onClick={save} disabled={saving} className="w-full">
        {saving ? "Salvando..." : "Salvar configurações do agente"}
      </Button>
    </div>
  );
}
