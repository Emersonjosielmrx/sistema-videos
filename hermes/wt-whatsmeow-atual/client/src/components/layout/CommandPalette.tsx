import { useEffect, useState } from "react";
import { Search, LayoutDashboard, Phone, KanbanSquare, Settings, ArrowRight } from "lucide-react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useNavigation, setView, setCommandOpen, type View } from "@/stores/navigation";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  // Abre também via botão "Delegar para IA" (flag no store), não só Ctrl+K.
  const commandOpen = useNavigation((s) => s.commandOpen);

  useEffect(() => {
    if (commandOpen) {
      setOpen(true);
      setCommandOpen(false);
    }
  }, [commandOpen]);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const runCommand = (action: () => void) => {
    action();
    setOpen(false);
    setSearch("");
  };

  const actions: { id: View; label: string; icon: React.ElementType }[] = [
    { id: "cost", label: "Ir para Visão Geral", icon: LayoutDashboard },
    { id: "calls", label: "Ir para Ligações", icon: Phone },
    { id: "crm", label: "Ir para Gestão de Leads", icon: KanbanSquare },
    { id: "settings", label: "Ir para Configurações", icon: Settings },
  ];

  const filtered = actions.filter((a) =>
    a.label.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="overflow-hidden p-0 shadow-2xl max-w-xl bg-card border-border/50 rounded-2xl">
        <div className="flex items-center border-b border-border/50 px-4">
          <Search className="mr-2 h-4 w-4 shrink-0 text-primary" />
          <input
            autoFocus
            className="flex h-12 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Digite um comando ou busque (ex: Visão Geral)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="max-h-[300px] overflow-y-auto p-2 custom-scrollbar">
          {filtered.length === 0 ? (
            <p className="p-4 text-center text-sm text-muted-foreground">
              Nenhum comando encontrado.
            </p>
          ) : (
            <div className="space-y-1">
              <p className="px-2 py-1 text-xs font-semibold uppercase text-muted-foreground">
                Navegação
              </p>
              {filtered.map((action) => (
                <div
                  key={action.id}
                  role="button"
                  tabIndex={0}
                  className="group relative flex cursor-default select-none items-center rounded-xl px-3 py-2.5 text-sm outline-none hover:bg-primary/10 hover:text-primary transition-colors cursor-pointer"
                  onClick={() => runCommand(() => setView(action.id))}
                >
                  <action.icon className="mr-3 h-4 w-4" />
                  <span className="font-medium">{action.label}</span>
                  <ArrowRight className="ml-auto h-4 w-4 opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="border-t border-border/50 p-3 flex justify-between items-center text-xs text-muted-foreground bg-muted/20">
          <div className="flex items-center gap-2">
            <kbd className="px-1.5 py-0.5 rounded-md bg-background border border-border font-mono shadow-sm">esc</kbd> para fechar
          </div>
          <div>Hermes Command</div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
