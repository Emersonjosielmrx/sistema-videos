import React, {useMemo} from 'react';
import {
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {ProgressBar} from './ProgressBar';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Dono} from './Cena1Dono';
import {Cena2Conversa} from './Cena2Conversa';
import {Cena3Dono} from './Cena3Dono';
import {Cena4Cartao} from './Cena4Cartao';
import briefingData from '../../../trabalhos/followupia_ia_20261118_114526/public/briefing.json';
import {BriefingData} from './types';

const briefing = briefingData as unknown as BriefingData;

const {fontFamily} = loadFont('normal', {
  weights: ['400', '600', '700', '800', '900'],
});

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Background music volume calculation:
  // ~0.10 during narration, rises to ~0.22 after narration ends (~frame 818 / 27.27s),
  // with fade-in at start and fade-out at the end.
  const trilhaVolume = useMemo(() => {
    return (currentFrame: number) => {
      // Initial fade-in (0 to 15 frames)
      const fadeIn = interpolate(currentFrame, [0, 15], [0, 0.1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });

      // Post-narration swell (frame 818 to 835)
      const swell = interpolate(currentFrame, [818, 835], [0.1, 0.22], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });

      // Final fade-out (last 20 frames)
      const fadeOut = interpolate(
        currentFrame,
        [durationInFrames - 20, durationInFrames],
        [1, 0],
        {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        }
      );

      const baseVol = currentFrame < 818 ? fadeIn : swell;
      return baseVol * fadeOut;
    };
  }, [durationInFrames]);

  // Subtitle words preparation:
  // 1. Exclude scene 4 (final card has NO subtitles, only CTA)
  // 2. Mark `quebraApos` on the last word of each scene so words are never merged across scenes.
  const palavrasFiltradas = useMemo((): PalavraK[] => {
    const semFinal = briefing.palavras.filter((p) => p.cena !== 4);
    return semFinal.map((p, idx, arr) => {
      const prox = arr[idx + 1];
      const isUltimaDaCena = prox && prox.cena !== p.cena;
      return {
        p: p.p,
        ini: p.ini,
        fim: p.fim,
        quebraApos: isUltimaDaCena,
      };
    });
  }, []);

  const totalFrames = Math.ceil(briefing.duracao_s * 30);

  // Exact frames for each scene
  const f0Ini = 0;
  const f0Dur = Math.round(briefing.cenas[0].fim * 30); // 145 frames

  const f1Ini = Math.round(briefing.cenas[1].ini * 30); // 134 frames
  const f1Dur = Math.round((briefing.cenas[1].fim - briefing.cenas[1].ini) * 30); // 191 frames

  const f2Ini = Math.round(briefing.cenas[2].ini * 30); // 315 frames
  const f2Dur = Math.round((briefing.cenas[2].fim - briefing.cenas[2].ini) * 30); // 219 frames

  const f3Ini = Math.round(briefing.cenas[3].ini * 30); // 523 frames
  const f3Dur = Math.round((briefing.cenas[3].fim - briefing.cenas[3].ini) * 30); // 245 frames

  const f4Ini = Math.round(briefing.cenas[4].ini * 30); // 758 frames
  const f4Dur = totalFrames - f4Ini; // 119 frames

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: '#111827',
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Complete Narration Audio */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Background Music with dynamic ducking & fades */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Cena 0: Pergunta / Gancho */}
      <Sequence from={f0Ini} durationInFrames={f0Dur}>
        <Cena0Pergunta
          fontFamily={fontFamily}
          ganchoTela={briefing.gancho_tela}
        />
      </Sequence>

      {/* Cena 1: Dono - O Problema */}
      <Sequence from={f1Ini} durationInFrames={f1Dur}>
        <Cena1Dono fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa WhatsApp 3D */}
      <Sequence from={f2Ini} durationInFrames={f2Dur}>
        <Cena2Conversa fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono - O Resultado */}
      <Sequence from={f3Ini} durationInFrames={f3Dur}>
        <Cena3Dono fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final CTA */}
      <Sequence from={f4Ini} durationInFrames={f4Dur}>
        <Cena4Cartao
          fontFamily={fontFamily}
          marca={briefing.marca}
          arroba={briefing.arroba}
          titulo={briefing.titulo}
        />
      </Sequence>

      {/* Global Karaoke Subtitles (Cenas 0 a 3, strictly excluded from Cena 4) */}
      <Karaoke
        palavras={palavrasFiltradas}
        fontFamily={fontFamily}
        destaque={briefing.cores.destaque}
        textoDestaque={briefing.cores.texto_sobre_marca}
        tamanho={48}
        base={360}
      />

      {/* Top Global Progress Bar (Safe Zone y >= 150) */}
      <ProgressBar color={briefing.cores.destaque} />
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoSegundos = briefing.duracao_s;
  const duracaoFrames = Math.ceil(duracaoSegundos * 30);

  return (
    <Composition
      id="Main"
      component={MainVideo}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={duracaoFrames}
    />
  );
};
