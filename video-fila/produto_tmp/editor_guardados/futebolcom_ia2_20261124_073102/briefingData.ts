import {PalavraK} from '../../lib/karaoke';

export interface PalavraBriefing extends PalavraK {
  cena: number;
}

export const PALAVRAS_RAW: PalavraBriefing[] = [
  { p: 'Seu', ini: 0.316, fim: 0.571, cena: 0 },
  { p: 'cliente', ini: 0.582, fim: 0.964, cena: 0 },
  { p: 'desiste', ini: 0.976, fim: 1.404, cena: 0 },
  { p: 'do', ini: 1.416, fim: 1.508, cena: 0 },
  { p: 'pedido', ini: 1.52, fim: 1.948, cena: 0 },
  { p: 'quando', ini: 1.96, fim: 2.203, cena: 0 },
  { p: 'precisa', ini: 2.214, fim: 2.654, cena: 0 },
  { p: 'instalar', ini: 2.666, fim: 3.059, cena: 0 },
  { p: 'alguma', ini: 3.071, fim: 3.407, cena: 0 },
  { p: 'coisa', ini: 3.418, fim: 3.87, cena: 0 },
  { p: 'Eu', ini: 5.455, fim: 5.559, cena: 1 },
  { p: 'temia', ini: 5.571, fim: 5.953, cena: 1 },
  { p: 'que', ini: 5.965, fim: 6.057, cena: 1 },
  { p: 'o', ini: 6.069, fim: 6.115, cena: 1 },
  { p: 'cliente', ini: 6.127, fim: 6.532, cena: 1 },
  { p: 'desistisse', ini: 6.543, fim: 7.134, cena: 1 },
  { p: 'na', ini: 7.145, fim: 7.261, cena: 1 },
  { p: 'hora', ini: 7.272, fim: 7.515, cena: 1 },
  { p: 'de', ini: 7.527, fim: 7.608, cena: 1 },
  { p: 'baixar', ini: 7.62, fim: 8.025, cena: 1 },
  { p: 'um', ini: 8.036, fim: 8.117, cena: 1 },
  { p: 'aplicativo', ini: 8.129, fim: 8.8, cena: 1 },
  { p: 'só', ini: 8.812, fim: 8.997, cena: 1 },
  { p: 'para', ini: 9.009, fim: 9.228, cena: 1 },
  { p: 'ver', ini: 9.24, fim: 9.402, cena: 1 },
  { p: 'o', ini: 9.414, fim: 9.448, cena: 1 },
  { p: 'meu', ini: 9.46, fim: 9.587, cena: 1 },
  { p: 'cardápio', ini: 9.599, fim: 10.166, cena: 1 },
  { p: 'Aqui', ini: 11.571, fim: 11.837, cena: 2 },
  { p: 'não', ini: 11.849, fim: 12.011, cena: 2 },
  { p: 'tem', ini: 12.023, fim: 12.173, cena: 2 },
  { p: 'instalação', ini: 12.185, fim: 12.833, cena: 2 },
  { p: 'O', ini: 13.072, fim: 13.142, cena: 2 },
  { p: 'cardápio', ini: 13.153, fim: 13.697, cena: 2 },
  { p: 'abre', ini: 13.709, fim: 13.952, cena: 2 },
  { p: 'direto', ini: 13.963, fim: 14.368, cena: 2 },
  { p: 'no', ini: 14.38, fim: 14.461, cena: 2 },
  { p: 'navegador', ini: 14.473, fim: 15.005, cena: 2 },
  { p: 'do', ini: 15.017, fim: 15.121, cena: 2 },
  { p: 'celular', ini: 15.132, fim: 15.642, cena: 2 },
  { p: 'com', ini: 15.688, fim: 15.85, cena: 2 },
  { p: 'fotos', ini: 15.862, fim: 16.336, cena: 2 },
  { p: 'e', ini: 16.533, fim: 16.602, cena: 2 },
  { p: 'a', ini: 16.614, fim: 16.649, cena: 2 },
  { p: 'IA', ini: 16.66, fim: 17.841, cena: 2 },
  { p: 'responde', ini: 17.852, fim: 18.327, cena: 2 },
  { p: 'dúvidas', ini: 18.338, fim: 18.767, cena: 2 },
  { p: 'na', ini: 18.778, fim: 18.929, cena: 2 },
  { p: 'hora', ini: 18.94, fim: 19.23, cena: 2 },
  { p: 'O', ini: 20.639, fim: 20.72, cena: 3 },
  { p: 'cliente', ini: 20.732, fim: 21.102, cena: 3 },
  { p: 'escolhe', ini: 21.114, fim: 21.496, cena: 3 },
  { p: 'pelas', ini: 21.507, fim: 21.774, cena: 3 },
  { p: 'fotos', ini: 21.785, fim: 22.202, cena: 3 },
  { p: 'faz', ini: 22.318, fim: 22.433, cena: 3 },
  { p: 'o', ini: 22.445, fim: 22.549, cena: 3 },
  { p: 'pedido', ini: 22.561, fim: 22.966, cena: 3 },
  { p: 'pelo', ini: 22.977, fim: 23.151, cena: 3 },
  { p: 'WhatsApp', ini: 23.162, fim: 23.776, cena: 3 },
  { p: 'e', ini: 23.799, fim: 23.88, cena: 3 },
  { p: 'a', ini: 23.892, fim: 23.95, cena: 3 },
  { p: 'sua', ini: 23.961, fim: 24.146, cena: 3 },
  { p: 'loja', ini: 24.158, fim: 24.505, cena: 3 },
  { p: 'não', ini: 24.517, fim: 24.713, cena: 3 },
  { p: 'perde', ini: 24.725, fim: 25.037, cena: 3 },
  { p: 'venda', ini: 25.049, fim: 25.35, cena: 3 },
  { p: 'por', ini: 25.362, fim: 25.5, cena: 3 },
  { p: 'causa', ini: 25.524, fim: 25.824, cena: 3 },
  { p: 'de', ini: 25.836, fim: 25.905, cena: 3 },
  { p: 'aplicativo', ini: 25.917, fim: 26.646, cena: 3 },
  { p: 'Chame', ini: 28.051, fim: 28.387, cena: 4 },
  { p: 'a', ini: 28.399, fim: 28.456, cena: 4 },
  { p: 'gente', ini: 28.468, fim: 28.78, cena: 4 },
  { p: 'no', ini: 28.792, fim: 28.885, cena: 4 },
  { p: 'direct', ini: 28.896, fim: 29.486, cena: 4 },
];

