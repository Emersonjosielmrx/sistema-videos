import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, Lock, RefreshCw, SlidersHorizontal } from "lucide-react";
import { apiGet } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

// Configuração do servidor (só a dona da plataforma). Dados: GET /api/admin/configuracao
// (cmd/server/env_catalog.go). Mostra cada variável de ambiente do catálogo (.env.example),
// se está definida NESTE servidor e o valor — segredo nunca vem do servidor, só "definida".
// Só leitura: pra mudar, é no arquivo do systemd na VPS (ver .env.example, topo).

interface Item {
  nome: string;
  grupo: string;
  ajuda: string;
  segredo: boolean;
  definida: boolean;
  valor?: string;
}

interface Dados {
  build: string;
  itens: Item[];
  desconhecidas: string[];
}

export function ConfiguracaoServidorSettings() {
  const [dados, setDados] = useState<Dados | null>(null);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [busca, setBusca] = useState("");
  const [soDefinidas, setSoDefinidas] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro("");
    try {
      setDados(await apiGet<Dados>("/api/admin/configuracao"));
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Não consegui carregar.");
    } finally {
      setCarregando(false);
    }
  }, []);
  useEffect(() => { carregar(); }, [carregar]);

  const grupos = useMemo(() => {
    const q = busca.trim().toLowerCase();
    const out: { grupo: string; itens: Item[] }[] = [];
    for (const it of dados?.itens ?? []) {
      if (soDefinidas && !it.definida) continue;
      if (q && !`${it.nome} ${it.ajuda} ${it.valor ?? ""}`.toLowerCase().includes(q)) continue;
      let g = out.find((x) => x.grupo === it.grupo);
      if (!g) {
        g = { grupo: it.grupo, itens: [] };
        out.push(g);
      }
      g.itens.push(it);
    }
    return out;
  }, [dados, busca, soDefinidas]);

  const definidas = dados?.itens.filter((i) => i.definida).length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex gap-3">
          <SlidersHorizontal className="w-5 h-5 text-emerald-500 mt-1 shrink-0" />
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Configuração do servidor</h2>
            <p className="text-muted-foreground text-sm mt-1 max-w-2xl">
              O que está ligado neste servidor. Só leitura: para mudar, é no arquivo do servidor (veja o topo do
              <code className="mx-1 text-xs">.env.example</code>no repositório). Segredos aparecem só como “definido”.
            </p>
            {dados && (
              <p className="text-xs text-muted-foreground mt-1">
                {definidas} de {dados.itens.length} definidas · versão {dados.build || "—"}
              </p>
            )}
          </div>
        </div>
        <button onClick={carregar} className="p-1.5 rounded-lg border border-border/50" title="Atualizar">
          <RefreshCw className={`w-4 h-4 ${carregando ? "animate-spin" : ""}`} />
        </button>
      </div>

      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {!dados && !erro && <p className="text-sm text-muted-foreground">Carregando…</p>}

      {dados && dados.desconhecidas.length > 0 && (
        <Card className="border-amber-500/40 bg-amber-500/5 p-4 text-sm">
          <div className="flex gap-2 font-medium text-amber-700 dark:text-amber-400">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            Definidas no servidor, mas o sistema não usa nenhuma com esse nome
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Costuma ser erro de digitação: a configuração “não pega” e parece que não funciona.
          </p>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {dados.desconhecidas.map((n) => (
              <code key={n} className="text-xs px-1.5 py-0.5 rounded bg-amber-500/10">{n}</code>
            ))}
          </div>
        </Card>
      )}

      {dados && (
        <div className="flex items-center gap-3 flex-wrap">
          <Input
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Procurar (ex.: voz, campanha, GROQ)"
            className="max-w-xs"
          />
          <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
            <input type="checkbox" checked={soDefinidas} onChange={(e) => setSoDefinidas(e.target.checked)} />
            Só as definidas
          </label>
        </div>
      )}

      {grupos.map((g) => (
        <Card key={g.grupo} className="bg-glass border-border/50 shadow-soft overflow-hidden">
          <div className="px-4 py-2.5 text-sm font-semibold border-b border-border/50">{g.grupo}</div>
          <div className="divide-y divide-border/30">
            {g.itens.map((it) => (
              <div key={it.nome} className="px-4 py-3 grid gap-1 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] md:gap-4">
                <div className="min-w-0">
                  <code className="text-xs font-semibold break-all">{it.nome}</code>
                  <div className="mt-1">
                    {it.definida ? (
                      it.segredo ? (
                        <Badge variant="outline" className="text-emerald-600 border-emerald-600/40 gap-1">
                          <Lock className="w-3 h-3" /> definido
                        </Badge>
                      ) : (
                        <code className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 break-all">
                          {it.valor}
                        </code>
                      )
                    ) : (
                      <span className="text-xs text-muted-foreground">padrão (não definida)</span>
                    )}
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">{it.ajuda}</p>
              </div>
            ))}
          </div>
        </Card>
      ))}

      {dados && grupos.length === 0 && <p className="text-sm text-muted-foreground">Nada encontrado.</p>}
    </div>
  );
}
