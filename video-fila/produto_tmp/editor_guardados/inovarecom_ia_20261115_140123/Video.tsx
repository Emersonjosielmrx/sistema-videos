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
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import briefing from '../../../trabalhos/inovarecom_ia_20261115_140123/public/briefing.json';

const {fontFamily} = loadFont();

// Volume dinâmico para a trilha musical com ducking automático durante a fala
const getTrilhaVolume = (f: number) => {
  const t = f / 30;
  // Fade in no início
  if (t < 0.4) {
    return interpolate(t, [0, 0.4], [0, 0.1], {extrapolateRight: 'clamp'});
  }
  // Fade out no final do vídeo
  if (t >= 29.8) {
    return interpolate(t, [29.8, 30.37], [0.22, 0], {
      extrapolateRight: 'clamp',
    });
  }
  // Momentos de fala ativa -> volume 0.10; pausas/transições -> volume 0.22
  const isSpeech =
    (t >= 0.3 && t <= 4.0) ||
    (t >= 5.7 && t <= 12.5) ||
    (t >= 13.2 && t <= 18.6) ||
    (t >= 19.8 && t <= 25.6) ||
    (t >= 26.9 && t <= 28.5);

  return isSpeech ? 0.1 : 0.22;
};

// Palavras para exibir Karaokê nas cenas 0 a 3 (suprimido na Cena 4 para não duplicar o CTA)
const palavrasKaraoke = briefing.palavras
  .filter((p) => p.cena < 4)
  .map((p) => {
    // Ajustar o fim da última palavra da cena 3 ('horas') para que +2.0s do Karaoke termine exatamente em 26.47s (antes do corte da cena 4)
    if (p.cena === 3 && p.p === 'horas') {
      return {...p, fim: 24.46};
    }
    return p;
  });

export const MainComponent: React.FC = () => {
  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: '#082E16',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* 1. Trilha Sonora de Fundo com volume ducking */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} loop />

      {/* 2. Locução Completa montada (Voz narradora + Dono) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 3. Barra de Progresso no Topo (y=152) */}
      <ProgressBar />

      {/* 4. Cenas em Sequences com tempos precisos do briefing */}
      {/* Cena 0: pergunta (0.00s a 5.31s | 160 frames) */}
      <Sequence from={0} durationInFrames={160}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: dono (4.96s a 13.15s | 246 frames, starts at frame 149) */}
      <Sequence from={149} durationInFrames={246}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: conversa (12.80s a 19.74s | 208 frames, starts at frame 384) */}
      <Sequence from={384} durationInFrames={208}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: veo (19.39s a 26.82s | 223 frames, starts at frame 582) */}
      <Sequence from={582} durationInFrames={223}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: cartao (26.47s a 30.37s | 118 frames, starts at frame 794) */}
      <Sequence from={794} durationInFrames={118}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* 5. Karaokê Oficial ancorado acima de y=1510 (base=410) */}
      <Karaoke
        palavras={palavrasKaraoke}
        fontFamily={fontFamily}
        destaque="#25D366"
        textoDestaque="#121216"
        base={410}
        maxLetras={26}
      />
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainComponent}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
