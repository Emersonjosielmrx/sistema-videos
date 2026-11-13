import { Tabs, TabsContent, TabsList } from "@/components/ui/tabs";
import { HideableTab } from "@/components/ui/HideableTab";
import { SecuritySettings } from "@/components/settings/SecuritySettings";
import { AccessListSettings } from "@/components/settings/AccessListSettings";
import { ScheduleSettings } from "@/components/settings/ScheduleSettings";
import { RateLimitSettings } from "@/components/settings/RateLimitSettings";
import { useEffect, useState } from "react";
import { getSchedule, getRateLimit, getIPWhitelist } from "@/services/security";
import type { ScheduleConfig, RateLimitConfig, IPWhitelistConfig } from "@/types/settings";
import { logError } from "@/lib/log";

export function SecurityPage() {
  const [schedule, setSchedule] = useState<ScheduleConfig | null>(null);
  const [scheduleErr, setScheduleErr] = useState(false);
  const [rateLimit, setRateLimit] = useState<RateLimitConfig | null>(null);
  const [ipwl, setIpwl] = useState<IPWhitelistConfig | null>(null);

  const load = () => {
    setScheduleErr(false);
    getSchedule().then(setSchedule).catch((e) => { setScheduleErr(true); logError("getSchedule")(e); });
    getRateLimit().then(setRateLimit).catch(logError("getRateLimit"));
    getIPWhitelist().then(setIpwl).catch(logError("getIPWhitelist"));
  };

  useEffect(() => { load(); }, []);

  const ipActive = !!ipwl?.enabled && (ipwl?.ips?.length ?? 0) > 0;

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
         <h2 className="text-xl font-semibold">Segurança & Controle</h2>
         <div className="flex gap-2">
            <div className={`px-3 py-1 text-xs font-bold rounded-lg flex items-center gap-2 border ${ipActive ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" : "bg-muted/50 border-border/50 text-muted-foreground"}`}>
               IP Whitelisting: {ipActive ? "ATIVO" : "INATIVO"}
            </div>
         </div>
      </div>
      <Tabs defaultValue="security" className="w-full">
        <TabsList className="bg-muted/50 p-1 rounded-xl inline-flex flex-wrap w-fit gap-1 mb-4">
          <HideableTab value="security" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2">2FA & Sessões</HideableTab>
          <HideableTab value="access" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2">Lista de Acesso</HideableTab>
          <HideableTab value="schedule" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2">Horário Comercial</HideableTab>
          <HideableTab value="ratelimit" className="rounded-lg font-semibold data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm px-4 py-2">Rate Limit</HideableTab>
        </TabsList>
        <TabsContent value="security">
          <SecuritySettings />
        </TabsContent>
        <TabsContent value="access">
          <AccessListSettings />
        </TabsContent>
        <TabsContent value="schedule">
          {schedule ? (
            <ScheduleSettings key={JSON.stringify(schedule)} initial={schedule} onSaved={load} />
          ) : (
            <p className="text-sm text-muted-foreground p-4">
              {scheduleErr ? "Não consegui carregar o horário comercial. Recarregue a página para tentar de novo." : "Carregando…"}
            </p>
          )}
        </TabsContent>
        <TabsContent value="ratelimit">
          {rateLimit && <RateLimitSettings initial={rateLimit} onSaved={load} />}
        </TabsContent>
      </Tabs>
    </div>
  );
}
