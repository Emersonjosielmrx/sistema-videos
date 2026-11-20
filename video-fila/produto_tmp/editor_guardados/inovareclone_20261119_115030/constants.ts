import {loadFont} from '@remotion/google-fonts/Montserrat';
import {PalavraK} from '../../lib/karaoke';

export const {fontFamily} = loadFont('normal', {
  weights: ['400', '600', '700', '800', '900'],
});

export const CORES = {
  marca: '#8B5CF6', // Violeta primário da marca
  marcaClara: '#A78BFA',
  marcaEscura: '#6D28D9',
  apoio: '#1F2937',
  fundoEscuro: '#0B0D14',
  fundoCard: 'rgba(15, 23, 42, 0.92)',
  texto: '#FFFFFF',
  textoSecundario: '#CBD5E1',
  sucesso: '#10B981',
  borda: 'rgba(139, 92, 246, 0.4)',
};

// Palavras separadas por cena para isolamento acústico e visual perfeito
export const PALAVRAS_CENA_0: PalavraK[] = [
  {p: 'Consigo', ini: 0.318, fim: 0.775},
  {p: 'ter', ini: 0.787, fim: 0.967},
  {p: 'vídeos', ini: 0.979, fim: 1.364},
  {p: 'meus', ini: 1.376, fim: 1.58},
  {p: 'sem', ini: 1.592, fim: 1.772},
  {p: 'precisar', ini: 1.784, fim: 2.289},
  {p: 'sentar', ini: 2.301, fim: 2.686},
  {p: 'na', ini: 2.698, fim: 2.83},
  {p: 'frente', ini: 2.842, fim: 3.167},
  {p: 'da', ini: 3.179, fim: 3.299},
  {p: 'câmera', ini: 3.311, fim: 3.792},
];

export const PALAVRAS_CENA_1: PalavraK[] = [
  {p: 'Eu', ini: 6.836, fim: 7.196},
  {p: 'travava', ini: 7.196, fim: 8.136},
  {p: 'na', ini: 8.136, fim: 8.316},
  {p: 'hora', ini: 8.316, fim: 8.456},
  {p: 'de', ini: 8.456, fim: 8.716},
  {p: 'gravar', ini: 8.716, fim: 9.236},
  {p: 'para', ini: 9.236, fim: 9.436},
  {p: 'a', ini: 9.436, fim: 9.676},
  {p: 'empresa', ini: 9.676, fim: 9.876},
  {p: 'e', ini: 9.876, fim: 10.416},
  {p: 'o', ini: 10.416, fim: 10.576},
  {p: 'perfil', ini: 10.576, fim: 10.876},
  {p: 'ficava', ini: 10.876, fim: 11.216},
  {p: 'sem', ini: 11.216, fim: 11.456},
  {p: 'vídeos.', ini: 11.456, fim: 11.836},
];

export const PALAVRAS_CENA_2: PalavraK[] = [
  {p: 'O', ini: 12.779, fim: 12.863},
  {p: 'sistema', ini: 12.875, fim: 13.296},
  {p: 'gera', ini: 13.308, fim: 13.632},
  {p: 'o', ini: 13.644, fim: 13.68},
  {p: 'avatar', ini: 13.693, fim: 14.077},
  {p: 'da', ini: 14.089, fim: 14.197},
  {p: 'pessoa', ini: 14.209, fim: 14.702},
  {p: 'com', ini: 14.738, fim: 14.894},
  {p: 'fala', ini: 14.906, fim: 15.159},
  {p: 'em', ini: 15.171, fim: 15.243},
  {p: 'português', ini: 15.255, fim: 15.7},
  {p: 'e', ini: 15.712, fim: 15.82},
  {p: 'posturas', ini: 15.844, fim: 16.253},
  {p: 'automáticas', ini: 16.265, fim: 17.034},
  {p: 'para', ini: 17.046, fim: 17.214},
  {p: 'os', ini: 17.226, fim: 17.346},
  {p: 'vídeos', ini: 17.358, fim: 17.839},
];

export const PALAVRAS_CENA_3: PalavraK[] = [
  {p: 'Hoje', ini: 19.086, fim: 19.556},
  {p: 'meu', ini: 19.556, fim: 20.026},
  {p: 'perfil', ini: 20.026, fim: 20.496},
  {p: 'tem', ini: 20.496, fim: 20.956},
  {p: 'conteúdo', ini: 20.956, fim: 21.426},
  {p: 'frequente', ini: 21.426, fim: 21.896},
  {p: 'e', ini: 21.896, fim: 22.366},
  {p: 'eu', ini: 22.366, fim: 22.836},
  {p: 'continuo', ini: 22.836, fim: 23.306},
  {p: 'atendendo', ini: 23.306, fim: 23.776},
  {p: 'meus', ini: 23.776, fim: 24.246},
  {p: 'clientes', ini: 24.246, fim: 24.706},
  {p: 'sem', ini: 24.706, fim: 25.176},
  {p: 'essa', ini: 25.176, fim: 25.646},
  {p: 'cobrança.', ini: 25.646, fim: 26.116},
];
