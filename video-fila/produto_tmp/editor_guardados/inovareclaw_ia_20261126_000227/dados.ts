import {PalavraK} from '../../lib/karaoke';

export const DADOS_VIDEO = {
  duracao_s: 33.34,
  fps: 30,
  totalFrames: 1001,
  marca: 'Inovare Claw',
  arroba: '@inovareclaw.ia',
  cores: {
    marca: '#7C3AED',
    apoio: '#111827',
    fundo_escuro: '#111827',
    destaque: '#7C3AED',
    texto_sobre_marca: '#FFFFFF',
  },
};

// Palavras das cenas 0 a 3 formatadas para o Karaoke (sem cena 4 do cartão final)
export const PALAVRAS_KARAOKE: PalavraK[] = [
  // Cena 0: Pergunta (0.0 - 6.59s)
  // Bloco 1: "QUERO UMA IA / TRABALHANDO POR MIM," (equilibrado em 2 linhas, sem preposição 'POR' órfã)
  {p: 'Quero', ini: 0.318, fim: 0.534, quebraAntes: true},
  {p: 'uma', ini: 0.546, fim: 0.643},
  {p: 'IA', ini: 0.655, fim: 1.869},
  {p: 'trabalhando', ini: 1.881, fim: 2.421, quebraLinha: true},
  {p: 'por', ini: 2.433, fim: 2.59},
  {p: 'mim,', ini: 2.602, fim: 2.842, quebraApos: true},
  // Bloco 2: "MAS NÃO ENTENDO / NADA DE TECNOLOGIA?"
  {p: 'mas', ini: 3.107, fim: 3.287, quebraAntes: true},
  {p: 'não', ini: 3.299, fim: 3.443},
  {p: 'entendo', ini: 3.455, fim: 3.816},
  {p: 'nada', ini: 3.828, fim: 4.14, quebraLinha: true},
  {p: 'de', ini: 4.152, fim: 4.26},
  {p: 'tecnologia?', ini: 4.272, fim: 5.126, quebraApos: true},

  // Cena 1: Dono 1 (6.24 - 14.42s)
  // Bloco 1: "MUITO DONO DE NEGÓCIO QUER / USAR INTELIGÊNCIA ARTIFICIAL,"
  {p: 'Muito', ini: 7.086, fim: 7.826, quebraAntes: true},
  {p: 'dono', ini: 7.826, fim: 8.106},
  {p: 'de', ini: 8.106, fim: 8.266},
  {p: 'negócio', ini: 8.266, fim: 8.626},
  {p: 'quer', ini: 8.626, fim: 8.826, quebraLinha: true},
  {p: 'usar', ini: 8.826, fim: 9.106},
  {p: 'inteligência', ini: 9.106, fim: 9.646},
  {p: 'artificial,', ini: 9.646, fim: 10.246, quebraApos: true},
  // Bloco 2: "MAS TRAVA NA IDEIA DE QUE" (garantido visível, sem pular)
  {p: 'mas', ini: 10.966, fim: 11.286, quebraAntes: true},
  {p: 'trava', ini: 11.286, fim: 11.586},
  {p: 'na', ini: 11.586, fim: 11.786},
  {p: 'ideia', ini: 11.786, fim: 12.086},
  {p: 'de', ini: 12.086, fim: 12.326},
  {p: 'que', ini: 12.326, fim: 12.586, quebraApos: true},
  // Bloco 3: "PRECISA SABER PROGRAMAR."
  {p: 'precisa', ini: 12.586, fim: 12.806, quebraAntes: true},
  {p: 'saber', ini: 12.806, fim: 13.166},
  {p: 'programar.', ini: 13.166, fim: 13.786, quebraApos: true},

  // Cena 2: Dono 2 (14.07 - 22.25s)
  // Bloco 1: "O INOVARE CLAW JÁ VEM PRONTO."
  {p: 'O', ini: 15.109, fim: 15.669, quebraAntes: true},
  {p: 'Inovare', ini: 15.669, fim: 16.049},
  {p: 'Claw', ini: 16.049, fim: 16.429},
  {p: 'já', ini: 16.429, fim: 16.649},
  {p: 'vem', ini: 16.649, fim: 16.829},
  {p: 'pronto.', ini: 16.829, fim: 17.369, quebraApos: true},
  // Bloco 2: "EU PASSO A TAREFA E O AGENTE" (garantido na legenda antes de executa por mim)
  {p: 'Eu', ini: 18.369, fim: 18.569, quebraAntes: true},
  {p: 'passo', ini: 18.569, fim: 18.789},
  {p: 'a', ini: 18.789, fim: 19.009},
  {p: 'tarefa', ini: 19.009, fim: 19.629},
  {p: 'e', ini: 19.629, fim: 19.969},
  {p: 'o', ini: 19.969, fim: 20.169},
  {p: 'agente', ini: 20.169, fim: 20.629, quebraApos: true},
  // Bloco 3: "EXECUTA POR MIM."
  {p: 'executa', ini: 20.629, fim: 21.209, quebraAntes: true},
  {p: 'por', ini: 21.209, fim: 21.389},
  {p: 'mim.', ini: 21.389, fim: 21.589, quebraApos: true},

  // Cena 3: Dono 3 (21.90 - 29.74s)
  // Bloco 1: "EU NÃO PRECISEI APRENDER NADA TÉCNICO."
  {p: 'Eu', ini: 22.783, fim: 23.283, quebraAntes: true},
  {p: 'não', ini: 23.283, fim: 23.543},
  {p: 'precisei', ini: 23.543, fim: 23.943},
  {p: 'aprender', ini: 23.943, fim: 24.323},
  {p: 'nada', ini: 24.323, fim: 24.643},
  {p: 'técnico.', ini: 24.643, fim: 25.843, quebraApos: true},
  // Bloco 2: "HOJE O AGENTE TRABALHA SOZINHO" (garantido visível, sem supressão)
  {p: 'Hoje', ini: 26.143, fim: 26.323, quebraAntes: true},
  {p: 'o', ini: 26.323, fim: 26.523},
  {p: 'agente', ini: 26.523, fim: 26.823},
  {p: 'trabalha', ini: 26.823, fim: 27.223},
  {p: 'sozinho', ini: 27.223, fim: 27.723, quebraApos: true},
  // Bloco 3: "E EU CUIDO DO MEU NEGÓCIO."
  {p: 'e', ini: 27.723, fim: 28.003, quebraAntes: true},
  {p: 'eu', ini: 28.003, fim: 28.123},
  {p: 'cuido', ini: 28.123, fim: 28.303},
  {p: 'do', ini: 28.303, fim: 28.423},
  {p: 'meu', ini: 28.423, fim: 28.583},
  {p: 'negócio.', ini: 28.583, fim: 28.943, quebraApos: true},
];
