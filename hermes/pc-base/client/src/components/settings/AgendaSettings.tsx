import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { CalendarX, XCircle, CalendarDays, Link } from "lucide-react";
import { apiGet, apiPut } from "@/lib/api";

type BlockedDate = { id: string; date_str: string; description?: string };

// A agenda guarda config como chave-valor JSON (/api/agenda/config/{key}).
// Usamos duas chaves: blocked_days (dias da semana) e blocked_dates (datas específicas).
export function AgendaSettings() {
  const [loading, setLoading] = useState(false);
  const [blockedDays, setBlockedDays] = useState<string[]>([]);
  const [blockedDates, setBlockedDates] = useState<BlockedDate[]>([]);
  const [newDate, setNewDate] = useState("");
  const [googleConnected, setGoogleConnected] = useState(false);

  // O GET devolve {key, value} onde value é o JSON salvo (ou null).
  const loadKey = async <T,>(key: string, fallback: T): Promise<T> => {
    try {
      const data = await apiGet<{ key: string; value: T | null }>(`/api/agenda/config/${key}`);
      return data?.value ?? fallback;
    } catch {
      return fallback;
    }
  };

  const loadSettings = async () => {
    const [days, dates, google] = await Promise.all([
      loadKey<string[]>("blocked_days", []),
      loadKey<string[]>("blocked_dates", []),
      loadKey<boolean>("google_connected", false),
    ]);
    setBlockedDays(days);
    setBlockedDates(dates.map((d) => ({ id: d, date_str: d })));
    setGoogleConnected(google);
  };

  useEffect(() => { loadSettings(); }, []);

  const toggleDay = (day: string) => {
    setBlockedDays(prev => prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]);
  };

  // PUT do array de datas na chave blocked_dates (o body inteiro é o value JSON).
  const persistDates = async (dates: string[]) => {
    await apiPut(`/api/agenda/config/blocked_dates`, dates);
  };

  const addDate = async () => {
    if (!newDate) return;
    if (blockedDates.some((d) => d.date_str === newDate)) {
      toast.info("Essa data já está bloqueada.");
      return;
    }
    try {
      setLoading(true);
      const next = [...blockedDates.map((d) => d.date_str), newDate];
      await persistDates(next);
      setBlockedDates(next.map((d) => ({ id: d, date_str: d })));
      setNewDate("");
      toast.success("Data bloqueada com sucesso!");
    } catch (e: any) {
      toast.error(e.message || "Erro ao bloquear data");
    } finally {
      setLoading(false);
    }
  };

  const removeDate = async (id: string) => {
    try {
      setLoading(true);
      const next = blockedDates.map((d) => d.date_str).filter((d) => d !== id);
      await persistDates(next);
      setBlockedDates(next.map((d) => ({ id: d, date_str: d })));
      toast.success("Data desbloqueada!");
    } catch (e: any) {
      toast.error(e.message || "Erro ao remover data");
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);
      await apiPut(`/api/agenda/config/blocked_days`, blockedDays);
      toast.success("Configurações da agenda salvas!");
    } catch (e: any) {
      toast.error(e.message || "Erro ao salvar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-6 bg-glass border-border/50 max-w-2xl mx-auto space-y-6">
      <div>
        <h3 className="text-lg font-bold flex items-center gap-2"><Link className="h-5 w-5 text-primary" /> Integração de Calendário</h3>
        <p className="text-sm text-muted-foreground mt-1">Conecte seu Google Calendar para sincronizar eventos em tempo real.</p>
        <div className="mt-4">
          {googleConnected ? (
            <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 py-1.5 px-3">Google Calendar Conectado ✓</Badge>
          ) : (
            <Button disabled variant="outline" className="gap-2 opacity-60 cursor-not-allowed">
              <CalendarDays className="h-4 w-4" /> Conectar Google Calendar (Em Breve)
            </Button>
          )}
        </div>
      </div>

      <div className="pt-6 border-t border-border/50">
        <h3 className="text-lg font-bold flex items-center gap-2"><CalendarX className="h-5 w-5 text-destructive" /> Exclusões e Limites</h3>
        <p className="text-sm text-muted-foreground mt-1">Configure os dias e horários em que a IA está proibida de agendar.</p>
      </div>
      
      <div className="space-y-3">
        <label className="text-sm font-medium">Dias da Semana Bloqueados</label>
        <div className="flex flex-wrap gap-2">
          {["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"].map(day => {
            const isBlocked = blockedDays.includes(day);
            return (
              <Badge 
                key={day} 
                variant="outline" 
                className={`cursor-pointer text-sm py-1.5 px-4 transition-colors ${isBlocked ? 'bg-destructive text-destructive-foreground border-destructive' : 'hover:bg-destructive/10 hover:text-destructive hover:border-destructive/50'}`}
                onClick={() => toggleDay(day)}
              >
                {day}
              </Badge>
            );
          })}
        </div>
      </div>

      <div className="space-y-3 pt-4 border-t border-border/50">
        <label className="text-sm font-medium">Datas Específicas Bloqueadas (Ex: Feriados)</label>
        <div className="flex gap-2">
          <Input type="date" className="w-auto h-10 bg-background/50" value={newDate} onChange={(e) => setNewDate(e.target.value)} />
          <Button variant="outline" className="h-10" onClick={addDate} disabled={loading || !newDate}>Adicionar Data</Button>
        </div>
        <div className="flex flex-wrap gap-2 pt-2">
          {blockedDates.length === 0 && <span className="text-xs text-muted-foreground">Nenhuma data específica bloqueada.</span>}
          {blockedDates.map(d => (
            <Badge key={d.id} variant="secondary" className="pl-3 pr-2 py-1 flex items-center gap-1 bg-destructive/10 text-destructive border-destructive/20">
              {d.date_str} <button onClick={() => removeDate(d.id)}><XCircle className="h-3 w-3" /></button>
            </Badge>
          ))}
        </div>
      </div>

      <div className="pt-6 flex justify-end">
         <Button onClick={saveSettings} disabled={loading} className="bg-primary text-primary-foreground shadow-glow">Salvar Alterações</Button>
      </div>
    </Card>
  );
}
