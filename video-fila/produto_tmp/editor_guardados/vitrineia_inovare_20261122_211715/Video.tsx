import React from 'react';
import {
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {briefing} from './briefing';
import {ProgressBar} from './ProgressBar';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Dono} from './Cena1Dono';
import {Cena2Conversa} from './Cena2Conversa';
import {Cena3Dono} from './Cena3Dono';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont();

// Filtra as palavras para o karaokê: proíbe legenda no cartão final (cena 4)
const palavrasKaraoke = briefing.palavras.filter((p) => p.cena < 4);

export const MainVideo: React.FC = () => {
  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: briefing.cores.fundo_escuro,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio Oficial da Narração Completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha Sonora com volume ajustado e fade in/out suave */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const fadeIn = interpolate(f, [0, 30], [0, 0.11], {
            extrapolateRight: 'clamp',
          });
          const fadeOut = interpolate(f, [960, 1000], [0.11, 0], {
            extrapolateLeft: 'clamp',
          });
          return Math.min(fadeIn, fadeOut);
        }}
      />

      {/* CENA 0: Pergunta / Dor Inicial (0.0s a 5.41s | Frames 0 a 162) */}
      <Sequence from={0} durationInFrames={162}>
        <Cena0Pergunta
          fontFamily={fontFamily}
          marcaCor={briefing.cores.marca}
          apoioCor={briefing.cores.apoio}
        />
      </Sequence>

      {/* CENA 1: Dono - O Problema (5.06s a 13.24s | Frames 152 a 397) */}
      <Sequence from={152} durationInFrames={245}>
        <Cena1Dono
          fontFamily={fontFamily}
          marcaCor={briefing.cores.marca}
        />
      </Sequence>

      {/* CENA 2: Conversa - Como Funciona (12.89s a 21.90s | Frames 387 a 657) */}
      <Sequence from={387} durationInFrames={270}>
        <Cena2Conversa
          fontFamily={fontFamily}
          marcaCor={briefing.cores.marca}
          apoioCor={briefing.cores.apoio}
        />
      </Sequence>

      {/* CENA 3: Dono - O Resultado (21.55s a 29.74s | Frames 647 a 892) */}
      <Sequence from={647} durationInFrames={245}>
        <Cena3Dono
          fontFamily={fontFamily}
          marcaCor={briefing.cores.marca}
        />
      </Sequence>

      {/* CENA 4: Cartão Final / CTA (29.39s a 33.33s | Frames 882 a 1000) */}
      <Sequence from={882} durationInFrames={118}>
        <Cena4Cartao
          fontFamily={fontFamily}
          marcaCor={briefing.cores.marca}
          apoioCor={briefing.cores.apoio}
          arroba={briefing.arroba}
          convite={briefing.convite}
        />
      </Sequence>

      {/* Legenda Karaokê Oficial (y=1320 a 1580, base 360 -> bottom em 1560) */}
      <Karaoke
        palavras={palavrasKaraoke}
        fontFamily={fontFamily}
        destaque={briefing.cores.destaque}
        textoDestaque={briefing.cores.texto_sobre_marca}
        tamanho={46}
        base={360}
      />

      {/* Barra de Progresso Fina no Topo da Safe Zone (y=152) */}
      <ProgressBar color={briefing.cores.marca} />
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
      durationInFrames={1000}
    />
  );
};
