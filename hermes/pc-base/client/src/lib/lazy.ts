import { lazy, type ComponentType, type LazyExoticComponent } from "react";

// Carregamento sob demanda das telas (code-splitting): cada tela vira um arquivo JS
// separado, baixado só quando a pessoa abre a tela.
//
// Se o arquivo de uma tela (ou o CSS dela) não existir mais — o painel foi atualizado
// enquanto a aba estava aberta e os nomes dos arquivos mudaram —, recarrega a página UMA
// vez para pegar a versão nova, em vez de mostrar erro.
// A trava anti-loop é POR ARQUIVO/TELA: o sucesso de outra tela não apaga a trava desta
// (antes uma trava única podia ser zerada por outra tela e a página entrava em loop).

const LOCK_PREFIX = "hermes.chunk_reload:";

const errText = (err: unknown): string => (err instanceof Error ? err.message : String(err ?? ""));

const isChunkLoadError = (err: unknown): boolean =>
  /dynamically imported module|Importing a module script failed|Failed to fetch|error loading dynamically|Unable to preload CSS/i.test(errText(err));

// Nome do arquivo citado no erro (ex.: /assets/CRMPage-abc123.js), quando houver.
const fileFromError = (err: unknown): string => {
  const m = /\/assets\/[^\s'"()]+\.(?:js|css)/.exec(errText(err));
  return m ? m[0] : "";
};

// Recarrega uma vez por chave. Devolve false se essa chave já recarregou (não insiste).
const reloadOnce = (key: string): boolean => {
  try {
    const k = LOCK_PREFIX + key;
    if (sessionStorage.getItem(k)) return false;
    sessionStorage.setItem(k, "1");
  } catch {
    return false; // sem sessionStorage não dá para garantir que não entra em loop
  }
  window.location.reload();
  return true;
};

const clearLock = (key: string) => {
  try { sessionStorage.removeItem(LOCK_PREFIX + key); } catch { /* sem storage */ }
};

// O Vite avisa por este evento quando falha o pré-carregamento de um JS/CSS de uma tela
// (ex.: "Unable to preload CSS for /assets/X.css"). Recarrega uma vez por arquivo.
if (typeof window !== "undefined") {
  window.addEventListener("vite:preloadError", (event: Event) => {
    const payload = (event as Event & { payload?: unknown }).payload;
    const key = fileFromError(payload) || "preload:" + errText(payload).slice(0, 80);
    if (reloadOnce(key)) event.preventDefault();
    // Já recarregou por este arquivo: deixa o erro seguir para a tela de erro da página.
  });
}

const loadWithReload = async <M>(loader: () => Promise<M>, key: string): Promise<M> => {
  try {
    const mod = await loader();
    clearLock(key); // só a trava DESTA tela
    return mod;
  } catch (err) {
    if (isChunkLoadError(err) && reloadOnce(fileFromError(err) || key)) {
      return new Promise<M>(() => { /* aguarda o reload */ });
    }
    throw err;
  }
};

// lazyNamed(() => import("@/pages/X"), "X") — para módulos com export nomeado.
export function lazyNamed<K extends string, M extends Record<K, ComponentType<any>>>(
  loader: () => Promise<M>,
  name: K,
): LazyExoticComponent<M[K]> {
  return lazy(() => loadWithReload(loader, name).then((m) => ({ default: m[name] })));
}
