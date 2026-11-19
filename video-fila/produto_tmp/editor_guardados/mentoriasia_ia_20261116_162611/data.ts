export interface Palavra {
  p: string;
  ini: number;
  fim: number;
  cena: number;
  quebraAntes?: boolean;
  quebraApos?: boolean;
  quebraLinha?: boolean;
}

export interface Cena {
  n: number;
  ini: number;
  fim: number;
  tipo: 'pergunta' | 'dono' | 'conversa' | 'cartao' | 'imagem' | 'real' | 'veo';
  fala: string;
  rotulo: string | null;
  foto?: string;
  video?: string;
  conversa?: Array<{
    de: 'cliente' | 'empresa';
    texto: string;
  }> | null;
}

export const BRIEFING = {
  marca: 'Treinamentos e Mentorias IA',
  produto: 'Treinamentos e Mentorias IA',
  fatos: [
    'Treinamento Vibe Coding, consultoria de otimizacao, pack de prompts, mapa mental',
    'Aprenda a criar automações com IA',
    'Treinamento de Vibe Coding, consultoria e pack de prompts validados para você montar suas próprias automações com IA.'
  ],
  cores: {
    marca: '#2563EB',
    apoio: '#111827',
    fundo_escuro: '#111827',
    destaque: '#2563EB',
    texto_sobre_marca: '#FFFFFF',
    verde_whatsapp: '#10B981',
    balao_cliente: '#1E293B',
    balao_empresa: '#1D4ED8',
    borda_sutil: 'rgba(255, 255, 255, 0.12)',
    card_bg: 'rgba(15, 23, 42, 0.88)'
  },
  arroba: '@mentoriasia.ia',
  convite: 'Chame no direct',
  convite_voz: 'Chame a gente no direct.',
  titulo: 'Como planejar suas automações com IA usando mapa mental',
  gancho_tela: 'Planejar automações com IA',
  duracao_s: 31.43,
  totalFrames: Math.ceil(31.43 * 30), // 943
  cenas: [
    {
      n: 0,
      ini: 0.0,
      fim: 5.19,
      tipo: 'pergunta',
      fala: 'Quer automatizar sua empresa, mas não sabe por onde começar?',
      rotulo: null,
      foto: 'img_0.jpg'
    },
    {
      n: 1,
      ini: 4.84,
      fim: 12.66,
      tipo: 'dono',
      fala: 'Eu não sabia qual tarefa automatizar primeiro, até usar o mapa mental para estruturar minhas ideias.',
      rotulo: 'O desafio',
      video: 'dono_1.mp4'
    },
    {
      n: 2,
      ini: 12.31,
      fim: 20.84,
      tipo: 'conversa',
      fala: 'Com o mapa mental, consultoria de otimização, pack de prompts validados e treinamento Vibe Coding, você planeja tudo.',
      rotulo: 'Como funciona',
      foto: 'img_2.jpg',
      conversa: [
        {
          de: 'cliente',
          texto: 'Tenho várias ideias, mas não sei o que automatizar primeiro.'
        },
        {
          de: 'empresa',
          texto: 'Começamos pelo mapa mental para estruturar seus fluxos de trabalho.'
        },
        {
          de: 'cliente',
          texto: 'E depois de desenhar o processo no mapa mental?'
        },
        {
          de: 'empresa',
          texto: 'Você usa o treinamento de Vibe Coding e os prompts validados para montar suas próprias automações com IA.'
        }
      ]
    },
    {
      n: 3,
      ini: 20.49,
      fim: 27.83,
      tipo: 'dono',
      fala: 'Hoje planejo cada etapa no mapa mental antes de montar minhas próprias automações com IA.',
      rotulo: 'O resultado',
      video: 'dono_3.mp4'
    },
    {
      n: 4,
      ini: 27.48,
      fim: 31.43,
      tipo: 'cartao',
      fala: 'Chame a gente no direct.',
      rotulo: null,
      foto: 'img_4.jpg'
    }
  ] as Cena[],
  palavras: [
    { p: 'Quer', ini: 0.318, fim: 0.486, cena: 0, quebraAntes: true },
    { p: 'automatizar', ini: 0.498, fim: 1.196, cena: 0 },
    { p: 'sua', ini: 1.208, fim: 1.364, cena: 0 },
    { p: 'empresa,', ini: 1.376, fim: 1.881, cena: 0, quebraApos: true },
    { p: 'mas', ini: 2.121, fim: 2.265, cena: 0, quebraAntes: true },
    { p: 'não', ini: 2.277, fim: 2.421, cena: 0 },
    { p: 'sabe', ini: 2.433, fim: 2.77, cena: 0, quebraLinha: true },
    { p: 'por', ini: 2.782, fim: 2.95, cena: 0 },
    { p: 'onde', ini: 2.962, fim: 3.179, cena: 0 },
    { p: 'começar?', ini: 3.191, fim: 3.732, cena: 0, quebraApos: true },

    { p: 'Eu', ini: 5.244, fim: 5.764, cena: 1, quebraAntes: true },
    { p: 'não', ini: 5.764, fim: 6.004, cena: 1 },
    { p: 'sabia', ini: 6.004, fim: 6.304, cena: 1 },
    { p: 'qual', ini: 6.304, fim: 6.544, cena: 1 },
    { p: 'tarefa', ini: 6.544, fim: 7.024, cena: 1 },
    { p: 'automatizar', ini: 7.024, fim: 7.664, cena: 1 },
    { p: 'primeiro,', ini: 7.664, fim: 8.164, cena: 1, quebraLinha: true, quebraApos: true },
    { p: 'até', ini: 8.764, fim: 8.924, cena: 1, quebraAntes: true },
    { p: 'usar', ini: 8.924, fim: 9.304, cena: 1 },
    { p: 'o', ini: 9.304, fim: 9.504, cena: 1 },
    { p: 'mapa', ini: 9.504, fim: 9.684, cena: 1 },
    { p: 'mental', ini: 9.684, fim: 10.124, cena: 1 },
    { p: 'para', ini: 10.124, fim: 10.384, cena: 1 },
    { p: 'estruturar', ini: 10.384, fim: 11.024, cena: 1 },
    { p: 'minhas', ini: 11.024, fim: 11.324, cena: 1 },
    { p: 'ideias.', ini: 11.324, fim: 11.864, cena: 1, quebraApos: true },

    { p: 'Com', ini: 12.807, fim: 12.963, cena: 2, quebraAntes: true },
    { p: 'o', ini: 12.975, fim: 12.999, cena: 2 },
    { p: 'mapa', ini: 13.011, fim: 13.288, cena: 2 },
    { p: 'mental,', ini: 13.3, fim: 13.769, cena: 2, quebraLinha: true },
    { p: 'consultoria', ini: 13.793, fim: 14.442, cena: 2 },
    { p: 'de', ini: 14.454, fim: 14.562, cena: 2 },
    { p: 'otimização,', ini: 14.574, fim: 15.379, cena: 2, quebraLinha: true },
    { p: 'pack', ini: 15.535, fim: 15.8, cena: 2 },
    { p: 'de', ini: 15.812, fim: 15.908, cena: 2 },
    { p: 'prompts', ini: 15.92, fim: 16.353, cena: 2 },
    { p: 'validados', ini: 16.365, fim: 16.882, cena: 2, quebraLinha: true },
    { p: 'e', ini: 16.894, fim: 17.002, cena: 2 },
    { p: 'treinamento', ini: 17.026, fim: 17.603, cena: 2 },
    { p: 'Vibe', ini: 17.615, fim: 17.879, cena: 2 },
    { p: 'Coding,', ini: 17.891, fim: 18.312, cena: 2, quebraLinha: true },
    { p: 'você', ini: 18.432, fim: 18.684, cena: 2 },
    { p: 'planeja', ini: 18.696, fim: 19.165, cena: 2 },
    { p: 'tudo.', ini: 19.189, fim: 19.55, cena: 2, quebraApos: true },

    { p: 'Hoje', ini: 21.154, fim: 21.974, cena: 3, quebraAntes: true },
    { p: 'planejo', ini: 21.974, fim: 22.634, cena: 3 },
    { p: 'cada', ini: 22.634, fim: 22.914, cena: 3 },
    { p: 'etapa', ini: 22.914, fim: 23.314, cena: 3 },
    { p: 'no', ini: 23.314, fim: 23.474, cena: 3, quebraApos: true },
    { p: 'mapa', ini: 23.474, fim: 23.694, cena: 3, quebraAntes: true },
    { p: 'mental', ini: 23.694, fim: 24.134, cena: 3 },
    { p: 'antes', ini: 24.134, fim: 24.654, cena: 3, quebraLinha: true },
    { p: 'de', ini: 24.654, fim: 24.814, cena: 3 },
    { p: 'montar', ini: 24.814, fim: 25.134, cena: 3, quebraApos: true },
    { p: 'minhas', ini: 25.134, fim: 25.474, cena: 3, quebraAntes: true },
    { p: 'próprias', ini: 25.474, fim: 25.834, cena: 3 },
    { p: 'automações', ini: 25.834, fim: 26.494, cena: 3, quebraLinha: true },
    { p: 'com', ini: 26.494, fim: 26.734, cena: 3 },
    { p: 'IA.', ini: 26.734, fim: 27.034, cena: 3, quebraApos: true },

    { p: 'Chame', ini: 27.977, fim: 28.326, cena: 4, quebraAntes: true },
    { p: 'a', ini: 28.338, fim: 28.398, cena: 4 },
    { p: 'gente', ini: 28.41, fim: 28.734, cena: 4 },
    { p: 'no', ini: 28.746, fim: 28.842, cena: 4 },
    { p: 'direct.', ini: 28.855, fim: 29.468, cena: 4, quebraApos: true }
  ] as Palavra[]
};
