import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Field, ToggleField } from "@/components/ui/field";
import {
  getAuditLog,
  setup2FA,
  enable2FA,
  disable2FA,
  getLoginSessions,
  revokeSession,
  revokeAllSessions,
  getIPWhitelist,
  updateIPWhitelist,
  adminDisable2FA,
} from "@/services/security";
import { isPlatformAdmin } from "@/lib/auth";
import { logError } from "@/lib/log";
import { apiErrorBody, apiErrorStatus, apiErrorMessage } from "@/lib/api";

// Mensagem dos erros de ligar/desligar 2FA (o servidor manda "message"; sem ela, traduz o código).
const twoFAError = (e: unknown): string => {
  const body = apiErrorBody(e);
  if (typeof body?.message === "string" && body.message.trim()) return body.message;
  if (body?.error === "password_required") return "Digite a sua senha atual.";
  if (body?.error === "invalid_password") return "Senha atual incorreta.";
  if (body?.error === "invalid_code") return "Código inválido. Confira o app autenticador.";
  if (apiErrorStatus(e) === 429) return "Muitas tentativas. Aguarde alguns minutos e tente de novo.";
  return "Não consegui concluir agora. Tente de novo.";
};
import type { AuditEntry, LoginSession, TwoFASetup } from "@/types/security";
import type { IPWhitelistConfig } from "@/types/settings";

