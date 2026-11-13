import { useState, useEffect, useCallback } from "react";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import { testAIKey } from "@/services/aimodels";
import { Plus, Trash2, KeyRound, AlertTriangle, CheckCircle2, Search, Link2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Select } from "@/components/ui/select";

// OpenRouter: vira uma credencial "custom" com este endereço. Todas as chaves com o
// mesmo endereço entram no rodízio automático do servidor (pool).
const OPENROUTER_BASE = "https://openrouter.ai/api/v1";

// parseBulkKeys lê a caixa "várias de uma vez": uma chave por linha, opcionalmente com
// um nome antes ("Conta Maria sk-or-..."). A chave é a última palavra da linha.
function parseBulkKeys(text: string): { name: string; key: string }[] {
  const seen = new Set<string>();
  const out: { name: string; key: string }[] = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const parts = line.split(/[\s;,|]+/).filter(Boolean);
    const key = parts.pop() || "";
    if (key.length < 8 || seen.has(key)) continue;
    seen.add(key);
    out.push({ name: parts.join(" ").replace(/[:=-]+$/, "").trim(), key });
  }
  return out;
}

interface AICredential {
  id: string;
  name: string;
  provider: string;
  baseUrl?: string;
  masked_key: string;
  created_at: string;
  status: "active" | "error";
  failsThisWeek?: number;
  last_error_reason?: string;
}

