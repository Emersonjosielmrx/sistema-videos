// 🧩 O diagnóstico serve? Roda de novo a cada volta da espera ($runIndex = quantas voltas já deu).
//  pronto  = tem diagnóstico novo (até 7 dias) da mesma conta → usa
//  pedir   = não tem ou está velho → chama o fluxo 📈 Relatório do Perfil (ele gera e guarda em ig:diagnostico)
//  esperar = já pediu, o relatório ainda está sendo feito → espera 25 s e lê de novo
//  sem     = o dono não pediu, é de outra conta, ou cansou de esperar → planeja só com os dados do negócio
const v = $('🧩 Confere o pedido').first().json;
const SENHA_RELATORIO = '<SEGREDO_REMOVIDO>'; // a mesma do node "Decide o que fazer" do fluxo 📈 Relatório do Perfil
const VALIDADE_DIAS = 7;
const MAX_VOLTAS = 7; // 1 pedido + 6 esperas de 25 s ≈ 2,5 min
const volta = $runIndex;
if (!v.usar_diag) return [{ json: { acao: 'sem', motivo: '' } }];

let d = null;
try { d = JSON.parse($input.first().json.diag || 'null'); } catch (e) {}
const perfil = String(v.negocio.perfil || '').toLowerCase();
if (d && perfil && d.usuario && perfil !== d.usuario) {
  return [{ json: { acao: 'sem', motivo: `O diagnóstico guardado é do @${d.usuario} (a conta conectada ao n8n), não do @${perfil}. O mês foi planejado só com os dados do negócio.` } }];
}
const idadeH = d ? (Date.now() - Date.parse(d.geradoEm)) / 3600000 : Infinity;
if (d && idadeH < VALIDADE_DIAS * 24) return [{ json: { acao: 'pronto', diag: JSON.stringify(d), voltas: volta } }];
if (volta === 0) {
  return [{ json: { acao: 'pedir', url: `${v.base}/insta-relatorio?senha=${encodeURIComponent(SENHA_RELATORIO)}&atualizar=1` } }];
}
if (volta < MAX_VOLTAS) return [{ json: { acao: 'esperar' } }];
if (d) return [{ json: { acao: 'pronto', diag: JSON.stringify(d), voltas: volta, aviso: 'O diagnóstico novo não ficou pronto a tempo; usei o último (mais antigo).' } }];
return [{ json: { acao: 'sem', motivo: 'O diagnóstico do Instagram não ficou pronto a tempo. O mês foi planejado só com os dados do negócio; abra o 📈 Relatório e tente de novo depois.' } }];
