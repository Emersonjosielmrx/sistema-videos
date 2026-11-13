import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Headset, Ear, MessageSquareWarning, Save, Bot, Smartphone, PhoneCall, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { apiGet, apiPut } from "@/lib/api";

export const HumanAssistTab = () => {
  const [state, setState] = useState({
    enabled: true,
    channel: "whatsapp",
    adminNumber: "", // antes vinha "+55 11 99999-9999" (fictício) e podia ser salvo assim
    stallMessage: "Só um minutinho que estou verificando essa informação exata no sistema pra você... Aproveitando, você prefere a entrega para qual data?",
    autoLearn: true
  });
  const [saving, setSaving] = useState(false);

  // Carrega o que ja' foi salvo (bloco human_assist de GET /api/settings).
  useEffect(() => {
    // O servidor guarda em snake_case (internal/settings HumanAssistConfig).
    apiGet<{ human_assist?: { enabled?: boolean; channel?: string; admin_number?: string; stall_message?: string; auto_learn?: boolean } }>("/api/settings").then(s => {
      const h = s.human_assist;
      if (h && (h.admin_number !== undefined || h.stall_message !== undefined || h.channel)) {
        setState(prev => ({
          enabled: h.enabled ?? prev.enabled,
          channel: h.channel || prev.channel,
          adminNumber: h.admin_number ?? prev.adminNumber,
          stallMessage: h.stall_message ?? prev.stallMessage,
          autoLearn: h.auto_learn ?? prev.autoLearn,
        }));
      }
    }).catch(() => { /* sem config salva ainda: mantem defaults */ });
  }, []);

  const updateState = (key: keyof typeof state, value: any) => {
    setState(prev => ({ ...prev, [key]: value }));
  };

  const save = async () => {
    setSaving(true);
    try {
      await apiPut("/api/settings/human-assist", {
        enabled: state.enabled,
        channel: state.channel,
        admin_number: state.adminNumber,
        stall_message: state.stallMessage,
        auto_learn: state.autoLearn,
      });
      toast.success("Ajuda Humana salva.", { description: "Configuração guardada. A ação automática da IA está em desenvolvimento." });
    } catch (e) {
      toast.error("Não consegui salvar a Ajuda Humana", { description: (e as Error).message });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-violet-500/10 to-purple-500/10 border border-violet-500/20 shadow-[0_0_30px_rgba(139,92,246,0.15)] relative overflow-hidden">
        <div className="absolute -right-10 -top-10 opacity-10 pointer-events-none">
          <Ear className="w-40 h-40 text-violet-500" />
        </div>
        <div className="flex items-center gap-4 relative z-10">
          <div className="bg-violet-500/20 p-3 rounded-xl border border-violet-500/30">
            <Headset className="h-8 w-8 text-violet-500" />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-purple-400 drop-shadow-sm">
              Ajuda Humana (SOS)
            </h2>
            <p className="text-sm text-violet-500/80 font-medium">Seu Funcionário de IA pede ajuda aos gerentes quando não sabe responder, sem perder o cliente.</p>
          </div>
        </div>
        <div className="flex items-center gap-3 relative z-10">
           <span className="text-sm font-semibold text-muted-foreground">Ponto Ligado</span>
           <Switch checked={state.enabled} onCheckedChange={c => updateState("enabled", c)} className="data-[state=checked]:bg-violet-500" />
        </div>
      </div>

      <Card className="p-8 bg-black/20 backdrop-blur-md border-border/50 shadow-soft space-y-8">
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2 mb-1"><MessageSquareWarning className="h-5 w-5 text-violet-500"/> 1. Como chamar ajuda?</h3>
              <p className="text-xs text-muted-foreground">Por onde a IA deve gritar por você?</p>
            </div>
            
            <div className="space-y-3">
              <label className="text-sm font-medium">Canal de Contato</label>
              <div className="flex gap-2">
                <Button 
                  variant={state.channel === "whatsapp" ? "default" : "outline"}
                  onClick={() => updateState("channel", "whatsapp")}
                  className={cn("flex-1", state.channel === "whatsapp" && "bg-violet-500 hover:bg-violet-600")}
                >
                  <Smartphone className="h-4 w-4 mr-2"/> WhatsApp
                </Button>
                <Button 
                  variant={state.channel === "call" ? "default" : "outline"}
                  onClick={() => updateState("channel", "call")}
                  className={cn("flex-1", state.channel === "call" && "bg-violet-500 hover:bg-violet-600")}
                >
                  <PhoneCall className="h-4 w-4 mr-2"/> Ligação Fantasma
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Número do Gerente / Admin</label>
              <Input 
                value={state.adminNumber}
                onChange={e => updateState("adminNumber", e.target.value)}
                className="bg-background/50 h-12 focus-visible:ring-violet-500" 
                placeholder="+55 11 99999-9999"
              />
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2 mb-1"><Bot className="h-5 w-5 text-violet-500"/> 2. Estratégia de Enrolação</h3>
              <p className="text-xs text-muted-foreground">O que o Agente diz para o cliente enquanto espera você responder?</p>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Mensagem de Ganho de Tempo</label>
              <Textarea 
                value={state.stallMessage}
                onChange={e => updateState("stallMessage", e.target.value)}
                className="min-h-[100px] bg-background/50 focus-visible:ring-violet-500 resize-none"
                placeholder="Vou checar isso agora..."
              />
            </div>
            
            <div className="p-4 bg-violet-500/10 border border-violet-500/20 rounded-xl">
               <div className="flex items-center justify-between">
                 <div>
                   <h4 className="font-bold text-sm text-violet-300">Aprender com a Resposta</h4>
                   <p className="text-xs text-violet-400/70 mt-1">Quando você responder, a IA injeta sua resposta no RAG automaticamente para não perguntar de novo.</p>
                 </div>
                 <Switch checked={state.autoLearn} onCheckedChange={c => updateState("autoLearn", c)} className="data-[state=checked]:bg-emerald-500" />
               </div>
            </div>

          </div>

        </div>

        <div className="mt-8 pt-6 border-t border-border/50 flex justify-end">
          <Button disabled={saving} className="bg-violet-500 hover:bg-violet-600 text-white shadow-glow border-none gap-2 h-12 px-8" onClick={save}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Salvar Ajuda Humana
          </Button>
        </div>

      </Card>
    </div>
  );
};
