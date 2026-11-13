// Planilhas (CSV) que o painel baixa. Regras, pra qualquer tela que exportar:
// - ";" e BOM UTF-8: abre direto no Excel em português (que usa ";") e no Google Planilhas.
// - Célula de texto que começa com = + - @ (ou tab/enter) ganha um apóstrofo na frente: o Excel
//   não executa como fórmula. Isso protege de texto vindo de lead ("=HYPERLINK(...)").
// - Telefone: passe csvTelefone(numero) como valor da célula. Sai ="+5591…" (só dígitos
//   dentro, nada a injetar): o Excel mostra +5591… como TEXTO, sem virar 5,59E+12 e sem o
//   apóstrofo aparecendo na célula (no CSV o Excel mostra o apóstrofo; ele só some quando é
//   digitado na célula).
// - Aspas em todas as células (vírgula, ";" e quebra de linha dentro do texto não quebram a linha).

const FORMULA_START = /^[=+\-@\t\r\n]/;
const BOM = String.fromCharCode(0xfeff);

// Célula de telefone (ver csvTelefone).
export class CelulaTelefone {
  digitos: string;
  constructor(digitos: string) {
    this.digitos = digitos;
  }
}

export function csvTelefone(v: unknown): CelulaTelefone {
  return new CelulaTelefone(String(v ?? "").replace(/\D/g, ""));
}

export function csvCell(v: unknown): string {
  if (v instanceof CelulaTelefone) return v.digitos ? `"=""+${v.digitos}"""` : '""';
  let s = v === null || v === undefined ? "" : String(v);
  if (FORMULA_START.test(s)) s = "'" + s;
  return `"${s.replace(/"/g, '""')}"`;
}

export function toCSV(head: string[], rows: unknown[][]): string {
  return BOM + [head.map(csvCell).join(";"), ...rows.map((r) => r.map(csvCell).join(";"))].join("\r\n");
}

export function downloadCSV(fileName: string, head: string[], rows: unknown[][]): void {
  const url = URL.createObjectURL(new Blob([toCSV(head, rows)], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(url);
}
