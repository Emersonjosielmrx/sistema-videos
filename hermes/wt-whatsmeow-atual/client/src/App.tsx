import { Suspense, useEffect, useState } from "react";
import { AlertTriangle, X, Loader2 } from "lucide-react";
import { apiGet } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { AppShell } from "@/components/layout/AppShell";
import { lazyNamed } from "@/lib/lazy";
import { SessionPairing } from "@/components/domain/session/SessionPairing";
import { SessionHeader } from "@/components/domain/session/SessionHeader";
import { IncomingCallModal } from "@/components/domain/call/IncomingCallModal";
import { AdminSummonCard } from "@/components/domain/call/AdminSummonCard";
import { EmptyState } from "@/components/shared/EmptyState";
import { ensureSessionsWired, useSessions } from "@/stores/sessions";
import { ensureCallsWired } from "@/stores/calls";
import { useNavigation, setView } from "@/stores/navigation";
import { PageErrorBoundary } from "@/components/PageErrorBoundary";
import { useTheme } from "@/stores/theme";
import { t } from "@/lib/i18n";

// Cada tela é baixada só quando a pessoa abre (antes o painel inteiro vinha num único
// arquivo JS de ~2,3 MB, inclusive gráficos e o editor de fluxo que quase ninguém abre).
const TelephonyPage = lazyNamed(() => import("@/pages/TelephonyPage"), "TelephonyPage");
const ContactsPage = lazyNamed(() => import("@/pages/ContactsPage"), "ContactsPage");
const MassCallPage = lazyNamed(() => import("@/pages/MassCallPage"), "MassCallPage");
const MassMessagePage = lazyNamed(() => import("@/pages/MassMessagePage"), "MassMessagePage");
const DashboardPage = lazyNamed(() => import("@/pages/DashboardPage"), "DashboardPage");
const SettingsPage = lazyNamed(() => import("@/pages/SettingsPage"), "SettingsPage");
const LogsPage = lazyNamed(() => import("@/pages/LogsPage"), "LogsPage");
const AnalyticsPage = lazyNamed(() => import("@/pages/AnalyticsPage"), "AnalyticsPage");
const EasyFollowUpWizard = lazyNamed(() => import("@/components/settings/EasyFollowUpWizard"), "EasyFollowUpWizard");
const KnowledgeManagerTab = lazyNamed(() => import("@/components/settings/KnowledgeManagerTab"), "KnowledgeManagerTab");
const PromisesManagerTab = lazyNamed(() => import("@/components/settings/PromisesManagerTab"), "PromisesManagerTab");
const CampaignsPage = lazyNamed(() => import("@/pages/CampaignsPage"), "CampaignsPage");
const ListsPage = lazyNamed(() => import("@/pages/ListsPage"), "ListsPage");
const CRMPage = lazyNamed(() => import("@/pages/CRMPage"), "CRMPage");
const HelpPage = lazyNamed(() => import("@/pages/HelpPage"), "HelpPage");
const SetupWizard = lazyNamed(() => import("@/components/onboarding/SetupWizard"), "SetupWizard");
const CostsHubPage = lazyNamed(() => import("@/pages/CostsHubPage"), "CostsHubPage");
const AgendaPage = lazyNamed(() => import("@/pages/AgendaPage"), "AgendaPage");
const SpecializedAgents = lazyNamed(() => import("@/components/settings/SpecializedAgents"), "SpecializedAgents");
const CatalogPage = lazyNamed(() => import("@/pages/CatalogPage"), "CatalogPage");
const ProfilePage = lazyNamed(() => import("@/pages/ProfilePage"), "ProfilePage");
const TeamPage = lazyNamed(() => import("@/pages/TeamPage"), "TeamPage");
const MeetingAIPage = lazyNamed(() => import("@/pages/MeetingAIPage"), "MeetingAIPage");
const RecordingsPage = lazyNamed(() => import("@/pages/RecordingsPage"), "RecordingsPage");
const TranscriptsPage = lazyNamed(() => import("@/pages/TranscriptsPage"), "TranscriptsPage");
const ChatPage = lazyNamed(() => import("@/pages/ChatPage"), "ChatPage");

// Enquanto o arquivo da tela baixa: um indicador discreto (sem piscar a tela inteira).
const PageFallback = () => (
  <div className="flex items-center justify-center py-24 text-muted-foreground" role="status" aria-label="Carregando">
    <Loader2 className="h-5 w-5 animate-spin opacity-60" />
  </div>
);

type AICredential = { name: string; provider: string; status: string; failsThisWeek: number };

