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
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

const Main: React.FC = () => {
  const frame = useCurrentFrame();

  // Volume da trilha de fundo com ducking e fade-in/fade-out
  const trilhaVolume = interpolate(
    frame,
    [0, 25, 862, 925, 955, 981],
    [0, 0.09, 0.09, 0.16, 0.16, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Barra de progresso contínua no topo (y=152px)
  const progressPercent = Math.min(100, Math.max(0, (frame / 981) * 100));

  // Palavras para o Karaokê (inclui a fala final da Cena 4 "Chame a gente no direct")
  const karaokePalavras = briefingData.palavras;

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
      {/* Áudio principal (Locução + Dono da Barbearia) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha musical com volume calibrado */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* SEQUÊNCIAS DAS CENAS (com overlap de transição suave) */}

      {/* Cena 0: Pergunta / Gancho (0.0s a 5.6s -> frames 0 a 168) */}
      <Sequence from={0} durationInFrames={168}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Problema (5.25s a 13.44s -> frames 158 a 403) */}
      <Sequence from={158} durationInFrames={246}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Como Funciona (13.09s a 21.27s -> frames 393 a 638) */}
      <Sequence from={393} durationInFrames={246}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado (20.92s a 29.1s -> frames 628 a 873) */}
      <Sequence from={628} durationInFrames={246}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (28.75s a 32.7s -> frames 862 a 981) */}
      <Sequence from={862} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Fina no Topo Seguro (y=152px) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 4,
          backgroundColor: 'rgba(255, 255, 255, 0.18)',
          borderRadius: 4,
          overflow: 'hidden',
          zIndex: 80,
          boxShadow: '0 1px 4px rgba(0, 0, 0, 0.5)',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progressPercent}%`,
            background:
              'linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%)',
            boxShadow: '0 0 10px rgba(245, 158, 11, 0.8)',
            borderRadius: 4,
          }}
        />
      </div>

      {/* Legenda Karaokê Pronta: ativa desde o frame 0 (Cenas 0 a 3) e desativada na Cena 4 (cartão final) */}
      {frame < 862 && (
        <Karaoke
          palavras={karaokePalavras}
          fontFamily={fontFamily}
          destaque="#F59E0B"
          textoDestaque="#121216"
          tamanho={44}
          base={400}
          maxLetras={28}
          pausaQuebra={0.6}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Main}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={981}
    />
  );
};
