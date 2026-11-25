import React from 'react';
import {
  Audio,
  Composition,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Carrega briefing estático
const briefing = require('../../../trabalhos/landingpageia_ia_20261122_180432/public/briefing.json');

// Duração total exata
const DURAÇÃO_S = briefing.duracao_s || 31.8;
const TOTAL_FRAMES = Math.ceil(DURAÇÃO_S * 30); // 954 frames

// Prepara palavras para o Karaokê com quebras harmônicas e equilibradas
const rawPalavras = (briefing.palavras as PalavraK[]).filter(
  (p: any) => p.cena !== 4
);

const karaokePalavras: PalavraK[] = rawPalavras.map((w, i) => {
  const item: PalavraK = {...w};

  // Quebras de Cena obrigatórias
  if (i > 0 && (w as any).cena !== (rawPalavras[i - 1] as any).cena) {
    item.quebraAntes = true;
  }
  if (
    i < rawPalavras.length - 1 &&
    (w as any).cena !== (rawPalavras[i + 1] as any).cena
  ) {
    item.quebraApos = true;
  }

  // Cena 0:
  // "Por que eu repito" | "as mesmas respostas" | "no WhatsApp / o dia inteiro"
  if (i === 3) item.quebraApos = true; // "repito"
  if (i === 6) item.quebraApos = true; // "respostas"
  if (i === 9) item.quebraLinha = true; // "o" (L2: "o dia inteiro")

  // Cena 1:
  // "Eu passava o dia" | "respondendo as mesmas / dúvidas no WhatsApp," | "explicando meu produto / para cada cliente," | "um por um."
  if (i === 15) item.quebraApos = true; // "dia"
  if (i === 19) item.quebraLinha = true; // "dúvidas"
  if (i === 21) item.quebraApos = true; // "WhatsApp,"
  if (i === 25) item.quebraLinha = true; // "para"
  if (i === 27) item.quebraApos = true; // "cliente,"

  // Cena 2:
  // "Hoje uso uma / página de vendas pronta," | "com vídeo de demonstração" | "que apresenta / o produto por mim."
  if (i === 34) item.quebraLinha = true; // "página"
  if (i === 37) item.quebraApos = true; // "pronta,"
  if (i === 41) item.quebraApos = true; // "demonstração"
  if (i === 44) item.quebraLinha = true; // "o" (L2: "o produto por mim.")

  // Cena 3:
  // "Agora o cliente já / chega entendendo o produto," | "e eu uso meu / tempo para vender," | "não para explicar."
  if (i === 52) item.quebraLinha = true; // "chega"
  if (i === 55) item.quebraApos = true; // "produto,"
  if (i === 60) item.quebraLinha = true; // "tempo"
  if (i === 62) item.quebraApos = true; // "vender,"

  return item;
});

// Componente Principal
const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Controle de volume da trilha sonora (0.10 durante narração, 0.20 no cartão final, fades suaves)
  const volumeTrilha = (f: number) => {
    if (f < 15) return (f / 15) * 0.1;
    if (f < 836) return 0.1;
    if (f < 924) return 0.2;
    return Math.max(0, ((954 - f) / 30) * 0.2);
  };

  // Progresso do topo (0% a 100%)
  const progresso = Math.min(100, (frame / TOTAL_FRAMES) * 100);

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#0B0D13',
        overflow: 'hidden',
      }}
    >
      {/* Áudio: Narração completa (voz da narradora + dono) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Áudio: Trilha sonora balanceada */}
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha} />

      {/* Cenas sequenciadas com sobreposição suave de transição */}

      {/* Cena 0: Pergunta / Gancho dramático (0.00s a 5.17s) */}
      <Sequence from={0} durationInFrames={155}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O Problema (4.82s a 13.00s) */}
      <Sequence from={145} durationInFrames={245}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Dono - Como Funciona (12.65s a 20.37s) */}
      <Sequence from={380} durationInFrames={232}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono - O Resultado (20.02s a 28.21s) */}
      <Sequence from={601} durationInFrames={246}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (27.86s a 31.80s) */}
      <Sequence from={836} durationInFrames={118}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (Safe Zone y >= 150) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 4,
          borderRadius: 2,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: '#F59E0B',
            boxShadow: '0 0 10px rgba(245, 158, 11, 0.9)',
          }}
        />
      </div>

      {/* Legenda Karaokê Pronta e Sincronizada (oculta no cartão final frame >= 836) */}
      {frame < 836 && (
        <Karaoke
          palavras={karaokePalavras}
          fontFamily={fontFamily}
          destaque="#F59E0B"
          textoDestaque="#121216"
          tamanho={44}
          base={360}
          maxLetras={50}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={TOTAL_FRAMES}
    />
  );
};
