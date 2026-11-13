import { useEffect, useState } from "react";
import { Plug, Save, KeyRound } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { apiGet, apiPost } from "@/lib/api";

export function N8nSettings() {
  const [loading, setLoading] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    apiGet<{ url: string; token: string; has_token: boolean }>("/api/n8n")
      .then((c) => {
        setWebhookUrl(c.url || "");
        setApiKey(c.token || ""); // vem mascarado (***abcd) se já salvo
        setHasToken(c.has_token);
      })
      .catch(() => {
        /* sem config ainda: mantém vazio */
      });
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      // Se o usuário não mexeu no token (ainda mascarado), manda vazio p/ o backend preservar.
      const token = hasToken && apiKey.startsWith("***") ? "" : apiKey;
      await apiPost("/api/n8n", { url: webhookUrl, token, behavior: "" });
      toast.success("Configurações do n8n salvas com sucesso!");
    } catch {
      toast.error("Falha ao salvar configurações do n8n.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-border/50 shadow-soft bg-glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <Plug className="h-6 w-6 text-primary" />
          Integração Nativa n8n
          <Badge variant="outline" className="ml-2 text-xs text-emerald-400 border-emerald-400/30">/api/n8n</Badge>
        </CardTitle>
        <CardDescription>
          Configure o endpoint do seu servidor n8n para enviar e receber eventos do Hermes Call.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
           {/* Monitor visual — reflete o estado REAL da config (não inventa ping/workflows) */}
           <div className="bg-background/50 border border-border/50 rounded-xl p-4 flex flex-col justify-center items-center text-center space-y-2">
              <div className="relative">
                 <div className={`w-12 h-12 rounded-full flex items-center justify-center ${webhookUrl ? "bg-emerald-500/20" : "bg-muted"}`}>
                    <Plug className={`w-6 h-6 ${webhookUrl ? "text-emerald-500" : "text-muted-foreground"}`} />
                 </div>
                 {webhookUrl && <div className="absolute top-0 right-0 w-3 h-3 bg-emerald-500 rounded-full border-2 border-background animate-pulse"></div>}
              </div>
              <div>
                 <h4 className="font-bold text-sm">{webhookUrl ? "Endpoint Configurado" : "Não Configurado"}</h4>
                 <p className="text-xs text-muted-foreground truncate max-w-[200px]">{webhookUrl || "Informe a Webhook URL abaixo"}</p>
              </div>
           </div>

           {/* Blueprint Deployer — abre a doc/loja do n8n (deploy automático via API ainda não disponível) */}
           <div className="bg-background/50 border border-border/50 rounded-xl p-4 space-y-3 flex flex-col justify-between">
              <div>
                 <h4 className="font-bold text-sm text-sky-500">Loja de Blueprints (n8n)</h4>
                 <p className="text-xs text-muted-foreground mt-1">Fluxos prontos pra importar no seu n8n.</p>
              </div>
              <Button
                size="sm" variant="outline"
                className="w-full gap-2 border-sky-500/30 hover:bg-sky-500/10 text-sky-500"
                onClick={() => window.open("https://n8n.io/workflows/", "_blank")}
              >
                 Ver Blueprints no n8n.io
              </Button>
           </div>
        </div>

        <div className="grid gap-2 border-t border-border/50 pt-6">
          <Label htmlFor="webhookUrl">Webhook URL (n8n)</Label>
          <Input 
            id="webhookUrl" 
            placeholder="https://n8n.suaempresa.com/webhook/..." 
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">O endereço principal para onde enviaremos eventos de transbordo e logs.</p>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="apiKey">Chave de API / Header Token</Label>
          <div className="relative">
            <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input 
              id="apiKey" 
              type="password"
              placeholder="Sua chave de segurança" 
              className="pl-9"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
          <p className="text-xs text-muted-foreground">Utilizado no header Authorization (Bearer) ao chamar seu webhook.</p>
        </div>

        <div className="pt-4 border-t border-border/50">
          <Button onClick={handleSave} disabled={loading} className="w-full sm:w-auto bg-primary text-primary-foreground shadow-glow">
            {loading ? "Salvando..." : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Salvar Configurações n8n
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
