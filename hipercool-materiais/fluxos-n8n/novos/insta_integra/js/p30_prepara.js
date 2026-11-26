// 🧩 Prepara o diagnóstico para as IAs:
//  texto   = vai para a 🤖 Estrategista (planeja o mês em cima dele)
//  redacao = regras curtas que vão para a 🤖 Redatora (escrever legendas do jeito que o perfil responde melhor)
//  resumo  = o que aparece no topo da página do calendário
const r = $input.first().json;
let d = null;
try { d = r.acao === 'pronto' ? JSON.parse(r.diag) : null; } catch (e) {}
if (!d) return [{ json: { usado: false, texto: '', redacao: '', aviso: r.motivo || '', resumo: null } }];

const texto = JSON.stringify({
  conta: '@' + d.usuario, seguidores: d.seguidores, posts_analisados: d.posts_analisados, nota_saude: d.nota_saude,
  engajamento_medio_percent: d.engajamento_medio_percent, posts_ultimos_30_dias: d.posts_ultimos_30_dias, resumo: d.resumo,
  o_que_funciona: d.o_que_funciona, o_que_melhorar: d.o_que_melhorar, pilares_que_funcionam: d.pilares_que_funcionam, evitar: d.evitar,
  ideias: d.ideias, melhor_dia: d.melhor_dia, melhor_horario: d.melhor_horario, frequencia: d.frequencia,
  mix_formatos_obrigatorio: d.mix_formatos,
  numeros: { por_formato: d.numeros && d.numeros.por_formato, legendas: d.numeros && d.numeros.legendas,
    calendario_anterior: d.numeros && d.numeros.calendario, top5: d.numeros && d.numeros.top5 },
}, null, 1);
const redacao = [...(d.regras_para_legenda || []), ...(d.o_que_melhorar || []).slice(0, 3).map(x => 'Corrigir: ' + x), ...(d.evitar || []).slice(0, 3).map(x => 'Evitar: ' + x)]
  .join('\n- ').replace(/^/, '- ');
const resumo = { status: 'usado', usuario: d.usuario, geradoEm: d.geradoEm, nota_saude: d.nota_saude, o_que_melhorar: d.o_que_melhorar,
  mix_formatos: d.mix_formatos, hora_sugerida: d.hora_sugerida, aviso: r.aviso || '', redacao: (d.regras_para_legenda || []).length || (d.o_que_melhorar || []).length ? redacao : '' };
return [{ json: { usado: true, texto, redacao: resumo.redacao, aviso: r.aviso || '', resumo } }];
