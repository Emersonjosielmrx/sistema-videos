import React from 'react';
import {
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke} from '../../lib/karaoke';
import {briefingData} from './briefingData';
import {ProgressBar} from './ProgressBar';
import {Cena0_Pergunta} from './Cena0_Pergunta';
import {Cena1_Problema} from './Cena1_Problema';
import {Cena2_ComoFunciona} from './Cena2_ComoFunciona';
import {Cena3_Resultado} from './Cena3_Resultado';
import {Cena4_CartaoFinal} from './Cena4_CartaoFinal';

const {fontFamily} = loadFont();

// Filtra as palavras para não exibir karaokê no cartão final (regra explícita do manual)
const palavrasKaraoke = briefingData.palavras.filter((p) => p.cena !== 4);

export const Main: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* 1. Narração Completa Oficial */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha Sonora de Fundo com Fade In/Out e Ducking */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          if (f < 15) {
            return interpolate(f, [0, 15], [0, 0.10], {extrapolateRight: 'clamp'});
          }
          if (f < 885) {
            return 0.10;
          }
          if (f < 920) {
            // Cresce no encerramento musical após a fala terminar
            return interpolate(f, [885, 920], [0.10, 0.22], {extrapolateRight: 'clamp'});
          }
          // Fade out final
          return interpolate(f, [925, 943], [0.22, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
        }}
      />

      {/* 3. Barra de Progresso Superior (y=152) */}
      <ProgressBar destaque="#F472B6" />

      {/* 4. Cenas em Sequência com Transições Suaves */}
      {/* Cena 0: Pergunta do Cliente (0.00s a 5.89s -> frames 0 a 177) */}
      <Sequence from={0} durationInFrames={177}>
        <Cena0_Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Problema - Dono (5.54s a 13.21s -> frames 166 a 396) */}
      <Sequence from={166} durationInFrames={230}>
        <Cena1_Problema fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona - Dono (12.86s a 20.89s -> frames 386 a 627) */}
      <Sequence from={386} durationInFrames={241}>
        <Cena2_ComoFunciona fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado - Dono (20.54s a 27.84s -> frames 616 a 835) */}
      <Sequence from={616} durationInFrames={219}>
        <Cena3_Resultado fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final de Conversão (27.49s a 31.43s -> frames 825 a 943) */}
      <Sequence from={825} durationInFrames={118}>
        <Cena4_CartaoFinal fontFamily={fontFamily} />
      </Sequence>

      {/* 5. Legenda Karaokê Oficial (apenas nas cenas 0, 1, 2, 3; oculta no cartão final) */}
      {frame < 825 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#F472B6"
          textoDestaque="#111827"
          tamanho={42}
          base={360}
          maxLetras={32}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoSegundos = briefingData.duracao_s; // 31.43s
  const duracaoFrames = Math.ceil(duracaoSegundos * 30); // 943 frames

  return (
    <Composition
      id="Main"
      component={Main}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={duracaoFrames}
    />
  );
};
