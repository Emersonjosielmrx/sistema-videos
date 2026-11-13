import { useState, useEffect, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { Save, ShieldAlert, KeyRound, Bell, UserCircle, ShieldCheck, Settings, MonitorSmartphone, Palette, Mic, Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";
import { apiGet, apiPut } from "@/lib/api";
import { toast } from "sonner";
import { logError } from "@/lib/log";

type Prefs = {
  timezone: string;
  language: string;
  alert_webhook_fail: boolean;
  weekly_token_report: boolean;
  whatsapp_marketing: boolean;
};


// O "extra" do perfil vem como texto JSON de um objeto; perfis salvos antes da correção de 04/10
// vinham com o texto embrulhado de novo. Sempre devolve um objeto (nunca quebra o salvar).
const parseExtra = (v: unknown): Record<string, any> => {
  let x: unknown = v;
  for (let i = 0; i < 3 && typeof x === "string"; i++) {
    try { x = JSON.parse(x); } catch { return {}; }
  }
  return x && typeof x === "object" && !Array.isArray(x) ? (x as Record<string, any>) : {};
};

export const ProfilePage = ({ inSettings = false }: { inSettings?: boolean }) => {
  const [activeTab, setActiveTab] = useState("identidade");
  const [prefs, setPrefs] = useState<Prefs>({
    timezone: "America/Sao_Paulo", language: "pt-BR",
    alert_webhook_fail: true, weekly_token_report: false, whatsapp_marketing: true,
  });
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [savingIdentity, setSavingIdentity] = useState(false);
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    apiGet<{ extra?: string, email?: string, store_name?: string, logo_url?: string }>("/api/profile").then((p) => {
      if (p.email) setEmail(p.email);
      if (p.store_name) setName(p.store_name);
      if (p.logo_url) setAvatarUrl(p.logo_url);
      const ex = parseExtra(p.extra);
      if (ex.prefs) setPrefs((cur) => ({ ...cur, ...ex.prefs }));
      if (ex.role) setRole(ex.role);
    }).catch(logError("/api/profile"));

    // Busca o número realmente conectado no WhatsApp. Em erro/desconexão NÃO inventamos
    // número (antes um setTimeout fingia "Conectado", enganando o dono sobre o pareamento).
    apiGet<{ number?: string }>("/api/whatsapp/status").then(res => {
      if (res.number) setPhone(res.number);
    }).catch(logError("/api/whatsapp/status"));
  }, []);

  const savePrefs = async () => {
    setSavingPrefs(true);
    try {
      // Preserva o resto do extra (ex.: cnpj) e grava prefs dentro dele.
      const cur = await apiGet<{ extra?: string; store_name?: string; email?: string; address?: string; segment?: string }>("/api/profile").catch(() => ({} as any));
      const ex = parseExtra(cur.extra);
      ex.prefs = prefs;
      // Só o extra: o servidor mantém o resto (nome, foto, WhatsApp) como está.
      await apiPut("/api/profile", { extra: ex });
      toast.success("Preferências salvas!");
    } catch {
      toast.error("Falha ao salvar preferências.");
    } finally {
      setSavingPrefs(false);
    }
  };

  const saveIdentity = async () => {
    setSavingIdentity(true);
    try {
      const cur = await apiGet<{ extra?: string; address?: string; segment?: string }>("/api/profile").catch(() => ({} as any));
      const ex = parseExtra(cur.extra);
      ex.role = role;
      await apiPut("/api/profile", { store_name: name, email, logo_url: avatarUrl, extra: ex });
      toast.success("Identidade salva com sucesso!");
    } catch {
      toast.error("Falha ao salvar identidade.");
    } finally {
      setSavingIdentity(false);
    }
  };

  const changePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error("Preencha a senha atual e a nova senha.");
      return;
    }
    if (newPassword.length < 6) {
      toast.error("A nova senha deve ter pelo menos 6 caracteres.");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("A nova senha e a confirmação não coincidem.");
      return;
    }
    setChangingPassword(true);
    try {
      await apiPut("/api/auth/password", { current_password: currentPassword, new_password: newPassword });
      toast.success("Senha alterada com sucesso!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (e: any) {
      const msg = e?.message || e?.error || "Falha ao alterar senha.";
      toast.error(msg.includes("incorrect") ? "Senha atual incorreta." : msg);
    } finally {
      setChangingPassword(false);
    }
  };

  const handleAvatarSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      toast.error("Imagem muito grande (máx 2MB).");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setAvatarUrl(dataUrl);
      toast.success("Foto carregada! Clique em Salvar Identidade para aplicar.");
    };
    reader.readAsDataURL(file);
  };

  const passwordStrength = (pw: string) => {
    if (!pw) return { label: "", color: "" };
    if (pw.length < 6) return { label: "Muito Fraca", color: "text-red-500" };
    if (pw.length < 8) return { label: "Fraca", color: "text-orange-500" };
    const has = [/[a-z]/, /[A-Z]/, /[0-9]/, /[^a-zA-Z0-9]/].filter(r => r.test(pw)).length;
    if (has >= 4) return { label: "Forte", color: "text-emerald-500" };
    if (has >= 3) return { label: "Boa", color: "text-blue-500" };
    return { label: "Média", color: "text-yellow-500" };
  };

  return (
    <div className={cn("space-y-6 max-w-[1600px] mx-auto", !inSettings && "pb-10")}>
      
      {/* Header IAM Security Hub */}
      {!inSettings && (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/50 pb-4">
          <div className="flex items-center gap-3">
            <div className="bg-background p-2 rounded-xl border border-border/50 flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-primary" />
              <h2 className="text-sm font-bold tracking-tight">IAM SECURITY HUB</h2>
            </div>
          </div>
          <div className="flex items-center gap-4">
             <Bell className="h-4 w-4 text-muted-foreground" />
             <div className="flex flex-col bg-muted/30 px-3 py-1.5 rounded-full border border-border/50">
               <span className="text-xs font-semibold leading-tight">Emerson Joziel Cunha da silva</span>
               <span className="text-[10px] text-muted-foreground leading-tight">CEO / Especialista IA</span>
             </div>
          </div>
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-8">
        
        {/* Sidebar Vertical Tabs */}
        <div className="w-full md:w-64 shrink-0 space-y-6">
           <div className="flex flex-col space-y-1">
             <button 
                onClick={() => setActiveTab('identidade')}
                className={cn("flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors", activeTab === 'identidade' ? "bg-primary/10 text-primary border border-primary/20 shadow-soft" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground")}
             >
                <UserCircle className="h-5 w-5" /> Identidade & Avatar
             </button>
             <button 
                onClick={() => setActiveTab('sessoes')}
                className={cn("flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors", activeTab === 'sessoes' ? "bg-primary/10 text-primary border border-primary/20 shadow-soft" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground")}
             >
                <MonitorSmartphone className="h-5 w-5" /> Segurança & Sessões
             </button>
             <button 
                onClick={() => setActiveTab('preferencias')}
                className={cn("flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors", activeTab === 'preferencias' ? "bg-primary/10 text-primary border border-primary/20 shadow-soft" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground")}
             >
                <Settings className="h-5 w-5" /> Preferências Globais
             </button>
           </div>

           <div className="pt-8 border-t border-border/50">
             <button className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-destructive hover:bg-destructive/10 rounded-xl transition-colors w-full">
               <ShieldAlert className="h-5 w-5" /> Zona de Perigo
             </button>
           </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 max-w-4xl">
           
           {activeTab === 'identidade' && (
             <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
               <div>
                 <h2 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-emerald-400 drop-shadow-sm w-fit">Identidade Corporativa</h2>
                 <p className="text-muted-foreground text-sm mt-1">Configure os dados básicos de apresentação e comunicação com a central.</p>
               </div>

               <Card className="p-6 bg-glass border-border/50 shadow-soft flex items-center gap-6">
                 {avatarUrl ? (
                   <img src={avatarUrl} alt="Avatar" className="h-20 w-20 rounded-full object-cover shadow-glow shrink-0" />
                 ) : (
                   <div className="h-20 w-20 rounded-full bg-primary flex items-center justify-center text-3xl font-bold text-primary-foreground shadow-glow shrink-0">
                     {name ? name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() : "?"}
                   </div>
                 )}
                 <div>
                   <h3 className="font-bold">Foto do Perfil</h3>
                   <p className="text-xs text-muted-foreground mb-3">Recomendado: 500x500px, máx 2MB (PNG/JPG).</p>
                   <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={handleAvatarSelect} />
                   <Button variant="outline" className="h-8 text-xs gap-2 rounded-lg bg-background" onClick={() => fileInputRef.current?.click()}>
                     <Upload className="h-4 w-4" /> Carregar Nova Foto
                   </Button>
                 </div>
               </Card>

               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                 <Field label="Nome de Exibição Completo">
                   <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Seu nome" className="rounded-xl bg-background/50 border-border/50" />
                 </Field>
                 <Field label="E-mail de Cadastro (Verificado)">
                   <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="seu@email.com" className="rounded-xl bg-background/50 border-border/50" />
                 </Field>
                 <Field label="Telefone / WhatsApp (Vinculado Oficialmente)">
                   <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Nenhuma linha conectada" className="rounded-xl bg-emerald-500/5 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-medium" />
                 </Field>
                 <Field label="Cargo Institucional">
                   <Input value={role} onChange={(e) => setRole(e.target.value)} placeholder="Ex.: Proprietário" className="rounded-xl bg-background/50 border-border/50" />
                 </Field>
               </div>

               <Button onClick={saveIdentity} disabled={savingIdentity} className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow rounded-xl h-11 font-bold">
                  <Save className="h-4 w-4 mr-2" /> {savingIdentity ? "Salvando..." : "Salvar Identidade"}
               </Button>
             </div>
           )}

           {activeTab === 'sessoes' && (
             <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
               <div>
                 <h2 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-emerald-400 drop-shadow-sm w-fit">Escudo de Segurança & Controle de Acesso</h2>
                 <p className="text-muted-foreground text-sm mt-1">Altere sua senha de autenticação e revogue acesso de dispositivos desconhecidos.</p>
               </div>

               <Card className="p-8 bg-glass border-border/50 shadow-soft">
                  <h3 className="font-bold flex items-center gap-2 mb-6"><KeyRound className="h-5 w-5" /> Alterar Credencial Mestra</h3>
                  
                  <div className="space-y-4 mb-6">
                    <Field label="Senha Atual">
                      <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} placeholder="••••••••" className="rounded-xl bg-background/50 border-border/50" />
                    </Field>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Field label="Nova Senha Segura">
                        <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="••••••••" className="rounded-xl bg-background/50 border-border/50" />
                        {newPassword && <div className={cn("text-[10px] mt-1 text-right", passwordStrength(newPassword).color)}>{passwordStrength(newPassword).label}</div>}
                      </Field>
                      <Field label="Confirme a Nova Senha">
                        <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••" className="rounded-xl bg-background/50 border-border/50" />
                      </Field>
                    </div>
                  </div>

                  <Button onClick={changePassword} disabled={changingPassword} className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow rounded-xl h-11 font-bold">
                    <KeyRound className="h-4 w-4 mr-2" /> {changingPassword ? "Atualizando..." : "Atualizar Senha"}
                  </Button>
               </Card>

               <div>
                 <div className="flex items-center justify-between mb-4">
                   <h3 className="font-bold flex items-center gap-2"><MonitorSmartphone className="h-5 w-5" /> Instâncias Autenticadas (Sessões)</h3>
                 </div>

                 <div className="bg-glass rounded-xl border border-border/50 overflow-hidden">
                   <table className="w-full text-sm">
                     <thead className="bg-muted/50 text-muted-foreground border-b border-border/50 text-xs uppercase tracking-wider text-left">
                       <tr>
                         <th className="px-4 py-3 font-semibold">Dispositivo / OS</th>
                         <th className="px-4 py-3 font-semibold">Último Pulso</th>
                         <th className="px-4 py-3 font-semibold">Status</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-border/50">
                       <tr className="bg-background/30">
                         <td className="px-4 py-4 flex items-center gap-2">
                           <MonitorSmartphone className="h-4 w-4 text-muted-foreground" />
                           <span className="font-medium">{navigator.userAgent.includes("Mobile") ? "Mobile" : "Desktop"} — {navigator.userAgent.match(/Chrome|Firefox|Safari|Edge/)?.[0] || "Browser"}</span>
                         </td>
                         <td className="px-4 py-4 text-muted-foreground">{new Date().toLocaleString("pt-BR")}</td>
                         <td className="px-4 py-4">
                           <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[0.65rem]">Sessão Atual</Badge>
                         </td>
                       </tr>
                     </tbody>
                   </table>
                 </div>
                 <p className="text-xs text-muted-foreground mt-3">Apenas a sessão atual é exibida. Para revogar acessos de outros dispositivos, altere sua senha.</p>
               </div>
             </div>
           )}

           {activeTab === 'preferencias' && (
             <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
               <div>
                 <h2 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-emerald-400 drop-shadow-sm w-fit">Sintonia & Preferências Globais</h2>
                 <p className="text-muted-foreground text-sm mt-1">Personalize os eventos que disparam alertas na central.</p>
               </div>

               <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-6 border-b border-border/50">
                 <Field label="Fuso Horário Global">
                   <select
                     value={prefs.timezone}
                     onChange={(e) => setPrefs({ ...prefs, timezone: e.target.value })}
                     className="flex h-10 w-full rounded-xl border border-border/50 bg-background/50 px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring appearance-none">
                     <option value="America/Sao_Paulo">America/Sao_Paulo (BRT)</option>
                     <option value="America/Manaus">America/Manaus (AMT)</option>
                     <option value="America/Bahia">America/Bahia (BRT)</option>
                     <option value="America/Fortaleza">America/Fortaleza (BRT)</option>
                   </select>
                 </Field>
                 <Field label="Idioma da Inteligência (Dashboard)">
                   <select
                     value={prefs.language}
                     onChange={(e) => setPrefs({ ...prefs, language: e.target.value })}
                     className="flex h-10 w-full rounded-xl border border-border/50 bg-background/50 px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring appearance-none">
                     <option value="pt-BR">Português (Brasil)</option>
                     <option value="en">English</option>
                     <option value="es">Español</option>
                   </select>
                 </Field>
               </div>

               <div>
                 <h3 className="font-bold mb-4">Comunicações do Sistema</h3>
                 <div className="space-y-4">
                   <div className="flex items-center justify-between p-4 bg-glass border border-border/50 rounded-xl">
                     <div>
                       <h4 className="font-semibold text-sm">Alertas Críticos da IA (Falha de Webhook)</h4>
                       <p className="text-xs text-muted-foreground mt-0.5">Receber e-mail imediato se a inteligência parar.</p>
                     </div>
                     <Switch checked={prefs.alert_webhook_fail} onCheckedChange={(v) => setPrefs({ ...prefs, alert_webhook_fail: v })} />
                   </div>

                   <div className="flex items-center justify-between p-4 bg-glass border border-border/50 rounded-xl">
                     <div>
                       <h4 className="font-semibold text-sm">Relatórios Semanais de Consumo de Tokens</h4>
                       <p className="text-xs text-muted-foreground mt-0.5">Um extrato detalhado dos custos de requisição via e-mail.</p>
                     </div>
                     <Switch checked={prefs.weekly_token_report} onCheckedChange={(v) => setPrefs({ ...prefs, weekly_token_report: v })} />
                   </div>

                   <div className="flex items-center justify-between p-4 bg-glass border border-border/50 rounded-xl">
                     <div>
                       <h4 className="font-semibold text-sm">WhatsApp Marketing (Inovare AI)</h4>
                       <p className="text-xs text-muted-foreground mt-0.5">Receber novidades sobre novos modelos de IA no seu WhatsApp.</p>
                     </div>
                     <Switch checked={prefs.whatsapp_marketing} onCheckedChange={(v) => setPrefs({ ...prefs, whatsapp_marketing: v })} />
                   </div>
                 </div>
                 <div className="flex justify-end mt-6">
                   <Button onClick={savePrefs} disabled={savingPrefs} className="gap-2 shadow-glow">
                     <Save className="h-4 w-4" /> {savingPrefs ? "Salvando..." : "Salvar Preferências"}
                   </Button>
                 </div>
               </div>
             </div>
           )}
        </div>
      </div>
      
      {/* Action Buttons Float */}
      <div className="fixed bottom-6 right-6 flex flex-col gap-2 pointer-events-auto z-50">
        <Button size="icon" className="h-12 w-12 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white shadow-glow border-none">
          <Mic className="h-5 w-5" />
        </Button>
        <Button size="icon" className="h-12 w-12 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow border-none">
          <Palette className="h-5 w-5" />
        </Button>
      </div>

    </div>
  );
};
