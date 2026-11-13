import { Card } from "@/components/ui/card";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Ban } from "lucide-react";
import { useState, useEffect } from "react";
import { apiGet } from "@/lib/api";
import { logError } from "@/lib/log";

const INIT_BLOCKS = [
  { name: "Seg", bloqueios: 0 }, { name: "Ter", bloqueios: 0 }, { name: "Qua", bloqueios: 0 },
  { name: "Qui", bloqueios: 0 }, { name: "Sex", bloqueios: 0 }, { name: "Sáb", bloqueios: 0 },
  { name: "Dom", bloqueios: 0 },
];

export function BlocksAnalytics() {
  const [data, setData] = useState(INIT_BLOCKS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<any>("/api/analytics/blocks")
      .then((r) => { if (r.volume) setData(r.volume); })
      .catch(logError("BlocksAnalytics"))
      .finally(() => setLoading(false));
  }, []);

  const hasData = data.some(d => d.bloqueios > 0);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 mt-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 bg-glass border-border/50 shadow-soft lg:col-span-2 relative">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <Ban className="h-4 w-4 text-destructive" /> Histórico de Bloqueios (7 Dias)
            </h4>
          </div>
          <div className="h-[250px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} opacity={0.5} />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'hsl(var(--muted)/0.3)' }} contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))', borderRadius: '12px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="bloqueios" stroke="#ef4444" fill="url(#colorBlock)" strokeWidth={2} />
                <defs>
                  <linearGradient id="colorBlock" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
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
      </div>
    </div>
  );
}
