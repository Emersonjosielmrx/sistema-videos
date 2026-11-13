/**
 * Normaliza números brasileiros para o formato esperado pelo WhatsApp.
 * 
 * Regra: DDDs de celular no Brasil têm 9 dígitos (com o 9 na frente).
 * Porém, alguns DDDs (especialmente 91/PA) são cadastrados no WhatsApp SEM o 9 extra.
 * 
 * Esta função detecta e sugere a correção, mas não altera automaticamente
 * pois a regra não é 100% determinística.
 */

// DDDs que frequentemente NÃO usam o 9 extra no WhatsApp
const dddsSem9 = new Set([91, 92, 93, 94, 95, 96, 97, 98, 99]);

export function normalizePhone(raw: string): string {
  let phone = raw.replace(/\D/g, "").replace(/^\+/, "");
  
  // Se não começa com 55, adiciona
  if (!phone.startsWith("55") && phone.length <= 11) {
    phone = "55" + phone;
  }
  
  return phone;
}

export function phoneHint(phone: string): string | null {
  const normalized = normalizePhone(phone);
  
  if (normalized.length < 12) return null;
  
  // 55 + DDD(2) + number(9) = 13 digits
  if (normalized.length === 13 && normalized.startsWith("55")) {
    const ddd = parseInt(normalized.slice(2, 4));
    if (dddsSem9.has(ddd)) {
      const withoutNine = normalized.slice(0, 4) + normalized.slice(5);
      return `DDD ${ddd}: tente sem o 9 → ${withoutNine}`;
    }
  }
  
  return null;
}

export function formatPhoneDisplay(phone: string): string {
  const n = normalizePhone(phone);
  if (n.length === 13) {
    return `+${n.slice(0, 2)} (${n.slice(2, 4)}) ${n.slice(4, 5)} ${n.slice(5, 9)}-${n.slice(9)}`;
  }
  if (n.length === 12) {
    return `+${n.slice(0, 2)} (${n.slice(2, 4)}) ${n.slice(4, 8)}-${n.slice(8)}`;
  }
  return phone;
}
