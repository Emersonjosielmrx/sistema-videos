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
import {BRIEFING} from './dados';
import {ProgressBar} from './ProgressBar';
import {Cena0Pergunta} from './Cena0Pergunta';
import {Cena1Dono} from './Cena1Dono';
import {Cena2Conversa} from './Cena2Conversa';
import {Cena3Dono} from './Cena3Dono';
import {Cena4Cartao} from './Cena4Cartao';

const {fontFamily} = loadFont();

export const MainComponent: React.FC = () => {
  // Palavras para o Karaokê (cenas 0 a 3, proibido no cartão final)
  const palavrasKaraoke = BRIEFING.palavras.filter((p) => p.cena < 4);

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 1920,
        backgroundColor: BRIEFING.cores.fundo_escuro,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Narração Completa (narradora + falas do dono) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha Sonora com ducking inteligente: ~0.10 com fala, ~0.22 sem fala, fade in/out */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const s = f / 30;
          if (s < 0.5) {
            return interpolate(s, [0, 0.5], [0, 0.1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
          }
          if (s < 27.38) {
            return 0.1;
          }
          if (s < 28.5) {
            return interpolate(s, [27.38, 28.0], [0.1, 0.22], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
          }
          return interpolate(s, [28.5, 29.36], [0.22, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
        }}
      />

      {/* Barra de Progresso no Topo (y=160, safe zone) */}
      <ProgressBar cor={BRIEFING.cores.destaque} />

      {/* Cena 0: Pergunta (0.00s a 5.43s) */}
      <Sequence from={0} durationInFrames={163}>
        <Cena0Pergunta fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono (5.08s a 12.81s) */}
      <Sequence from={152} durationInFrames={232}>
        <Cena1Dono fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa WhatsApp 3D (12.46s a 18.21s) */}
      <Sequence from={374} durationInFrames={172}>
        <Cena2Conversa fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono (17.86s a 25.72s) */}
      <Sequence from={536} durationInFrames={236}>
        <Cena3Dono fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final de Alta Conversão (25.37s a 29.36s) */}
      <Sequence from={761} durationInFrames={120}>
        <Cena4Cartao fontFamily={fontFamily} />
      </Sequence>

      {/* Karaokê Oficial Remotion ancorado em y=1560 (base=360), cortado aos 25.37s para NÃO existir no cartão final */}
      <Sequence from={0} durationInFrames={761}>
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={BRIEFING.cores.destaque}
          textoDestaque={BRIEFING.cores.texto_sobre_marca}
          tamanho={46}
          base={360}
        />
      </Sequence>
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoFrames = Math.ceil(BRIEFING.duracao_s * 30); // 881 frames

  return (
    <Composition
      id="Main"
      component={MainComponent}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={duracaoFrames}
    />
  );
};
