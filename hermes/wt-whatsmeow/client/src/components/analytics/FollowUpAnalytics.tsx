import { Card } from "@/components/ui/card";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Timer, MessageCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { apiGet } from "@/lib/api";
import { logError } from "@/lib/log";

const INIT_VOL = [
  { name: "Seg", envios: 0, respostas: 0 },
  { name: "Ter", envios: 0, respostas: 0 },
  { name: "Qua", envios: 0, respostas: 0 },
  { name: "Qui", envios: 0, respostas: 0 },
  { name: "Sex", envios: 0, respostas: 0 },
  { name: "Sáb", envios: 0, respostas: 0 },
  { name: "Dom", envios: 0, respostas: 0 },
];

const INIT_ENG = [
  { name: "Alta Intenção", value: 1, color: "#10b981" },
  { name: "Dúvida", value: 1, color: "#f59e0b" },
  { name: "Descarte", value: 1, color: "#ef4444" },
];

export function FollowUpAnalytics() {
  const [vol, setVol] = useState(INIT_VOL);
  const [eng, setEng] = useState(INIT_ENG);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<any>("/api/analytics/followup")
      .then((r) => { if (r.volume) setVol(r.volume); if (r.engagement) setEng(r.engagement); })
      .catch(logError("FollowUpAnalytics"))
      .finally(() => setLoading(false));
  }, []);

  const hasData = vol.some(d => d.envios > 0 || d.respostas > 0);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 mt-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6 bg-glass border-border/50 shadow-soft lg:col-span-2 relative">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <MessageCircle className="h-4 w-4 text-fuchsia-500" /> Disparos &amp; Retornos (7 Dias)
            </h4>
            <div className="flex items-center gap-4 text-[0.65rem] font-bold">
               <div className="flex items-center gap-1.5"><div className="w-4 h-1.5 rounded-full bg-muted-foreground/30"></div> Envios</div>
               <div className="flex items-center gap-1.5"><div className="w-4 h-1.5 rounded-full bg-fuchsia-500"></div> Respostas</div>
            </div>
          </div>
          <div className="h-[250px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={vol} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} opacity={0.5} />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'hsl(var(--muted)/0.3)' }} contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))', borderRadius: '12px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="envios" stroke="hsl(var(--muted-foreground))" fill="none" strokeWidth={2} />
                <Area type="monotone" dataKey="respostas" stroke="#d946ef" fill="url(#colorResp)" strokeWidth={2} />
                <defs>
                  <linearGradient id="colorResp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#d946ef" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#d946ef" stopOpacity={0}/>
                  </linearGradient>
                </defs>
              </AreaChart>
            </ResponsiveContainer>
            {!hasData && !loading && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                <span className="bg-background/80 px-4 py-1.5 rounded-full text-xs font-medium text-muted-foreground border border-border/50 backdrop-blur-sm">Aguardando novos dados...</span>
              </div>
            )}
          </div>
        </Card>
        <Card className="p-6 bg-glass border-border/50 shadow-soft relative flex flex-col items-center justify-center text-center">
           <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider absolute top-6 left-6">Classificação das Respostas</h4>
           <div className={`h-[180px] w-full mt-6 relative ${!hasData ? 'opacity-20' : ''} pointer-events-none`}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={eng} innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value" stroke="none">
                    {eng.map((e: any, i: number) => (<Cell key={`c-${i}`} fill={e.color} />))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
           </div>
           {!hasData && !loading && (
             <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <Timer className="h-8 w-8 text-muted-foreground mb-2 opacity-50" />
                <span className="text-xs font-medium bg-background px-3 py-1 rounded-full border border-border/50 shadow-sm">Sem dados</span>
             </div>
           )}
        </Card>
      </div>
    </div>
  );
}
