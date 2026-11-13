import { useEffect, useState } from "react";

export function useEventSource<T>(url: string, eventType: string = "message"): T | null {
  const [data, setData] = useState<T | null>(null);

  useEffect(() => {
    // Reutilizar o helper que busca com Headers / Bearer auth (se houvesse helper nativo para SSE com autenticação).
    // O navegador EventSource não envia cabeçalhos Authorization. Para auth simples na nossa stack, se a URL precisar de Auth, 
    // costumamos usar ?apiKey ou query params. Na V2 as sessoes podem ter o auth via apiKeys.
    
    const source = new EventSource(url);

    source.addEventListener(eventType, (e: MessageEvent) => {
      try {
        const parsed = JSON.parse(e.data);
        setData(parsed);
      } catch (err) {
        console.error("Failed to parse SSE data", err);
      }
    });

    source.onerror = () => {
      // Ignora erro silencioso no log pro caso de fechamento
      source.close();
    };

    return () => {
      source.close();
    };
  }, [url, eventType]);

  return data;
}
