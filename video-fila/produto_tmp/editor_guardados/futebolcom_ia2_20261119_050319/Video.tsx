import React from 'react';
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
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Palavras da locução filtradas para remover a cena final (sem karaokê no cartão de encerramento)
const briefingPalavras = [
  {p: 'Seu', ini: 0.316, fim: 0.582, cena: 0},
  {p: 'cliente', ini: 0.594, fim: 0.964, cena: 0},
  {p: 'desiste', ini: 0.976, fim: 1.439, cena: 0},
  {p: 'de', ini: 1.451, fim: 1.532, cena: 0},
  {p: 'pedir', ini: 1.543, fim: 1.914, cena: 0},
  {p: 'porque', ini: 1.937, fim: 2.214, cena: 0},
  {p: 'demora', ini: 2.226, fim: 2.619, cena: 0},
  {p: 'para', ini: 2.631, fim: 2.805, cena: 0},
  {p: 'responder', ini: 2.816, fim: 3.372, cena: 0, quebraApos: true},
  {p: 'Quando', ini: 5.37, fim: 5.93, cena: 1},
  {p: 'eu', ini: 5.93, fim: 6.11, cena: 1},
  {p: 'demorava', ini: 6.11, fim: 6.53, cena: 1},
  {p: 'a', ini: 6.53, fim: 6.71, cena: 1},
  {p: 'responder', ini: 6.71, fim: 6.95, cena: 1},
  {p: 'o', ini: 6.95, fim: 7.15, cena: 1},
  {p: 'cardápio,', ini: 7.15, fim: 8.01, cena: 1, quebraApos: true},
  {p: 'o', ini: 8.39, fim: 8.43, cena: 1},
  {p: 'cliente', ini: 8.43, fim: 8.81, cena: 1},
  {p: 'cansava', ini: 8.81, fim: 9.35, cena: 1},
  {p: 'de', ini: 9.35, fim: 9.63, cena: 1},
  {p: 'esperar', ini: 9.63, fim: 9.95, cena: 1},
  {p: 'e', ini: 9.95, fim: 10.81, cena: 1},
  {p: 'pedia', ini: 10.81, fim: 11.07, cena: 1},
  {p: 'no', ini: 11.07, fim: 11.27, cena: 1},
  {p: 'concorrente.', ini: 11.27, fim: 11.81, cena: 1, quebraApos: true},
  {p: 'Com', ini: 12.853, fim: 13.413, cena: 2},
  {p: 'o', ini: 13.413, fim: 13.613, cena: 2},
  {p: 'cardápio', ini: 13.613, fim: 13.973, cena: 2},
  {p: 'digital,', ini: 13.973, fim: 14.493, cena: 2, quebraApos: true},
  {p: 'o', ini: 15.153, fim: 15.173, cena: 2},
  {p: 'cliente', ini: 15.173, fim: 15.673, cena: 2},
  {p: 'olha', ini: 15.673, fim: 15.833, cena: 2},
  {p: 'as', ini: 15.833, fim: 16.033, cena: 2},
  {p: 'fotos', ini: 16.033, fim: 16.593, cena: 2},
  {p: 'e', ini: 16.593, fim: 17.233, cena: 2},
  {p: 'tira', ini: 17.233, fim: 17.493, cena: 2},
  {p: 'dúvida', ini: 17.633, fim: 17.913, cena: 2},
  {p: 'com', ini: 17.913, fim: 18.133, cena: 2},
  {p: 'a', ini: 18.133, fim: 18.313, cena: 2},
  {p: 'IA', ini: 18.313, fim: 18.593, cena: 2},
  {p: 'sem', ini: 18.593, fim: 18.953, cena: 2},
  {p: 'esperar.', ini: 18.953, fim: 19.373, cena: 2, quebraApos: true},
  {p: 'Hoje', ini: 19.823, fim: 20.563, cena: 3},
  {p: 'o', ini: 20.803, fim: 20.963, cena: 3},
  {p: 'pedido', ini: 20.963, fim: 21.363, cena: 3},
  {p: 'sai', ini: 21.363, fim: 21.583, cena: 3},
  {p: 'do', ini: 21.583, fim: 21.803, cena: 3},
  {p: 'cardápio', ini: 21.803, fim: 22.383, cena: 3},
  {p: 'direto', ini: 22.383, fim: 22.863, cena: 3},
  {p: 'para', ini: 22.863, fim: 22.963, cena: 3},
  {p: 'o', ini: 22.963, fim: 23.063, cena: 3},
  {p: 'WhatsApp', ini: 22.963, fim: 23.583, cena: 3},
  {p: 'e', ini: 23.583, fim: 24.183, cena: 3},
  {p: 'eu', ini: 24.183, fim: 24.403, cena: 3},
  {p: 'deixo', ini: 24.403, fim: 24.903, cena: 3},
  {p: 'de', ini: 24.903, fim: 25.043, cena: 3},
  {p: 'perder', ini: 25.043, fim: 25.423, cena: 3},
  {p: 'venda', ini: 25.423, fim: 25.863, cena: 3},
  {p: 'pela', ini: 25.863, fim: 26.123, cena: 3},
  {p: 'demora.', ini: 26.123, fim: 26.663, cena: 3, quebraApos: true},
] as PalavraK[];

const MainContent: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  // Volume da trilha com fade-in e fade-out
  const volumeTrilha = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    if (f > durationInFrames - 25) {
      return interpolate(f, [durationInFrames - 25, durationInFrames], [0.1, 0], {
        extrapolateLeft: 'clamp',
      });
    }
    return 0.1;
  };

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        backgroundColor: '#140206',
        overflow: 'hidden',
      }}
    >
      {/* ÁUDIO PRINCIPAL: Narração completa (voz da narradora + fala do dono) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* ÁUDIO DE FUNDO: Trilha sonora licenciada */}
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha(frame)} />

      {/* BARRA DE PROGRESSO NO TOPO (y = 150) */}
      <ProgressBar
        totalFrames={durationInFrames}
        corPrimaria="#E11D48"
        corApoio="#FACC15"
      />

      {/* CENA 0: Pergunta / Gancho (0.0s a 4.81s | Frames 0 a 145) */}
      <Sequence from={0} durationInFrames={145}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 1: Dono - O Problema (4.46s a 12.64s | Frames 134 a 379) */}
      <Sequence from={134} durationInFrames={246}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 2: Dono - Como Funciona (12.29s a 20.17s | Frames 369 a 605) */}
      <Sequence from={369} durationInFrames={236}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 3: Dono - O Resultado (19.82s a 27.46s | Frames 595 a 824) */}
      <Sequence from={595} durationInFrames={229}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* CENA 4: Cartão Final / Encerramento CTA (27.11s a 30.96s | Frames 813 a 929) */}
      <Sequence from={813} durationInFrames={116}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* KARAOKÊ PROFISSIONAL (Apenas até o início do cartão final, frame 813) */}
      {frame < 813 && (
        <Karaoke
          palavras={briefingPalavras}
          fontFamily={fontFamily}
          destaque="#E11D48"
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={360}
          maxLetras={30}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainContent}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(30.96 * 30)}
    />
  );
};
