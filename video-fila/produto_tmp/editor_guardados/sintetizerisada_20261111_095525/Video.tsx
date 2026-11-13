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
import {briefing} from './briefingData';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import {ProgressBar} from './ProgressBar';

const {fontFamily} = loadFont();

// Filtra palavras para não exibir legenda no cartão final (regra obrigatória)
const palavrasKaraoke = briefing.palavras.filter((p) => p.cena < 4);

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Curva de volume da trilha sonora (0.10 durante fala, 0.22 no encerramento)
  const volumeTrilha = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    if (f < 735) {
      return 0.1;
    }
    if (f < 765) {
      return interpolate(f, [735, 765], [0.1, 0.22], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    if (f < 825) {
      return 0.22;
    }
    return interpolate(f, [825, 855], [0.22, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  };

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        backgroundColor: briefing.cores.fundo_escuro,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Áudio principal (Voz montada narradora + dono) */}
      <Audio src={staticFile('narracao.mp3')} volume={1} />

      {/* Trilha musical de fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha(frame)} />

      {/* Sequência das Cenas */}
      {/* Cena 0: Pergunta (0.0s a 5.17s) */}
      <Sequence from={0} durationInFrames={155}>
        <Cena0 fontFamily={fontFamily} cores={briefing.cores} />
      </Sequence>

      {/* Cena 1: Dono (4.82s a 12.48s) */}
      <Sequence from={145} durationInFrames={230}>
        <Cena1 fontFamily={fontFamily} cores={briefing.cores} />
      </Sequence>

      {/* Cena 2: Conversa WhatsApp (12.13s a 19.36s) */}
      <Sequence from={364} durationInFrames={217}>
        <Cena2 fontFamily={fontFamily} cores={briefing.cores} />
      </Sequence>

      {/* Cena 3: O Resultado / Checklist (19.01s a 24.86s) */}
      <Sequence from={570} durationInFrames={176}>
        <Cena3 fontFamily={fontFamily} cores={briefing.cores} />
      </Sequence>

      {/* Cena 4: Cartão Final Vivo (24.51s a 28.5s) */}
      <Sequence from={735} durationInFrames={120}>
        <Cena4
          fontFamily={fontFamily}
          cores={briefing.cores}
          arroba={briefing.arroba}
          convite={briefing.convite}
        />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (y=152) */}
      <ProgressBar destaque={briefing.cores.destaque} />

      {/* Legenda Karaokê com destaque na palavra falada (Cenas 0 a 3, proibida no cartão final) */}
      {frame < 735 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={briefing.cores.destaque}
          textoDestaque={briefing.cores.texto_sobre_marca}
          base={360}
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
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
