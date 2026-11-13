import { Card } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";
import { Zap, PackageX, AlertTriangle, ArrowDownToLine, CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect } from "react";
import { apiGet } from "@/lib/api";
import { logError } from "@/lib/log";

const INIT_ACT = [
  { name: "Seg", value: 0 }, { name: "Ter", value: 0 }, { name: "Qua", value: 0 },
  { name: "Qui", value: 0 }, { name: "Sex", value: 0 }, { name: "Sáb", value: 0 }, { name: "Dom", value: 0 },
];

const INIT_OPS = [
  { name: "Seg", criacoes: 0, edicoes: 0, exclusoes: 0 }, { name: "Ter", criacoes: 0, edicoes: 0, exclusoes: 0 },
  { name: "Qua", criacoes: 0, edicoes: 0, exclusoes: 0 }, { name: "Qui", criacoes: 0, edicoes: 0, exclusoes: 0 },
  { name: "Sex", criacoes: 0, edicoes: 0, exclusoes: 0 }, { name: "Sáb", criacoes: 0, edicoes: 0, exclusoes: 0 },
  { name: "Dom", criacoes: 0, edicoes: 0, exclusoes: 0 },
];

type StockReport = { esgotado: number; critico: number; baixo: number; normal: number };

export function CatalogAnalytics() {
  const [act, setAct] = useState(INIT_ACT);
  const [ops, setOps] = useState(INIT_OPS);
  const [stock, setStock] = useState<StockReport>({ esgotado: 0, critico: 0, baixo: 0, normal: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<any>("/api/analytics/catalog")
      .then((r) => {
        if (r.activity) setAct(r.activity);
        if (r.operations) setOps(r.operations);
        if (r.stock) setStock(r.stock);
      })
      .catch(logError("CatalogAnalytics"))
      .finally(() => setLoading(false));
  }, []);

  const hasData = act.some(d => d.value > 0);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 bg-glass border-border/50 shadow-soft">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" /> Atividade (7 Dias)
            </h4>
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[0.65rem] px-2 py-0.5">Ao Vivo</Badge>
          </div>
          <div className="h-[250px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={act} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} opacity={0.5} />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'hsl(var(--muted)/0.3)' }} contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))', borderRadius: '12px', fontSize: '12px' }} />
                <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} barSize={32} />
              </BarChart>
            </ResponsiveContainer>
            {!hasData && !loading && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <span className="bg-background/80 px-4 py-1.5 rounded-full text-xs font-medium text-muted-foreground border border-border/50 backdrop-blur-sm">Aguardando novos dados...</span>
              </div>
            )}
          </div>
        </Card>

        <Card className="p-6 bg-glass border-border/50 shadow-soft">
          <div className="flex items-center justify-between mb-6">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <PackageX className="h-4 w-4 text-sky-500" /> Top Produtos (30 Dias)
            </h4>
            {/* FIX #7: sem endpoint de top-products; reusava `act` só como fundo borrado.
                Marcado "Em breve" pra não parecer gráfico real vazio. */}
            <Badge variant="outline" className="text-[8px] h-4 bg-background border-amber-500/30 text-amber-500">Em breve</Badge>
          </div>
          <div className="h-[250px] w-full flex items-center justify-center flex-col text-muted-foreground relative">
             <ResponsiveContainer width="100%" height="100%" className="absolute inset-0 opacity-20">
              <BarChart data={act} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
              </BarChart>
            </ResponsiveContainer>
            {!hasData && !loading && (
              <>
                <div className="bg-muted/30 p-2 rounded-lg mb-2 z-10"><PackageX className="h-6 w-6 opacity-50" /></div>
                <span className="text-xs font-medium bg-background px-3 py-1 rounded-full border border-border/50 z-10 shadow-sm">Sem dados</span>
              </>
            )}
          </div>
        </Card>
      </div>

      <Card className="p-6 bg-glass border-border/50 shadow-soft">
        <div className="flex items-center justify-between mb-6">
          <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Breakdown de Operações</h4>
          <div className="flex items-center gap-4 text-[0.65rem] font-bold">
             <div className="flex items-center gap-1.5"><div className="w-4 h-1.5 rounded-full bg-emerald-500"></div> Criações</div>
             <div className="flex items-center gap-1.5"><div className="w-4 h-1.5 rounded-full bg-sky-500"></div> Edições</div>
             <div className="flex items-center gap-1.5"><div className="w-4 h-1.5 rounded-full bg-destructive"></div> Exclusões</div>
          </div>
        </div>
        <div className="h-[250px] w-full relative">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={ops} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} opacity={0.5} />
              <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))', borderRadius: '12px', fontSize: '12px' }} />
              <Area type="monotone" dataKey="criacoes" stroke="#10b981" fill="url(#colorCria)" strokeWidth={2} />
              <Area type="monotone" dataKey="edicoes" stroke="#0ea5e9" fill="url(#colorEdi)" strokeWidth={2} />
              <Area type="monotone" dataKey="exclusoes" stroke="#ef4444" fill="url(#colorExc)" strokeWidth={2} />
              <defs>
                <linearGradient id="colorCria" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/><stop offset="95%" stopColor="#10b981" stopOpacity={0}/></linearGradient>
                <linearGradient id="colorEdi" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/><stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/></linearGradient>
                <linearGradient id="colorExc" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/><stop offset="95%" stopColor="#ef4444" stopOpacity={0}/></linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="p-6 bg-glass border-border/50 shadow-soft">
         <div className="flex items-center justify-between mb-6">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Relatório de Estoque</h4>
            <span className="text-[0.65rem] text-muted-foreground hover:text-foreground cursor-pointer transition-colors">↻ Atualizar</span>
         </div>
         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-4 flex flex-col items-center justify-center text-center">
               <span className="text-3xl font-black text-destructive mb-1">{stock.esgotado}</span>
               <span className="text-[0.6rem] font-bold text-destructive uppercase tracking-widest flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> Esgotado</span>
            </div>
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex flex-col items-center justify-center text-center">
               <span className="text-3xl font-black text-amber-500 mb-1">{stock.critico}</span>
               <span className="text-[0.6rem] font-bold text-amber-500 uppercase tracking-widest flex items-center gap-1"><ArrowDownToLine className="h-3 w-3" /> Crítico</span>
            </div>
            <div className="bg-sky-500/10 border border-sky-500/20 rounded-xl p-4 flex flex-col items-center justify-center text-center">
               <span className="text-3xl font-black text-sky-500 mb-1">{stock.baixo}</span>
               <span className="text-[0.6rem] font-bold text-sky-500 uppercase tracking-widest">Baixo</span>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 flex flex-col items-center justify-center text-center">
               <span className="text-3xl font-black text-emerald-500 mb-1">{stock.normal}</span>
               <span className="text-[0.6rem] font-bold text-emerald-500 uppercase tracking-widest flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> Normal</span>
            </div>
         </div>
      </Card>
    </div>
  );
}
