// Validação de CPF/CNPJ pelos dígitos verificadores (não só pela quantidade de caracteres).
// Usado no cadastro com plano pago, na tela de teste vencido e na assinatura.
//
// CNPJ ALFANUMÉRICO (Receita Federal, desde jul/2026): as 12 primeiras posições podem ter
// letras maiúsculas A-Z ou números; as 2 últimas (dígitos verificadores) são sempre números.
// No cálculo do DV, cada caractere vale (código ASCII − 48): '0'..'9' = 0..9, 'A' = 17,
// 'B' = 18 … 'Z' = 42. Pesos e módulo 11 iguais aos do CNPJ numérico. O CPF continua só
// com números. O backend valida do mesmo jeito.
//
// Exemplos conferidos com este código (npx tsx, 2026-10-02):
//   CNPJ alfanumérico válido: 12.ABC.345/01DE-35 (exemplo publicado pela Receita)
//                             12abc34501de35 → normaliza para 12ABC34501DE35 (válido)
//   CNPJ alfanumérico inválido: 12.ABC.345/01DE-36 (DV errado)
//   CNPJ numérico válido: 11.222.333/0001-81   inválido: 11.222.333/0001-82
//   CPF válido: 529.982.247-25, 390.533.447-05  inválidos: 529.982.247-24, 111.111.111-11

export const onlyDigits = (v: string): string => (v || "").replace(/\D/g, "");

// Mantém só [0-9A-Z] (minúsculas viram maiúsculas). É o formato enviado ao servidor.
export const normalizeCpfCnpj = (v: string): string => (v || "").toUpperCase().replace(/[^0-9A-Z]/g, "");

export function isValidCPF(raw: string): boolean {
  const d = onlyDigits(raw);
  if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false;
  const calc = (len: number) => {
    let sum = 0;
    for (let i = 0; i < len; i++) sum += Number(d[i]) * (len + 1 - i);
    const r = (sum * 10) % 11;
    return r === 10 ? 0 : r;
  };
  return calc(9) === Number(d[9]) && calc(10) === Number(d[10]);
}

// CNPJ numérico ou alfanumérico.
export function isValidCNPJ(raw: string): boolean {
  const c = normalizeCpfCnpj(raw);
  if (!/^[0-9A-Z]{12}[0-9]{2}$/.test(c)) return false;
  if (/^(\d)\1{13}$/.test(c)) return false; // 00000000000000, 11111111111111…
  const val = (ch: string) => ch.charCodeAt(0) - 48;
  const calc = (len: number) => {
    const weights = len === 12 ? [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] : [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    let sum = 0;
    for (let i = 0; i < len; i++) sum += val(c[i]) * weights[i];
    const r = sum % 11;
    return r < 2 ? 0 : 11 - r;
  };
  return calc(12) === Number(c[12]) && calc(13) === Number(c[13]);
}

// Devolve a mensagem de erro (pt-BR) ou null se o documento é válido.
export function cpfCnpjError(raw: string): string | null {
  const c = normalizeCpfCnpj(raw);
  if (!c) return "Informe seu CPF ou CNPJ.";
  const hasLetter = /[A-Z]/.test(c);
  if (!hasLetter && c.length === 11) return isValidCPF(c) ? null : "CPF inválido. Confira os números.";
  if (c.length === 14) {
    if (!/[0-9]{2}$/.test(c)) return "CNPJ inválido: os 2 últimos caracteres são sempre números.";
    return isValidCNPJ(c) ? null : "CNPJ inválido. Confira os caracteres.";
  }
  return hasLetter
    ? "O CNPJ tem 14 caracteres (letras e números; os 2 últimos são números)."
    : "O CPF tem 11 números e o CNPJ tem 14 caracteres.";
}

// Máscara enquanto a pessoa digita: 000.000.000-00 (CPF) ou AA.AAA.AAA/AAAA-00 (CNPJ).
// Letras só são aceitas nas 12 primeiras posições (as 2 últimas são o DV numérico); com
// letra, já é CNPJ.
export function formatCpfCnpj(raw: string): string {
  let c = "";
  for (const ch of normalizeCpfCnpj(raw)) {
    if (c.length >= 14) break;
    if (/[A-Z]/.test(ch) && c.length >= 12) continue;
    c += ch;
  }
  const isCnpj = /[A-Z]/.test(c) || c.length > 11;
  if (!isCnpj) {
    return c
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1-$2");
  }
  const p = [c.slice(0, 2), c.slice(2, 5), c.slice(5, 8), c.slice(8, 12), c.slice(12, 14)];
  let out = p[0];
  if (p[1]) out += "." + p[1];
  if (p[2]) out += "." + p[2];
  if (p[3]) out += "/" + p[3];
  if (p[4]) out += "-" + p[4];
  return out;
}
