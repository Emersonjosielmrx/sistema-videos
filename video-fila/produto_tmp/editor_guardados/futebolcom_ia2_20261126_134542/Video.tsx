import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {fontFamily} from './fontes';
import {Karaoke} from '../../lib/karaoke';
import briefingData from '../../../trabalhos/futebolcom_ia2_20261126_134542/public/briefing.json';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const CORES = {
  marca: '#E11D48',
  apoio: '#FACC15',
  fundo_escuro: '#31060F',
  destaque: '#E11D48',
};

const DURACOES = {
  total_s: 30.44,
  fps: 30,
};

// Não exibe karaokê no cartão final (cena 4) e evita linha órfã com "NO" isolado na cena 1
const palavrasKaraoke = briefingData.palavras
  .filter((p) => p.cena < 4)
  .map((p) => {
    // Evita linha órfã com "NO" isolado na cena 1: força quebra após "mensagem"
    if (p.cena === 1 && p.p.toLowerCase() === 'mensagem') {
      return {...p, quebraApos: true};
    }
    return p;
  });

// ----------------------------------------------------
// Barra de progresso no topo (y = 152)
// ----------------------------------------------------
const TopProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const progresso = Math.min(1, Math.max(0, frame / durationInFrames));

  return (
    <div
      style={{
        position: 'absolute',
        top: 152,
        left: 60,
        right: 60,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        borderRadius: 3,
        overflow: 'hidden',
        zIndex: 100,
      }}
    >
      <div
        style={{
          width: `${progresso * 100}%`,
          height: '100%',
          backgroundColor: CORES.apoio,
          borderRadius: 3,
          boxShadow: `0 0 10px ${CORES.apoio}`,
        }}
      />
    </div>
  );
};

// ----------------------------------------------------
// COMPOSIÇÃO PRINCIPAL
// ----------------------------------------------------
export const Video: React.FC = () => {
  const {fps} = useVideoConfig();

  const fCena0 = 0;
  const dCena0 = Math.round(4.69 * fps);

  const fCena1 = Math.round(4.34 * fps);
  const dCena1 = Math.round((11.28 - 4.34) * fps);

  const fCena2 = Math.round(10.93 * fps);
  const dCena2 = Math.round((19.11 - 10.93) * fps);

  const fCena3 = Math.round(18.76 * fps);
  const dCena3 = Math.round((26.95 - 18.76) * fps);

  const fCena4 = Math.round(26.6 * fps);
  const dCena4 = Math.round((30.44 - 26.6) * fps);

  return (
    <AbsoluteFill style={{backgroundColor: '#000000'}}>
      {/* 1. Trilha Sonora de fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={0.1} />

      {/* 2. Narração completa original */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 3. Sequências visuais modulares */}
      <Sequence from={fCena0} durationInFrames={dCena0}>
        <Cena0 />
      </Sequence>

      <Sequence from={fCena1} durationInFrames={dCena1}>
        <Cena1 />
      </Sequence>

      <Sequence from={fCena2} durationInFrames={dCena2}>
        <Cena2 />
      </Sequence>

      <Sequence from={fCena3} durationInFrames={dCena3}>
        <Cena3 />
      </Sequence>

      <Sequence from={fCena4} durationInFrames={dCena4}>
        <Cena4 />
      </Sequence>

      {/* 4. Barra de progresso no topo presente no vídeo todo */}
      <TopProgressBar />

      {/* 5. Legenda Karaokê pronta (só nas falas das cenas 0 a 3, NÃO no cartão final) */}
      <Sequence from={0} durationInFrames={fCena4}>
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={CORES.destaque}
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={360}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Video}
      fps={DURACOES.fps}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(DURACOES.total_s * DURACOES.fps)}
    />
  );
};
