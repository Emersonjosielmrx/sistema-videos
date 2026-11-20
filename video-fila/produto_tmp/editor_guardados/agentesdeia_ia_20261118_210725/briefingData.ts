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
  tipo: 'pergunta' | 'dono' | 'cartao';
  fala: string;
  rotulo: string | null;
  foto?: string;
  video?: string;
}

export const BRIEFING = {
  marca: "Agentes de IA",
  produto: "Agente Pessoal IA",
  publico: "profissionais e empreendedores com muita tarefa no dia",
  fatos: [
    "Agente pessoal de tarefas com IA",
    "Agente IA que faz tarefas por você",
    "Delegue tarefas reais a um agente IA. Pesquisa, agendamento, follow-up, qualquer coisa."
  ],
  cliente_real: false,
  cores: {
    marca: "#10B981",
    apoio: "#111827",
    fundo_escuro: "#111827",
    destaque: "#10B981",
    texto_sobre_marca: "#FFFFFF"
  },
  arroba: "@agentesdeia.ia",
  convite: "Chame no direct",
  convite_voz: "Chame a gente no direct.",
  titulo: "Delegue a pesquisa a um agente IA",
  gancho_tela: "Manhã inteira pesquisando?",
  duracao_s: 31.52,
  cenas: [
    {
      n: 0,
      ini: 0.0,
      fim: 5.03,
      tipo: "pergunta" as const,
      fala: "Dá para receber a pesquisa pronta enquanto cuido do meu negócio?",
      rotulo: null,
      foto: "img_0.jpg"
    },
    {
      n: 1,
      ini: 4.68,
      fim: 12.86,
      tipo: "dono" as const,
      fala: "Eu gastava a manhã inteira buscando informação na internet, e o resto do trabalho ficava parado esperando.",
      rotulo: "O problema",
      video: "dono_1.mp4"
    },
    {
      n: 2,
      ini: 12.51,
      fim: 20.09,
      tipo: "dono" as const,
      fala: "Agora eu explico o que preciso ao Agente Pessoal IA, e ele pesquisa por mim.",
      rotulo: "Como funciona",
      video: "dono_2.mp4"
    },
    {
      n: 3,
      ini: 19.74,
      fim: 27.92,
      tipo: "dono" as const,
      fala: "Eu recebo a tarefa concluída e uso a manhã para cuidar do que faz a empresa crescer.",
      rotulo: "O resultado",
      video: "dono_3.mp4"
    },
    {
      n: 4,
      ini: 27.57,
      fim: 31.52,
      tipo: "cartao" as const,
      fala: "Chame a gente no direct.",
      rotulo: null,
      foto: "img_4.jpg"
    }
  ],
  palavras: [
    { p: "Dá", ini: 0.318, fim: 0.498, cena: 0 },
    { p: "para", ini: 0.51, fim: 0.691, cena: 0 },
    { p: "receber", ini: 0.703, fim: 1.087, cena: 0 },
    { p: "a", ini: 1.099, fim: 1.147, cena: 0 },
    { p: "pesquisa", ini: 1.159, fim: 1.64, cena: 0 },
    { p: "pronta", ini: 1.652, fim: 1.989, cena: 0, quebraApos: true },
    { p: "enquanto", ini: 2.001, fim: 2.397, cena: 0 },
    { p: "cuido", ini: 2.409, fim: 2.698, cena: 0 },
    { p: "do", ini: 2.71, fim: 2.806, cena: 0 },
    { p: "meu", ini: 2.818, fim: 2.95, cena: 0 },
    { p: "negócio", ini: 2.962, fim: 3.551, cena: 0, quebraApos: true },
    { p: "Eu", ini: 5.456, fim: 5.996, cena: 1 },
    { p: "gastava", ini: 5.996, fim: 6.456, cena: 1 },
    { p: "a", ini: 6.456, fim: 6.576, cena: 1 },
    { p: "manhã", ini: 6.576, fim: 6.936, cena: 1 },
    { p: "inteira", ini: 6.936, fim: 7.316, cena: 1, quebraApos: true },
    { p: "buscando", ini: 7.316, fim: 7.736, cena: 1 },
    { p: "informação", ini: 7.736, fim: 8.296, cena: 1 },
    { p: "na", ini: 8.296, fim: 8.536, cena: 1 },
    { p: "internet,", ini: 8.536, fim: 8.996, cena: 1, quebraApos: true },
    { p: "e", ini: 8.996, fim: 9.716, cena: 1 },
    { p: "o", ini: 9.716, fim: 9.816, cena: 1 },
    { p: "resto", ini: 9.816, fim: 10.036, cena: 1 },
    { p: "do", ini: 10.036, fim: 10.236, cena: 1 },
    { p: "trabalho", ini: 10.236, fim: 10.616, cena: 1 },
    { p: "ficava", ini: 10.616, fim: 11.076, cena: 1, quebraLinha: true },
    { p: "parado", ini: 11.076, fim: 11.516, cena: 1 },
    { p: "esperando.", ini: 11.516, fim: 11.976, cena: 1, quebraApos: true },
    { p: "Agora", ini: 13.489, fim: 14.189, cena: 2 },
    { p: "eu", ini: 14.189, fim: 14.529, cena: 2 },
    { p: "explico", ini: 14.529, fim: 14.789, cena: 2 },
    { p: "o", ini: 14.789, fim: 14.869, cena: 2 },
    { p: "que", ini: 14.869, fim: 15.169, cena: 2 },
    { p: "preciso", ini: 15.169, fim: 15.649, cena: 2, quebraApos: true },
    { p: "ao", ini: 15.649, fim: 16.249, cena: 2 },
    { p: "Agente", ini: 16.249, fim: 16.629, cena: 2 },
    { p: "Pessoal", ini: 16.629, fim: 17.049, cena: 2 },
    { p: "IA,", ini: 17.049, fim: 17.449, cena: 2, quebraApos: true },
    { p: "e", ini: 17.449, fim: 18.229, cena: 2 },
    { p: "ele", ini: 18.229, fim: 18.449, cena: 2 },
    { p: "pesquisa", ini: 18.449, fim: 18.869, cena: 2 },
    { p: "por", ini: 18.869, fim: 19.069, cena: 2 },
    { p: "mim.", ini: 19.069, fim: 19.289, cena: 2, quebraApos: true },
    { p: "Eu", ini: 20.879, fim: 21.459, cena: 3 },
    { p: "recebo", ini: 21.459, fim: 21.779, cena: 3 },
    { p: "a", ini: 21.779, fim: 21.899, cena: 3 },
    { p: "tarefa", ini: 21.899, fim: 22.279, cena: 3 },
    { p: "concluída", ini: 22.279, fim: 22.899, cena: 3, quebraApos: true },
    { p: "e", ini: 22.899, fim: 23.319, cena: 3 },
    { p: "uso", ini: 23.319, fim: 23.499, cena: 3 },
    { p: "a", ini: 23.499, fim: 24.289, cena: 3 },
    { p: "manhã", ini: 24.289, fim: 25.079, cena: 3 },
    { p: "para", ini: 25.079, fim: 25.259, cena: 3 },
    { p: "cuidar", ini: 25.259, fim: 25.679, cena: 3, quebraApos: true },
    { p: "do", ini: 25.679, fim: 25.759, cena: 3 },
    { p: "que", ini: 25.759, fim: 25.919, cena: 3 },
    { p: "faz", ini: 25.919, fim: 26.119, cena: 3 },
    { p: "a", ini: 26.119, fim: 26.259, cena: 3 },
    { p: "empresa", ini: 26.259, fim: 26.539, cena: 3 },
    { p: "crescer.", ini: 26.539, fim: 27.039, cena: 3, quebraApos: true },
    { p: "Chame", ini: 28.066, fim: 28.415, cena: 4 },
    { p: "a", ini: 28.427, fim: 28.487, cena: 4 },
    { p: "gente", ini: 28.499, fim: 28.823, cena: 4 },
    { p: "no", ini: 28.835, fim: 28.931, cena: 4 },
    { p: "direct", ini: 28.944, fim: 29.557, cena: 4 }
  ]
};
