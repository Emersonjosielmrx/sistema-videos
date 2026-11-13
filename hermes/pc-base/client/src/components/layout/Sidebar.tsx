import { useState } from "react";
import { Loader2, Plus, LayoutDashboard, Phone, Settings, HelpCircle, KanbanSquare, ChevronLeft, ChevronRight, Users, Calendar, Store, Bot, LogOut, Edit3, X, RefreshCcw, Headset, Video, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { setActiveSession } from "@/stores/sessions";
import { createSession, deleteSession } from "@/services/sessions";
import { useNavigation, setView, setSidebarCollapsed, setEditMode, setEmployeeEditMode, toggleHiddenView, resetHiddenViews, type View } from "@/stores/navigation";
import type { SessionInfo } from "@/types/session";
import { ManagerChat } from "@/components/chat/ManagerChat";
import { ThemeToggle } from "./ThemeToggle";
import { logout, isAuthed } from "@/lib/auth";


// fmtPhone formata um número BR (só dígitos) como +55 (11) 99999-9999. Fallback: com "+".

function NavButton({ view, icon: Icon, label, onNavigate, customTrigger }: { view: View | "manager_chat"; icon?: React.ElementType; label?: string, onNavigate?: () => void, customTrigger?: React.ReactNode }) {
  const current = useNavigation((s) => s.view);
  const collapsed = useNavigation((s) => s.sidebarCollapsed);
  const isEditMode = useNavigation((s) => s.isEditMode);
  const hiddenViews = useNavigation((s) => s.hiddenViews);
  const isEmployeeEditMode = useNavigation((s) => s.isEmployeeEditMode);
  const hiddenViewsEmployee = useNavigation((s) => s.hiddenViewsEmployee);
  const userRole = useNavigation((s) => s.userRole);
  
  const isHiddenForEmployee = hiddenViewsEmployee.includes(view as View);
  const isHiddenForMe = hiddenViews.includes(view as View);
  const isHidden = userRole === "employee" ? isHiddenForEmployee : isHiddenForMe;
  const isCore = view === "settings" || view === "help"; // Settings and Help cannot be hidden

  // Se estiver escondido e não estiver editando a visão daquele painel, some.
  if (isHidden && !isEditMode && !isEmployeeEditMode) return null;
  // Se for employee e estiver escondido, some (mesmo se de alguma forma o modo estiver ativo).
  if (userRole === "employee" && isHiddenForEmployee) return null;
  // Se for admin editando seu próprio painel, ele não vê o que já está escondido.
  // Wait, no modo de edição o admin TEM que ver para poder desocultar!
  // No, o Admin tem o botão de "Reset" para desocultar. 
  if (isEditMode && isHiddenForMe) return null;

  const isActiveEditMode = isEditMode || isEmployeeEditMode;
  const currentlyHiddenInThisMode = isEmployeeEditMode ? isHiddenForEmployee : isHiddenForMe;

  const handleAction = () => {
    if (isActiveEditMode) {
      if (!isCore) toggleHiddenView(view as View);
      return;
    }
    if (view !== "manager_chat") {
      setView(view as View); 
      onNavigate?.(); 
    }
  };

  const InnerButton = () => {
    if (customTrigger) {
      return (
        <div onClickCapture={(e) => { if (isActiveEditMode) { e.preventDefault(); e.stopPropagation(); handleAction(); } }} className={cn(isActiveEditMode && "pointer-events-none", currentlyHiddenInThisMode && "opacity-50 grayscale")}>
          {customTrigger}
        </div>
      );
    }
    return (
      <button
        id={`nav-${view}`}
        onClick={handleAction}
        className={cn(
          "flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all overflow-hidden whitespace-nowrap",
          current === view && !isActiveEditMode
            ? "bg-emerald-500/10 text-emerald-500" 
            : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
          !isActiveEditMode && "hover:translate-x-1",
          currentlyHiddenInThisMode && "opacity-50 grayscale bg-transparent border border-dashed border-border"
        )}
        title={collapsed ? label : undefined}
      >
        {Icon && <Icon className="h-5 w-5 shrink-0" />}
        {!collapsed && <span>{label}</span>}
      </button>
    );
  };

  return (
    <div className={cn("relative", isActiveEditMode && !isCore && "animate-jiggle")}>
      <InnerButton />
      {isActiveEditMode && !isCore && (
         <div 
           className={cn("absolute -top-1 -left-1 z-10 w-5 h-5 rounded-full flex items-center justify-center cursor-pointer shadow-md text-white font-bold text-xs transition-transform hover:scale-110", currentlyHiddenInThisMode ? "bg-emerald-500" : "bg-destructive")}
           onClick={(e) => { e.stopPropagation(); toggleHiddenView(view as View); }}
           title={currentlyHiddenInThisMode ? "Mostrar" : "Ocultar"}
         >
           {currentlyHiddenInThisMode ? <Plus className="w-3 h-3"/> : <X className="w-3 h-3"/>}
         </div>
      )}
    </div>
  );
}

export const Sidebar = ({ onNavigate }: { onNavigate?: () => void }) => {
  const collapsed = useNavigation((s) => s.sidebarCollapsed);
  const isEditMode = useNavigation((s) => s.isEditMode);
  const isEmployeeEditMode = useNavigation((s) => s.isEmployeeEditMode);
  const hiddenViews = useNavigation((s) => s.hiddenViews);
  const hiddenViewsEmployee = useNavigation((s) => s.hiddenViewsEmployee);
  const userRole = useNavigation((s) => s.userRole);
  const currentView = useNavigation((s) => s.view);
  const [creating, setCreating] = useState(false);
  const [toDelete, setToDelete] = useState<SessionInfo | null>(null);

  const onNew = async () => {
    setCreating(true);
    try {
      const { id } = await createSession("WhatsApp");
      setActiveSession(id);
      if (useNavigation.getState().view !== "calls") setView("calls");
      onNavigate?.();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const remove = async (id: string) => {
    try {
      await deleteSession(id);
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  return (
    <div className="flex h-full flex-col gap-1 p-3">
      {/* Brand / Logo */}
      <div className={cn("flex items-center px-2 pb-5 pt-2", collapsed ? "justify-center" : "gap-2.5")}>
        <div className="flex items-center gap-2 cursor-pointer group" onClick={() => { setView("cost"); onNavigate?.(); }} title="Ir para a Visão Geral">
          <img src="/hermesLogo.png" alt="Hermes" className="h-12 w-12 object-contain rounded-xl shadow-glow shrink-0 transition-transform duration-300 group-hover:scale-105" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-emerald-600 drop-shadow-[0_0_8px_rgba(16,185,129,0.3)] leading-none">
                Hermes Call
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main Global Navigation */}
      {/* min-h-0 + overflow-y-auto: em telas baixas (ou com a barra de favoritos do
          navegador ocupando altura) a lista ROLA em vez de esconder o último item
          ("Central de Telefonia"). Antes era overflow-hidden + flex-1 filler, que
          espremia e cortava o item de baixo. */}
      <div className="space-y-2 mb-6 min-h-0 overflow-y-auto mt-4">
        <NavButton view="cost" icon={LayoutDashboard} label="Visão Geral" onNavigate={onNavigate} />
        <NavButton view="crm" icon={KanbanSquare} label="Gestão de Leads" onNavigate={onNavigate} />
        <NavButton view="chat" icon={MessageSquare} label="Chat" onNavigate={onNavigate} />
        <NavButton
          view="manager_chat"
          customTrigger={
            <ManagerChat
              trigger={
                <button title={collapsed ? "Funcionário Gestor" : undefined} className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all hover:translate-x-1 text-emerald-500 hover:text-emerald-400 hover:bg-emerald-500/10 overflow-hidden whitespace-nowrap">
                  <Bot className="h-5 w-5 shrink-0 text-emerald-500" />
                  {!collapsed && <span>Funcionário Gestor</span>}
                </button>
              }
            />
          }
        />
        <NavButton view="specialized" icon={Users} label="Funcionários IA" onNavigate={onNavigate} />
        <NavButton view="agenda" icon={Calendar} label="Agenda" onNavigate={onNavigate} />
        <NavButton view="catalog" icon={Store} label="Vitrine de Produtos" onNavigate={onNavigate} />
        <NavButton view="calls" icon={Phone} label="Central de Telefonia" onNavigate={onNavigate} />
        <NavButton view="meeting-ai" icon={Video} label="Meet com IA" onNavigate={onNavigate} />
      </div>

      {/* Filler para empurrar o menu inferior */}
      <div className="flex-1" />

      {/* Menu Adicional (Grid 2x2 para economizar espaço) */}
      <div className={cn("pt-2 mt-2 border-t border-border/50", collapsed ? "space-y-1" : "grid grid-cols-2 gap-2 p-1")}>
        {!collapsed ? (
          <>
            <button onClick={() => { setView('settings'); onNavigate?.(); }} className={cn("flex flex-col items-center justify-center gap-1.5 rounded-2xl py-3.5 text-xs font-medium transition-all border", currentView === 'settings' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-muted/20 text-muted-foreground border-transparent hover:bg-muted/50 hover:text-foreground")}>
              <Settings className="h-5 w-5" /> Configurações
            </button>
            <button onClick={onNew} disabled={creating} className="flex flex-col items-center justify-center gap-1.5 rounded-2xl bg-emerald-500/10 hover:bg-emerald-500/20 py-3.5 text-xs font-semibold text-emerald-500 transition-all border border-emerald-500/20">
              {creating ? <Loader2 className="h-5 w-5 animate-spin" /> : <Plus className="h-5 w-5" />} Nova Linha
            </button>
            <button onClick={() => { setView('help'); onNavigate?.(); }} className={cn("flex flex-col items-center justify-center gap-1.5 rounded-2xl py-3.5 text-xs font-medium transition-all border", currentView === 'help' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-muted/20 text-muted-foreground border-transparent hover:bg-muted/50 hover:text-foreground")}>
              <HelpCircle className="h-5 w-5" /> Ajuda
            </button>
            <a href="https://wa.me/5591984698653" target="_blank" rel="noopener noreferrer" className="flex flex-col items-center justify-center gap-1.5 rounded-2xl bg-muted/20 hover:bg-muted/50 py-3.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-all border border-transparent">
              <Headset className="h-5 w-5" /> Suporte
            </a>
          </>
        ) : (
          <>
            <NavButton view="settings" icon={Settings} label="Configurações" onNavigate={onNavigate} />
            <NavButton 
              view={"newline" as any}
              customTrigger={
                <button onClick={onNew} disabled={creating} className="flex w-full justify-center items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all text-emerald-500 hover:bg-emerald-500/10">
                  {creating ? <Loader2 className="h-5 w-5 animate-spin" /> : <Plus className="h-5 w-5" />}
                </button>
              }
            />
            <NavButton view="help" icon={HelpCircle} label="Ajuda" onNavigate={onNavigate} />
            <a href="https://wa.me/5591984698653" target="_blank" rel="noopener noreferrer" className="flex w-full items-center justify-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all text-muted-foreground hover:text-emerald-500 hover:bg-emerald-500/10" title="Suporte">
              <Headset className="h-5 w-5" />
            </a>
          </>
        )}
      </div>

      {/* Recolher Toggle */}
      {/* Ações e Recolher */}
      <div className={cn("pt-2 mt-2 border-t border-border/50 flex", collapsed ? "flex-col items-center gap-2" : "items-center justify-between")}>
        <div className={cn("flex items-center", collapsed ? "flex-col gap-2" : "gap-1")}>
          <ThemeToggle />
          {userRole !== "employee" && (
            <>
              <Button
                variant="ghost"
                size="icon"
                className={cn("text-muted-foreground transition-colors h-9 w-9", isEditMode ? "text-primary bg-primary/10 shadow-glow" : "hover:text-primary")}
                onClick={() => setEditMode(!isEditMode)}
                title={isEditMode ? "Sair do modo de edição" : "Ocultar/Personalizar Meu Menu"}
              >
                <Edit3 className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={cn("text-muted-foreground transition-colors h-9 w-9", isEmployeeEditMode ? "text-sky-400 bg-sky-400/10 shadow-glow" : "hover:text-sky-400")}
                onClick={() => setEmployeeEditMode(!isEmployeeEditMode)}
                title={isEmployeeEditMode ? "Sair da configuração de funcionários" : "Ocultar para Funcionários"}
              >
                <Users className="h-4 w-4" />
              </Button>
              {((isEditMode && hiddenViews.length > 0) || (isEmployeeEditMode && hiddenViewsEmployee.length > 0)) && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-amber-500 bg-amber-500/10 shadow-glow transition-colors h-9 w-9"
                  onClick={resetHiddenViews}
                  title="Restaurar originais"
                >
                  <RefreshCcw className="h-4 w-4" />
                </Button>
              )}
            </>
          )}
          {isAuthed() && (
            <Button
              variant="ghost"
              size="icon"
              aria-label="Sair"
              className="text-muted-foreground hover:text-destructive transition-colors h-9 w-9"
              onClick={() => {
                // Avisa o servidor (encerra a sessão lá) e sai mesmo se ele não responder.
                logout().finally(() => location.reload());
              }}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          )}
        </div>
        <button 
          onClick={() => setSidebarCollapsed(!collapsed)}
          className={cn("rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors flex justify-center items-center h-9 w-9", collapsed ? "" : "")}
          title={collapsed ? "Expandir menu" : "Recolher menu"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="Excluir Linha?"
        description={toDelete ? `${toDelete.name} será desconectada e removida.` : undefined}
        confirmLabel="Excluir"
        destructive
        onConfirm={() => {
          if (toDelete) void remove(toDelete.id);
        }}
      />
    </div>
  );
};