export function SecuritySettings() {
  // 2FA state
  const [twoFA, setTwoFA] = useState<TwoFASetup | null>(null);
  const [code, setCode] = useState("");
  // Senha atual: o servidor exige para ligar ou desligar o 2FA.
  const [enablePass, setEnablePass] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [disablePass, setDisablePass] = useState("");
  const [busy2FA, setBusy2FA] = useState(false);

  // Sessions state
  const [sessions, setSessions] = useState<LoginSession[]>([]);

  // IP Whitelist state
  const [ipCfg, setIpCfg] = useState<IPWhitelistConfig>({ enabled: false, ips: [] });
  const [newIp, setNewIp] = useState("");
  // Servidor recusou a lista porque o IP atual ficaria de fora (400 current_ip_not_in_list).
  const [ipBlock, setIpBlock] = useState<{ message: string; ip: string; attempted: IPWhitelistConfig } | null>(null);
  const [savingIp, setSavingIp] = useState(false);

  // Admin da plataforma: desligar o 2FA de uma conta.
  const [adminEmail, setAdminEmail] = useState("");
  const [adminBusy, setAdminBusy] = useState(false);

  // Audit log state
  const [audit, setAudit] = useState<AuditEntry[]>([]);

  useEffect(() => {
    getLoginSessions().then((r) => setSessions(r.sessions || [])).catch(logError("getLoginSessions"));
    getIPWhitelist().then((r) => setIpCfg(r || { enabled: false, ips: [] })).catch(logError("getIPWhitelist"));
    getAuditLog(20, 0).then((r) => setAudit(r.entries || [])).catch(logError("getAuditLog"));
  }, []);

  // 2FA handlers
  const handleSetup2FA = async () => {
    try {
      const res = await setup2FA();
      setTwoFA(res);
    } catch (e) { toast.error((e as Error).message); }
  };

  const handleEnable2FA = async () => {
    setBusy2FA(true);
    try {
      await enable2FA(twoFA!.secret, code, enablePass);
      toast.success("2FA ativado com sucesso");
      setTwoFA(null);
      setCode("");
      setEnablePass("");
    } catch (e) {
      toast.error("Não consegui ativar o 2FA", { description: twoFAError(e) });
    } finally {
      setBusy2FA(false);
    }
  };

  const handleDisable2FA = async () => {
    setBusy2FA(true);
    try {
      await disable2FA(disableCode, disablePass);
      toast.success("2FA desativado");
      setDisableCode("");
      setDisablePass("");
    } catch (e) {
      toast.error("Não consegui desativar o 2FA", { description: twoFAError(e) });
    } finally {
      setBusy2FA(false);
    }
  };

  // Sessions handlers
  const handleRevoke = async (id: string) => {
    try {
      await revokeSession(id);
      setSessions((s) => s.filter((x) => x.id !== id));
      toast.success("Sessão revogada");
    } catch (e) { toast.error((e as Error).message); }
  };

  const handleRevokeAll = async () => {
    try {
      await revokeAllSessions(true);
      const r = await getLoginSessions();
      setSessions(r.sessions);
      toast.success("Todas as outras sessões revogadas");
    } catch (e) { toast.error((e as Error).message); }
  };

  // IP Whitelist handlers — a tela só muda depois que o servidor aceita (antes mudava na hora
  // e, se o servidor recusasse, mostrava uma lista que não estava valendo).
  const saveIpCfg = async (updated: IPWhitelistConfig, okMsg: string): Promise<boolean> => {
    setSavingIp(true);
    try {
      await updateIPWhitelist(updated);
      setIpCfg(updated);
      setIpBlock(null);
      toast.success(okMsg);
      return true;
    } catch (e) {
      const body = apiErrorBody(e);
      if (body?.error === "current_ip_not_in_list") {
        setIpBlock({
          message: typeof body.message === "string" && body.message ? body.message : "Sua conexão atual precisa estar na lista, senão você perde o acesso.",
          ip: typeof body.ip === "string" ? body.ip : "",
          attempted: updated,
        });
      } else {
        toast.error("Não consegui salvar a lista de IPs", { description: apiErrorMessage(e, "Tente de novo em instantes.") });
      }
      return false;
    } finally {
      setSavingIp(false);
    }
  };

  const addIp = async () => {
    const ip = newIp.trim();
    if (!ip) return;
    if (await saveIpCfg({ ...ipCfg, ips: [...(ipCfg.ips || []), ip] }, "IP adicionado")) setNewIp("");
  };

  const removeIp = (ip: string) => {
    saveIpCfg({ ...ipCfg, ips: (ipCfg.ips || []).filter((i) => i !== ip) }, "IP removido");
  };

  const toggleWhitelist = (enabled: boolean) => {
    saveIpCfg({ ...ipCfg, enabled }, enabled ? "Whitelist de IP ativada" : "Whitelist de IP desativada");
  };

  // "Adicionar meu IP (x)": repete o que a pessoa tentou salvar, com o IP atual incluído.
  const addMyIp = () => {
    if (!ipBlock?.ip) return;
    const a = ipBlock.attempted;
    const ips = (a.ips || []).includes(ipBlock.ip) ? a.ips : [...(a.ips || []), ipBlock.ip];
    saveIpCfg({ ...a, ips }, `Seu IP (${ipBlock.ip}) foi adicionado e a lista foi salva`);
  };

  // Admin da plataforma: desliga o 2FA de uma conta (com confirmação).
  const handleAdminDisable2FA = async () => {
    const email = adminEmail.trim();
    if (!email.includes("@")) {
      toast.error("Digite o e-mail da conta.");
      return;
    }
    if (!window.confirm(`Desligar a verificação em duas etapas da conta ${email}? O dono da conta será avisado.`)) return;
    setAdminBusy(true);
    try {
      const r = await adminDisable2FA(email);
      toast.success(`2FA desligado na conta ${r.email || email}.`);
      setAdminEmail("");
    } catch (e) {
      toast.error("Não consegui desligar o 2FA", { description: apiErrorMessage(e, "Tente de novo em instantes.") });
    } finally {
      setAdminBusy(false);
    }
  };

  return (
    <Card className="mt-4 bg-glass border-border/50 shadow-soft overflow-hidden">
      <Tabs defaultValue="2fa">
        <div className="border-b border-border/50 bg-muted/20 px-4 py-3">
          <TabsList className="bg-transparent space-x-2">
            <TabsTrigger value="2fa" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary rounded-lg">2FA</TabsTrigger>
            <TabsTrigger value="sessions" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary rounded-lg">Sessões Ativas</TabsTrigger>
            <TabsTrigger value="whitelist" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary rounded-lg">Whitelist IP</TabsTrigger>
            <TabsTrigger value="audit" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary rounded-lg">Audit Log</TabsTrigger>
          </TabsList>
        </div>

        <div className="p-6">
          <TabsContent value="2fa" className="space-y-4 m-0">
            {!twoFA ? (
              <Field label="Configurar 2FA" hint="Gera um codigo QR para usar com app autenticador (Google Authenticator, Authy, etc). Exige o codigo de 6 digitos alem da senha no login.">
                <Button onClick={handleSetup2FA} className="rounded-xl shadow-glow bg-emerald-500 hover:bg-emerald-600 text-white border-0">Configurar 2FA</Button>
              </Field>
            ) : (
              <div className="space-y-3 bg-muted/20 p-4 rounded-xl border border-border/50">
                <Field label="URI para app autenticador" hint="Escaneie este codigo com seu app autenticador (Google Authenticator, Authy).">
                  <code className="block break-all rounded-xl bg-background border border-border/50 p-3 text-sm font-mono text-primary">{twoFA.uri}</code>
                </Field>
                <Separator className="bg-border/50" />
                <Field label="Codigo de verificacao" hint="Digite o codigo de 6 digitos que aparece no seu app autenticador.">
                  <Input value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} placeholder="000000" maxLength={6} inputMode="numeric" autoComplete="one-time-code" className="rounded-xl max-w-[200px]" />
                </Field>
                <Field label="Sua senha atual" hint="Por segurança, confirme a senha da sua conta para ativar o 2FA.">
                  <Input type="password" value={enablePass} onChange={(e) => setEnablePass(e.target.value)} placeholder="Senha atual" autoComplete="current-password" className="rounded-xl max-w-[260px]" />
                </Field>
                <Button onClick={handleEnable2FA} disabled={busy2FA || code.length < 6 || !enablePass} className="rounded-xl">Ativar 2FA</Button>
              </div>
            )}
            <Separator className="bg-border/50" />
            <Field label="Desativar 2FA" hint="Remove a verificacao em dois passos. Depois do desativado, login usa apenas usuario e senha.">
              <div className="flex flex-wrap gap-2">
                <Input value={disableCode} onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ""))} placeholder="Código atual" maxLength={6} inputMode="numeric" autoComplete="one-time-code" className="rounded-xl max-w-[160px]" />
                <Input type="password" value={disablePass} onChange={(e) => setDisablePass(e.target.value)} placeholder="Senha atual" autoComplete="current-password" className="rounded-xl max-w-[200px]" aria-label="Senha atual" />
                <Button variant="destructive" onClick={handleDisable2FA} disabled={busy2FA || disableCode.length < 6 || !disablePass} className="rounded-xl">Desativar</Button>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">Para desativar, informe o código do app autenticador e a sua senha atual.</p>
            </Field>
            {isPlatformAdmin() && (
              <>
                <Separator className="bg-border/50" />
                <Field label="Administração: desligar o 2FA de uma conta" hint="Só para a administração da plataforma. Use quando o dono de uma conta perdeu o app autenticador. O dono é avisado.">
                  <div className="flex flex-wrap gap-2">
                    <Input type="email" value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} placeholder="email@da-conta.com" className="rounded-xl max-w-[280px]" aria-label="E-mail da conta" />
                    <Button variant="destructive" onClick={handleAdminDisable2FA} disabled={adminBusy || !adminEmail.trim()} className="rounded-xl">
                      Desligar 2FA da conta
                    </Button>
                  </div>
                </Field>
              </>
            )}
          </TabsContent>

          <TabsContent value="sessions" className="space-y-3 m-0">
            <Field label="Revogar todas" hint="Encerra todas as sessoes de login exceto a atual. Útil se suspeita que outra pessoa esta usando sua conta.">
              <Button variant="outline" onClick={handleRevokeAll} className="rounded-xl border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive">Revogar todas (exceto atual)</Button>
            </Field>
            <Separator className="bg-border/50" />
            <div className="grid gap-2">
              {sessions.map((s) => (
                <div key={s.id} className="flex items-center justify-between rounded-xl border border-border/50 p-4 bg-background/50 hover:bg-muted/20 transition-colors">
                  <div className="space-y-1 text-sm">
                    <p className="font-bold flex items-center gap-2">{s.ip} {s.is_current ? <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-600 border-emerald-500/30">Atual</Badge> : <Badge variant="outline" className="text-[10px] bg-primary/5 text-primary border-primary/20">Ativa</Badge>}</p>
                    <p className="text-muted-foreground text-xs">{s.user_agent}</p>
                    <p className="text-xs text-muted-foreground/70 font-mono">Último acesso: {new Date(s.last_active).toLocaleString("pt-BR")}</p>
                  </div>
                  {!s.is_current && <Button size="sm" variant="destructive" onClick={() => handleRevoke(s.id)} className="rounded-lg shadow-sm shrink-0">Revogar</Button>}
                </div>
              ))}
              {sessions.length === 0 && <p className="text-sm text-muted-foreground text-center py-4 bg-muted/10 rounded-xl border border-dashed">Nenhuma sessão encontrada.</p>}
            </div>
          </TabsContent>

          <TabsContent value="whitelist" className="space-y-4 m-0">
            {ipBlock && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm space-y-2" role="alert">
                <p className="text-amber-600 dark:text-amber-400">{ipBlock.message}</p>
                <div className="flex flex-wrap gap-2">
                  {ipBlock.ip && (
                    <Button size="sm" onClick={addMyIp} disabled={savingIp} className="rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white">
                      Adicionar meu IP ({ipBlock.ip})
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => setIpBlock(null)} className="rounded-lg">Fechar</Button>
                </div>
              </div>
            )}
            <ToggleField
              label="Whitelist de IP ativa"
              hint="Quando ativa, apenas os IPs listados abaixo podem acessar o painel. A sua conexão atual precisa estar na lista."
              checked={ipCfg.enabled}
              onChange={toggleWhitelist}
            />
            <div className="flex gap-2 items-end">
              <div className="flex-1 max-w-sm">
                <Field label="Adicionar IP" hint="Digite um endereco IP para liberar o acesso. Ex: 192.168.1.100">
                  <Input value={newIp} onChange={(e) => setNewIp(e.target.value)} placeholder="192.168.1.100" className="rounded-xl" />
                </Field>
              </div>
              <Button onClick={addIp} disabled={savingIp} className="rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white">Adicionar</Button>
            </div>
            <div className="flex flex-wrap gap-2 p-4 bg-muted/20 border border-border/50 rounded-xl">
              {(ipCfg.ips || []).map((ip) => (
                <Badge key={ip} variant="secondary" className="cursor-pointer bg-background border-border shadow-sm px-3 py-1 text-sm hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30 transition-colors" onClick={() => removeIp(ip)}>
                  {ip} <span className="ml-2 opacity-50">✕</span>
                </Badge>
              ))}
              {(!ipCfg.ips || ipCfg.ips.length === 0) && (
                <span className="text-xs text-muted-foreground">Nenhum IP cadastrado na whitelist.</span>
              )}
            </div>
          </TabsContent>

          <TabsContent value="audit" className="m-0">
            <div className="overflow-x-auto rounded-xl border border-border/50 bg-background/50">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/50 text-left text-muted-foreground bg-muted/30">
                    <th className="px-4 py-3 font-semibold text-xs uppercase tracking-wider">Ação</th>
                    <th className="px-4 py-3 font-semibold text-xs uppercase tracking-wider">Detalhe</th>
                    <th className="px-4 py-3 font-semibold text-xs uppercase tracking-wider">IP</th>
                    <th className="px-4 py-3 font-semibold text-xs uppercase tracking-wider">Data</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {audit.map((e) => (
                    <tr key={e.id} className="hover:bg-muted/10 transition-colors">
                      <td className="px-4 py-3 font-medium">{e.action}</td>
                      <td className="px-4 py-3 text-muted-foreground/80">{e.detail}</td>
                      <td className="px-4 py-3 font-mono text-xs">{e.ip}</td>
                      <td className="px-4 py-3 text-xs">{new Date(e.created_at).toLocaleString("pt-BR")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {audit.length === 0 && <p className="py-8 text-center text-muted-foreground">Nenhum registro de auditoria encontrado.</p>}
            </div>
          </TabsContent>
        </div>
      </Tabs>
    </Card>
  );
}
