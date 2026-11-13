import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Download, Database } from "lucide-react";
import { apiGet } from "@/lib/api";
import { downloadCSV, csvTelefone } from "@/lib/csv";
import { toast } from "sonner";

type CollectedContact = { jid: string; phone: string; fields: Record<string, string>; updated_at: string };

export function CollectedDataTab() {
  const [searchTerm, setSearchTerm] = useState("");
  const [data, setData] = useState<CollectedContact[]>([]);
  const [loading, setLoading] = useState(true);

  // Dados REAIS que a IA coletou dos contatos (campos custom). Antes era mock.
  useEffect(() => {
    apiGet<{ contacts: CollectedContact[] }>("/api/contacts/collected")
      .then((r) => setData(r.contacts || []))
      .catch(() => toast.error("Erro ao carregar dados coletados"))
      .finally(() => setLoading(false));
  }, []);

  const fmtDate = (s: string) => { try { return new Date(s).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }); } catch { return s; } };

  const filtered = data.filter((c) => {
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase();
    if (c.phone.toLowerCase().includes(q)) return true;
    return Object.values(c.fields).some((v) => String(v).toLowerCase().includes(q));
  });

  const exportCSV = () => {
    if (filtered.length === 0) return;
    const cols = Array.from(new Set(filtered.flatMap((c) => Object.keys(c.fields))));
    // lib/csv: o que o lead falou pode começar com = + - @ (vira texto, não fórmula) e o
    // telefone sai como texto.
    downloadCSV("dados-coletados.csv", ["telefone", ...cols], filtered.map((c) => [csvTelefone(c.phone), ...cols.map((k) => c.fields[k] || "")]));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div>
          <h3 className="text-lg font-bold flex items-center gap-2"><Database className="h-5 w-5 text-emerald-500"/> Dados Coletados pela IA</h3>
          <p className="text-sm text-muted-foreground">Formulários e informações extraídas ativamente durante as conversas.</p>
        </div>
        
        <div className="flex gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Buscar por nome, telefone..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 bg-background"
            />
          </div>
          <Button variant="outline" className="gap-2" onClick={exportCSV} disabled={filtered.length === 0}><Download className="h-4 w-4"/> Exportar CSV</Button>
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center text-muted-foreground">Carregando...</div>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground flex flex-col items-center">
          <Database className="h-10 w-10 mb-3 opacity-40 text-primary" />
          <p className="text-lg font-semibold text-foreground">Nenhum dado coletado ainda.</p>
          <p className="text-sm">Quando a IA coletar informações dos contatos (nome, email, interesse...), elas aparecem aqui.</p>
        </div>
      ) : (
      <div className="grid grid-cols-1 gap-4">
        {filtered.map((item) => (
          <Card key={item.jid} className="p-4 bg-background/50 border-border/50 hover:bg-card/80 transition-colors">
            <div className="flex flex-col md:flex-row justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-foreground">+{item.phone}</span>
                </div>
                <p className="text-xs text-muted-foreground">{fmtDate(item.updated_at)}</p>
              </div>

              <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-4 bg-muted/20 p-3 rounded-xl border border-border/50">
                {Object.entries(item.fields).map(([key, value]) => (
                  <div key={key} className="flex flex-col">
                    <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">{key}</span>
                    <span className="text-sm font-semibold truncate">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        ))}
      </div>
      )}
    </div>
  );
}
