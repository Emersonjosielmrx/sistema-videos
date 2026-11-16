import React from 'react';
import {
  Composition,
  Sequence,
  Audio,
  staticFile,
  interpolate,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {CORES, TOTAL_FRAMES} from './constants';
import {PALAVRAS_KARAOKE} from './palavras';
import {Karaoke} from '../../lib/karaoke';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont('normal', {
  weights: ['400', '600', '700', '800', '900'],
  subsets: ['latin'],
});

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Curva de volume da trilha musical
  const getTrilhaVolume = (f: number) => {
    // Fade in no início
    if (f < 30) {
      return interpolate(f, [0, 30], [0, 0.10], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    // Fade out nos últimos frames
    if (f > 930) {
      return interpolate(f, [930, 963], [0.15, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    // No cartão final, sobe para dar energia ao CTA
    if (f >= 843) {
      return 0.15;
    }
    // Volume constante durante fala
    return 0.10;
  };

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: CORES.fundo_escuro,
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio Oficial da Narração e Trilha Sonora */}
      <Audio src={staticFile('narracao.mp3')} />
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => getTrilhaVolume(f)}
      />

      {/* Cenas Sequenciais com Pequena Sobreposição Suave */}
      <Sequence from={0} durationInFrames={178} name="Cena 0 - Pergunta">
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={168} durationInFrames={199} name="Cena 1 - Problema">
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={356} durationInFrames={268} name="Cena 2 - Conversa">
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={613} durationInFrames={241} name="Cena 3 - Dono">
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={843} durationInFrames={120} name="Cena 4 - Cartão Final">
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (y = 152) */}
      <ProgressBar />

      {/* Karaokê Oficial sincronizado com a fala (mantido até o final do vídeo) */}
      <Karaoke
        palavras={PALAVRAS_KARAOKE}
        fontFamily={fontFamily}
        destaque={CORES.destaque}
        textoDestaque="#111827"
        base={440}
        tamanho={41}
        maxLetras={55}
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
