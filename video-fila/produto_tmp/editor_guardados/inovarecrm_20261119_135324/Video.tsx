import React from 'react';
import {
  Audio,
  Composition,
  Sequence,
  staticFile,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {briefingData} from './briefingData';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const TOTAL_FRAMES = Math.ceil(briefingData.duracao_s * 30); // 987 frames

// Controle de volume profissional da trilha sonora (fade in, ducking com voz e fade out)
const getTrilhaVolume = (frame: number) => {
  const t = frame / 30;
  // Fade in inicial de 0.8s
  const fadeIn = Math.min(1, t / 0.8);
  // Fade out final de 1.5s
  const fadeOut = Math.max(0, Math.min(1, (briefingData.duracao_s - t) / 1.5));
  // Volume com fala: ~0.10; no final sem fala: ~0.20
  const baseVolume = t > 31.0 ? 0.20 : 0.10;
  return baseVolume * fadeIn * fadeOut;
};

const MainVideo: React.FC = () => {
  const {fontFamily} = loadFont();

  // Palavras para o Karaokê (excluindo a cena 4 para cumprir a regra de não ter legenda no cartão final)
  const karaokePalavras = briefingData.palavras.filter((p) => p.cena !== 4);

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio Oficial Completo */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* CENA 0: Pergunta / Dor (0.0s a 5.22s | frames 0 a 157) */}
      <Sequence from={0} durationInFrames={157}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 1: Apresentador / Dono (4.87s a 12.41s | frames 146 a 372) */}
      <Sequence from={146} durationInFrames={226}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 2: Conversa / Como Funciona (12.06s a 21.33s | frames 362 a 640) */}
      <Sequence from={362} durationInFrames={278}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 3: Resultado / Benefícios (20.98s a 29.27s | frames 629 a 878) */}
      <Sequence from={629} durationInFrames={249}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 4: Cartão Final / CTA (28.92s a 32.87s | frames 868 a 987) */}
      <Sequence from={868} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* BARRA DE PROGRESSO NO TOPO (y=150) */}
      <ProgressBar totalFrames={TOTAL_FRAMES} cor="#38BDF8" />

      {/* KARAOKÊ OFICIAL PRONTO (y <= 1560) */}
      <Karaoke
        palavras={karaokePalavras}
        fontFamily={fontFamily}
        destaque={briefingData.cores.destaque}
        textoDestaque="#FFFFFF"
        tamanho={46}
        base={360}
      />
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
