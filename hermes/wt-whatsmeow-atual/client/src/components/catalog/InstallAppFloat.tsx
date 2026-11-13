import { Smartphone, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function InstallAppFloat() {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-8 slide-in-from-right-8 duration-500">
      <div className="bg-glass/80 backdrop-blur-md border border-primary/20 shadow-[0_8px_32px_-12px_rgba(139,92,246,0.5)] rounded-2xl p-4 flex items-center gap-4">
        <div className="bg-primary/20 p-2.5 rounded-xl text-primary">
          <Smartphone className="h-6 w-6" />
        </div>
        <div className="mr-2">
          <h4 className="font-bold text-sm tracking-tight">Instalar Vitrine IA</h4>
          <p className="text-xs text-muted-foreground mt-0.5">Instale como um app (Rápido e Leve)</p>
        </div>
        <Button className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow h-9 rounded-xl px-4 text-xs font-bold">
          Instalar
        </Button>
        <button 
          onClick={() => setIsVisible(false)}
          className="text-muted-foreground hover:text-foreground transition-colors p-1"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
