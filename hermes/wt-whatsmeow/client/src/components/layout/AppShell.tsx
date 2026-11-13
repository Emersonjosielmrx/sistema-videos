import { useState, useEffect, type ReactNode } from "react";
import { Menu, LogOut, Bot, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { isAuthed, logout } from "@/lib/auth";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Sidebar } from "./Sidebar";
import { ThemeToggle } from "./ThemeToggle";
import { InstallApp } from "@/components/InstallApp";
import { CommandPalette } from "./CommandPalette";
import { useNavigation, setChatOpen } from "@/stores/navigation";
import { cn } from "@/lib/utils";

export const AppShell = ({ children }: { children: ReactNode }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dismissedFab, setDismissedFab] = useState(false);
  const view = useNavigation((s) => s.view);
  const collapsed = useNavigation((s) => s.sidebarCollapsed);
  const commandOpen = useNavigation((s) => s.commandOpen);
  const chatOpen = useNavigation((s) => s.chatOpen);

  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    setDismissedFab(sessionStorage.getItem('ai_fab_dismissed') === 'true');
    setIsIOS(/iphone|ipad|ipod/i.test(navigator.userAgent));
  }, []);

  const getAiSuggestion = () => {
    // Basic hash read, ignore standard '#' if empty
    const hash = window.location.hash ? window.location.hash.replace('#', '') : '';
    
    const suggestions: Record<string, string[]> = {
      'settings_appearance': [
        "Sugira uma paleta de cores moderna inspirada em SaaS premium...",
        "Como deixo minha plataforma com maior contraste e acessibilidade?",
        "Analise minha identidade visual e sugira ajustes de UI/UX...",
      ],
      'settings_ai': [
        "Ajuste o prompt do Cérebro para usar gatilhos de escassez e urgência...",
        "Analise minhas regras de negócio e aponte brechas na lógica da IA...",
        "Quais as melhores práticas para evitar alucinação do modelo neste contexto?",
      ],
      'settings_call': [
        "Otimize o tempo de silêncio para não cortar clientes que falam devagar...",
        "Me ajude a calibrar a latência do motor cognitivo...",
        "Quero que a IA pareça mais rápida e corte menos as pessoas...",
      ],
      'settings_voice': [
        "Qual a melhor voz TTS para soar extremamente empática e humanizada?",
        "Me sugira palavras 'fillers' (humm, entendi) para deixar a IA natural...",
        "Qual o melhor som ambiente para disfarçar a latência?",
      ],
      'settings_telephony': [
        "Quantas ligações por dia posso fazer por linha sem risco de bloqueio?",
        "O que fazer quando uma linha do WhatsApp desconecta?",
      ],
      'settings_webhooks': [
        "Crie um payload de exemplo para integrar os eventos com o RD Station...",
        "Escreva um código para receber o webhook de finalização de chamada...",
      ],
      'settings_wizard': [
        "Analise se esqueci de preencher algum dado crucial do setup...",
        "Revise as permissões do Gestor de Inteligência...",
      ],
      'settings': [
         "Faça uma auditoria nas minhas configurações e sugira otimizações...",
         "Como posso reduzir a latência total e baratear os custos da IA?",
      ],
      'crm': [
        "Cruze os dados e me liste os leads que estão esfriando no funil...",
        "Escreva uma mensagem persuasiva de follow-up para os leads em Negociação...",
        "Analise os motivos de perda das últimas semanas e sugira um plano de ação...",
        "Mova todos os leads sem interação há 7 dias para a lixeira..."
      ],
      'calls': [
        "Resuma as objeções de vendas mais comuns mencionadas hoje...",
        "Filtre as ligações onde o sentimento do cliente foi negativo...",
        "Gere um script matador de vendas baseado na ligação de maior duração...",
        "Transcreva e resuma os compromissos assumidos na última ligação...",
      ],
      'cost': [
        "Projete meu gasto com Tokens se o volume de chamadas triplicar...",
        "Analise qual provedor (OpenAI vs Groq) está pesando mais na fatura...",
        "Gere um relatório calculando o meu Custo de IA por Lead convertido...",
      ]
    };

    const specificKey = `${view}_${hash}`;
    let pool = suggestions[specificKey] || suggestions[view];
    
    if (!pool || pool.length === 0) {
      pool = [
        "Analise meus dados recentes e extraia insights de negócio...",
        "Crie uma automação inteligente para otimizar meu trabalho...",
        "Cruze os dados atuais e me mostre onde estou perdendo dinheiro..."
      ];
    }
    
    // Pick a random suggestion from the pool
    return pool[Math.floor(Math.random() * pool.length)];
  };

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <header className="sticky top-0 z-30 flex md:hidden h-14 items-center justify-between border-b border-border/50 bg-background/60 px-4 backdrop-blur-xl sm:px-6 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="md:hidden" aria-label="Menu">
                <Menu className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
              <SheetTitle className="sr-only">Navegação Principal</SheetTitle>
              <Sidebar onNavigate={() => setMobileOpen(false)} />
            </SheetContent>
          </Sheet>
          
          <div className="hidden md:flex items-center gap-2 text-sm font-medium text-muted-foreground">
          </div>
        </div>
        <div className="flex items-center gap-2 pointer-events-auto">
          <ThemeToggle />
          {isAuthed() && (
            <Button
              variant="ghost"
              size="icon"
              aria-label="Sair"
              className="text-muted-foreground hover:text-destructive transition-colors"
              onClick={() => {
                // Avisa o servidor (encerra a sessão lá) e sai mesmo se ele não responder.
                logout().finally(() => location.reload());
              }}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          )}
        </div>
      </header>
      <div className="flex flex-1 overflow-hidden relative">
        <aside className={cn("hidden shrink-0 md:block p-4 pr-0 transition-all duration-300", collapsed ? "w-[88px]" : "w-[280px]")}>
          <div className="h-full rounded-2xl border border-border/50 bg-glass shadow-soft overflow-hidden flex flex-col">
            <Sidebar />
          </div>
        </aside>
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">{children}</main>
        
        {/* Floating Action Buttons */}
        <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end gap-3 pointer-events-none">
          {!commandOpen && !chatOpen && !dismissedFab && !isIOS && (
             <div className="flex items-center rounded-2xl bg-[#10b981] text-white shadow-[0_4px_20px_rgba(16,185,129,0.4)] overflow-hidden transition-all hover:shadow-[0_4px_30px_rgba(16,185,129,0.6)] hover:-translate-y-1 h-11 pointer-events-auto">
               <Button 
                 variant="ghost"
                 className="h-full px-4 rounded-none hover:bg-black/10 font-bold gap-2 text-white border-r border-white/20"
                 onClick={() => setChatOpen(true, getAiSuggestion())}
               >
                 <Bot className="h-5 w-5" />
                 Delegar para IA
               </Button>
               <Button variant="ghost" size="icon" className="h-full w-8 rounded-none hover:bg-black/10 text-white opacity-70 hover:opacity-100 bg-[#10b981]" onClick={() => { setDismissedFab(true); sessionStorage.setItem('ai_fab_dismissed', 'true'); }}>
                 <X className="h-4 w-4" />
               </Button>
             </div>
          )}
          <div className="pointer-events-auto">
            <InstallApp />
          </div>
        </div>
      </div>
      <CommandPalette />
    </div>
  );
};
