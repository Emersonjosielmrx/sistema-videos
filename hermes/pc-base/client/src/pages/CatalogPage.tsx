import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Store, Plus, Package, DollarSign, Search, Box, Link as LinkIcon, Trash2, ShieldAlert, LayoutDashboard, LineChart, KanbanSquare, LayoutPanelLeft, HelpCircle, RefreshCcw, Sparkles } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import { logError } from "@/lib/log";
import { CatalogAnalytics } from "@/components/analytics/CatalogAnalytics";

// CatalogPage — catálogo de produtos (backend /api/catalog/*). Lista produtos,
// métricas (total, estoque crítico, receita potencial), cria produtos e move status
// por estoque (rascunho=inativo / disponível / esgotado).

type Product = {
  id: string;
  name: string;
  company: string;
  price: number;
  cost: number;
  stock: number;
  category: string;
  active: boolean;
  payment_link: string;
  main_image: string;
  ai_pitch?: string; // O que a IA deve falar
  max_discount?: number; // % máximo de desconto autorizado
  upsell_id?: string; // ID do produto para cross-sell
  ai_hit_rate?: number; // % de sucesso da IA vendendo isso
};

const brl = (n: number) => n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export const CatalogPage = () => {
  const [viewMode, setViewMode] = useState<"list" | "kanban">("list");
  const [activeTab, setActiveTab] = useState<"dashboard" | "analytics">("dashboard");
  const [items, setItems] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  // form novo produto
  const [fName, setFName] = useState("");
  const [fPrice, setFPrice] = useState("");
  const [fStock, setFStock] = useState("");
  const [fCategory, setFCategory] = useState("");
  const [fPayLink, setFPayLink] = useState("");
  const [fPitch, setFPitch] = useState("");
  const [fMaxDiscount, setFMaxDiscount] = useState("");
  const [fUpsellId, setFUpsellId] = useState("");

  const reload = () => {
    setLoading(true);
    apiGet<{ products: Product[] }>("/api/catalog/products?limit=200")
      .then((r) => setItems(r.products ?? []))
      .catch(logError("/api/catalog/products"))
      .finally(() => setLoading(false));
  };
  useEffect(() => { reload(); }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return items;
    return items.filter((p) => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q));
  }, [items, search]);

  const totalProducts = items.length;
  const criticalStock = items.filter((p) => p.stock <= 3).length;
  const potentialRevenue = items.reduce((sum, p) => sum + p.price * p.stock, 0);

  const create = async () => {
    if (!fName.trim()) { toast.error("Dê um nome ao produto"); return; }
    setSaving(true);
    try {
      await apiPost("/api/catalog/products", {
        name: fName,
        price: parseFloat(fPrice) || 0,
        stock: parseInt(fStock) || 0,
        category: fCategory,
        payment_link: fPayLink,
        ai_pitch: fPitch,
        max_discount: parseFloat(fMaxDiscount) || 0,
        upsell_id: fUpsellId || null,
      });
      toast.success("Produto criado");
      setFName(""); setFPrice(""); setFStock(""); setFCategory(""); setFPayLink("");
      setFPitch(""); setFMaxDiscount(""); setFUpsellId("");
      setDialogOpen(false);
      reload();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id: string) => {
    if (!confirm("Mover este produto para a lixeira?")) return;
    try { await apiDelete(`/api/catalog/products/${id}`); reload(); }
    catch (e) { toast.error((e as Error).message); }
  };

  const statusOf = (p: Product): "rascunho" | "disponivel" | "esgotado" =>
    !p.active ? "rascunho" : p.stock <= 0 ? "esgotado" : "disponivel";

  const ProductRow = ({ p }: { p: Product }) => (
    <div className="grid grid-cols-[1fr_1fr_1fr_1fr_auto] gap-4 p-4 border-b border-border/50 text-sm items-center hover:bg-muted/10 group">
      <div>
         <div className="font-bold flex items-center gap-2">
            {p.name}
            {p.ai_pitch && <span title="Treinado para a IA"><Sparkles className="h-3 w-3 text-sky-500" /></span>}
         </div>
         <div className="text-[10px] text-muted-foreground mt-0.5 truncate max-w-[200px]">
           {p.ai_pitch ? p.ai_pitch : "Sem pitch de vendas."}
         </div>
      </div>
      <div>
         <div className="text-foreground font-semibold">{brl(p.price)}</div>
         {p.max_discount && p.max_discount > 0 ? (
            <div className="text-[10px] text-emerald-500 font-medium bg-emerald-500/10 px-1.5 py-0.5 rounded w-fit mt-1">
               IA pode dar {p.max_discount}% de desconto
            </div>
         ) : null}
      </div>
      <div className={cn(p.stock <= 3 ? "text-amber-500 font-bold" : "text-muted-foreground")}>{p.stock} un.</div>
      <div>
        <Badge variant="outline" className={cn("text-[0.65rem] px-2 py-0.5",
          statusOf(p) === "disponivel" ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" :
          statusOf(p) === "esgotado" ? "bg-destructive/10 text-destructive border-destructive/20" :
          "bg-muted/30 text-muted-foreground")}>
          {statusOf(p) === "disponivel" ? "Ativo no Agente" : statusOf(p) === "esgotado" ? "Esgotado" : "Rascunho"}
        </Badge>
      </div>
      <button onClick={() => remove(p.id)} className="h-8 w-8 flex items-center justify-center rounded-lg bg-destructive/10 text-destructive hover:bg-destructive hover:text-white transition-colors opacity-0 group-hover:opacity-100 justify-self-end" aria-label="Excluir">
         <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );

  const ProductCard = ({ p }: { p: Product }) => (
    <Card className="group relative p-4 text-sm bg-glass border-border/50 shadow-soft space-y-3 hover:border-primary/50 transition-colors overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
           <span className="font-bold truncate text-base">{p.name}</span>
           <div className="text-xs font-semibold text-primary mt-0.5">{brl(p.price)}</div>
        </div>
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
           <button onClick={() => remove(p.id)} className="h-7 w-7 flex items-center justify-center rounded-lg bg-destructive/10 text-destructive hover:bg-destructive hover:text-white transition-colors" aria-label="Excluir"><Trash2 className="h-3.5 w-3.5" /></button>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-2 bg-background/50 p-2 rounded-lg border border-border/50 text-xs text-muted-foreground">
         <div className="flex items-center gap-1.5"><Box className="h-3.5 w-3.5 text-amber-500" /> {p.stock} em estoque</div>
         <div className="flex items-center justify-end gap-1.5">
           <Sparkles className="h-3.5 w-3.5 text-sky-500" /> IA Treinada
         </div>
      </div>
      
      {p.max_discount && p.max_discount > 0 ? (
         <div className="text-[10px] text-emerald-500 font-medium border border-emerald-500/20 bg-emerald-500/5 px-2 py-1 rounded w-fit">
           Permitido: Desconto até {p.max_discount}%
         </div>
      ) : null}
      
      {p.category && <div className="text-[0.65rem] text-muted-foreground pt-1">{p.category}</div>}
    </Card>
  );

  const KANBAN = [
    { key: "rascunho", label: "Rascunho", cls: "text-muted-foreground", head: "bg-muted/20" },
    { key: "disponivel", label: "Disponível", cls: "text-emerald-500", head: "bg-emerald-500/5 border-emerald-500/30" },
    { key: "esgotado", label: "Esgotado", cls: "text-destructive", head: "bg-destructive/5 border-destructive/30" },
  ] as const;

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-10">
      {/* Cabeçalho Compacto Vitrine */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-rose-500/10 via-background to-background border border-rose-500/20 p-4 shadow-glow flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
          <Store className="w-16 h-16 text-rose-500" />
        </div>
        <div className="relative z-10 flex items-center gap-3">
          <div className="p-2 bg-rose-500/10 rounded-xl border border-rose-500/20 shadow-glow hidden sm:block">
            <Store className="h-6 w-6 text-rose-500" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-rose-500 to-rose-400 drop-shadow-sm">
                Motor de Vendas (Catálogo)
              </h2>
              <Badge className="bg-rose-500/10 text-rose-500 border-rose-500/20 hidden md:inline-flex text-[10px] px-1.5 py-0">
                Treinamento de Produtos
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Cadastre o que você vende e diga como a IA deve negociar os descontos no chat.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" className="h-9 w-9 rounded-full bg-glass" onClick={reload}><RefreshCcw className="h-4 w-4" /></Button>
          <Button variant="outline" size="icon" className="h-9 w-9 rounded-full bg-glass"><HelpCircle className="h-4 w-4" /></Button>
          <Button onClick={() => setDialogOpen(true)} className="shadow-glow gap-2 rounded-xl h-9 text-xs ml-2"><Plus className="h-3.5 w-3.5" /> Novo</Button>
        </div>
      </div>

      {/* Abas internas */}
      <div className="bg-muted/50 p-1 rounded-xl inline-flex flex-wrap w-fit gap-1 mb-2">
        <button onClick={() => setActiveTab("dashboard")} className={cn("flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg transition-colors", activeTab === "dashboard" ? "bg-primary shadow-sm text-primary-foreground" : "text-muted-foreground hover:bg-muted/50")}>
          <LayoutDashboard className="h-4 w-4" /> Dashboard
        </button>
        <button onClick={() => setActiveTab("analytics")} className={cn("flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg transition-colors", activeTab === "analytics" ? "bg-primary shadow-sm text-primary-foreground" : "text-muted-foreground hover:bg-muted/50")}>
          <LineChart className="h-4 w-4" /> Analytics
        </button>
      </div>

      <div className="mt-6">
        {activeTab === "analytics" && <CatalogAnalytics />}
        {activeTab === "dashboard" && (
          <>
            {/* Métricas */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card className="p-6 bg-glass border-border/50 shadow-soft relative overflow-hidden">
                <Package className="h-20 w-20 text-muted-foreground/10 absolute right-4 top-1/2 -translate-y-1/2" />
                <h4 className="text-[0.65rem] font-bold text-muted-foreground uppercase tracking-widest mb-2">Total Produtos</h4>
                <p className="text-5xl font-black">{totalProducts}</p>
              </Card>
              <Card className="p-6 bg-glass border-amber-500/30 shadow-soft relative overflow-hidden">
                <ShieldAlert className="h-20 w-20 text-amber-500/10 absolute right-4 top-1/2 -translate-y-1/2" />
                <h4 className="text-[0.65rem] font-bold text-amber-500 uppercase tracking-widest mb-2">Estoque Crítico</h4>
                <p className="text-5xl font-black">{criticalStock}</p>
              </Card>
              <Card className="p-6 bg-glass border-emerald-500/30 shadow-soft relative overflow-hidden">
                <DollarSign className="h-20 w-20 text-emerald-500/10 absolute right-4 top-1/2 -translate-y-1/2" />
                <h4 className="text-[0.65rem] font-bold text-emerald-500 uppercase tracking-widest mb-2">Receita Potencial</h4>
                <p className="text-5xl font-black">{brl(potentialRevenue)}</p>
              </Card>
            </div>

            {/* Toolbar */}
            <Card className="mt-6 bg-glass border-border/50 shadow-soft overflow-hidden">
              <div className="p-4 flex flex-wrap items-center gap-2 border-b border-border/50">
                <div className="relative w-full sm:w-auto">
                  <Search className="h-3 w-3 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input placeholder="Buscar produto ou categoria" value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 w-full sm:w-64 pl-8 rounded-lg bg-background text-xs" />
                </div>
                <div className="flex gap-1 ml-auto">
                  <Button onClick={() => setViewMode("list")} variant={viewMode === "list" ? "default" : "outline"} size="icon" className={cn("h-8 w-8", viewMode === "list" ? "bg-primary text-primary-foreground" : "bg-background")}><LayoutPanelLeft className="h-4 w-4" /></Button>
                  <Button onClick={() => setViewMode("kanban")} variant={viewMode === "kanban" ? "default" : "outline"} size="icon" className={cn("h-8 w-8", viewMode === "kanban" ? "bg-primary text-primary-foreground" : "bg-background")}><KanbanSquare className="h-4 w-4" /></Button>
                </div>
              </div>

              {loading ? (
                <p className="p-8 text-sm text-muted-foreground text-center">Carregando…</p>
              ) : items.length === 0 ? (
                <div className="p-16 flex flex-col items-center justify-center text-center text-muted-foreground h-64 bg-background/20">
                  <Box className="h-10 w-10 mb-3 opacity-20" />
                  <p className="text-sm font-medium">Nenhum produto. Clique em "Novo".</p>
                </div>
              ) : viewMode === "list" ? (
                <>
                  <div className="grid grid-cols-[1fr_1fr_1fr_1fr_auto] gap-4 p-4 border-b border-border/50 text-xs font-bold text-muted-foreground uppercase tracking-wider bg-background/50">
                    <div>Produto</div><div>Preço</div><div>Estoque</div><div>Status</div><div className="text-right">Ações</div>
                  </div>
                  {filtered.map((p) => <ProductRow key={p.id} p={p} />)}
                </>
              ) : (
                <div className="p-6 flex gap-4 overflow-x-auto custom-scrollbar bg-background/20 min-h-[400px]">
                  {KANBAN.map((col) => {
                    const list = filtered.filter((p) => statusOf(p) === col.key);
                    return (
                      <div key={col.key} className="flex w-72 shrink-0 flex-col rounded-2xl border border-border/50 bg-glass shadow-soft overflow-hidden">
                        <div className={cn("p-3 border-b border-border/50 flex justify-between items-center", col.head)}>
                          <h5 className={cn("text-[0.65rem] font-bold uppercase tracking-wider", col.cls)}>{col.label}</h5>
                          <Badge variant="secondary" className="h-5 px-1.5 text-[0.6rem]">{list.length}</Badge>
                        </div>
                        <div className="p-3 space-y-2 flex-1">
                          {list.length === 0 ? <p className="text-xs text-muted-foreground text-center py-6">Vazio</p> : list.map((p) => <ProductCard key={p.id} p={p} />)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          </>
        )}
      </div>

      {/* Dialog novo produto AI-Focused */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[700px] rounded-2xl bg-glass border-border/50 shadow-glow max-h-[90vh] overflow-y-auto custom-scrollbar">
          <DialogHeader>
             <DialogTitle className="text-xl flex items-center gap-2">
               <Store className="w-5 h-5 text-rose-500"/> Treinar IA com Novo Produto
             </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 mt-4">
             {/* Info Básica */}
             <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-background/30 p-4 rounded-xl border border-border/50">
               <div className="md:col-span-2">
                 <Field label="Nome do Produto"><Input value={fName} onChange={(e) => setFName(e.target.value)} placeholder="Ex: Tênis Esportivo ProX" className="rounded-xl bg-background" /></Field>
               </div>
               <Field label="Preço (R$)"><Input type="number" value={fPrice} onChange={(e) => setFPrice(e.target.value)} placeholder="299.90" className="rounded-xl bg-background" /></Field>
               <Field label="Estoque Atual (Unidades)"><Input type="number" value={fStock} onChange={(e) => setFStock(e.target.value)} placeholder="15" className="rounded-xl bg-background" /></Field>
             </div>

             {/* Cérebro de Vendas */}
             <div className="space-y-4 bg-sky-500/5 p-4 rounded-xl border border-sky-500/20">
                <div className="flex items-center gap-2 mb-2">
                   <Sparkles className="w-5 h-5 text-sky-500" />
                   <h4 className="font-bold text-sky-500 text-sm">Diretrizes de Negociação para a IA</h4>
                </div>
                
                <Field label="Pitch de Vendas (Argumento)">
                   <textarea
                     value={fPitch}
                     onChange={(e) => setFPitch(e.target.value)}
                     className="w-full h-20 rounded-xl bg-background border border-border/50 p-3 text-sm focus:outline-none focus:border-sky-500/50 resize-none"
                     placeholder="Ex: Foque em dizer que este produto tem garantia vitalícia. Se o lead reclamar do preço, mencione o parcelamento em 12x."
                   />
                </Field>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Field label="Desconto Máximo Permitido (%)" hint="A IA só dará desconto se o lead pressionar.">
                     <Input type="number" value={fMaxDiscount} onChange={(e) => setFMaxDiscount(e.target.value)} placeholder="10" className="rounded-xl bg-background border-border/50 focus:border-sky-500/50" />
                  </Field>
                  <Field label="Upsell Automático (Cross-sell)" hint="Qual produto oferecer junto?">
                     <select value={fUpsellId} onChange={(e) => setFUpsellId(e.target.value)} className="w-full rounded-xl bg-background border border-border/50 p-2.5 text-sm h-10">
                        <option value="">Nenhum (Venda Simples)</option>
                        {items.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
                     </select>
                  </Field>
                </div>
             </div>

             {/* Pagamento */}
             <div className="md:col-span-2 pt-2">
               <Field label="Link de Pagamento Automático" hint="A IA enviará este link (Stripe, Asaas, MercadoPago) quando o cliente fechar a compra.">
                 <div className="flex gap-2">
                   <LinkIcon className="h-10 w-10 p-2.5 bg-background rounded-xl text-muted-foreground border border-border/50 shrink-0 shadow-sm" />
                   <Input value={fPayLink} onChange={(e) => setFPayLink(e.target.value)} placeholder="https://pay.asaas.com/..." className="rounded-xl bg-background shadow-sm h-10" />
                 </div>
               </Field>
             </div>
          </div>
          <DialogFooter className="mt-6 border-t border-border/50 pt-4">
            <Button variant="outline" className="rounded-xl" onClick={() => setDialogOpen(false)}>Cancelar</Button>
            <Button className="rounded-xl shadow-glow gap-2 bg-rose-600 hover:bg-rose-700 text-white" onClick={create} disabled={saving}>
               {saving ? "Salvando…" : "Ativar no Cérebro da IA"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
