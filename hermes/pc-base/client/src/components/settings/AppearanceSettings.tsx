import { Palette, Moon, Sun, RotateCcw } from "lucide-react";
import { useTheme } from "@/stores/theme";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";

export function AppearanceSettings() {
  const { theme, setTheme } = useTheme();

  // Persistência das cores personalizadas em localStorage (não há backend p/ isso).
  // Sem isso a cor era aplicada no DOM mas perdida no refresh.
  const BRAND_KEY = "hermes.brandColor";
  const BG_KEY = "hermes.bgColor";
  const DEFAULT_BRAND = "#10b981";
  const DEFAULT_BG = "#09090b";

  const [brandColor, setBrandColor] = useState(() => {
    try { return localStorage.getItem(BRAND_KEY) || DEFAULT_BRAND; } catch { return DEFAULT_BRAND; }
  });

  const [bgColor, setBgColor] = useState(() => {
    try { return localStorage.getItem(BG_KEY) || DEFAULT_BG; } catch { return DEFAULT_BG; }
  });

  const hexToHsl = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }
    return { h: h * 360, s: s * 100, l: l * 100 };
  };

  useEffect(() => {
    if (brandColor) {
       const applyPrimaryColor = (hex: string) => {
         const { h, s, l } = hexToHsl(hex);
         const hslVal = `${h.toFixed(0)} ${s.toFixed(0)}% ${l.toFixed(0)}%`;
         document.documentElement.style.setProperty('--primary', hslVal);
         document.documentElement.style.setProperty('--ring', hslVal);
       };
       applyPrimaryColor(brandColor);
       try {
         if (brandColor === DEFAULT_BRAND) localStorage.removeItem(BRAND_KEY);
         else localStorage.setItem(BRAND_KEY, brandColor);
       } catch { /* localStorage indisponível */ }
    }
  }, [brandColor, theme]);

  useEffect(() => {
    const props = ['--background', '--card', '--popover', '--muted', '--border'];
    const clearBg = () => props.forEach((p) => document.documentElement.style.removeProperty(p));

    // Só sobrescreve o fundo quando o usuário REALMENTE escolheu uma cor custom
    // (diferente do default). Com o default, remove os inline styles e deixa o CSS
    // do tema (claro/escuro) mandar. Sem isso, o default escuro (#09090b) era forçado
    // inline mesmo no tema claro — a tela ficava preta e trocar o tema não revertia,
    // porque o inline style vence a classe .dark/.light.
    if (!bgColor || bgColor === DEFAULT_BG) {
      clearBg();
      try { localStorage.removeItem(BG_KEY); } catch { /* localStorage indisponível */ }
      return;
    }

    const { h, s, l } = hexToHsl(bgColor);
    const isDark = document.documentElement.classList.contains('dark') || theme.startsWith('dark');
    const hVal = h.toFixed(0);
    const sVal = s.toFixed(0);
    if (isDark) {
      document.documentElement.style.setProperty('--background', `${hVal} ${sVal}% ${l.toFixed(0)}%`);
      document.documentElement.style.setProperty('--card', `${hVal} ${sVal}% ${(l + 2).toFixed(0)}%`);
      document.documentElement.style.setProperty('--popover', `${hVal} ${sVal}% ${(l + 2).toFixed(0)}%`);
      document.documentElement.style.setProperty('--muted', `${hVal} ${sVal}% ${(l + 6).toFixed(0)}%`);
      document.documentElement.style.setProperty('--border', `${hVal} ${sVal}% ${(l + 12).toFixed(0)}%`);
    } else {
      document.documentElement.style.setProperty('--background', `${hVal} ${sVal}% ${l.toFixed(0)}%`);
      document.documentElement.style.setProperty('--card', `${hVal} ${sVal}% ${(l > 2 ? l - 2 : 0).toFixed(0)}%`);
      document.documentElement.style.setProperty('--popover', `${hVal} ${sVal}% ${(l > 2 ? l - 2 : 0).toFixed(0)}%`);
      document.documentElement.style.setProperty('--muted', `${hVal} ${sVal}% ${(l > 6 ? l - 6 : 0).toFixed(0)}%`);
      document.documentElement.style.setProperty('--border', `${hVal} ${sVal}% ${(l > 12 ? l - 12 : 0).toFixed(0)}%`);
    }
    try { localStorage.setItem(BG_KEY, bgColor); } catch { /* localStorage indisponível */ }
  }, [bgColor, theme]);

  const resetToDefault = () => {
    setBrandColor("#10b981");
    setBgColor("#09090b");
    // Explicitly reset the tinted backgrounds to default neutral
    document.documentElement.style.removeProperty('--background');
    document.documentElement.style.removeProperty('--card');
    document.documentElement.style.removeProperty('--popover');
    document.documentElement.style.removeProperty('--muted');
    document.documentElement.style.removeProperty('--border');
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Tema e Cores</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Personalize a aparência do sistema para você.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Light Theme */}
        <button
          onClick={() => setTheme("light")}
          className={cn(
            "flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all hover:border-primary/50 bg-white text-zinc-950",
            theme === "light" ? "border-primary shadow-glow ring-2 ring-primary/20" : "border-border/50"
          )}
        >
          <div className="h-20 w-full rounded-lg bg-zinc-100 flex items-center justify-center border border-zinc-200">
            <Sun className="h-8 w-8 text-zinc-500" />
          </div>
          <span className="font-medium">Claro</span>
        </button>

        {/* Pure Black Theme */}
        <button
          onClick={() => setTheme("dark-black")}
          className={cn(
            "flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all hover:border-primary/50 bg-zinc-950 text-zinc-50",
            theme === "dark-black" ? "border-primary shadow-glow ring-2 ring-primary/20" : "border-border/50"
          )}
        >
          <div className="h-20 w-full rounded-lg bg-black flex items-center justify-center border border-zinc-800">
            <Moon className="h-8 w-8 text-zinc-400" />
          </div>
          <span className="font-medium">Escuro (Preto)</span>
        </button>

        {/* Dark Blue Theme */}
        <button
          onClick={() => setTheme("dark-blue")}
          className={cn(
            "flex flex-col items-center gap-3 p-4 rounded-xl border-2 transition-all hover:border-primary/50 bg-slate-900 text-slate-50",
            theme === "dark-blue" ? "border-primary shadow-glow ring-2 ring-primary/20" : "border-border/50"
          )}
        >
          <div className="h-20 w-full rounded-lg bg-slate-950 flex items-center justify-center border border-slate-800">
            <Palette className="h-8 w-8 text-slate-400" />
          </div>
          <span className="font-medium">Escuro (Azul)</span>
        </button>
      </div>

      <div className="pt-8 border-t border-border/50">
        <h3 className="text-lg font-medium mb-4">Identidade Visual Flexível</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col items-start gap-2 bg-muted/20 p-5 rounded-2xl border border-border/50">
            <h4 className="text-sm font-semibold mb-1">Cor Principal (Botões e Destaques)</h4>
            <div className="flex gap-4">
              <input type="color" value={brandColor} onChange={(e) => setBrandColor(e.target.value)} className="h-14 w-20 rounded-xl cursor-pointer border-0 bg-transparent p-0" /> 
              <span className="text-sm text-muted-foreground self-center">Altera botões, toggles, abas ativas e o anel de foco.</span>
            </div>
          </div>

          <div className="flex flex-col items-start gap-2 bg-muted/20 p-5 rounded-2xl border border-border/50">
            <h4 className="text-sm font-semibold mb-1">Cor de Fundo Global</h4>
            <div className="flex gap-4">
              <input type="color" value={bgColor} onChange={(e) => setBgColor(e.target.value)} className="h-14 w-20 rounded-xl cursor-pointer border-0 bg-transparent p-0" /> 
              <span className="text-sm text-muted-foreground self-center">Altera a cor base do fundo, menu, painéis flutuantes e bordas.</span>
            </div>
          </div>
        </div>
        
        {(brandColor !== "#10b981" || bgColor !== "#09090b") && (
          <div className="mt-4 flex justify-end">
            <Button variant="outline" onClick={resetToDefault} className="h-10 text-xs font-bold bg-background">
              <RotateCcw className="w-4 h-4 mr-2"/> Restaurar Cores Padrão
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