export function AICredentialsSettings() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [search, setSearch] = useState("");

  const [credentials, setCredentials] = useState<AICredential[]>([]);
  const [loading, setLoading] = useState(true);

  // Carrega o cofre do backend (GET /api/settings/ai/credentials — shape com
  // masked_key/status/failsThisWeek). Substitui o mock antigo.
  const loadCredentials = useCallback(async () => {
    try {
      const data = await apiGet<AICredential[]>("/api/settings/ai/credentials");
      setCredentials(Array.isArray(data) ? data : []);
    } catch {
      // silencioso: sem credencial ainda ou backend indisponível → lista vazia
      setCredentials([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadCredentials(); }, [loadCredentials]);

  const [newName, setNewName] = useState("");
  const [newProvider, setNewProvider] = useState("openai");
  const [newBaseUrl, setNewBaseUrl] = useState("");
  const [newApiKey, setNewApiKey] = useState("");
  const [bulkMode, setBulkMode] = useState(false);
  const [bulkText, setBulkText] = useState("");
  const [saving, setSaving] = useState(false);

  // "openrouter" é um atalho da tela: salva como provedor "custom" com o endereço dele.
  const effProvider = newProvider === "openrouter" ? "custom" : newProvider;
  const effBaseUrl = newProvider === "openrouter" ? OPENROUTER_BASE : newBaseUrl.trim();
  const isProxy = newProvider === "webshare";
  const isChatProvider = newProvider !== "elevenlabs" && newProvider !== "meta" && !isProxy;
  const credType = newProvider === "elevenlabs" ? "tts" : newProvider === "meta" ? "social" : isProxy ? "proxy" : "llm";
  const canBulk = isChatProvider || isProxy;
  const bulkItems = bulkMode ? parseBulkKeys(bulkText) : [];

  // Várias chaves de uma vez: testa e salva uma por uma; as recusadas ficam na caixa.
  const handleBulkSave = async () => {
    if (bulkItems.length === 0) {
      toast.error("Cole pelo menos uma chave (uma por linha).");
      return;
    }
    setSaving(true);
    const used = new Set(credentials.map((c) => c.name.toLowerCase()));
    const prefix = newName.trim() || getProviderLabel(newProvider);
    let n = 0;
    const nextName = () => {
      let name = "";
      do { n++; name = `${prefix} ${n}`; } while (used.has(name.toLowerCase()));
      return name;
    };
    let ok = 0;
    const fails: { line: string; why: string }[] = [];
    for (let i = 0; i < bulkItems.length; i++) {
      const it = bulkItems[i];
      const name = it.name && !used.has(it.name.toLowerCase()) ? it.name : nextName();
      used.add(name.toLowerCase());
      toast.loading(`Testando chave ${i + 1} de ${bulkItems.length}...`, { id: "cred-bulk" });
      try {
        if (isChatProvider) {
          const res = await testAIKey(effProvider, it.key, effBaseUrl);
          if (!res.ok) {
            fails.push({ line: (it.name ? it.name + " " : "") + it.key, why: `${name}: ${res.hint || res.error || "recusada"}` });
            continue;
          }
        }
        await apiPost("/api/credentials", { name, type: credType, provider: effProvider, api_key: it.key, base_url: effBaseUrl });
        ok++;
      } catch {
        fails.push({ line: (it.name ? it.name + " " : "") + it.key, why: `${name}: falha ao salvar` });
      }
    }
    toast.dismiss("cred-bulk");
    await loadCredentials();
    setSaving(false);
    if (fails.length === 0) {
      toast.success(isProxy
        ? `${ok} ${ok === 1 ? "proxy salvo" : "proxies salvos"}. A ordem de cadastro é a prioridade.`
        : `${ok} ${ok === 1 ? "chave validada e salva" : "chaves validadas e salvas"}. Elas entram no rodízio automático.`);
      handleCloseDialog();
      return;
    }
    // Deixa na caixa só as que falharam, pra corrigir e tentar de novo.
    setBulkText(fails.map((f) => f.line).join("\n"));
    toast.error(`${ok} salvas, ${fails.length} recusadas (ficaram na caixa).`, {
      description: fails.map((f) => f.why).join(" • ").slice(0, 400),
    });
  };

  const handleSave = async () => {
    if (bulkMode) {
      await handleBulkSave();
      return;
    }
    if (!newName.trim() || !newApiKey.trim()) {
      toast.error("Preencha o nome e a chave de API.");
      return;
    }
    setSaving(true);
    try {
      // Testa DE VERDADE antes de salvar: chama POST /api/ai/test (chamada mínima
      // real no provider). Se a chave for inválida, aborta e NÃO salva — assim o
      // "Testar e Salvar" não aceita mais chave quebrada como se estivesse ativa.
      // elevenlabs (tts) e meta (social) não são providers de chat, então o ping
      // de chat não se aplica — pulamos o teste pra eles e apenas salvamos.
      if (isChatProvider) {
        toast.loading("Testando a chave no provedor...", { id: "cred-test" });
        const res = await testAIKey(effProvider, newApiKey.trim(), effBaseUrl);
        toast.dismiss("cred-test");
        if (!res.ok) {
          toast.error(res.hint || `Chave recusada pelo provedor: ${res.error || "verifique a chave e o endpoint."}`, {
            description: res.reason,
          });
          setSaving(false);
          return;
        }
      }
      // Backend espera {name, type, provider, api_key, base_url}. type: elevenlabs=tts, resto=llm.
      await apiPost("/api/credentials", {
        name: newName.trim(),
        type: credType,
        provider: effProvider,
        api_key: newApiKey.trim(),
        base_url: effBaseUrl,
      });
      toast.success(isChatProvider ? "Chave validada e salva com sucesso!" : "Credencial salva com sucesso!");
      handleCloseDialog();
      await loadCredentials();
    } catch (e) {
      toast.dismiss("cred-test");
      toast.error("Falha ao salvar a credencial. Tente novamente.");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async (id: string) => {
    if (!confirm("Tem certeza que deseja remover esta credencial? Agentes que dependem dela pararão de funcionar.")) {
      return;
    }
    try {
      await apiDelete(`/api/credentials/${id}`);
      toast.success("Credencial removida.");
      await loadCredentials();
    } catch {
      toast.error("Falha ao remover a credencial.");
    }
  };

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setNewName("");
    setNewProvider("openai");
    setNewBaseUrl("");
    setNewApiKey("");
    setBulkMode(false);
    setBulkText("");
  };

  const filtered = credentials.filter(c => c.name.toLowerCase().includes(search.toLowerCase()) || c.provider.toLowerCase().includes(search.toLowerCase()));


  function getProviderLabel(val: string, baseUrl?: string) {
    if (val === "openrouter" || (baseUrl || "").toLowerCase().includes("openrouter.ai")) return "OpenRouter";
    const map: Record<string, string> = {
      "openai": "OpenAI",
      "anthropic": "Anthropic (Claude)",
      "groq": "Groq",
      "elevenlabs": "ElevenLabs",
      "webshare": "Proxy Webshare",
      "meta": "Meta Graph API (Social)",
      "custom": "Custom / Proxy (Padrão OpenAI)"
    };
    return map[val] || val;
  }

  return (
    <Card className="bg-glass border-border/50 shadow-soft overflow-hidden">
      <div className="p-4 border-b border-border/50 bg-muted/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <KeyRound className="w-5 h-5 text-emerald-500" />
          <div>
             <h3 className="font-bold text-sm">Cofre de Credenciais IA</h3>
             <p className="text-xs text-muted-foreground mt-0.5">Gerencie centralmente suas chaves privadas para conectar Agentes aos LLMs.</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 w-full md:w-auto">
            <div className="relative w-full md:w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar credencial..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9 rounded-xl bg-background text-sm"
              />
            </div>
            
            <Dialog open={isDialogOpen} onOpenChange={(open) => !open ? handleCloseDialog() : setIsDialogOpen(true)}>
              <DialogTrigger asChild>
                <Button className="h-9 rounded-xl shadow-glow gap-2 shrink-0 bg-emerald-500 hover:bg-emerald-600 text-white border-0">
                  <Plus className="w-4 h-4" /> Nova Credencial
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Cadastrar Nova Credencial de IA</DialogTitle>
                  <DialogDescription>
                    Adicione uma nova chave de API para disponibilizar aos seus agentes.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Provedor / Modelo Base</Label>
                    <Select
                      value={newProvider}
                      onChange={(e) => setNewProvider(e.target.value)}
                      className="w-full bg-background/50 rounded-xl"
                      options={[
                        { value: "openai", label: "OpenAI (ChatGPT)" },
                        { value: "anthropic", label: "Anthropic (Claude)" },
                        { value: "groq", label: "Groq (qwen3.8 — o mais rápido)" },
                        { value: "openrouter", label: "OpenRouter (várias contas em rodízio)" },
                        { value: "webshare", label: "Proxy Webshare (saída dos pedidos sem pressa)" },
                        { value: "elevenlabs", label: "ElevenLabs (Voz)" },
                        { value: "meta", label: "Meta Graph API (Instagram/Facebook)" },
                        { value: "custom", label: "Outro / Proxy (Ex: OmniRoute, Ollama)" }
                      ]}
                    />
                  </div>

                  {canBulk && (
                    <div className="flex rounded-xl border border-border/50 p-1 text-xs bg-muted/20">
                      <button type="button" onClick={() => setBulkMode(false)}
                        className={`flex-1 rounded-lg py-1.5 font-semibold transition-colors ${!bulkMode ? "bg-background shadow-sm" : "text-muted-foreground"}`}>
                        Uma chave
                      </button>
                      <button type="button" onClick={() => setBulkMode(true)}
                        className={`flex-1 rounded-lg py-1.5 font-semibold transition-colors ${bulkMode ? "bg-background shadow-sm" : "text-muted-foreground"}`}>
                        Várias de uma vez
                      </button>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label>{bulkMode ? "Nome base (vira \"Nome 1\", \"Nome 2\"...)" : "Nome de Identificação (Para você encontrar depois)"}</Label>
                    <Input
                      placeholder={bulkMode ? `Ex: ${getProviderLabel(newProvider)}` : "Ex: Minha Chave Groq Rápida"}
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      className="rounded-xl bg-background/50"
                    />
                  </div>

                  {newProvider === "custom" && (
                    <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
                      <Label>Base URL (Custom Endpoint)</Label>
                      <Input
                        placeholder="https://api.meu-proxy.com/v1"
                        value={newBaseUrl}
                        onChange={(e) => setNewBaseUrl(e.target.value)}
                        className="rounded-xl bg-background/50"
                      />
                      <p className="text-[0.65rem] text-muted-foreground mt-1 px-1">O endpoint deve ser compatível com a API da OpenAI.</p>
                    </div>
                  )}

                  {isProxy && (
                    <p className="text-[0.7rem] text-muted-foreground px-1">
                      Os pedidos de IA <b>sem pressa</b> (atendimento por texto, assistente, análises, testes) saem por
                      estes proxies. A ligação continua direta e o Gemini fica de fora. A ordem é a prioridade: quando um
                      plano acaba ou o proxy cai, o próximo assume sozinho; sem nenhum, o pedido vai direto.
                    </p>
                  )}

                  {newProvider === "openrouter" && (
                    <p className="text-[0.7rem] text-muted-foreground px-1">
                      Endereço preenchido sozinho ({OPENROUTER_BASE}). Todas as chaves do OpenRouter entram no
                      rodízio: se uma bater limite ou ficar sem crédito, a próxima é usada na hora.
                    </p>
                  )}

                  {bulkMode ? (
                    <div className="space-y-2">
                      <Label>Chaves (uma por linha)</Label>
                      <textarea
                        value={bulkText}
                        onChange={(e) => setBulkText(e.target.value)}
                        rows={6}
                        spellCheck={false}
                        autoComplete="off"
                        placeholder={isProxy
                          ? "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80\nConta 2 http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80\nou host:porta:usuario:senha"
                          : "sk-or-v1-...\nConta Maria sk-or-v1-...\nConta João sk-or-v1-..."}
                        className="w-full rounded-xl border border-input bg-background/50 px-3 py-2 text-xs font-mono [-webkit-text-security:disc] focus:[-webkit-text-security:none] outline-none focus:ring-2 focus:ring-ring"
                      />
                      <p className="text-[0.65rem] text-muted-foreground px-1">
                        {bulkItems.length > 0
                          ? `${bulkItems.length} ${bulkItems.length === 1 ? "item encontrado" : "itens encontrados"}.${isChatProvider ? " Cada chave é testada antes de salvar." : ""}`
                          : "Pode pôr um nome antes da chave na mesma linha. Linhas começando com # são ignoradas."}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Label>{isProxy ? "Endereço do proxy (com usuário e senha)" : "Chave da API (Secret Key)"}</Label>
                      <Input
                        type="password"
                        placeholder={isProxy ? "http://<USUARIO>:<SEGREDO_REMOVIDO>@p.webshare.io:80" : "sk-..."}
                        value={newApiKey}
                        onChange={(e) => setNewApiKey(e.target.value)}
                        className="rounded-xl bg-background/50 font-mono"
                      />
                    </div>
                  )}
                </div>
                
                <div className="bg-primary/5 rounded-xl p-3 border border-primary/20 text-xs text-primary-foreground space-y-2">
                  <p className="font-bold">💡 Dicas de Modelos e Chaves</p>
                  <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                    <li>
                      <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-primary hover:underline">Google AI Studio</a>: Recomendado Gemini Flash para conversas rápidas por voz, ou Gemini Pro para textos complexos.
                    </li>
                    <li>
                      <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer" className="text-primary hover:underline">Groq Console</a>: Modelos ultrarrápidos (qwen3.8). Excelente para a ligação e para o Whisper (STT) com latência quase zero.
                    </li>
                    <li>
                      <a href="https://openrouter.ai/keys" target="_blank" rel="noreferrer" className="text-primary hover:underline">OpenRouter</a>: O mesmo modelo da ligação (qwen3.8) em vários provedores — serve de reserva automática da ligação.
                    </li>
                    <li>
                      <a href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer" className="text-primary hover:underline">OpenAI Platform</a>: Recomendado GPT-4o mini para equilíbrio custo-benefício.
                    </li>
                    <li>
                      <a href="https://developers.facebook.com" target="_blank" rel="noreferrer" className="text-primary hover:underline">Meta for Developers</a>: Gere um Token de Acesso de Sistema para habilitar Inbound do Instagram/Messenger.
                    </li>
                  </ul>
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={handleCloseDialog} className="rounded-xl">Cancelar</Button>
                  <Button onClick={handleSave} disabled={saving || (bulkMode ? bulkItems.length === 0 : !newName.trim() || !newApiKey.trim())} className="rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white">
                    {saving ? "Salvando..." : bulkMode ? `Testar e Salvar ${bulkItems.length || ""}`.trim() : "Testar e Salvar"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      
      <div className="p-6">
        {loading ? (
          <div className="text-center py-10 text-muted-foreground text-sm">Carregando credenciais...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-10 border border-dashed rounded-xl bg-muted/10">
            <KeyRound className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-30" />
            <p className="text-muted-foreground font-medium">Nenhuma credencial encontrada</p>
            <p className="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">Cadastre suas chaves de API acima para que os Agentes de IA possam consumi-las livremente em seus fluxos.</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {filtered.map((k) => {
              const isError = k.status === "error";
              return (
              <div key={k.id} className={`flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-xl transition-colors gap-4 ${isError ? 'border-destructive/50 bg-destructive/5 hover:bg-destructive/10' : 'border-border/50 bg-background/50 hover:bg-muted/20'}`}>
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl border shrink-0 ${isError ? 'bg-destructive/10 border-destructive/20 text-destructive' : 'bg-primary/10 border-primary/20 text-primary'}`}>
                    {isError ? <AlertTriangle className="h-5 w-5" /> : <Link2 className="h-5 w-5" />}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className={`font-bold text-sm ${isError ? 'text-destructive' : ''}`}>{k.name}</p>
                      {k.status === "active" && (
                        <span className="flex items-center gap-1 text-[0.6rem] uppercase tracking-wider font-bold bg-emerald-500/10 text-emerald-500 px-2 py-0.5 rounded-full">
                          <CheckCircle2 className="h-3 w-3" /> Conectado
                        </span>
                      )}
                      {k.status === "error" && (
                        <span className="flex items-center gap-1 text-[0.6rem] uppercase tracking-wider font-bold bg-destructive/20 text-destructive px-2 py-0.5 rounded-full shadow-sm">
                          <AlertTriangle className="h-3 w-3" /> Falhando
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground/70">{getProviderLabel(k.provider, k.baseUrl)}</span>
                      <span>•</span>
                      <span className="font-mono bg-muted px-1.5 py-0.5 rounded border border-border/50">
                        {k.masked_key}
                      </span>
                      {k.baseUrl && (
                        <>
                          <span>•</span>
                          <span className="truncate max-w-[150px]">{k.baseUrl}</span>
                        </>
                      )}
                    </div>
                    {isError && k.failsThisWeek !== undefined && (
                      <div className="mt-2 text-xs font-bold text-destructive flex items-center gap-1 bg-destructive/10 inline-flex px-2 py-1 rounded-md">
                        <AlertTriangle className="h-3 w-3" />
                        {k.last_error_reason || `Sua chave teve ${k.failsThisWeek} recusas nesta semana. Verifique o saldo ou crie outra chave no provedor.`}
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="hidden sm:block text-right text-xs">
                    <p>Adicionada em</p>
                    <p className="font-medium">{new Date(k.created_at).toLocaleDateString("pt-BR")}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive hover:bg-destructive/10 shrink-0 rounded-xl"
                    onClick={() => handleRemove(k.id)}
                    title="Remover Credencial"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
}
