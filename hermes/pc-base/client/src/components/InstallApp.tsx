import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Download, X } from "lucide-react";
import { silentAll } from "@/lib/log";

// InstallApp — botão "Instalar app" (PWA). Aparece no painel quando o navegador
// permite instalar (evento beforeinstallprompt, Android/desktop Chrome/Edge). No
// iOS o Safari não dispara esse evento, então mostramos uma dica de "Compartilhar
// › Adicionar à Tela de Início". Registra o service worker pra o app ser instalável.

// Tipo do evento (não é padrão no lib DOM do TS).
type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

export function InstallApp() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [installed, setInstalled] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [, setShowIOSHint] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setDismissed(sessionStorage.getItem('install_dismissed') === 'true');
    // Registra o SW (necessário pra instalar). Silencioso se falhar.
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(silentAll());
    }
    // Já está rodando instalado? Então não mostra o botão.
    const standalone = window.matchMedia("(display-mode: standalone)").matches
      || (window.navigator as unknown as { standalone?: boolean }).standalone === true;
    if (standalone) { setInstalled(true); return; }

    // iOS não dispara beforeinstallprompt.
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    setIsIOS(ios);

    const onPrompt = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    };
    const onInstalled = () => { setInstalled(true); setDeferred(null); };
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  if (installed) return null;

  const install = async () => {
    if (isIOS) { setShowIOSHint((v) => !v); return; }
    if (!deferred) return;
    await deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
  };

  // Só mostra se dá pra instalar (tem prompt) ou é iOS (mostra dica).
  if (!deferred && !isIOS) return null;
  // Per user request, do not show install prompt on iOS at all.
  if (isIOS) return null;
  if (dismissed) return null;

  return (
    <div className="relative">
      <div className="flex items-center rounded-full border border-border/50 bg-background/50 overflow-hidden h-9 shadow-sm">
        <Button variant="ghost" size="sm" className="gap-2 px-4 h-full rounded-none font-semibold text-xs text-foreground/90 hover:bg-muted" onClick={install}>
          <Download className="h-3.5 w-3.5" /> Instalar app
        </Button>
        <Button variant="ghost" size="icon" className="h-full w-8 rounded-none border-l border-border/50 hover:bg-muted opacity-60 hover:opacity-100" onClick={() => { setDismissed(true); sessionStorage.setItem('install_dismissed', 'true'); }}>
          <X className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}