// Legenda Karaokê com isolamento estrito por blocos semânticos e sem cartão final
export const PALAVRAS_KARAOKE: PalavraK[] = PALAVRAS_RAW
  .filter((w) => w.cena < 4) // Cartão final (cena 4) não mostra legenda
  .map((w, idx, arr) => {
    const isPrimeiraDaCena = idx === 0 || arr[idx - 1].cena !== w.cena;
    const isUltimaDaCena = idx === arr.length - 1 || arr[idx + 1].cena !== w.cena;

    // Quebras semânticas para blocos harmônicos e evitar palavras órfãs (Regra 18)
    let quebraApos = isUltimaDaCena;
    let quebraAntes = isPrimeiraDaCena;

    // Cena 0
    if (w.p === 'pedido' && w.cena === 0) quebraApos = true;
    if (w.p === 'quando' && w.cena === 0) quebraAntes = true;

    // Cena 1
    if (w.p === 'cliente' && w.cena === 1) quebraApos = true;
    if (w.p === 'desistisse' && w.cena === 1) quebraAntes = true;
    if (w.p === 'hora' && w.cena === 1) quebraApos = true;
    if (w.p === 'de' && w.cena === 1) quebraAntes = true;
    if (w.p === 'aplicativo' && w.cena === 1) quebraApos = true;
    if (w.p === 'só' && w.cena === 1) quebraAntes = true;

    // Cena 2
    if (w.p === 'instalação' && w.cena === 2) quebraApos = true;
    if (w.p === 'O' && w.cena === 2) quebraAntes = true;
    if (w.p === 'direto' && w.cena === 2) quebraApos = true;
    if (w.p === 'no' && w.cena === 2) quebraAntes = true;
    if (w.p === 'celular' && w.cena === 2) quebraApos = true;
    if (w.p === 'com' && w.cena === 2) quebraAntes = true;
    if (w.p === 'fotos' && w.cena === 2) quebraApos = true;
    if (w.p === 'e' && w.cena === 2) quebraAntes = true;

    // Cena 3
    if (w.p === 'fotos' && w.cena === 3) quebraApos = true;
    if (w.p === 'faz' && w.cena === 3) quebraAntes = true;
    if (w.p === 'WhatsApp' && w.cena === 3) quebraApos = true;
    if (w.p === 'e' && w.cena === 3) quebraAntes = true;
    if (w.p === 'venda' && w.cena === 3) quebraApos = true;
    if (w.p === 'por' && w.cena === 3) quebraAntes = true;

    return {
      p: w.p,
      ini: w.ini,
      fim: w.fim,
      quebraAntes,
      quebraApos,
    };
  });
