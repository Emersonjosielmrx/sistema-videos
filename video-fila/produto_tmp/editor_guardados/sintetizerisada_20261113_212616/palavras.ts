import {PalavraK} from '../../lib/karaoke';

export const PALAVRAS_BRIEFING: (PalavraK & {cena: number})[] = [
  // CENA 0: Pergunta
  {p: 'Uma', ini: 0.319, fim: 0.466, cena: 0},
  {p: 'IA', ini: 0.478, fim: 1.679, cena: 0},
  {p: 'realmente', ini: 1.692, fim: 2.231, cena: 0},
  {p: 'dá', ini: 2.243, fim: 2.378, cena: 0, quebraLinha: true},
  {p: 'conta', ini: 2.415, fim: 2.733, cena: 0},
  {p: 'de', ini: 2.746, fim: 2.831, cena: 0},
  {p: 'organizar', ini: 2.844, fim: 3.407, cena: 0, quebraAntes: true},
  {p: 'toda', ini: 3.505, fim: 3.726, cena: 0},
  {p: 'a', ini: 3.738, fim: 3.763, cena: 0},
  {p: 'minha', ini: 3.775, fim: 3.934, cena: 0},
  {p: 'agenda', ini: 3.946, fim: 5.250, cena: 0},

  // CENA 1: O Problema
  {p: 'Eu', ini: 6.082, fim: 6.205, cena: 1, quebraAntes: true},
  {p: 'achava', ini: 6.217, fim: 6.621, cena: 1},
  {p: 'que', ini: 6.633, fim: 6.744, cena: 1},
  {p: 'só', ini: 6.756, fim: 6.928, cena: 1},
  {p: 'uma', ini: 6.94, fim: 7.087, cena: 1, quebraLinha: true},
  {p: 'pessoa', ini: 7.099, fim: 7.504, cena: 1},
  {p: 'na', ini: 7.516, fim: 7.602, cena: 1},
  {p: 'recepção', ini: 7.614, fim: 8.153, cena: 1},
  {p: 'conseguia', ini: 8.165, fim: 8.717, cena: 1, quebraAntes: true},
  {p: 'organizar', ini: 8.729, fim: 9.293, cena: 1},
  {p: 'nossos', ini: 9.305, fim: 9.611, cena: 1, quebraLinha: true},
  {p: 'horários', ini: 9.624, fim: 10.138, cena: 1},
  {p: 'sem', ini: 10.151, fim: 10.322, cena: 1},
  {p: 'confusão', ini: 10.334, fim: 11.200, cena: 1},

  // CENA 2: Como Funciona
  {p: 'A', ini: 12.366, fim: 12.489, cena: 2, quebraAntes: true},
  {p: 'tecnologia', ini: 12.501, fim: 13.261, cena: 2},
  {p: 'faz', ini: 13.273, fim: 13.620, cena: 2},
  {p: 'agendamentos', ini: 13.620, fim: 14.450, cena: 2},
  {p: 'automáticos', ini: 14.450, fim: 15.300, cena: 2, quebraLinha: true},
  {p: '24', ini: 15.300, fim: 15.908, cena: 2},
  {p: 'horas', ini: 15.92, fim: 16.312, cena: 2},
  {p: 'confirmando', ini: 16.422, fim: 17.158, cena: 2, quebraAntes: true},
  {p: 'e', ini: 17.182, fim: 17.231, cena: 2},
  {p: 'reagendando', ini: 17.243, fim: 17.868, cena: 2},
  {p: 'horários', ini: 17.881, fim: 18.285, cena: 2, quebraLinha: true},
  {p: 'direto', ini: 18.297, fim: 18.714, cena: 2},
  {p: 'no', ini: 18.726, fim: 18.8, cena: 2},
  {p: 'WhatsApp', ini: 18.812, fim: 19.800, cena: 2},

  // CENA 3: O Resultado
  {p: 'Minha', ini: 20.436, fim: 20.776, cena: 3, quebraAntes: true},
  {p: 'recepção', ini: 20.776, fim: 21.616, cena: 3},
  {p: 'atende', ini: 21.616, fim: 22.196, cena: 3, quebraLinha: true},
  {p: 'dia', ini: 22.196, fim: 22.716, cena: 3},
  {p: 'e', ini: 22.716, fim: 23.016, cena: 3},
  {p: 'noite', ini: 23.016, fim: 23.376, cena: 3},
  {p: 'sem', ini: 23.756, fim: 23.876, cena: 3, quebraAntes: true},
  {p: 'conflito', ini: 23.876, fim: 24.556, cena: 3},
  {p: 'e', ini: 24.556, fim: 25.096, cena: 3, quebraAntes: true},
  {p: 'sem', ini: 25.096, fim: 25.516, cena: 3},
  {p: 'duplo', ini: 25.516, fim: 26.096, cena: 3},
  {p: 'agendamento', ini: 26.096, fim: 26.936, cena: 3, quebraLinha: true},
  {p: 'no', ini: 26.936, fim: 27.296, cena: 3},
  {p: 'WhatsApp.', ini: 27.296, fim: 28.000, cena: 3},

  // CENA 4: Cartão Final / CTA
  {p: 'Chame', ini: 28.598, fim: 28.953, cena: 4, quebraAntes: true},
  {p: 'a', ini: 28.966, fim: 29.027, cena: 4},
  {p: 'gente', ini: 29.039, fim: 29.37, cena: 4},
  {p: 'no', ini: 29.382, fim: 29.48, cena: 4},
  {p: 'direct', ini: 29.493, fim: 30.600, cena: 4},
];

export const PALAVRAS_KARAOKE: PalavraK[] = PALAVRAS_BRIEFING.map((p, idx, arr) => ({
  p: p.p,
  ini: p.ini,
  fim: p.fim,
  quebraAntes: p.quebraAntes ?? (idx === 0 || p.cena !== arr[idx - 1].cena),
  quebraLinha: p.quebraLinha,
}));
