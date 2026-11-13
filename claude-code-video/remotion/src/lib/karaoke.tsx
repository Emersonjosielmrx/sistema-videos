import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {movimento, Movimento} from './efeitos';

// Legenda karaokê PRONTA (27/10). Editor escrevendo a sua dava "TUMBAMONUMENTAL": a palavra ativa crescia
// (scale) e o brilho comia a margem. Aqui: espaço real entre palavras (gap), destaque por pílula de cor (sem
// scale) e a caixa nunca aparece vazia (o bloco fica até a fala seguinte começar).
// 28/10: opções do caption-fine do Hypit (padrão: entrada 'mola' + resposta 'pop'; o resto o editor escolhe):
//   modo      'pilula' (padrão) | 'trilha' (o que já foi dito fica na cor) | 'varrer' (a cor enche a palavra
//             enquanto ela é falada) | 'cor' (só a letra muda de cor, sem pílula)
//   entrada   movimento do bloco quando ele aparece ('mola', 'pop', 'subir', 'desfoque'... os do <Surgir>)
//   revelar   'todas' (padrão) | 'ao_falar' (cada palavra aparece quando é dita) | 'digitar' (letra por letra)
//   resposta  'nenhuma' (padrão) | 'pop' | 'mola': pulinho da palavra falada (o espaço cresce junto, não gruda)
//   falante + cores: quem fala muda a cor do destaque e começa bloco novo (diálogo, entrevista, debate)
//   caixa     false = sem a caixa escura, com contorno na letra (para cima de foto clara)

export type PalavraK = {p: string; ini: number; fim: number; falante?: string}; // segundos absolutos no vídeo
export type Palavra = PalavraK; // nome antigo: vídeos de 27/10 importam assim e o editor copia deles

type Props = {
  palavras: PalavraK[];
  fontFamily?: string;
  destaque: string; // cor da pílula da palavra falada
  textoDestaque?: string; // cor da letra dentro da pílula
  tamanho?: number; // px (>= 40)
  base?: number; // distância do fundo da tela até a BASE da caixa (base da caixa em y = 1920 - base <= 1580)
  maxLetras?: number; // letras por bloco (2 linhas no máximo)
  pausaQuebra?: number; // silêncio (s) que começa bloco novo
  modo?: 'pilula' | 'trilha' | 'varrer' | 'cor';
  entrada?: Movimento | 'nenhuma';
  entradaQuadros?: number;
  revelar?: 'todas' | 'ao_falar' | 'digitar';
  resposta?: 'nenhuma' | 'pop' | 'mola';
  cores?: Record<string, string>; // falante -> cor do destaque
  caixa?: boolean;
  maiusculas?: boolean;
};

const blocos = (ps: PalavraK[], maxLetras: number, pausa: number) => {
  const out: PalavraK[][] = [];
  let atual: PalavraK[] = [];
  let letras = 0;
  ps.forEach((w, i) => {
    const pausaAntes = i > 0 && w.ini - ps[i - 1].fim > pausa;
    const fimFrase = i > 0 && /[.!?]$/.test(ps[i - 1].p);
    const trocaFalante = i > 0 && (w.falante ?? '') !== (ps[i - 1].falante ?? '');
    if (atual.length && (letras + w.p.length > maxLetras || pausaAntes || fimFrase || trocaFalante)) {
      out.push(atual);
      atual = [];
      letras = 0;
    }
    atual.push(w);
    letras += w.p.length + 1;
  });
  if (atual.length) out.push(atual);
  return out;
};

