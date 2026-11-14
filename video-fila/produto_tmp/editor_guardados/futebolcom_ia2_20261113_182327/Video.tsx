import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import briefing from '../../../trabalhos/futebolcom_ia2_20261113_182327/public/briefing.json';
import {Karaoke} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import {ProgressBar} from './ProgressBar';

const {fontFamily} = loadFont();

// Palavras para karaokê apenas até a cena 3 (proibido no cartão final)
const palavrasKaraoke = briefing.palavras.filter((p: any) => p.cena < 4);

// Intervalos de fala para ducking suave da trilha de fundo
const INTERVALOS_FALA: [number, number][] = [
  [0.316, 4.02],
  [5.599, 10.68],
  [12.075, 17.77],
  [19.175, 24.372],
  [25.771, 27.206],
];

const calcularVolumeTrilha = (f: number): number => {
  const t = f / 30;
  // Fade in inicial (0 a 0.5s)
  if (t < 0.5) {
    return (t / 0.5) * 0.1;
  }
  // Fade out final (28.0 a 29.13s)
  if (t > 28.0) {
    return Math.max(0, ((29.13 - t) / 1.13) * 0.2);
  }
  // Ducking: volume mais baixo durante falas (~0.10), mais alto em pausas (~0.22)
  const falaAtiva = INTERVALOS_FALA.some(
    ([inicio, fim]) => t >= inicio - 0.12 && t <= fim + 0.12
  );
  return falaAtiva ? 0.1 : 0.22;
};

export const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{backgroundColor: '#1A0307'}}>
      {/* Áudio Oficial: Narração completa montada no tempo exato */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha de Fundo com Ducking Dinâmico e Fades */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => calcularVolumeTrilha(f)}
      />

      {/* Sequências das Cenas com Overlap Suave de Transição */}
      {/* Cena 0: Pergunta / Gancho (0.00s a 5.46s | frames 0 a 164) */}
      <Sequence from={0} durationInFrames={164}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Problema (5.11s a 11.93s | frames 153 a 358) */}
      <Sequence from={153} durationInFrames={205}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona (11.58s a 19.03s | frames 347 a 571) */}
      <Sequence from={347} durationInFrames={224}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado (18.68s a 25.63s | frames 560 a 769) */}
      <Sequence from={560} durationInFrames={209}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (25.28s a 29.13s | frames 758 a 874) */}
      <Sequence from={758} durationInFrames={116}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Contínua no Topo Seguro (y=155) */}
      <ProgressBar />

      {/* Karaokê Oficial Sincronizado (Cenas 0 a 3, oculto no cartão final) */}
      {frame < 758 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#E11D48"
          textoDestaque="#FFFFFF"
          tamanho={44}
          base={360}
        />
      )}
    </AbsoluteFill>
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
