import React, {useMemo} from 'react';
import {
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import briefing from '../../../trabalhos/sintetizerisada_20261115_223919/public/briefing.json';

import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const SceneWrapper: React.FC<{
  children: React.ReactNode;
  fadeIn?: boolean;
  zoomTransition?: boolean;
}> = ({children, fadeIn = true, zoomTransition = false}) => {
  const frame = useCurrentFrame();
  const opacity = fadeIn
    ? interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'})
    : 1;
  const scale = zoomTransition
    ? interpolate(frame, [0, 12], [1.08, 1], {extrapolateRight: 'clamp'})
    : 1;
  const translateY = zoomTransition
    ? interpolate(frame, [0, 12], [28, 0], {extrapolateRight: 'clamp'})
    : 0;
  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        opacity,
        transform: zoomTransition ? `scale(${scale}) translateY(${translateY}px)` : undefined,
        transformOrigin: 'center center',
      }}
    >
      {children}
    </div>
  );
};

export const MainContent: React.FC = () => {
  const frame = useCurrentFrame();
  const duracaoTotalFrames = Math.ceil(briefing.duracao_s * 30);

  // Palavras preparadas para Karaokê: apenas cenas 0 a 3 (sem legenda no cartão final)
  const palavrasKaraoke = useMemo<PalavraK[]>(() => {
    const raw = (briefing.palavras as Array<{p: string; ini: number; fim: number; cena: number}>)
      .filter((w) => w.cena < 4)
      .map((w, idx, arr) => {
        const item: PalavraK = {
          p: w.p,
          ini: w.ini,
          fim: w.fim,
        };
        // Forçar quebra no final de cada cena para nunca juntar falas distintas
        const isFimCena = idx + 1 < arr.length && arr[idx + 1].cena !== w.cena;
        if (isFimCena) {
          item.quebraApos = true;
        }
        return item;
      });
    return raw;
  }, []);

  // Frame inicial e duração de cada cena a 30 fps
  const c1From = Math.round(briefing.cenas[1].ini * 30); // 141 (4.70s)
  const c0From = 0;
  const c0Duration = c1From; // Transição exata no início da fala do apresentador (frame 141)

  const c1Duration = Math.round((briefing.cenas[1].fim - briefing.cenas[1].ini) * 30); // 241

  const c2From = Math.round(briefing.cenas[2].ini * 30); // 371
  const c2Duration = Math.round((briefing.cenas[2].fim - briefing.cenas[2].ini) * 30); // 245

  const c3From = Math.round(briefing.cenas[3].ini * 30); // 606
  const c3Duration = Math.round((briefing.cenas[3].fim - briefing.cenas[3].ini) * 30); // 246

  const c4From = Math.round(briefing.cenas[4].ini * 30); // 842
  const c4Duration = duracaoTotalFrames - c4From; // 120

  const isCartaoFinal = frame >= c4From;

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
      {/* 1. Narração Principal (Voz do vídeo) */}
      <Audio src={staticFile('narracao.mp3')} volume={1.0} />

      {/* 2. Trilha Sonora com volume ajustado e fade in/out */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) =>
          interpolate(
            f,
            [0, 20, duracaoTotalFrames - 25, duracaoTotalFrames],
            [0, 0.09, 0.09, 0],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
          )
        }
      />

      {/* 3. Sequências das Cenas */}
      {/* Cena 0: Pergunta */}
      <Sequence from={c0From} durationInFrames={c0Duration}>
        <SceneWrapper fadeIn={false}>
          <Cena0 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 1: Dono - A situação */}
      <Sequence from={c1From} durationInFrames={c1Duration}>
        <SceneWrapper fadeIn={false} zoomTransition={true}>
          <Cena1 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 2: Dono - Como funciona */}
      <Sequence from={c2From} durationInFrames={c2Duration}>
        <SceneWrapper fadeIn={true}>
          <Cena2 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 3: Dono - O resultado */}
      <Sequence from={c3From} durationInFrames={c3Duration}>
        <SceneWrapper fadeIn={true}>
          <Cena3 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* Cena 4: Cartão Final */}
      <Sequence from={c4From} durationInFrames={c4Duration}>
        <SceneWrapper fadeIn={true}>
          <Cena4 fontFamily={fontFamily} />
        </SceneWrapper>
      </Sequence>

      {/* 4. Barra de Progresso no Topo (y=152) */}
      <ProgressBar cor="#FFA94D" />

      {/* 5. Legenda Karaokê Oficial (apenas cenas 0 a 3, proibido no cartão final) */}
      {!isCartaoFinal && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#FFA94D"
          textoDestaque="#1F2937"
          tamanho={46}
          base={360}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoTotalFrames = Math.ceil(briefing.duracao_s * 30);

  return (
    <Composition
      id="Main"
      component={MainContent}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={duracaoTotalFrames}
    />
  );
};
