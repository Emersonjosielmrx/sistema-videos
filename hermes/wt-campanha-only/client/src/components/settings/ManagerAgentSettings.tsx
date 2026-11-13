import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BrainCircuit, MessageSquare, Users, Send, CheckCircle2, Zap, MonitorSmartphone, Bot, Cpu, Network, User } from "lucide-react";
import { apiPut } from "@/lib/api";
import { fetchAIModels, testAIKey } from "@/services/aimodels";
import { updateAgentChat, createAgentGroup, agentChatSemRoteamento } from "@/services/settings";
import { CredentialSelect } from "@/components/settings/CredentialSelect";
import { logError } from "@/lib/log";
import { Field, ToggleField } from "@/components/ui/field";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import type { AgentChatSettings, AgentConfig } from "@/types/settings";

const providers = [
  { value: "anthropic", label: "Anthropic (Claude)" },
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Google Gemini" },
  { value: "groq", label: "Groq" },
  { value: "custom", label: "Custom / Proxy (compatível OpenAI)" },
];

// ---------- Manager Agent Config (embedded) ----------

function ManagerAgentConfig({ initial, onSaved }: {
  initial: AgentConfig;
  onSaved: () => void;
}) {
  const [cfg, setCfg] = useState<AgentConfig>(initial);
  const [saving, setSaving] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testing, setTesting] = useState(false);
  const isCustom = cfg.provider === "custom";

  const loadModels = async () => {
    if ((!cfg.api_key && !cfg.credential_id) || !cfg.provider) {
      toast.error("Selecione uma credencial ou preencha provider e API Key primeiro");
      return;
    }
    setLoadingModels(true);
    try {
      const list = await fetchAIModels(cfg.provider, cfg.api_key, cfg.base_url, cfg.credential_id);
      setModels(list);
      toast.success(`${list.length} modelos encontrados`);
    } catch (e) {
      toast.error("Erro ao buscar modelos", { description: (e as Error).message });
    } finally {
      setLoadingModels(false);
    }
  };

  const testKey = async () => {
    if (!cfg.api_key || !cfg.provider) {
      toast.error("Preencha provider e API Key primeiro");
      return;
    }
    setTesting(true);
    try {
      const r = await testAIKey(cfg.provider, cfg.api_key, cfg.base_url, cfg.model);
      if (r.ok) toast.success("Chave OK! A IA respondeu.");
      else toast.error("Chave não funcionou", { description: r.error });
    } catch (e) {
      toast.error("Erro ao testar", { description: (e as Error).message });
    } finally {
      setTesting(false);
    }
  };

  const save = async () => {
    setSaving(true);
    try {
      // Não envia os campos dos "superpoderes" (o servidor não os conhece e descartava calado).
      const { askManagerEnabled: _a, shadowingEnabled: _s, copilotEnabled: _c, promisesEnabled: _p, ...body } =
        cfg as AgentConfig & Record<string, unknown>;
      await apiPut("/api/settings/manager", body);
      toast.success("Agente Gerenciador salvo");
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
       {/* Health & Brain Engine */}
       <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
          <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
             <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-primary" />
                <h3 className="font-bold text-sm">Motor Cognitivo (LLM)</h3>
             </div>
             <Badge variant="outline" className={cn("gap-1.5 px-2", cfg.enabled ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-muted text-muted-foreground")}>
                <div className={cn("w-2 h-2 rounded-full", cfg.enabled ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground")}></div>
                {cfg.enabled ? "Cérebro Ativo" : "Desligado"}
             </Badge>
          </div>
          
          <div className="p-6 space-y-6">
             <div className="flex items-center justify-between p-4 bg-background/50 rounded-xl border border-border/50">
                <div>
                   <p className="font-semibold">Independência Cognitiva</p>
                   <p className="text-xs text-muted-foreground mt-0.5">Se ativo, usa um provedor/modelo específico apenas para o Gerenciador (não herda do padrão).</p>
                </div>
                <ToggleField label="" checked={cfg.enabled} onChange={(v) => setCfg({ ...cfg, enabled: v })} />
             </div>

             {cfg.enabled && (
               <div className="space-y-6 animate-in fade-in zoom-in-95">
                 <Field label="Credencial de IA" hint="Escolha uma credencial já cadastrada. A chave é resolvida no servidor.">
                   <CredentialSelect
                     type="llm"
                     value={cfg.credential_id ?? ""}
                     onChange={(id, cred) => {
                       setCfg({ ...cfg, credential_id: id, ...(id ? { api_key: "", provider: cred?.provider || cfg.provider, base_url: cred?.base_url || "" } : {}) });
                       setModels([]);
                       if (id && cred) {
                         fetchAIModels(cred.provider, "", cred.base_url, id).then(setModels).catch(logError("ManagerAgent/models"));
                       }
                     }}
                   />
                 </Field>
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                   <Field label="Provedor de IA (Provider)">
                     <select
                       className="w-full bg-background border border-border/50 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-primary/50"
                       value={cfg.provider}
                       onChange={(e) => setCfg({ ...cfg, provider: e.target.value })}
                     >
                       <option value="">Herdar da IA Padrão</option>
                       {providers.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                     </select>
                   </Field>
                   <Field label="Modelo de Linguagem">
                     <div className="flex gap-2">
                       {models.length > 0 && !isCustom ? (
                         <select className="w-full bg-background border border-border/50 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-primary/50" value={cfg.model} onChange={(e) => setCfg({ ...cfg, model: e.target.value })}>
                           <option value="">Selecione...</option>
                           {models.map((m) => <option key={m} value={m}>{m}</option>)}
                         </select>
                       ) : (
                         <Input className="flex-1 bg-background" name="mgr-model" autoComplete="off" value={cfg.model} onChange={(e) => setCfg({ ...cfg, model: e.target.value })} placeholder="claude-3-5-sonnet-20240620" />
                       )}
                       {!isCustom && cfg.provider && (
                         <Button type="button" variant="secondary" onClick={loadModels} disabled={loadingModels} className="shrink-0">
                           {loadingModels ? "Buscando..." : "Listar"}
                         </Button>
                       )}
                     </div>
                   </Field>
                 </div>

                 {!cfg.credential_id && (
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                     <Field label="Chave de API (Secret Key)">
                       <Input type="password" name="mgr-apikey" autoComplete="new-password" value={cfg.api_key} onChange={(e) => setCfg({ ...cfg, api_key: e.target.value })} placeholder="sk-..." className="bg-background" />
                     </Field>
                     <Field label="Base URL (Proxy/Custom)">
                       <Input value={cfg.base_url} onChange={(e) => setCfg({ ...cfg, base_url: e.target.value })} placeholder="https://api.anthropic.com" className="bg-background" />
                     </Field>
                   </div>
                 )}

                 <div className="pt-4 border-t border-border/50 flex items-center justify-between">
                   <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Zap className="w-4 h-4 text-amber-500" /> Teste a conexão antes de salvar.
                   </div>
                   <div className="flex items-center gap-2">
                      <Button type="button" variant="outline" onClick={testKey} disabled={testing} className="gap-2">
                        {testing ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-foreground"></span> : <CheckCircle2 className="w-4 h-4" />}
                        {testing ? "Diagnosticando..." : "Diagnóstico de Rede"}
                      </Button>
                      <Button onClick={save} disabled={saving} className="gap-2 shadow-glow">
                        <Zap className="w-4 h-4"/> Salvar Motor
                      </Button>
                   </div>
                 </div>
               </div>
             )}
          </div>
       </Card>

       {/* Persona Builder */}
       <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
          <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
             <div className="flex items-center gap-2">
                <BrainCircuit className="w-5 h-5 text-primary" />
                <h3 className="font-bold text-sm">Personalidade & Diretrizes (System Prompt)</h3>
             </div>
          </div>
          <div className="p-6 space-y-6">
             <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-1 space-y-4">
                   <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 flex flex-col items-center text-center gap-3">
                      <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center border-2 border-primary/50 text-primary">
                         <Bot className="w-8 h-8" />
                      </div>
                      <div>
                         <h4 className="font-bold text-sm">Avatar IA</h4>
                         <p className="text-xs text-muted-foreground mt-1">Este é o cérebro que opera o sistema e fala com os clientes.</p>
                      </div>
                   </div>

                   <p className="text-xs text-muted-foreground">
                     O tom de voz do agente é definido pelo Prompt de Sistema ao lado — descreva ali
                     como ele deve falar (formal, descontraído, focado em vendas, etc.).
                   </p>
                </div>
                <div className="md:col-span-2">
                   <Field label="Prompt de Sistema Principal (Master Prompt)">
                      <Textarea
                        value={cfg.system_message}
                        onChange={(e) => setCfg({ ...cfg, system_message: e.target.value })}
                        rows={10}
                        className="bg-[#0D1117] text-[#C9D1D9] border-border/50 font-mono text-sm resize-none focus:ring-primary/50"
                        placeholder="Você é o Hermes, assistente que opera o WhatsApp a pedido do DONO da conta..."
                      />
                   </Field>
                   <p className="text-xs text-muted-foreground mt-2">
                     <strong>Atenção:</strong> Este prompt é do <strong>Agente Gestor</strong> — a IA de <strong>supervisão</strong> que conversa com <strong>você</strong> (dono do negócio) via Telegram/WhatsApp para coordenar, monitorar e ajudar a gerenciar seus bots. Não confunda com a "IA Padrão" (Configurações Base IA), que define como seus bots conversam com os clientes.
                   </p>
                   <p className="text-xs text-muted-foreground mt-1">Dica: Use markdown para estruturar as regras. O agente terá acesso nativo a ferramentas como ler agenda e fazer tags.</p>
                </div>
             </div>
             {cfg.enabled && (
                <div className="flex justify-end pt-2">
                   <Button onClick={save} disabled={saving} className="shadow-glow">Salvar Diretrizes</Button>
                </div>
             )}
          </div>
       </Card>

    </div>
  );
}

// ---------- Main unified component ----------

export function ManagerAgentSettings({
  initialChat,
  initialManager,
  onSaved,
}: {
  initialChat: AgentChatSettings;
  initialManager: AgentConfig;
  onSaved: () => void;
}) {
  const [chatCfg, setChatCfg] = useState<AgentChatSettings>(initialChat);
  const [savingChat, setSavingChat] = useState(false);
  const [creatingGroup, setCreatingGroup] = useState(false);
  const [groupName, setGroupName] = useState(chatCfg.group_name || "Hermes Call - Assistente IA");

  const saveChat = async () => {
    setSavingChat(true);
    try {
      await updateAgentChat(agentChatSemRoteamento(chatCfg));
      toast.success("Configurações do canal salvas");
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingChat(false);
    }
  };

  const handleCreateGroup = async () => {
    setCreatingGroup(true);
    try {
      const result = await createAgentGroup(groupName, chatCfg.welcome_msg || "Olá! Sou o Hermes, seu assistente IA. Mande uma mensagem e eu respondo!");
      setChatCfg({ ...chatCfg, group_jid: result.group_jid, group_name: result.name });
      toast.success(`Grupo "${result.name}" criado!`);
      onSaved();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCreatingGroup(false);
    }
  };

  return (
    <div className="space-y-8 mt-4 pb-20">
      
      <div className="flex flex-col md:flex-row gap-6">
        
        {/* Left Col: Channels & Skills */}
        <div className="flex-1 space-y-6">
           
           {/* Omnichannel Matrix */}
           <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
             <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
                <div className="flex items-center gap-2">
                   <MessageSquare className="w-5 h-5 text-emerald-500" />
                   <h3 className="font-bold text-sm">Matriz de Comunicação (WhatsApp)</h3>
                </div>
                <Switch checked={chatCfg.enabled} onCheckedChange={(v) => setChatCfg({ ...chatCfg, enabled: v })} />
             </div>
             
             <div className={cn("p-6 space-y-6 transition-opacity", !chatCfg.enabled && "opacity-50 pointer-events-none")}>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div 
                    onClick={() => setChatCfg({ ...chatCfg, mode: "private" })}
                    className={cn(
                      "p-4 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-3",
                      chatCfg.mode === "private" ? "border-emerald-500 bg-emerald-500/10 shadow-glow" : "border-border/50 hover:border-emerald-500/50 bg-background/50"
                    )}
                  >
                     <div className={cn("w-12 h-12 rounded-full flex items-center justify-center", chatCfg.mode === "private" ? "bg-emerald-500 text-white" : "bg-muted text-muted-foreground")}>
                        <User className="w-6 h-6" />
                     </div>
                     <div>
                        <h4 className="font-bold">WhatsApp Privado</h4>
                        <p className="text-xs text-muted-foreground mt-1">O Agente intercepta e responde DMs 1 a 1 automaticamente.</p>
                     </div>
                  </div>

                  <div 
                    onClick={() => setChatCfg({ ...chatCfg, mode: "group" })}
                    className={cn(
                      "p-4 rounded-xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-3",
                      chatCfg.mode === "group" ? "border-emerald-500 bg-emerald-500/10 shadow-glow" : "border-border/50 hover:border-emerald-500/50 bg-background/50"
                    )}
                  >
                     <div className={cn("w-12 h-12 rounded-full flex items-center justify-center", chatCfg.mode === "group" ? "bg-emerald-500 text-white" : "bg-muted text-muted-foreground")}>
                        <Users className="w-6 h-6" />
                     </div>
                     <div>
                        <h4 className="font-bold">Grupo Corporativo</h4>
                        <p className="text-xs text-muted-foreground mt-1">O Agente atua apenas dentro de um grupo específico criado para ele.</p>
                     </div>
                  </div>
                </div>

                {chatCfg.mode === "group" && (
                  <div className="p-4 bg-background/50 border border-border/50 rounded-xl space-y-3 animate-in fade-in">
                    {chatCfg.group_jid ? (
                      <div className="flex items-center justify-between">
                         <div>
                            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Grupo Vinculado</p>
                            <p className="font-bold text-emerald-500 flex items-center gap-2"><CheckCircle2 className="w-4 h-4"/> {chatCfg.group_name}</p>
                            <p className="text-[10px] text-muted-foreground font-mono mt-0.5">{chatCfg.group_jid}</p>
                         </div>
                      </div>
                    ) : (
                      <>
                        <Field label="Nome do Novo Grupo">
                          <Input value={groupName} onChange={(e) => setGroupName(e.target.value)} placeholder="Agente IA - Suporte" className="bg-background" />
                        </Field>
                        <Button size="sm" onClick={handleCreateGroup} disabled={creatingGroup} className="w-full gap-2">
                          <Users className="w-4 h-4" /> {creatingGroup ? "Criando Grupo no WhatsApp..." : "Criar Grupo e Vincular"}
                        </Button>
                      </>
                    )}

                  </div>
                )}

                <Field label="Mensagem de Boas-vindas Automática">
                   <Textarea
                     value={chatCfg.welcome_msg}
                     onChange={(e) => setChatCfg({ ...chatCfg, welcome_msg: e.target.value })}
                     placeholder="Ex: Olá! Sou o assistente de IA. Como posso ajudar você hoje?"
                     className="bg-background resize-none min-h-[80px]"
                   />
                </Field>

                <div className="space-y-2">
                   <div className="flex items-center justify-between p-3 bg-background/50 border border-border/50 rounded-lg">
                      <div className="flex items-center gap-3">
                         <Send className="w-4 h-4 text-sky-500" />
                         <div>
                            <p className="text-sm font-semibold">Notificar ações no Telegram</p>
                            <p className="text-xs text-muted-foreground">Receba relatórios curtos no TG sempre que a IA resolver um ticket.</p>
                         </div>
                      </div>
                      <Switch checked={chatCfg.notify_telegram} onCheckedChange={(v) => setChatCfg({ ...chatCfg, notify_telegram: v })} />
                   </div>
                   <div className="flex items-center justify-between p-3 bg-background/50 border border-border/50 rounded-lg">
                      <div className="flex items-center gap-3">
                         <MonitorSmartphone className="w-4 h-4 text-purple-500" />
                         <div>
                            <p className="text-sm font-semibold">Self-Chat (Falar consigo mesmo)</p>
                            <p className="text-xs text-muted-foreground">O agente responde mensagens que você manda pro seu próprio número.</p>
                         </div>
                      </div>
                      <Switch checked={chatCfg.owner_message_enabled} onCheckedChange={(v) => setChatCfg({ ...chatCfg, owner_message_enabled: v })} />
                   </div>
                </div>

                <Button onClick={saveChat} disabled={savingChat} className="w-full shadow-glow">
                  {savingChat ? "Salvando Matriz..." : "Salvar Configurações de Comunicação"}
                </Button>
             </div>
           </Card>

           {/* Tool Matrix — os toggles de ferramenta e o seletor de autonomia não eram
               salvos em lugar nenhum. Substituído por um aviso honesto. As ferramentas
               que a IA realmente usa (agenda, tags, catálogo) são nativas e passam pelo
               gate de administrador para ações destrutivas. */}
           <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
             <div className="p-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-500" />
                <h3 className="font-bold text-sm">Ferramentas do Agente</h3>
             </div>
             <div className="p-6 space-y-3">
                <p className="text-xs text-muted-foreground">
                  O agente já usa ferramentas nativas (ler/gerar agenda, aplicar tags, consultar o
                  catálogo, enviar mensagens/áudio conforme habilitado em Configurações da IA). A
                  ativação/desativação granular de cada ferramenta e o nível de autonomia por perfil
                  ainda estão em desenvolvimento.
                </p>
             </div>
           </Card>
        </div>

        {/* Right Col: Brain Config */}
        <div className="flex-1 space-y-6">
           <ManagerAgentConfig initial={initialManager} onSaved={onSaved} />
           
           {/* OpenClaw Ext / Roteador Multi-Agentes */}
           <Card className="bg-gradient-to-br from-[#0D1117] to-background border-border/50 shadow-soft overflow-hidden">
              <div className="p-4 border-b border-border/50 flex items-center justify-between">
                 <div className="flex items-center gap-2">
                    <Network className="w-5 h-5 text-sky-500" />
                    <h3 className="font-bold text-sm text-foreground">Orquestração Multi-Agentes (Delegador)</h3>
                 </div>
                 <Switch checked={chatCfg.openclaw.enabled} onCheckedChange={(v) => setChatCfg({ ...chatCfg, openclaw: { ...chatCfg.openclaw, enabled: v } })} />
              </div>
              {chatCfg.openclaw.enabled && (
                <div className="p-6 space-y-4 animate-in fade-in zoom-in-95">
                   <p className="text-xs text-muted-foreground">
                     O Gestor atua como <strong>Agente Mestre</strong> (Roteador). Ele intercepta todas as mensagens, lê a intenção, e repassa o atendimento para Especialistas, evitando que ele mesmo responda tudo e fique confuso.
                   </p>
                   
                   <div className="space-y-4 pt-2">
                     <Field label="Endpoint OpenClaw Swarm">
                       <Input
                         value={chatCfg.openclaw.url}
                         onChange={(e) => setChatCfg({ ...chatCfg, openclaw: { ...chatCfg.openclaw, url: e.target.value } })}
                         placeholder="https://sua-api.com/v1/openclaw/swarm"
                         className="bg-[#0D1117] border-border/50 focus:border-sky-500/50"
                       />
                     </Field>
                     <Field label="Chave de Autenticação Swarm">
                       <Input
                         type="password"
                         value={chatCfg.openclaw.api_key}
                         onChange={(e) => setChatCfg({ ...chatCfg, openclaw: { ...chatCfg.openclaw, api_key: e.target.value } })}
                         placeholder="sk-openclaw-..."
                         className="bg-[#0D1117] border-border/50 focus:border-sky-500/50"
                       />
                     </Field>
                   </div>
                   
                   <div className={cn("p-3 border rounded-lg", chatCfg.openclaw.url ? "bg-sky-500/10 border-sky-500/20" : "bg-muted/30 border-dashed border-border/50")}>
                      <p className="text-[10px] font-medium font-mono uppercase text-muted-foreground">Status de Delegação</p>
                      <p className="text-xs font-semibold text-foreground mt-1">
                        {chatCfg.openclaw.url
                          ? "Endpoint configurado. A delegação para o Swarm será usada nas próximas mensagens; se falhar, o agente local responde como fallback."
                          : "Informe o endpoint do Swarm acima para ativar a delegação. Sem endpoint, o agente local responde tudo."}
                      </p>
                   </div>

                   <Button onClick={saveChat} disabled={savingChat} className="w-full shadow-glow" variant="default">
                     Atualizar Conexão do Enxame
                   </Button>
                </div>
              )}
           </Card>
        </div>
      </div>
    </div>
  );
}
