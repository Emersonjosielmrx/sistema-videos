import briefingData from '../../../trabalhos/inovaresites_20261119_151614/public/briefing.json';

export const BRIEFING = briefingData;

export const FPS = 30;
export const TOTAL_DURATION_S = briefingData.duracao_s; // 29.77
export const TOTAL_FRAMES = Math.ceil(TOTAL_DURATION_S * FPS); // 894

export const CORES = {
  marca: '#EC4899', // Rosa vibrante da Inovare Sites
  marcaGlow: 'rgba(236, 72, 153, 0.45)',
  marcaDark: '#BE185D',
  apoio: '#18181B',
  fundoCard: '#0B0D13',
  bordaCard: 'rgba(255, 255, 255, 0.14)',
  bordaAtiva: 'rgba(236, 72, 153, 0.85)',
  textoBranco: '#FFFFFF',
  textoMuted: '#94A3B8',
  textoDestaque: '#F472B6',
  alertaRed: '#EF4444',
  sucessoGreen: '#10B981',
};

// Cenas
export const CENAS = briefingData.cenas;

export const PALAVRAS_CENA0 = [
  {p: 'Seu', ini: 0.318, fim: 0.607},
  {p: 'cliente', ini: 0.619, fim: 1.063},
  {p: 'entra', ini: 1.075, fim: 1.34},
  {p: 'na', ini: 1.352, fim: 1.472},
  {p: 'página', ini: 1.484, fim: 1.977, quebraApos: true},
  {p: 'e', ini: 2.001, fim: 2.085},
  {p: 'vai', ini: 2.097, fim: 2.277},
  {p: 'embora', ini: 2.289, fim: 2.662},
  {p: 'sem', ini: 2.674, fim: 2.89},
  {p: 'entender?', ini: 2.902, fim: 3.347},
];

export const PALAVRAS_CENA1 = [
  {p: 'Muitas', ini: 5.8, fim: 6.56},
  {p: 'pessoas', ini: 6.56, fim: 7.08},
  {p: 'chegam', ini: 7.08, fim: 7.54},
  {p: 'na', ini: 7.54, fim: 7.7},
  {p: 'página', ini: 7.7, fim: 8.1, quebraApos: true},
  {p: 'não', ini: 8.38, fim: 8.6},
  {p: 'leem', ini: 8.6, fim: 8.9},
  {p: 'o', ini: 8.9, fim: 9.1},
  {p: 'texto', ini: 9.1, fim: 9.44, quebraApos: true},
  {p: 'e', ini: 9.44, fim: 9.98},
  {p: 'saem', ini: 9.98, fim: 10.44},
  {p: 'sem', ini: 10.44, fim: 10.68},
  {p: 'comprar', ini: 10.68, fim: 11.16},
  {p: 'nada', ini: 11.16, fim: 11.54},
];

export const PALAVRAS_CENA2 = [
  {p: 'A', ini: 12.96, fim: 13.58},
  {p: 'landing', ini: 13.58, fim: 13.78},
  {p: 'page', ini: 13.78, fim: 14.1},
  {p: 'pronta', ini: 14.1, fim: 14.48, quebraApos: true},
  {p: 'com', ini: 14.48, fim: 14.66},
  {p: 'vídeo', ini: 14.84, fim: 14.98},
  {p: 'demo', ini: 14.98, fim: 15.24},
  {p: 'mostra', ini: 15.24, fim: 15.6},
  {p: 'o', ini: 15.6, fim: 15.82, quebraLinha: true},
  {p: 'produto', ini: 15.82, fim: 16.06, quebraApos: true},
  {p: 'em', ini: 16.06, fim: 16.3},
  {p: 'ação', ini: 16.3, fim: 16.62},
  {p: 'e', ini: 16.62, fim: 16.9, quebraLinha: true},
  {p: 'retém', ini: 16.9, fim: 17.26},
  {p: 'a', ini: 17.26, fim: 17.36},
  {p: 'atenção', ini: 17.36, fim: 17.7},
];

export const PALAVRAS_CENA3 = [
  {p: 'Essa', ini: 18.15, fim: 18.75},
  {p: 'comunicação', ini: 18.75, fim: 19.47},
  {p: 'clara', ini: 19.47, fim: 20.19, quebraApos: true},
  {p: 'apresenta', ini: 20.19, fim: 20.89},
  {p: 'a', ini: 20.89, fim: 21.05},
  {p: 'solução', ini: 21.05, fim: 21.55},
  {p: 'de', ini: 21.55, fim: 21.79},
  {p: 'verdade', ini: 21.79, fim: 22.39, quebraApos: true},
  {p: 'para', ini: 22.39, fim: 22.99},
  {p: 'transformar', ini: 22.99, fim: 23.89},
  {p: 'visita', ini: 23.89, fim: 24.53, quebraLinha: true},
  {p: 'em', ini: 24.53, fim: 24.87},
  {p: 'cliente', ini: 24.87, fim: 25.43},
];
