import { useEffect, useState } from "react";
import { Bot, Link, KeyRound, CreditCard, ShieldCheck, User, ScrollText, Code2, Sparkles, FolderKanban, Plug, Network, Activity, SlidersHorizontal } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { TelegramSettings } from "@/components/settings/TelegramSettings";
import { AISettings } from "@/components/settings/AISettings";
import { CallAISettings } from "@/components/settings/CallAISettings";
import { ManagerAgentSettings } from "@/components/settings/ManagerAgentSettings";
import { EasySettingsWizard } from "@/components/settings/EasySettingsWizard";
import { HumanAssistTab } from "@/components/settings/HumanAssistTab";
import { HideableTab } from "@/components/ui/HideableTab";
import { VoiceSettings } from "@/components/settings/VoiceSettings";
import { WebhookSettings } from "@/components/settings/WebhookSettings";
import { APIKeysSettings } from "@/components/settings/APIKeysSettings";
import { AICredentialsSettings } from "@/components/settings/AICredentialsSettings";
import { N8nSettings } from "@/components/settings/N8nSettings";
import { RedeVPSSettings } from "@/components/settings/RedeVPSSettings";
import { SaudeLigacoesSettings } from "@/components/settings/SaudeLigacoesSettings";
import { ConfiguracaoServidorSettings } from "@/components/settings/ConfiguracaoServidorSettings";
import { WorkspaceSettings } from "@/components/settings/WorkspaceSettings";
import { AppearanceSettings } from "@/components/settings/AppearanceSettings";
import { SecurityPage } from "@/pages/SecurityPage";
import { Palette } from "lucide-react";
import { LogsPage } from "@/pages/LogsPage";
import { SubscriptionTab } from "@/components/catalog/SubscriptionTab";
import { ProfilePage } from "@/pages/ProfilePage";
import { getSettings } from "@/services/settings";
import { t } from "@/lib/i18n";
import { isPlatformAdmin } from "@/lib/auth";
import { logError } from "@/lib/log";
import type { AllSettings } from "@/types/settings";
import { useNavigation, toggleHiddenSettingsTab, consumeSettingsTab } from "@/stores/navigation";
import { X, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

function SettingsTab({ value, icon: Icon, label }: { value: string, icon: React.ElementType, label: string }) {
  const isEditMode = useNavigation((s) => s.isEditMode);
  const hiddenTabs = useNavigation((s) => s.hiddenSettingsTabs);
  const isHidden = hiddenTabs.includes(value);

  if (isHidden && !isEditMode) return null;

  return (
    <div className={cn("relative", isEditMode && "animate-wiggle")}>
      <TabsTrigger 
        value={value} 
        className={cn(
          "w-full justify-start px-4 py-3 h-auto rounded-xl text-sm font-medium transition-colors data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:border data-[state=active]:border-primary/20 data-[state=active]:shadow-soft hover:bg-muted/50 hover:text-foreground",
          isHidden ? "opacity-50 grayscale text-muted-foreground" : "text-muted-foreground"
        )}
      >
        <Icon className={cn("h-5 w-5 mr-3", isEditMode && "origin-center pointer-events-none")} /> {label}
      </TabsTrigger>
      {isEditMode && (
        <button
          onClick={(e) => { e.stopPropagation(); toggleHiddenSettingsTab(value); }}
          className="absolute -top-1.5 -left-1.5 z-10 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-destructive-foreground shadow-md hover:scale-110 transition-transform cursor-pointer"
        >
          {isHidden ? <Plus className="h-2.5 w-2.5" /> : <X className="h-2.5 w-2.5" />}
        </button>
      )}
    </div>
  );
}

export function SettingsPage() {
  const [settings, setSettings] = useState<AllSettings | null>(null);
  const [loading, setLoading] = useState(true);
  // Deep-link: se alguém pediu pra abrir numa aba específica (ex.: atalho da etapa de
  // áudio do wizard → aba "voice"), começa nela. Consome e limpa o flag do nav store.
  const [activeTab, setActiveTab] = useState(() => consumeSettingsTab() || "config_facil");

  const getTabTitle = () => {
    switch(activeTab) {
      case "config_facil": return "Configura Fácil";
      case "brain": return "Cérebro / IA";
      case "manager": return "Agente Gestor";
      case "webhook": return "Webhook";
      case "credentials": return "Credenciais IA";
      case "finance": return "Faturamento";
      case "security": return "Segurança";
      case "profile": return "Meu Perfil";
      case "workspaces": return "Workspaces";
      case "n8n": return "n8n (Tenant)";
      case "logs": return "Logs";
      case "api": return "API do Sistema";
      case "appearance": return "Cores e Aparência";
      default: return "Configurações Avançadas";
    }
  };

  const getTabDesc = () => {
    switch(activeTab) {
      case "config_facil": return "Configuração guiada passo a passo para iniciar sua plataforma.";
      case "brain": return "Modelos de IA padrão, transcrição e provedores de voz.";
      case "manager": return "Configurações do assistente mestre de sistema.";
      case "webhook": return "Integrações via webhooks.";
      case "credentials": return "Chaves de API (OpenAI, Anthropic, ElevenLabs, etc).";
      case "finance": return "Custos de LLM e assinatura.";
      case "security": return "Credenciais e segurança do acesso.";
      case "profile": return "Informações pessoais e avatar.";
      case "workspaces": return "Projetos e configurações de multi-tenancy.";
      case "n8n": return "Chaves e webhooks do n8n por tenant.";
      case "logs": return "Auditoria e erros de sistema.";
      case "api": return "Acesso programático à API.";
      case "appearance": return "Personalize o tema e cores da plataforma.";
      default: return "Gerencie credenciais, webhooks e parâmetros da sua IA.";
    }
  };

  const reload = () => {
    getSettings()
      .then(setSettings)
      .catch(logError("getSettings"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { reload(); }, []);

  if (loading) {
    return <div className="p-6 text-muted-foreground">{t("loading")}</div>;
  }

  const currentSettings = settings || ({} as AllSettings);

  const safeSettings: AllSettings = {
    telegram: { ...(currentSettings.telegram || {}), chat_ids: currentSettings.telegram?.chat_ids ?? [] },
    ai: { ...(currentSettings.ai || {}) },
    voice: {
      ...(currentSettings.voice || {}),
      callback_missed: currentSettings.voice?.callback_missed ?? true,
      filler_enabled: currentSettings.voice?.filler_enabled ?? false,
      filler_words: currentSettings.voice?.filler_words ?? [],
    },
    webhook: { ...(currentSettings.webhook || {}), events: currentSettings.webhook?.events ?? [] },
    agent_chat: {
      enabled: currentSettings.agent_chat?.enabled ?? false,
      mode: currentSettings.agent_chat?.mode || "private",
      group_jid: currentSettings.agent_chat?.group_jid || "",
      group_name: currentSettings.agent_chat?.group_name || "",
      welcome_msg: currentSettings.agent_chat?.welcome_msg || "",
      notify_telegram: currentSettings.agent_chat?.notify_telegram ?? false,
      openclaw: {
        enabled: currentSettings.agent_chat?.openclaw?.enabled ?? false,
        url: currentSettings.agent_chat?.openclaw?.url || "",
        api_key: currentSettings.agent_chat?.openclaw?.api_key || "",
      },
      owner_message_enabled: currentSettings.agent_chat?.owner_message_enabled ?? false,
      // Sem este, salvar a tela do Gestor desligava o "só ativo" (04/10).
      outbound_only: currentSettings.agent_chat?.outbound_only ?? false,
      // default_profile_id/voice_profile_id (roteamento) NÃO entram: são da tela de agentes, e a
      // foto daqui desfazia a troca feita em outra aba (revisão do PC, 04/10).
    },
    call_ai: currentSettings.call_ai || {
      enabled: false,
      provider: "openai",
      model: "gpt-4",
      api_key: "",
      api_base_url: "",
      system_message: "",
    },
    manager: currentSettings.manager || {
      enabled: false,
      provider: "openai",
      model: "gpt-4",
      api_key: "",
      base_url: "",
      system_message: "",
    }
  };

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto p-4 sm:p-6 pb-10">
      {/* Cabeçalho Compacto Configurações */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-500/10 via-background to-background border border-slate-500/20 p-4 shadow-glow flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
          <ShieldCheck className="w-16 h-16 text-slate-500" />
        </div>
        <div className="relative z-10 flex items-center gap-3">
          <div className="hidden sm:flex items-center justify-center p-2 bg-slate-500/10 rounded-xl border border-slate-500/20 shadow-glow shrink-0">
            <img src="/inovareLogo.png" alt="Inovare Logo" className="w-8 h-8 object-contain drop-shadow-[0_0_8px_rgba(16,185,129,0.3)] rounded-full" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-slate-500 to-slate-400 drop-shadow-sm">
                {getTabTitle()}
              </h2>
              <Badge className="bg-slate-500/10 text-slate-500 border-slate-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Hermes Call Inovare
              </Badge>
              <Badge className="bg-slate-500/10 text-slate-500 border-slate-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Controle Total
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {getTabDesc()}
            </p>
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-col md:flex-row gap-8 w-full">
        {/* Sidebar Vertical Tabs */}
        <div className="w-full md:w-64 shrink-0 space-y-6">
          <TabsList className="flex flex-col h-auto bg-transparent items-stretch p-0 space-y-1">
            <div className="pb-2">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-4">
                Início Rápido
              </div>
            </div>
            <SettingsTab value="config_facil" icon={Sparkles} label="Configura Fácil" />
            
            <div className="pt-4 pb-2">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-4">
                Plataforma & IA
              </div>
            </div>
            <SettingsTab value="brain" icon={Bot} label="Configurações Base IA" />
            <SettingsTab value="manager" icon={User} label="Funcionário Gestor" />
            <SettingsTab value="human_assist" icon={User} label="Ajuda Humana" />
            <SettingsTab value="webhook" icon={Link} label="Webhook" />
            <SettingsTab value="credentials" icon={KeyRound} label="Credenciais IA" />
            <SettingsTab value="finance" icon={CreditCard} label="Faturamento" />
            <SettingsTab value="security" icon={ShieldCheck} label="Segurança" />
            
            <div className="pt-4 pb-2">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-4">
                Administração
              </div>
            </div>
            
            <SettingsTab value="appearance" icon={Palette} label="Aparência" />
            <SettingsTab value="workspaces" icon={FolderKanban} label="Workspaces" />
            <SettingsTab value="n8n" icon={Plug} label="n8n (Integração)" />
            
            <div className="pt-4 pb-2">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-4">
                Sistema
              </div>
            </div>
            
            <SettingsTab value="profile" icon={User} label="Meu Perfil" />
            {/* Logs = servidor inteiro: só para o admin da plataforma (o servidor responde 403 aos demais). */}
            {isPlatformAdmin() && <SettingsTab value="logs" icon={ScrollText} label="Logs" />}
            {isPlatformAdmin() && <SettingsTab value="rede" icon={Network} label="Rede / VPS" />}
            {isPlatformAdmin() && <SettingsTab value="saude" icon={Activity} label="Saúde das ligações" />}
            {isPlatformAdmin() && <SettingsTab value="servidor" icon={SlidersHorizontal} label="Configuração do servidor" />}
            <SettingsTab value="api" icon={Code2} label="API do Sistema" />
          </TabsList>
        </div>

        {/* Tab Content */}
        <div className="flex-1 max-w-5xl">
          
          <TabsContent value="config_facil" className="m-0 focus-visible:outline-none">
            <EasySettingsWizard />
          </TabsContent>

          <TabsContent value="human_assist" className="m-0 focus-visible:outline-none">
            <HumanAssistTab />
          </TabsContent>

          <TabsContent value="brain" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">Cérebro / IA</h2>
              <p className="text-muted-foreground text-sm mt-1">Modelos de IA padrão, transcrição e provedores de voz da plataforma.</p>
            </div>
            <Tabs defaultValue="ai" className="w-full">
              <TabsList className="bg-muted/50 p-1 rounded-xl flex flex-wrap w-full h-auto justify-start gap-1 mb-2">
                <HideableTab value="ai" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 flex-1 sm:flex-none">IA Padrão</HideableTab>
                <HideableTab value="call_ai" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 flex-1 sm:flex-none">IA da Ligação</HideableTab>
                <HideableTab value="voice" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 flex-1 sm:flex-none">Voz & Transcrição</HideableTab>
              </TabsList>
              <TabsContent value="ai">
                <AISettings initial={safeSettings.ai} onSaved={reload} />
              </TabsContent>
              <TabsContent value="call_ai">
                <CallAISettings initial={safeSettings.call_ai as any} onSaved={reload} />
              </TabsContent>
              <TabsContent value="voice">
                <VoiceSettings initial={safeSettings.voice} onSaved={reload} />
              </TabsContent>
            </Tabs>
          </TabsContent>

          <TabsContent value="manager" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">Agente Gestor</h2>
              <p className="text-muted-foreground text-sm mt-1">Configure o canal principal de comando, como o Telegram.</p>
            </div>
            <Tabs defaultValue="agent" className="w-full">
              <TabsList className="bg-muted/50 p-1 rounded-xl flex flex-wrap w-full h-auto justify-start gap-1 mb-2">
                <HideableTab value="agent" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 flex-1 sm:flex-none">Agente & Canais</HideableTab>
                <HideableTab value="telegram" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2 flex-1 sm:flex-none">✈️ Telegram</HideableTab>
              </TabsList>
              <TabsContent value="agent">
                <ManagerAgentSettings initialChat={safeSettings.agent_chat} initialManager={safeSettings.manager!} onSaved={reload} />
              </TabsContent>
              <TabsContent value="telegram">
                <TelegramSettings initial={safeSettings.telegram} onSaved={reload} />
              </TabsContent>
            </Tabs>
          </TabsContent>

          <TabsContent value="webhook" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">Webhook Global</h2>
              <p className="text-muted-foreground text-sm mt-1">Envie eventos e conversas em tempo real para o n8n ou outro sistema.</p>
            </div>
            <WebhookSettings initial={safeSettings.webhook} onSaved={reload} />
          </TabsContent>

          <TabsContent value="credentials" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-emerald-400 drop-shadow-sm w-fit">Cadastro de Credenciais (Motores IA)</h2>
              <p className="text-muted-foreground text-sm mt-1">Gerencie os tokens e chaves privadas de fornecedores externos (OpenAI, Anthropic, Groq, ElevenLabs).</p>
            </div>
            
            <AICredentialsSettings />
          </TabsContent>

          <TabsContent value="finance" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">Faturamento</h2>
              <p className="text-muted-foreground text-sm mt-1">Gerencie sua assinatura, limites e métodos de pagamento.</p>
            </div>
            <SubscriptionTab />
          </TabsContent>

          <TabsContent value="security" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <SecurityPage />
          </TabsContent>

          <TabsContent value="profile" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* The ProfilePage already has its own nested sidebar, which is fine, 
                it will act as a sub-menu similar to how Cérebro/IA has sub-tabs. */}
            <ProfilePage inSettings />
          </TabsContent>

          <TabsContent value="workspaces" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <WorkspaceSettings />
          </TabsContent>

          <TabsContent value="n8n" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <N8nSettings />
          </TabsContent>

          <TabsContent value="logs" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <LogsPage />
          </TabsContent>

          <TabsContent value="rede" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {isPlatformAdmin() && <RedeVPSSettings />}
          </TabsContent>

          <TabsContent value="saude" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {isPlatformAdmin() && <SaudeLigacoesSettings />}
          </TabsContent>

          <TabsContent value="servidor" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {isPlatformAdmin() && <ConfiguracaoServidorSettings />}
          </TabsContent>

          <TabsContent value="api" className="m-0 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-emerald-400 drop-shadow-sm w-fit">API do Sistema (Integrações Externas)</h2>
              <p className="text-muted-foreground text-sm mt-1">Chaves e documentação para você conectar o seu ERP ou outro sistema ao nosso.</p>
            </div>
            
            {/* API Keys for INBOUND usage */}
            <APIKeysSettings />

            <div className="p-6 bg-glass border border-border/50 rounded-xl shadow-soft space-y-4">
              <h3 className="font-bold text-lg flex items-center gap-2"><Code2 className="h-5 w-5 text-primary" /> Documentação OpenAPI</h3>
              <p className="text-sm text-muted-foreground">
                Acesse a documentação completa da API (Swagger) para explorar endpoints, exemplos de request/response e testar integrações ao vivo.
              </p>
              <a
                href="/api-docs.html"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-primary text-primary-foreground px-5 py-2.5 text-sm font-bold shadow-glow hover:bg-primary/90 transition-all w-fit"
              >
                📖 Abrir Documentação Oficial
              </a>
            </div>
          </TabsContent>

          {/* Aparência */}
          <TabsContent value="appearance" className="m-0 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <AppearanceSettings />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
