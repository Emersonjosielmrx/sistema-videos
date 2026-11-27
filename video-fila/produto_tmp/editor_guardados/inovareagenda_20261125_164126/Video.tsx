import React from 'react';
import {
  Composition,
  Sequence,
  Audio,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Palavras das cenas 0 a 3 formatadas com quebras semânticas por fala
const PALAVRAS: PalavraK[] = [
  // Cena 0: Pergunta gancho
  {p: 'Perdendo', ini: 0.318, fim: 0.775},
  {p: 'cliente', ini: 0.787, fim: 1.22},
  {p: 'que', ini: 1.232, fim: 1.34},
  {p: 'chama', ini: 1.352, fim: 1.652, quebraApos: true},
  {p: 'de', ini: 1.664, fim: 1.748},
  {p: 'madrugada', ini: 1.76, fim: 2.337},
  {p: 'no', ini: 2.349, fim: 2.445},
  {p: 'WhatsApp?', ini: 2.457, fim: 3.179, quebraApos: true},

  // Cena 1: O problema
  {p: 'Eu', ini: 4.785, fim: 4.893},
  {p: 'perdia', ini: 4.905, fim: 5.29},
  {p: 'cliente', ini: 5.302, fim: 5.747},
  {p: 'que', ini: 5.759, fim: 5.831},
  {p: 'escrevia', ini: 5.843, fim: 6.312},
  {p: 'à', ini: 6.324, fim: 6.36},
  {p: 'noite.', ini: 6.372, fim: 6.864, quebraApos: true},

  {p: 'Ele', ini: 7.115, fim: 7.283},
  {p: 'queria', ini: 7.295, fim: 7.632},
  {p: 'horário', ini: 7.644, fim: 8.052},
  {p: 'para', ini: 8.076, fim: 8.245},
  {p: 'o', ini: 8.257, fim: 8.293},
  {p: 'dia', ini: 8.305, fim: 8.497},
  {p: 'seguinte', ini: 8.509, fim: 8.99, quebraApos: true},

  {p: 'e', ini: 9.002, fim: 9.026},
  {p: 'ninguém', ini: 9.038, fim: 9.362},
  {p: 'respondia.', ini: 9.375, fim: 10.084, quebraApos: true},

  // Cena 2: Como funciona
  {p: 'Hoje', ini: 11.525, fim: 11.826},
  {p: 'a', ini: 11.838, fim: 11.862},
  {p: 'Agenda', ini: 11.874, fim: 12.246},
  {p: 'IA', ini: 12.258, fim: 13.532},
  {p: 'responde', ini: 13.544, fim: 14.061},
  {p: 'no', ini: 14.073, fim: 14.157},
  {p: 'WhatsApp,', ini: 14.169, fim: 14.818, quebraApos: true},

  {p: 'oferece', ini: 15.059, fim: 15.528},
  {p: 'o', ini: 15.539, fim: 15.576},
  {p: 'horário', ini: 15.588, fim: 15.948},
  {p: 'livre', ini: 15.96, fim: 16.333, quebraApos: true},

  {p: 'e', ini: 16.345, fim: 16.393},
  {p: 'marca', ini: 16.405, fim: 16.802},
  {p: 'para', ini: 16.814, fim: 16.97},
  {p: 'o', ini: 16.982, fim: 17.006},
  {p: 'cliente', ini: 17.018, fim: 17.39},
  {p: 'sozinha.', ini: 17.403, fim: 17.967, quebraApos: true},

  // Cena 3: O resultado
  {p: 'Agora', ini: 19.393, fim: 19.742},
  {p: 'o', ini: 19.754, fim: 19.79},
  {p: 'cliente', ini: 19.802, fim: 20.162, quebraApos: true},
  {p: 'chama', ini: 20.174, fim: 20.559},
  {p: 'quando', ini: 20.571, fim: 20.811},
  {p: 'quiser', ini: 20.823, fim: 21.208, quebraApos: true},

  {p: 'e', ini: 21.22, fim: 21.28},
  {p: 'acorda', ini: 21.292, fim: 21.749},
  {p: 'com', ini: 21.761, fim: 21.917},
  {p: 'o', ini: 21.929, fim: 21.953, quebraLinha: true},
  {p: 'horário', ini: 21.965, fim: 22.278},
  {p: 'marcado.', ini: 22.29, fim: 22.831, quebraApos: true},

  {p: 'Eu', ini: 23.081, fim: 23.177},
  {p: 'não', ini: 23.189, fim: 23.333},
  {p: 'preciso', ini: 23.346, fim: 23.814},
  {p: 'responder', ini: 23.826, fim: 24.295, quebraLinha: true},
  {p: 'na', ini: 24.307, fim: 24.475},
  {p: 'hora.', ini: 24.487, fim: 24.776, quebraApos: true},
];

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Controle dinâmico do volume da trilha musical
  const trilhaVolume = (f: number) => {
    if (f < 15) return (f / 15) * 0.1;
    if (f > 870) return ((890 - f) / 20) * 0.1;
    const t = f / 30;
    if (
      (t > 3.3 && t < 4.7) ||
      (t > 10.2 && t < 11.4) ||
      (t > 18.1 && t < 19.3) ||
      (t > 24.9 && t < 26.1)
    ) {
      return 0.18;
    }
    return 0.1;
  };

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: '#0F172A',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Áudio principal da narração completa */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Trilha musical de fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume} />

      {/* Cenas sequenciadas com sobreposições suaves de 10 frames */}
      <Sequence from={0} durationInFrames={140}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={129} durationInFrames={213}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={331} durationInFrames={248}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={567} durationInFrames={216}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={771} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso elegante no topo (y=152) */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          height: 5,
          borderRadius: 999,
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
          overflow: 'hidden',
          zIndex: 100,
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${Math.min(100, (frame / 890) * 100)}%`,
            backgroundColor: '#F59E0B',
            boxShadow: '0 0 8px #F59E0B',
          }}
        />
      </div>

      {/* Karaokê sincronizado oficial — encerra estritamente antes do cartão final */}
      {frame < 771 && (
        <Karaoke
          palavras={PALAVRAS}
          fontFamily={fontFamily}
          destaque="#F59E0B"
          textoDestaque="#121216"
          base={410}
          tamanho={46}
          maxLetras={40}
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
      durationInFrames={890}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};
