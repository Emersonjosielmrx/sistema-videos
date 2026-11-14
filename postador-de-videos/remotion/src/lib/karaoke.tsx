import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

// Legenda karaokê PRONTA (27/10). Editor escrevendo a sua dava "TUMBAMONUMENTAL": a palavra ativa crescia
// (scale) e o brilho comia a margem. Aqui: espaço real entre palavras (gap), destaque por pílula de cor (sem
// scale) e a caixa nunca aparece vazia (o bloco fica até a fala seguinte começar).

export type PalavraK = {
  p: string;
  ini: number;
  fim: number;
  quebraAntes?: boolean;
  quebraApos?: boolean;
  quebraLinha?: boolean;
}; // segundos absolutos no vídeo

type Props = {
  palavras: PalavraK[];
  fontFamily?: string;
  destaque: string; // cor da pílula da palavra falada
  textoDestaque?: string; // cor da letra dentro da pílula
  tamanho?: number; // px (>= 40)
  base?: number; // distância do fundo da tela até a BASE da caixa (base da caixa em y = 1920 - base <= 1580)
  maxLetras?: number; // letras por bloco (2 linhas no máximo)
  pausaQuebra?: number; // silêncio (s) que começa bloco novo
};

const blocos = (ps: PalavraK[], maxLetras: number, pausa: number) => {
  const out: PalavraK[][] = [];
  let atual: PalavraK[] = [];
  let letras = 0;
  ps.forEach((w, i) => {
    const pausaAntes = i > 0 && w.ini - ps[i - 1].fim > pausa;
    const fimFrase = i > 0 && /[.!?]$/.test(ps[i - 1].p);
    const quebraForcada = Boolean(w.quebraAntes || (i > 0 && ps[i - 1].quebraApos));
    if (atual.length && (letras + w.p.length > maxLetras || pausaAntes || fimFrase || quebraForcada)) {
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
}) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const bs = blocos(palavras, maxLetras, pausaQuebra);
  // bloco visível: do início da 1ª palavra (−0,1 s) até o início do próximo bloco (ou 2,0 s depois da última para cobrir o final)
  const i = bs.findIndex((b, k) => {
    const ini = b[0].ini - 0.1;
    const fim = k + 1 < bs.length ? bs[k + 1][0].ini - 0.1 : b[b.length - 1].fim + 2.0;
    return t >= ini && t < fim;
  });
  if (i < 0) return null;
  const blocoAtual = bs[i];
  const blocoFim = i + 1 < bs.length ? bs[i + 1][0].ini - 0.1 : blocoAtual[blocoAtual.length - 1].fim + 2.0;
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
          columnGap: Math.round(tamanho * 0.16),
          rowGap: Math.round(tamanho * 0.18),
          maxWidth: 960,
          padding: '14px 22px',
          borderRadius: 22,
          background: 'rgba(10, 10, 12, 0.72)',
        }}
      >
        {blocoAtual.map((w, k) => {
          const proximoIni = k + 1 < blocoAtual.length ? blocoAtual[k + 1].ini : blocoFim;
          const fimEfetivo = k + 1 < blocoAtual.length ? proximoIni : Math.min(w.fim + 0.25, blocoFim);
          const ativa = t >= w.ini && t < fimEfetivo;
          const dita = t >= fimEfetivo;
          return (
            <React.Fragment key={k}>
              {w.quebraLinha && (
                <div style={{width: '100%', height: 0, flexBasis: '100%'}} />
              )}
              <span
                style={{
                  fontFamily,
                  fontSize: tamanho,
                  fontWeight: 900,
                  lineHeight: 1.15,
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                  padding: ativa ? '2px 8px' : '2px 3px',
                  borderRadius: 10,
                  background: ativa ? destaque : 'transparent',
                  color: ativa ? textoDestaque : dita ? '#FFFFFF' : '#CBD5E1',
                  textShadow: ativa ? 'none' : '0 3px 8px rgba(0,0,0,0.9)',
                }}
              >
                {w.p.trim()}
              </span>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
