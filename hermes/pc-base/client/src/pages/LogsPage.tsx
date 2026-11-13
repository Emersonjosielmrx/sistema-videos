import { useEffect, useRef, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ShieldAlert } from "lucide-react";
import { apiUrl, getToken, authHeaders, isPlatformAdmin } from "@/lib/auth";
import { t } from "@/lib/i18n";

interface LogEntry {
  timestamp: number;
  level: string;
  category: string;
  message: string;
  meta?: Record<string, unknown>;
}

const categories = ["all", "call", "telegram", "ai", "voice", "system"];

// Terminal com fundo escuro fixo — cores pensadas p/ ler sobre slate-950.
const levelColor: Record<string, string> = {
  error: "text-red-400",
  warn: "text-amber-400",
  info: "text-slate-100",
  debug: "text-slate-400",
};

const categoryColor: Record<string, string> = {
  call: "text-emerald-400",
  telegram: "text-cyan-400",
  ai: "text-purple-400",
  voice: "text-teal-300",
  system: "text-slate-500",
};

// Os logs são do SERVIDOR inteiro (todas as contas), então só o admin da plataforma vê.
// O servidor responde 403 para os demais; aqui nem abrimos a conexão para quem não é admin.
const AdminOnly = () => (
  <div className="flex flex-col items-center justify-center gap-3 p-10 text-center">
    <ShieldAlert className="h-8 w-8 text-muted-foreground" />
    <h2 className="text-lg font-semibold">Apenas administradores</h2>
    <p className="text-sm text-muted-foreground max-w-md">
      Os logs mostram o servidor inteiro, por isso só a administração da plataforma tem acesso.
    </p>
  </div>
);

export function LogsPage() {
  const admin = isPlatformAdmin();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState("all");
  const [forbidden, setForbidden] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!admin) return;
    const types = filter === "all" ? "" : `?types=${filter}`;
    const token = getToken();
    // FIX P0-006 (2026-07-25): JWT em URL é visível para proxies/CDNs/Sentry.
    // EventSource não suporta custom headers, então apiKey= vai na query.
    // TODO longo prazo: cookie httpOnly. Por agora, log explícito.
    if (token && typeof console !== "undefined") {
      console.warn("[SECURITY P0-006] JWT em URL (LogsPage) — visível para proxies.");
    }
    const url = apiUrl(`/api/logs${types}`) + (types ? "&" : "?") + `apiKey=${encodeURIComponent(token)}`;

    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (ev) => {
      try {
        const entry = JSON.parse(ev.data) as LogEntry;
        setLogs((prev) => [...prev.slice(-499), entry]);
      } catch {}
    };

    // EventSource não informa o status HTTP. Se a conexão for recusada de vez (CLOSED),
    // pergunta o status com um fetch rápido: 403 = não é admin da plataforma.
    let alive = true;
    es.onerror = () => {
      if (es.readyState !== EventSource.CLOSED) return; // queda normal: o navegador reconecta
      const ctrl = new AbortController();
      const timer = window.setTimeout(() => ctrl.abort(), 5000);
      fetch(apiUrl(`/api/logs${types}`), { headers: authHeaders(), signal: ctrl.signal })
        .then((r) => {
          if (alive && r.status === 403) setForbidden(true);
          ctrl.abort(); // não fica lendo o fluxo
        })
        .catch(() => {})
        .finally(() => window.clearTimeout(timer));
    };

    return () => { alive = false; es.close(); };
  }, [filter, admin]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const formatTime = (ts: number) => new Date(ts).toLocaleTimeString("pt-BR");

  if (!admin || forbidden) return <AdminOnly />;

  return (
    <div className="flex h-full flex-col gap-4 p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
           <h2 className="text-xl font-semibold">{t("logs")}</h2>
        </div>
        <div className="flex gap-1">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => { setLogs([]); setFilter(cat); }}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                filter === cat ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
            >
              {t(`filter_${cat}`)}
            </button>
          ))}
        </div>
      </div>

      <ScrollArea className="flex-1 rounded-md border border-slate-700 bg-slate-950 dark:bg-slate-950 text-slate-200 p-3 font-mono text-xs">
        <div className="space-y-0.5">
          {logs.length === 0 && <p className="text-slate-400">Aguardando logs...</p>}
          {logs.map((entry, i) => (
            <div key={i} className="flex gap-2">
              <span className="shrink-0 text-slate-500">{formatTime(entry.timestamp)}</span>
              <span className={`shrink-0 w-12 uppercase ${levelColor[entry.level] ?? "text-slate-300"}`}>{entry.level}</span>
              <span className={`shrink-0 w-16 ${categoryColor[entry.category] ?? "text-slate-400"}`}>[{entry.category}]</span>
              <span className={levelColor[entry.level] ?? "text-slate-200"}>{entry.message}</span>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
    </div>
  );
}
