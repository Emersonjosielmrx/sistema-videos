import {PalavraK} from '../../lib/karaoke';

export const BRIEFING = {
  marca: 'Cardápio Digital',
  produto: 'Cardápio Digital',
  publico: 'donos de restaurante, lanchonete, açaiteria, pizzaria e delivery',
  fatos: [
    'Cardapio digital para restaurante e lanchonete com pedido pelo WhatsApp e atendimento com IA',
    'Cardápio digital com pedido no WhatsApp',
    'O cliente vê o cardápio com fotos no celular e faz o pedido direto pelo WhatsApp, com a IA respondendo dúvidas na hora.',
  ],
  cores: {
    marca: '#E11D48',
    apoio: '#FACC15',
    fundo_escuro: '#31060F',
    destaque: '#E11D48',
    texto_sobre_marca: '#FFFFFF',
  },
  arroba: '@futebolcom.ia2',
  convite: 'Chame no direct',
  convite_voz: 'Chame a gente no direct.',
  titulo: 'Cardápio Digital: pedido completo no WhatsApp',
  gancho_tela: 'Pedido organizado no WhatsApp',
  duracao_s: 32.23,
  fps: 30,
  duracao_frames: Math.ceil(32.23 * 30), // 967 frames
};

// Cenas com tempos exatos em frames
export const CENAS_CONFIG = [
  {
    n: 0,
    ini_s: 0.0,
    fim_s: 5.05,
    from: 0,
    durationInFrames: Math.ceil(5.05 * 30), // 152 frames
    tipo: 'pergunta',
  },
  {
    n: 1,
    ini_s: 4.7,
    fim_s: 12.88,
    from: Math.floor(4.7 * 30), // 141
    durationInFrames: Math.ceil((12.88 - 4.7) * 30), // 246 frames
    tipo: 'dono',
    video: 'dono_1.mp4',
    rotulo: 'O problema',
  },
  {
    n: 2,
    ini_s: 12.53,
    fim_s: 21.38,
    from: Math.floor(12.53 * 30), // 375
    durationInFrames: Math.ceil((21.38 - 12.53) * 30), // 266 frames
    tipo: 'conversa',
    rotulo: 'Como funciona',
  },
  {
    n: 3,
    ini_s: 21.03,
    fim_s: 28.74,
    from: Math.floor(21.03 * 30), // 630
    durationInFrames: Math.ceil((28.74 - 21.03) * 30), // 232 frames
    tipo: 'dono',
    video: 'dono_3.mp4',
    rotulo: 'O resultado',
  },
  {
    n: 4,
    ini_s: 28.39,
    fim_s: 32.23,
    from: Math.floor(28.39 * 30), // 851
    durationInFrames: Math.ceil((32.23 - 28.39) * 30), // 116 frames
    tipo: 'cartao',
  },
];

