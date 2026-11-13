import { Card } from "@/components/ui/card";
import { setView } from "@/stores/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  Users, Megaphone, Bot, Zap, ArrowRight, Phone, MessageCircle, 
  LayoutDashboard, KanbanSquare, Calendar, Store, PlayCircle, KeyRound
} from "lucide-react";
import { useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";

const TUTORIALS = [
  { id: 1, title: "Visão Geral (Dashboard)", desc: "Interprete gráficos, métricas de duração, sentimento e economia gerada.", icon: LayoutDashboard, view: "cost", color: "text-emerald-500", bg: "bg-emerald-500/10", border: "hover:border-emerald-500/50" },
  { id: 2, title: "Gestão de Leads (CRM)", desc: "Como alternar entre Kanban e Lista, gerenciar o funil de vendas e fazer Follow Up inteligente.", icon: KanbanSquare, view: "crm", color: "text-emerald-500", bg: "bg-emerald-500/10", border: "hover:border-emerald-500/50" },
  { id: 3, title: "Criando Funcionários IA", desc: "Wizard passo a passo para criar personalidades, perfis de voz e bases de conhecimento (RAG).", icon: Users, view: "specialized", color: "text-violet-500", bg: "bg-violet-500/10", border: "hover:border-violet-500/50" },
  { id: 4, title: "Test Drive da IA", desc: "Como ligar para si mesmo e testar a IA antes de colocar os funcionários para atender clientes reais.", icon: Phone, view: "specialized", color: "text-violet-500", bg: "bg-violet-500/10", border: "hover:border-violet-500/50" },
  { id: 5, title: "Agenda Inteligente e Link Público", desc: "Bloqueie dias, configure limites e envie o link para seus clientes agendarem horários sozinhos.", icon: Calendar, view: "agenda", color: "text-amber-500", bg: "bg-amber-500/10", border: "hover:border-amber-500/50" },
  { id: 6, title: "Vitrine de Produtos", desc: "Cadastrando serviços e produtos para a IA consultar, comparar e tentar vender durante a chamada.", icon: Store, view: "catalog", color: "text-rose-500", bg: "bg-rose-500/10", border: "hover:border-rose-500/50" },
  { id: 7, title: "Central de Telefonia", desc: "Acompanhar ligações em andamento, ouvir transcrições e gerenciar instâncias de conexão.", icon: Phone, view: "calls", color: "text-sky-500", bg: "bg-sky-500/10", border: "hover:border-sky-500/50" },
  { id: 8, title: "Configuração de Provedores de IA", desc: "Onde inserir suas chaves API (OpenAI, Groq, ElevenLabs) na aba de Credenciais de forma segura.", icon: KeyRound, view: "settings", color: "text-slate-500", bg: "bg-slate-500/10", border: "hover:border-slate-500/50" },
  { id: 9, title: "Agente Gestor Automático", desc: "Peça no chat para o Agente Gestor criar campanhas ou responder clientes para você sem precisar clicar em nada.", icon: Bot, view: "cost", color: "text-emerald-500", bg: "bg-emerald-500/10", border: "hover:border-emerald-500/50" }
];

export const HelpPage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTutorials = TUTORIALS.filter(t => 
    t.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    t.desc.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-10">
      {/* Hero Banner - Agente Gestor */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-500/20 via-background to-background border border-emerald-500/20 p-8 sm:p-12 shadow-[0_0_40px_rgba(16,185,129,0.15)]">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <img src="/inovareLogo.png" alt="Inovare" className="w-64 h-64 object-contain filter drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
        </div>
        <div className="relative z-10 max-w-2xl">
          <Badge className="bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30 border-emerald-500/30 mb-6 backdrop-blur-sm">
            <Zap className="h-3 w-3 mr-1" /> O Atalho Supremo
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4 bg-clip-text text-transparent bg-gradient-to-br from-emerald-400 to-emerald-600 drop-shadow-sm w-fit">
            Preguiça de ler tutoriais?
          </h1>
          <p className="text-xl text-muted-foreground mb-8">
            Você não precisa aprender a usar este sistema se não quiser. 
            Basta pedir ao <strong className="text-foreground">Agente Gestor</strong> na barra lateral esquerda. Ele configura campanhas, escreve textos e liga para seus clientes enquanto você toma um café.
          </p>
          <div className="flex gap-4">
            <Button size="lg" className="rounded-xl shadow-glow gap-2 bg-emerald-500 text-black hover:bg-emerald-400" onClick={() => {
              const btn = document.querySelector('button[title="Agente Gestor"]') as HTMLButtonElement | null;
              if (btn) btn.click();
            }}>
              <Bot className="h-5 w-5" /> Falar com o Agente
            </Button>
          </div>
        </div>
      </div>

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mt-12 mb-6">
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <PlayCircle className="text-emerald-500 w-6 h-6 drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]" /> Central de Treinamento
          </h2>
          <p className="text-muted-foreground">Vídeos e guias práticos focados em cada função da plataforma Hermes Call.</p>
        </div>
        <div className="relative w-full md:w-80">
          <Input 
            placeholder="Buscar tutorial ou função..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-background/50 border-border/50 rounded-xl pl-4 h-10 shadow-soft focus-visible:ring-emerald-500/50"
          />
        </div>
      </div>

      {filteredTutorials.length === 0 ? (
        <Card className="p-16 flex flex-col items-center justify-center text-center text-muted-foreground bg-background/20 shadow-soft border-border/50 rounded-3xl">
          <Megaphone className="h-10 w-10 mb-3 opacity-20" />
          <p className="text-sm font-medium">Nenhum tutorial encontrado para "{searchQuery}".</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTutorials.map((t) => {
            const Icon = t.icon;
            return (
              <Card 
                key={t.id} 
                className={cn("p-6 bg-glass border-border/50 hover:shadow-soft transition-all group cursor-pointer", t.border)} 
                onClick={() => setView(t.view as any)}
              >
                <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform", t.bg, t.color)}>
                  <Icon className="h-5 w-5 drop-shadow-sm" />
                </div>
                <h3 className="text-lg font-bold mb-2 flex items-center justify-between">
                  {t.title}
                  <ArrowRight className={cn("h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity", t.color)} />
                </h3>
                <p className="text-sm text-muted-foreground">{t.desc}</p>
              </Card>
            );
          })}
        </div>
      )}

      {/* Dicas Colapsáveis - Escondendo a chatice */}
      <div className="pt-4">
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="item-1" className="border-border/50 bg-muted/20 px-6 rounded-2xl">
            <AccordionTrigger className="hover:no-underline font-medium">
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-amber-500" />
                Como evitar que o WhatsApp bloqueie meu número? (Boas Práticas)
              </div>
            </AccordionTrigger>
            <AccordionContent className="text-muted-foreground space-y-4 pt-2 pb-6">
              <p>O WhatsApp pode bloquear números que fazem "Spam". Para evitar isso, siga as regras básicas:</p>
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>Aqueça o chip:</strong> Se o número é novo, não ligue para 1000 pessoas no primeiro dia. Comece ligando para 10 ou 20 pessoas e vá subindo.</li>
                <li><strong>Intervalos Reais:</strong> Ao configurar o disparo, deixe um intervalo (tempo de pausa) entre as ligações simulando um humano.</li>
                <li><strong>Fale com quem te conhece:</strong> Tentar vender para listas compradas frias gera denúncias. Se 5 pessoas denunciarem seu número, o WhatsApp derruba ele.</li>
              </ul>
            </AccordionContent>
          </AccordionItem>
          
          <AccordionItem value="item-2" className="border-border/50 bg-muted/20 px-6 rounded-2xl mt-4">
            <AccordionTrigger className="hover:no-underline font-medium">
              <div className="flex items-center gap-2">
                <MessageCircle className="h-4 w-4 text-sky-500" />
                Dá pra fazer tudo pelo Telegram?
              </div>
            </AccordionTrigger>
            <AccordionContent className="text-muted-foreground space-y-4 pt-2 pb-6">
              <p>Sim! Se você conectar o Telegram nas Configurações, nem precisa abrir este site.</p>
              <ul className="list-disc pl-5 space-y-2">
                <li>Você envia um áudio no Telegram.</li>
                <li>Depois, digita o número do cliente (ex: 551199999999).</li>
                <li>O sistema faz a ligação automaticamente pelo seu WhatsApp.</li>
              </ul>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>

    </div>
  );
};
