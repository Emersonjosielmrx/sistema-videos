import { Card } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Tag, Sparkles } from "lucide-react";
import { useState, useEffect } from "react";
import { apiGet } from "@/lib/api";
import { logError } from "@/lib/log";

const INIT_USAGE = [
  { name: "Seg", aplicadas: 0, manuais: 0 }, { name: "Ter", aplicadas: 0, manuais: 0 },
  { name: "Qua", aplicadas: 0, manuais: 0 }, { name: "Qui", aplicadas: 0, manuais: 0 },
  { name: "Sex", aplicadas: 0, manuais: 0 }, { name: "Sáb", aplicadas: 0, manuais: 0 },
  { name: "Dom", aplicadas: 0, manuais: 0 },
];

const INIT_DISTR = [
  { name: "Automáticas (IA)", value: 1, color: "#0ea5e9" },
  { name: "Manuais", value: 1, color: "#8b5cf6" },
];

export function TagsAnalytics() {
  const [usage, setUsage] = useState(INIT_USAGE);
  const [distr, setDistr] = useState(INIT_DISTR);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<any>("/api/analytics/tags")
      .then((r) => { if (r.usage) setUsage(r.usage); if (r.distribution) setDistr(r.distribution); })
      .catch(logError("TagsAnalytics"))
      .finally(() => setLoading(false));
  }, []);

  const hasData = usage.some(d => d.aplicadas > 0 || d.manuais > 0);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 mt-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6 bg-glass border-border/50 shadow-soft lg:col-span-2 relative">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <Tag className="h-4 w-4 text-sky-500" /> Histórico de Tagueamento
            </h4>
          </div>
          <div className="h-[250px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={usage} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} opacity={0.5} />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'hsl(var(--muted)/0.3)' }} contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))', borderRadius: '12px', fontSize: '12px' }} />
                <Bar dataKey="aplicadas" stackId="a" fill="#0ea5e9" radius={[0, 0, 0, 0]} barSize={20} />
                <Bar dataKey="manuais" stackId="a" fill="#8b5cf6" radius={[4, 4, 0, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
            {!hasData && !loading && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                <span className="bg-background/80 px-4 py-1.5 rounded-full text-xs font-medium text-muted-foreground border border-border/50 backdrop-blur-sm">Aguardando novos dados...</span>
              </div>
            )}
          </div>
        </Card>

        <Card className="p-6 bg-glass border-border/50 shadow-soft relative flex flex-col items-center justify-center text-center">
           <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider absolute top-6 left-6">Origem</h4>
           <div className={`h-[180px] w-full mt-6 relative ${!hasData ? 'opacity-20' : ''} pointer-events-none`}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={distr} innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value" stroke="none">
                    {distr.map((e: any, i: number) => (<Cell key={`c-${i}`} fill={e.color} />))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
           </div>
           {!hasData && !loading && (
             <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <Sparkles className="h-8 w-8 text-muted-foreground mb-2 opacity-50" />
                <span className="text-xs font-medium bg-background px-3 py-1 rounded-full border border-border/50 shadow-sm">Sem dados</span>
             </div>
           )}
        </Card>
      </div>
    </div>
  );
}