export const Karaoke: React.FC<Props> = ({
  palavras,
  fontFamily,
  destaque,
  textoDestaque = '#111111',
  tamanho = 46,
  base = 360,
  maxLetras = 30,
  pausaQuebra = 0.7,
  modo = 'pilula',
  entrada = 'mola', // 28/10 (dona): legenda nova LIGADA — cada bloco entra com mola e a palavra falada dá um pulinho
  entradaQuadros = 6,
  revelar = 'todas',
  resposta = 'pop',
  cores,
  caixa = true,
  maiusculas = true,
}) => {
  const {fps} = useVideoConfig();
  const t = useCurrentFrame() / fps;
  const bs = blocos(palavras, maxLetras, pausaQuebra);
  // bloco visível: do início da 1ª palavra (−0,1 s) até o início do próximo bloco (ou 0,6 s depois da última)
  const i = bs.findIndex((b, k) => {
    const ini = b[0].ini - 0.1;
    const fim = k + 1 < bs.length ? bs[k + 1][0].ini - 0.1 : b[b.length - 1].fim + 0.6;
    return t >= ini && t < fim;
  });
  if (i < 0) return null;
  const bloco = bs[i];
  const corDe = (w: PalavraK) => (w.falante && cores?.[w.falante]) || destaque;
  const ent = entrada === 'nenhuma' ? null : movimento(entrada, ((t - (bloco[0].ini - 0.1)) * fps) / entradaQuadros);
  const pula = resposta !== 'nenhuma';
  const contorno = caixa ? '0 3px 8px rgba(0,0,0,0.9)'
    : '0 0 2px #000, 2px 2px 0 #000, -2px 2px 0 #000, 2px -2px 0 #000, -2px -2px 0 #000, 0 4px 12px rgba(0,0,0,0.9)';
  return (
    <div
      style={{
        position: 'absolute',
        left: 60,
        right: 60,
        bottom: base,
        display: 'flex',
        justifyContent: 'center',
        pointerEvents: 'none',
        zIndex: 90,
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'center',
          columnGap: Math.round(tamanho * (pula ? 0.45 : 0.32)),
          rowGap: Math.round(tamanho * (pula ? 0.26 : 0.18)),
          maxWidth: 940,
          padding: '14px 22px',
          borderRadius: 22,
          background: caixa ? 'rgba(10, 10, 12, 0.72)' : 'transparent',
          ...(ent ? {opacity: ent.opacity, transform: ent.transform,
            filter: ent.filter === 'none' ? undefined : ent.filter, clipPath: ent.clipPath} : {}),
        }}
      >
        {bloco.map((w, k) => {
          const ativa = t >= w.ini && t <= w.fim + 0.05;
          const dita = t > w.fim;
          const cor = corDe(w);
          const pilula = (modo === 'pilula' && ativa) || (modo === 'trilha' && (ativa || dita));
          const corLetra = pilula ? textoDestaque
            : modo === 'cor' && ativa ? cor
            : dita || modo === 'varrer' ? '#FFFFFF' : 'rgba(255,255,255,0.6)';
          // aparecer (ao_falar/digitar): a palavra ocupa o lugar desde o começo, o bloco não pula
          const antes = revelar !== 'todas' && t < w.ini - 0.02;
          const entra = revelar === 'ao_falar' && !antes ? movimento('pop', ((t - w.ini) * fps) / 5) : null;
          const pDig = revelar === 'digitar' ? Math.max(0, Math.min(1, (t - w.ini) / Math.max(0.12, w.fim - w.ini))) : 1;
          const nVis = revelar === 'digitar' ? Math.ceil(w.p.length * pDig) : w.p.length;
          const q = ((t - w.ini) * fps) / 7;
          const esc = pula && ativa && q <= 1
            ? (resposta === 'pop' ? 1 + 0.12 * Math.sin(Math.PI * q) : 1 + 0.12 * Math.exp(-4 * q) * Math.sin(12 * q))
            : 1;
          const pVarre = Math.max(0, Math.min(1, (t - w.ini) / Math.max(0.05, w.fim - w.ini)));
          const estilo: React.CSSProperties = {
            fontFamily,
            fontSize: tamanho,
            fontWeight: 900,
            lineHeight: 1.15,
            textTransform: maiusculas ? 'uppercase' : 'none',
            whiteSpace: 'nowrap',
            padding: '2px 10px',
            borderRadius: 10,
            position: 'relative',
            display: 'inline-block',
            background: pilula ? cor : 'transparent',
            color: corLetra,
            textShadow: pilula ? 'none' : contorno,
            opacity: antes ? 0 : entra ? entra.opacity : 1,
            transform: entra && entra.transform !== 'none' ? entra.transform : esc !== 1 ? `scale(${esc})` : undefined,
          };
          return (
            <span key={k} style={estilo}>
              {w.p.slice(0, nVis)}
              {nVis < w.p.length && <span style={{color: 'transparent', textShadow: 'none'}}>{w.p.slice(nVis)}</span>}
              {modo === 'varrer' && (dita || ativa) && (
                <span aria-hidden style={{position: 'absolute', left: 10, top: 2, color: cor, textShadow: contorno,
                  clipPath: `inset(0 ${(dita ? 0 : 1 - pVarre) * 100}% 0 0)`}}>
                  {w.p.slice(0, nVis)}
                </span>
              )}
            </span>
          );
        })}
      </div>
    </div>
  );
};
