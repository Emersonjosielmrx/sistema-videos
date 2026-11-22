import {PalavraK} from '../../lib/karaoke';

export const BRIEFING = {
  marca: "Inovare Clone",
  produto: "Avatar IA",
  arroba: "@inovareclone",
  convite: "Chame no direct",
  convite_voz: "Chame a gente no direct.",
  gancho_tela: "Vídeos da sua empresa",
  cores: {
    marca: "#8B5CF6",
    apoio: "#1F2937",
    fundo_escuro: "#0F172A",
    destaque: "#8B5CF6",
    destaque_brilho: "#A78BFA",
    destaque_claro: "#DDD6FE",
    texto_sobre_marca: "#FFFFFF",
    bg_card: "rgba(15, 23, 42, 0.88)",
    borda_card: "rgba(139, 92, 246, 0.35)",
  },
  duracao_s: 33.11,
  fps: 30,
};

export const CENAS_CONFIG = [
  { n: 0, ini: 0.0, fim: 4.55, tipo: "pergunta" },
  { n: 1, ini: 4.2, fim: 12.38, tipo: "dono" },
  { n: 2, ini: 12.03, fim: 21.69, tipo: "conversa" },
  { n: 3, ini: 21.34, fim: 29.52, tipo: "dono" },
  { n: 4, ini: 29.17, fim: 33.11, tipo: "cartao" },
];

// Palavras oficiais do briefing ajustadas para quebras de fala limpas
export const PALAVRAS_KARAOKE: PalavraK[] = [
  // Cena 0: Pergunta
  { p: "Falta", ini: 0.318, fim: 0.727, quebraAntes: true },
  { p: "tempo", ini: 0.739, fim: 1.075 },
  { p: "para", ini: 1.087, fim: 1.244 },
  { p: "explicar", ini: 1.256, fim: 1.736 },
  { p: "seus", ini: 1.748, fim: 1.965 },
  { p: "serviços", ini: 1.977, fim: 2.433 },
  { p: "em", ini: 2.445, fim: 2.65 },
  { p: "vídeo", ini: 2.662, fim: 3.082, quebraApos: true },

  // Cena 1: Dono (O problema)
  { p: "Eu", ini: 4.496, fim: 4.976, quebraAntes: true },
  { p: "passava", ini: 4.976, fim: 5.456 },
  { p: "o", ini: 5.456, fim: 5.936 },
  { p: "dia", ini: 5.936, fim: 6.416 },
  { p: "atendendo", ini: 6.416, fim: 6.886 },
  { p: "e", ini: 6.886, fim: 7.366 },
  { p: "nunca", ini: 7.366, fim: 7.846 },
  { p: "sobrava", ini: 7.846, fim: 8.326 },
  { p: "tempo", ini: 8.326, fim: 8.806 },
  { p: "para", ini: 8.806, fim: 9.286 },
  { p: "gravar", ini: 9.286, fim: 9.766 },
  { p: "vídeos", ini: 9.766, fim: 10.246 },
  { p: "explicando", ini: 10.246, fim: 10.726 },
  { p: "cada", ini: 10.726, fim: 11.196 },
  { p: "serviço.", ini: 11.196, fim: 11.676, quebraApos: true },

  // Cena 2: Conversa (A solução)
  { p: "Tenha", ini: 12.522, fim: 12.714, quebraAntes: true },
  { p: "seu", ini: 12.726, fim: 12.907 },
  { p: "próprio", ini: 12.919, fim: 13.291 },
  { p: "avatar", ini: 13.303, fim: 13.664 },
  { p: "IA", ini: 13.676, fim: 14.95 },
  { p: "postando", ini: 14.998, fim: 15.467 },
  { p: "todo", ini: 15.527, fim: 15.839 },
  { p: "dia", ini: 15.851, fim: 16.092 },
  { p: "nas", ini: 16.104, fim: 16.272 },
  { p: "redes", ini: 16.284, fim: 16.777 },
  { p: "Posturas", ini: 17.027, fim: 17.424 },
  { p: "automáticas", ini: 17.436, fim: 18.265 },
  { p: "fala", ini: 18.398, fim: 18.614 },
  { p: "em", ini: 18.626, fim: 18.698 },
  { p: "português", ini: 18.71, fim: 19.275 },
  { p: "cem", ini: 19.371, fim: 19.599 },
  { p: "por", ini: 19.612, fim: 19.744 },
  { p: "cento", ini: 19.756, fim: 20.056 },
  { p: "seu", ini: 20.068, fim: 20.393, quebraApos: true },

  // Cena 3: Dono (O resultado)
  { p: "Agora", ini: 21.737, fim: 22.617, quebraAntes: true },
  { p: "meus", ini: 22.797, fim: 22.817 },
  { p: "serviços", ini: 22.817, fim: 23.457 },
  { p: "ganham", ini: 23.457, fim: 23.737 },
  { p: "explicações", ini: 23.737, fim: 24.437 },
  { p: "claras", ini: 24.437, fim: 24.897 },
  { p: "nas", ini: 24.897, fim: 25.037 },
  { p: "redes", ini: 25.037, fim: 25.277 },
  { p: "sociais", ini: 25.277, fim: 25.777 },
  { p: "todos", ini: 25.777, fim: 26.217 },
  { p: "os", ini: 26.217, fim: 26.457 },
  { p: "dias,", ini: 26.457, fim: 26.917 },
  { p: "enquanto", ini: 26.917, fim: 27.397 },
  { p: "foco", ini: 27.397, fim: 27.937 },
  { p: "nos", ini: 27.937, fim: 28.137 },
  { p: "atendimentos.", ini: 28.137, fim: 28.797, quebraApos: true },
  // Cena 4 não entra no karaokê conforme regra de negócio
];
