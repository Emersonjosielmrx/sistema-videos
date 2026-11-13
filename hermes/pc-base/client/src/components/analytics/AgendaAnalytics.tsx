import { Card } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell } from "recharts";
import { CalendarCheck, Clock, Users } from "lucide-react";
import { useState, useEffect } from "react";
import { apiGet } from "@/lib/api";
import { logError } from "@/lib/log";

// Eixos vazios (zeros) só para o gráfico ter forma enquanto não há dados reais.
const EMPTY_AGENDA_DATA = [
  { name: "Seg", agendados: 0, cancelados: 0 },
  { name: "Ter", agendados: 0, cancelados: 0 },
  { name: "Qua", agendados: 0, cancelados: 0 },
  { name: "Qui", agendados: 0, cancelados: 0 },
  { name: "Sex", agendados: 0, cancelados: 0 },
  { name: "Sáb", agendados: 0, cancelados: 0 },
  { name: "Dom", agendados: 0, cancelados: 0 },
];

const EMPTY_PEAK_DATA = [
  { name: "08:00", volume: 0 },
  { name: "10:00", volume: 0 },
  { name: "12:00", volume: 0 },
  { name: "14:00", volume: 0 },
  { name: "16:00", volume: 0 },
  { name: "18:00", volume: 0 },
];

type ShowSlice = { name: string; value: number; color: string };

export function AgendaAnalytics() {
  const [agendaData, setAgendaData] = useState(EMPTY_AGENDA_DATA);
  const [peakData, setPeakData] = useState(EMPTY_PEAK_DATA);
  // Antes começava em 1 x 1 (pizza meio a meio) e ficava assim quando não havia dados.
  const [showNoShow, setShowNoShow] = useState<ShowSlice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<any>("/api/analytics/agenda")
      .then((res) => {
        if (res.weekly) setAgendaData(res.weekly);
        if (res.peak_hours) setPeakData(res.peak_hours);
        if (res.show_no_show) setShowNoShow(res.show_no_show);
      })
      .catch(logError("AgendaAnalytics"))
      .finally(() => setLoading(false));
  }, []);

  const hasData = agendaData.some(d => d.agendados > 0 || d.cancelados > 0);
  const peakHasData = peakData.some((d: any) => Number(d.volume) > 0);
  const pieHasData = showNoShow.some((d) => Number(d.value) > 0);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 mt-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Volume de Agendamentos */}
        <Card className="p-6 bg-glass border-border/50 shadow-soft lg:col-span-2 relative">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <CalendarCheck className="h-4 w-4 text-sky-500" /> Agendamentos (7 Dias)
            </h4>
            <div className="flex items-center gap-4 text-[0.65rem] font-bold">
               <div className="flex items-center gap-1.5"><div className="w-4 h-1.5 rounded-full bg-sky-500"></div> Realizados</div>
               <div className="flex items-center gap-1.5"><div className="w-4 h-1.5 rounded-full bg-destructive"></div> Cancelados</div>
            </div>
          </div>
          <div className="h-[250px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={agendaData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} opacity={0.5} />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{ fill: 'hsl(var(--muted)/0.3)' }}
                  contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))', borderRadius: '12px', fontSize: '12px' }} 
                />
                <Bar dataKey="agendados" fill="#0ea5e9" radius={[4, 4, 0, 0]} barSize={20} />
                <Bar dataKey="cancelados" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
            {!hasData && !loading && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                  <span className="bg-background/80 px-4 py-1.5 rounded-full text-xs font-medium text-muted-foreground border border-border/50 backdrop-blur-sm">Sem dados ainda</span>
              </div>
            )}
          </div>
        </Card>

        {/* Comparecimento vs No Show */}
        <Card className="p-6 bg-glass border-border/50 shadow-soft relative flex flex-col items-center justify-center text-center">
           <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider absolute top-6 left-6">
              Comparecimento
           </h4>
           {pieHasData ? (
             <>
               <div className="h-[180px] w-full mt-6 relative pointer-events-none">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={showNoShow} innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value" stroke="none">
                        {showNoShow.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
               </div>
               <div className="flex flex-wrap justify-center gap-3 text-[0.7rem] font-medium">
                 {showNoShow.map((d) => (
                   <span key={d.name} className="flex items-center gap-1.5">
                     <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} /> {d.name}: {d.value}
                   </span>
                 ))}
               </div>
             </>
           ) : (
             <div className="flex flex-col items-center justify-center h-[180px] mt-6">
                <Users className="h-8 w-8 text-muted-foreground mb-2 opacity-50" />
                <span className="text-xs font-medium bg-background px-3 py-1 rounded-full border border-border/50 shadow-sm">{loading ? "Carregando…" : "Sem dados ainda"}</span>
             </div>
           )}
        </Card>
      </div>

      {/* Horários de Pico */}
      <Card className="p-6 bg-glass border-border/50 shadow-soft">
        <div className="flex items-center justify-between mb-6">
          <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
             <Clock className="h-4 w-4 text-amber-500" /> Distribuição de Horários
          </h4>
        </div>
        <div className="h-[250px] w-full relative">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={peakData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} opacity={0.5} />
              <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))', borderRadius: '12px', fontSize: '12px' }} 
              />
              <Area type="monotone" dataKey="volume" stroke="#f59e0b" fill="url(#colorPeak)" strokeWidth={2} />
              <defs>
                <linearGradient id="colorPeak" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
          {!peakHasData && !loading && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                <span className="bg-background/80 px-4 py-1.5 rounded-full text-xs font-medium text-muted-foreground border border-border/50 backdrop-blur-sm">Sem dados ainda</span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
