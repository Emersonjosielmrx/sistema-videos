import { useEffect, useState } from "react";
import { getCredentials } from "@/services/settings";
import { logError } from "@/lib/log";
import type { Credential } from "@/types/settings";

// CredentialSelect — dropdown que lista as credenciais salvas de um TIPO específico
// ("llm" | "stt" | "tts") pra o usuário associar a uma função (IA Padrão, STT, TTS…).
// Envia apenas o ID escolhido. É a peça central da "aba única de credenciais": em vez
// de digitar chave/base URL em cada aba, o dono seleciona uma credencial já cadastrada.
//
// Quando o valor é "" significa "não usar credencial salva" (cai no modo manual/legado).

type Props = {
  type: "llm" | "stt" | "tts"; // filtra as credenciais que aparecem
  value: string;               // credential_id selecionado ("" = nenhum)
  onChange: (id: string, cred?: Credential) => void;
  emptyLabel?: string;         // rótulo da opção vazia
};

export function CredentialSelect({ type, value, onChange, emptyLabel = "— Nenhuma (chave manual) —" }: Props) {
  const [creds, setCreds] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    getCredentials()
      .then((list) => { if (alive) setCreds(list.filter((c) => c.type === type)); })
      .catch(logError("getCredentials"))
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [type]);

  return (
    <select
      className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
      value={value}
      disabled={loading}
      onChange={(e) => {
        const id = e.target.value;
        onChange(id, creds.find((c) => c.id === id));
      }}
    >
      <option value="">{loading ? "Carregando credenciais…" : emptyLabel}</option>
      {creds.map((c) => (
        <option key={c.id} value={c.id}>
          {c.name} · {c.provider}
        </option>
      ))}
    </select>
  );
}
