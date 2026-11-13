import { useState, useEffect } from "react";
import { MessageSquare, Bot } from "lucide-react";
import { apiGet } from "@/lib/api";
import { cn } from "@/lib/utils";
import { AgentChatTest } from "./AgentChatTest";

export function ChatMonitor() {
  const [agents, setAgents] = useState<any[]>([]);
  const [currentAgentId, setCurrentAgentId] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // FIX (QA IA): antes o Chat/Teste mostrava só 1 mock hardcoded ("Agente de Teste
    // UI Mock") porque o fetch estava desativado. Agora lê a MESMA lista de funcionários
    // IA de /api/agent-profiles (fonte única que Meus Funcionários / Lab / runtime usam),
    // então TODOS os agentes do dono aparecem na sandbox.
    apiGet<{ profiles: { id: string; name: string }[] }>("/api/agent-profiles")
      .then((r) => setAgents(r.profiles ?? []))
      .catch(() => setAgents([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] -m-4 sm:-m-6 bg-background">
      <div className="flex items-center justify-between p-4 px-6 border-b border-border/50 bg-background/80 backdrop-blur-md z-10 shrink-0">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2 text-primary">
            <MessageSquare className="h-5 w-5" /> Chat / Teste Sandbox
          </h2>
          <p className="text-sm text-muted-foreground hidden md:block">Simule ligações ou mensagens de texto com seus funcionários IA.</p>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar: Agents */}
        <div className="w-[250px] flex flex-col border-r border-border/50 bg-black/10">
          <div className="p-4 border-b border-border/50 shrink-0 font-semibold text-sm">Funcionários Disponíveis</div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {loading ? <div className="text-muted-foreground text-sm p-2">Carregando funcionários...</div> :
             agents.length === 0 ? <div className="text-muted-foreground text-sm p-2">Nenhum funcionário encontrado. Crie um em "Criar Funcionário Fácil".</div> :
             agents.map(ag => (
               <div 
                 key={ag.id} 
                 onClick={() => setCurrentAgentId(ag.id)}
                 className={cn(
                   "p-3 rounded-lg cursor-pointer transition-colors text-sm font-medium flex items-center gap-2 border",
                   currentAgentId === ag.id ? "bg-primary/10 border-primary text-primary" : "hover:bg-white/5 border-transparent text-muted-foreground"
                 )}
               >
                 <Bot className="h-4 w-4 shrink-0" />
                 <span className="truncate">{ag.name}</span>
               </div>
             ))
            }
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-background/50 p-6">
          {!currentAgentId ? (
            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed border-border/50 rounded-2xl bg-card/30">
              <Bot className="h-12 w-12 mb-4 opacity-50" />
              <p>Selecione um funcionário na lateral para iniciar a simulação.</p>
            </div>
          ) : (
            <div className="flex-1 relative">
              <AgentChatTest agentId={currentAgentId} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