// Palavras formatadas para o Karaoke component (sem as palavras do cartão final)
// com quebras de cena forçadas para jamais juntar falas de cenas diferentes
export const PALAVRAS_KARAOKE: PalavraK[] = [
  // Cena 0: Pergunta
  { p: 'Seu', ini: 0.316, fim: 0.571, quebraAntes: true },
  { p: 'cliente', ini: 0.582, fim: 0.964 },
  { p: 'pede', ini: 0.976, fim: 1.358 },
  { p: 'e', ini: 1.37, fim: 1.451 },
  { p: 'o', ini: 1.462, fim: 1.508 },
  { p: 'pedido', ini: 1.52, fim: 1.902 },
  { p: 'chega', ini: 1.914, fim: 2.203 },
  { p: 'bagunçado', ini: 2.214, fim: 2.805 },
  { p: 'no', ini: 2.816, fim: 2.909 },
  { p: 'WhatsApp?', ini: 2.92, fim: 3.603, quebraApos: true },

  // Cena 1: Dono (O problema)
  { p: 'Eu', ini: 5.29, fim: 5.85, quebraAntes: true },
  { p: 'perdia', ini: 5.85, fim: 6.25 },
  { p: 'tempo', ini: 6.25, fim: 6.59 },
  { p: 'lendo', ini: 6.59, fim: 6.89 },
  { p: 'mensagens', ini: 6.89, fim: 7.47 },
  { p: 'soltas', ini: 7.47, fim: 8.35 },
  { p: 'e', ini: 8.35, fim: 8.73 },
  { p: 'confirmando', ini: 8.73, fim: 9.37 },
  { p: 'item', ini: 9.37, fim: 9.67 },
  { p: 'por', ini: 9.67, fim: 9.97 },
  { p: 'item', ini: 9.97, fim: 10.21 },
  { p: 'com', ini: 10.21, fim: 10.57 },
  { p: 'cada', ini: 10.57, fim: 10.89 },
  { p: 'cliente', ini: 10.89, fim: 11.33 },
  { p: 'do', ini: 11.33, fim: 11.47 },
  { p: 'meu', ini: 11.47, fim: 11.69 },
  { p: 'restaurante.', ini: 11.69, fim: 12.19, quebraApos: true },

  // Cena 2: Conversa (Como funciona)
  { p: 'O', ini: 13.024, fim: 13.105, quebraAntes: true },
  { p: 'cliente', ini: 13.117, fim: 13.487 },
  { p: 'escolhe', ini: 13.499, fim: 13.904 },
  { p: 'os', ini: 13.916, fim: 13.962 },
  { p: 'itens', ini: 13.973, fim: 14.378 },
  { p: 'com', ini: 14.39, fim: 14.552 },
  { p: 'fotos', ini: 14.564, fim: 14.98 },
  { p: 'no', ini: 14.992, fim: 15.084 },
  { p: 'cardápio', ini: 15.096, fim: 15.547 },
  { p: 'digital,', ini: 15.559, fim: 16.103 },
  { p: 'a', ini: 16.323, fim: 16.369 },
  { p: 'IA', ini: 16.381, fim: 17.573 },
  { p: 'tira', ini: 17.585, fim: 17.804 },
  { p: 'as', ini: 17.816, fim: 17.92 },
  { p: 'dúvidas', ini: 17.932, fim: 18.302 },
  { p: 'e', ini: 18.314, fim: 18.429 },
  { p: 'o', ini: 18.453, fim: 18.51 },
  { p: 'pedido', ini: 18.522, fim: 18.904 },
  { p: 'segue', ini: 18.915, fim: 19.274 },
  { p: 'para', ini: 19.286, fim: 19.46 },
  { p: 'o', ini: 19.471, fim: 19.494 },
  { p: 'WhatsApp.', ini: 19.506, fim: 20.108, quebraApos: true },

  // Cena 3: Dono (O resultado)
  { p: 'Hoje', ini: 21.935, fim: 22.575, quebraAntes: true },
  { p: 'o', ini: 22.575, fim: 22.775 },
  { p: 'pedido', ini: 22.775, fim: 23.075 },
  { p: 'chega', ini: 23.075, fim: 23.315 },
  { p: 'completo', ini: 23.315, fim: 23.895 },
  { p: 'no', ini: 23.895, fim: 24.095 },
  { p: 'meu', ini: 24.095, fim: 24.175 },
  { p: 'WhatsApp', ini: 24.175, fim: 25.035 },
  { p: 'e', ini: 25.035, fim: 25.475 },
  { p: 'eu', ini: 25.475, fim: 25.735 },
  { p: 'consigo', ini: 25.735, fim: 25.975 },
  { p: 'cuidar', ini: 25.975, fim: 26.355 },
  { p: 'do', ini: 26.355, fim: 26.495 },
  { p: 'preparo', ini: 26.495, fim: 26.935 },
  { p: 'com', ini: 26.935, fim: 27.155 },
  { p: 'mais', ini: 27.155, fim: 27.375 },
  { p: 'tranquilidade.', ini: 27.375, fim: 27.935, quebraApos: true },
];
