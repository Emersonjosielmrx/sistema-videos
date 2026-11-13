import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Magnet, MapPin, Search, Database, Download, Users, Briefcase, Zap } from "lucide-react";
import { apiPost } from "@/lib/api";
import { downloadCSV, csvTelefone } from "@/lib/csv";
import { useLeadCaptureStore } from "@/stores/leads";

type Lead = { name: string; phone: string; source: string; segment: string; address?: string };

// Leads captados persistem no localStorage pra sobreviver a reload (a store só guarda em memória).
const STORAGE_KEY = "hermes-lead-capture-results";

export const LeadCaptureTab = ({ onExported }: { onExported?: () => void } = {}) => {
  const { results, segment, location, setResults, setSegment, setLocation } = useLeadCaptureStore();
  const [isSearching, setIsSearching] = useState(false);
  const [exporting, setExporting] = useState(false);

  // Carrega os resultados salvos ao montar o componente (fix #9: "somem ao sair e voltar").
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setResults(parsed);
        }
      }
    } catch (e) {
      console.warn("Falha ao carregar leads salvos:", e);
    }
  }, []);

  // Salva os resultados sempre que mudam (persiste entre abas/reloads).
  useEffect(() => {
    if (results.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(results));
      } catch (e) {
        console.warn("Falha ao salvar leads:", e);
      }
    }
  }, [results]);

  const handleSearch = async () => {
    if (!segment.trim() || !location.trim()) {
      toast.error("Preencha o ramo de atividade e a localização.");
      return;
    }
    setIsSearching(true);
    setResults([]);
    toast.info("Buscando estabelecimentos reais no OpenStreetMap...");
    try {
      const r = await apiPost<{ leads: Lead[]; count: number }>("/api/leads/capture", {
        segment: segment.trim(), location: location.trim(), limit: 40,
      });
      setResults(r.leads || []);
      if ((r.leads || []).length === 0) {
        toast.warning("Nenhum lead com telefone público encontrado. Tente outro ramo ou cidade.");
      } else {
        toast.success(`Captação concluída! ${r.leads.length} leads com telefone encontrados.`);
      }
    } catch (e) {
      toast.error("Falha na captação", { description: (e as Error).message });
    } finally {
      setIsSearching(false);
    }
  };

  // Enviar pra Disparos: salva os leads numa lista e leva o usuário pra aba Listas,
  // onde ele dispara chamada/mensagem em massa. Antes o botão só salvava e ficava aqui.
  const handleExport = async () => {
    if (results.length === 0) return;
    setExporting(true);
    try {
      const phones = results.map(l => l.phone);
      const name = `Leads: ${segment.trim()} - ${location.trim()}`;
      const r = await apiPost<{ ok: boolean; count: number }>("/api/leads/export", { name, phones });
      toast.success(`${r.count} contatos salvos na lista "${name}". Abrindo Listas / Disparo…`);
      onExported?.(); // navega pra aba de destino (Listas)
    } catch (e) {
      toast.error("Falha ao enviar pra disparos", { description: (e as Error).message });
    } finally {
      setExporting(false);
    }
  };

  const downloadLeadsCSV = () => {
    if (results.length === 0) return;
    // lib/csv: nome/endereço vêm de fora (busca de empresas) — "=..." vira texto, não fórmula;
    // aspas no nome não quebram mais a linha; telefone como texto.
    downloadCSV(
      `leads_${segment.trim().replace(/\s+/g, "_")}_${location.trim().replace(/\s+/g, "_")}.csv`,
      ["nome", "telefone", "segmento", "endereco", "fonte"],
      results.map((l) => [l.name, csvTelefone(l.phone), l.segment, l.address || "", l.source]),
    );
    toast.success(`${results.length} leads baixados como CSV`);
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/20 shadow-[0_0_30px_rgba(59,130,246,0.15)] relative overflow-hidden">
        <div className="absolute -right-10 -top-10 opacity-10 pointer-events-none">
          <Magnet className="w-40 h-40 text-blue-500" />
        </div>
        <div className="flex items-center gap-4 relative z-10">
          <div className="bg-blue-500/20 p-3 rounded-xl border border-blue-500/30">
            <Database className="h-8 w-8 text-blue-500" />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-400 drop-shadow-sm">
              Captação Ativa de Leads
            </h2>
            <p className="text-sm text-blue-500/80 font-medium">Extraia contatos segmentados em tempo real direto da web para alimentar seus Agentes.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Painel de Busca */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="p-6 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-6">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2 mb-1"><Search className="h-5 w-5 text-blue-500"/> Configurar Radar</h3>
              <p className="text-xs text-muted-foreground">Onde e quem você quer prospectar hoje?</p>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2"><Briefcase className="h-4 w-4 text-muted-foreground"/> Ramo de Atividade</label>
                <Input value={segment} onChange={e => setSegment(e.target.value)} placeholder="Ex: Dentistas, Imobiliárias..." className="bg-background/50 h-11 focus-visible:ring-blue-500" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2"><MapPin className="h-4 w-4 text-muted-foreground"/> Localização (Cidade/Estado)</label>
                <Input value={location} onChange={e => setLocation(e.target.value)} placeholder="Ex: São Paulo, SP" className="bg-background/50 h-11 focus-visible:ring-blue-500" />
              </div>
              
              <Button 
                onClick={handleSearch} 
                disabled={isSearching}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white shadow-glow h-12 mt-4"
              >
                {isSearching ? "Iniciando Varredura..." : <><Zap className="h-4 w-4 mr-2" /> Iniciar Captação (Auto-Scraping)</>}
              </Button>
            </div>
          </Card>
        </div>

        {/* Resultados */}
        <div className="lg:col-span-2">
          <Card className="p-6 bg-black/20 backdrop-blur-md border-border/50 shadow-soft min-h-[400px]">
             <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-bold flex items-center gap-2"><Users className="h-5 w-5 text-blue-500"/> Leads Encontrados</h3>
                {results.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Button onClick={downloadLeadsCSV} variant="outline" size="sm" className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10">
                      <Download className="h-4 w-4 mr-2" /> Baixar CSV
                    </Button>
                    <Button onClick={handleExport} disabled={exporting} variant="outline" size="sm" className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10 disabled:opacity-60">
                      <Download className="h-4 w-4 mr-2" /> {exporting ? "Enviando..." : "Enviar pra Disparos"}
                    </Button>
                    <Button onClick={() => { setResults([]); try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignora */ } toast.info("Resultados limpos."); }} variant="ghost" size="sm" className="text-destructive hover:bg-destructive/10" title="Limpar resultados salvos">
                      Limpar
                    </Button>
                  </div>
                )}
             </div>

             {results.length === 0 && !isSearching && (
               <div className="h-[250px] flex flex-col items-center justify-center text-center opacity-50">
                 <Magnet className="h-12 w-12 mb-3 text-muted-foreground" />
                 <p className="text-sm font-medium">Nenhum lead captado ainda.</p>
                 <p className="text-xs">Configure o radar ao lado para iniciar a prospecção ativa.</p>
               </div>
             )}

             {isSearching && (
               <div className="h-[250px] flex flex-col items-center justify-center">
                 <div className="h-8 w-8 rounded-full border-4 border-blue-500/30 border-t-blue-500 animate-spin mb-4" />
                 <p className="text-sm text-blue-400 animate-pulse font-medium">Infiltrando em diretórios e redes...</p>
               </div>
             )}

             {!isSearching && results.length > 0 && (
               <div className="space-y-3">
                 {results.map((lead, i) => (
                   <div key={lead.phone + i} className="p-4 bg-background/40 border border-border/50 rounded-xl flex items-center justify-between hover:border-blue-500/30 transition-colors">
                     <div>
                       <h4 className="font-bold text-sm">{lead.name}</h4>
                       <div className="flex gap-3 mt-1">
                         <span className="text-xs text-muted-foreground flex items-center gap-1"><Briefcase className="h-3 w-3" /> {lead.segment}</span>
                         <span className="text-xs text-muted-foreground flex items-center gap-1"><Search className="h-3 w-3" /> {lead.source}</span>
                       </div>
                     </div>
                     <div className="text-right">
                       <span className="text-sm font-mono text-foreground bg-black/30 px-3 py-1 rounded-md">{lead.phone}</span>
                     </div>
                   </div>
                 ))}
               </div>
             )}
          </Card>
        </div>

      </div>
    </div>
  );
};