function GlobalAIErrorBanner() {
  const [show, setShow] = useState(true);
  const [broken, setBroken] = useState<AICredential[]>([]);
  const [totalFails, setTotalFails] = useState(0);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        const creds = await apiGet<AICredential[]>("/api/settings/ai/credentials");
        if (!alive) return;
        // Só é falha de verdade: chave com status != active OU com falhas na semana.
        const bad = (creds || []).filter((c) => c.status !== "active" || (c.failsThisWeek ?? 0) > 0);
        setBroken(bad);
        setTotalFails(bad.reduce((sum, c) => sum + (c.failsThisWeek ?? 0), 0));
      } catch {
        // Se a API falhar, NÃO inventa erro de credencial — só não mostra o banner.
        if (alive) setBroken([]);
      }
    };
    check();
    const id = setInterval(check, 60000); // reavalia a cada 1 min
    return () => { alive = false; clearInterval(id); };
  }, []);

  // Só aparece quando há credencial realmente com problema.
  if (broken.length === 0 || !show) return null;

  const failMsg = totalFails > 0
    ? `${totalFails} ${totalFails === 1 ? "falha" : "falhas"} nesta semana`
    : `${broken.length} ${broken.length === 1 ? "chave" : "<SEGREDO_REMOVIDO>"} com problema`;

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[100] w-[95%] max-w-2xl pointer-events-auto">
      <div className="bg-destructive/95 border-2 border-destructive shadow-[0_0_20px_rgba(239,68,68,0.4)] backdrop-blur-md rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4 animate-in slide-in-from-top-4 fade-in">
        <div className="p-3 bg-background/20 rounded-xl shrink-0 animate-pulse hidden sm:block">
          <AlertTriangle className="h-6 w-6 text-white" />
        </div>
        <div className="flex-1 text-white">
          <h3 className="font-black text-lg flex items-center gap-2">
            <span className="sm:hidden"><AlertTriangle className="h-5 w-5" /></span>
            Atenção Crítica: Falha em Credenciais de IA
          </h3>
          <p className="text-sm font-medium mt-0.5 opacity-90">
            {failMsg} no seu Cofre de IA (recusa de conexão/sem saldo). Acesse as <b>Configurações &gt; Credenciais IA</b> para gerenciar.
          </p>
        </div>
        <Button variant="ghost" size="icon" className="text-white/70 hover:bg-white/20 hover:text-white shrink-0 self-start sm:self-center" onClick={() => setShow(false)}>
           <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export const App = () => {
  const sessions = useSessions((s) => s.sessions);
  const activeId = useSessions((s) => s.activeId);
  const view = useNavigation((s) => s.view);
  const theme = useTheme((s) => s.theme);
  // O tour de boas-vindas (8 telas) NÃO abre mais sozinho no 1º acesso: ele cobria o cartão
  // "Primeiros passos", que é o caminho único até a 1ª ligação (P2 do plano, 05/10). Quem quiser
  // ver o tour abre pelo link do cartão (evento "hermes:abrir-tour").
  const [showWizard, setShowWizard] = useState(false);

  useEffect(() => {
    ensureSessionsWired();
    ensureCallsWired();
  }, []);

  useEffect(() => {
    const abrir = () => setShowWizard(true);
    window.addEventListener("hermes:abrir-tour", abrir);
    return () => window.removeEventListener("hermes:abrir-tour", abrir);
  }, []);

  const active = sessions.find((s) => s.id === activeId) ?? null;

  const renderContent = () => {
    if (view === "dashboard") return <DashboardPage />;
    if (view === "contacts") return <ContactsPage />;
    if (view === "mass-call") return <MassCallPage />;
    if (view === "mass-message") return <MassMessagePage />;
    if (view === "settings") return <SettingsPage />;
    if (view === "logs") return <LogsPage />;
    if (view === "analytics") return <AnalyticsPage />;
    if (view === "campaigns") return <CampaignsPage />;
    if (view === "lists") return <ListsPage />;
    if (view === "crm") return <CRMPage />;
    if (view === "help") return <HelpPage />;
    if (view === "security") return <SettingsPage />; // SecurityPage is part of settings, redirecting to settings
    if (view === "cost") return <CostsHubPage />;
    if (view === "specialized") return <div className="p-4 sm:p-6 max-w-7xl mx-auto"><SpecializedAgents /></div>;
    if (view === "agenda") return <AgendaPage />;
    if (view === "catalog") return <CatalogPage />;
    if (view === "profile") return <ProfilePage />;
    if (view === "team") return <TeamPage />;
    if (view === "follow_up") return <div className="p-4 sm:p-6 max-w-5xl mx-auto"><EasyFollowUpWizard /></div>;
    if (view === "knowledge") return <div className="p-4 sm:p-6 max-w-5xl mx-auto"><KnowledgeManagerTab /></div>;
    if (view === "promises") return <div className="p-4 sm:p-6 max-w-5xl mx-auto"><PromisesManagerTab /></div>;
    if (view === "meeting-ai") return <MeetingAIPage />;
    if (view === "recordings") return <RecordingsPage />;
    if (view === "transcripts") return <TranscriptsPage />;
    if (view === "chat") return <ChatPage />;

    if (view === "calls") {
       if (active) {
         return (
           <div className="space-y-6">
             <SessionHeader session={active} />
             {active.paired ? (
               <>
                 {active.paired && !active.connected ? (
                   <div className="rounded-lg border border-amber-500/40 bg-amber-50/70 px-4 py-3 text-sm text-amber-900">
                     ⚠️ WhatsApp está pareado mas o socket caiu (sem internet, ban temporário ou em sleep).
                     O backend vai recusar ligações e mensagens até você reconectar — leia o QR de novo no painel.
                   </div>
                 ) : null}
                 <TelephonyPage sid={active.id} />
               </>
             ) : (
               <SessionPairing session={active} />
             )}
           </div>
         );
       }
       // If no active session, show the telephony page without a specific line selected
       return (
          <div className="space-y-6">
            <TelephonyPage sid="" />
          </div>
       );
    }

    return <EmptyState title={t("select_account")} description={t("select_account_desc")} />;
  };

  return (
    <TooltipProvider delayDuration={200}>
      <AppShell>
        {/* key={view}: trocar de tela limpa o erro. "Voltar ao Painel" troca a tela salva
            para a Visão Geral (o Painel, tela inicial). */}
        <PageErrorBoundary key={view} onHome={() => setView("cost")}>
          <Suspense fallback={<PageFallback />}>
            {renderContent()}
          </Suspense>
        </PageErrorBoundary>
      </AppShell>
      <IncomingCallModal />
      <AdminSummonCard />
      <GlobalAIErrorBanner />
      {showWizard && (
        <Suspense fallback={null}>
          <SetupWizard onClose={() => setShowWizard(false)} />
        </Suspense>
      )}
      <Toaster theme={theme === "light" ? "light" : "dark"} position="top-center" expand={true} richColors closeButton />
    </TooltipProvider>
  );
};
