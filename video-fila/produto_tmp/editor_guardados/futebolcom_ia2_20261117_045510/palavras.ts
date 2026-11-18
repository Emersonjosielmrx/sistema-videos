import briefingData from '../../../trabalhos/futebolcom_ia2_20261117_045510/public/briefing.json';
import {PalavraK} from '../../lib/karaoke';

export const getPalavrasFormatadas = (): PalavraK[] => {
  return briefingData.palavras.map((item) => {
    const w: PalavraK = {
      p: item.p,
      ini: item.ini,
      fim: item.fim,
    };

    // Cena 0: "Seu cliente ainda espera foto de cardápio para pedir?"
    if (item.p === 'espera' && item.cena === 0) {
      w.quebraLinha = true; // Quebra para 2 linhas equilibradas
    }
    if (item.p === 'pedir' && item.cena === 0) {
      w.quebraApos = true;
    }

    // Cena 1: "Eu enviava arquivo em PDF pesado e percebia que o cliente desistia antes mesmo de abrir."
    if (item.p === 'arquivo' && item.cena === 1) {
      w.quebraLinha = true;
    }
    if (item.p === 'pesado' && item.cena === 1) {
      w.quebraApos = true; // Quebra temática exata da fala
    }
    if (item.p === 'cliente' && item.cena === 1) {
      w.quebraApos = true;
    }
    if (item.p === 'mesmo' && item.cena === 1) {
      w.quebraLinha = true;
    }
    if (item.p === 'abrir.' && item.cena === 1) {
      w.quebraApos = true;
    }

    // Cena 2: "Mudei para o acesso no celular: o cliente visualiza pratos com fotos e a IA esclarece perguntas."
    if (item.p === 'acesso' && item.cena === 2) {
      w.quebraLinha = true;
    }
    if (item.p === 'celular' && item.cena === 2) {
      w.quebraApos = true; // Evita "O" órfão isolado na segunda linha
    }
    if (item.p === 'pratos' && item.cena === 2) {
      w.quebraLinha = true;
    }
    if (item.p === 'fotos' && item.cena === 2) {
      w.quebraApos = true;
    }
    if (item.p === 'IA' && item.cena === 2) {
      w.quebraLinha = true;
    }
    if (item.p === 'perguntas' && item.cena === 2) {
      w.quebraApos = true;
    }

    // Cena 3: "O pedido finalizado chega pronto no WhatsApp, tornando o dia a dia do delivery muito mais ágil."
    if (item.p === 'finalizado' && item.cena === 3) {
      w.quebraLinha = true;
    }
    if (item.p === 'WhatsApp,' && item.cena === 3) {
      w.quebraApos = true;
    }
    if (item.p === 'dia' && item.ini > 24.8 && item.cena === 3) {
      w.quebraLinha = true;
    }
    if (item.p === 'ágil.' && item.cena === 3) {
      w.quebraApos = true;
    }

    return w;
  });
};
