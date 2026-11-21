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
import briefing from '../../../trabalhos/vitrineia_inovare_20261120_010728/public/briefing.json';

const {fontFamily} = loadFont();

// Preparação das palavras do Karaokê com quebras otimizadas por cena e frase
const palavrasKaraoke: PalavraK[] = briefing.palavras
  .filter((w) => w.cena < 4) // Cartão final (cena 4) não tem legenda
  .map((w) => {
    const p: PalavraK = {
      p: w.p,
      ini: w.ini,
      fim: w.fim,
    };
    // Quebras estratégicas para garantir blocos equilibrados e sem palavras órfãs
    if (w.p === 'cliente' && w.cena === 0) p.quebraApos = true;
    if (w.p === 'atendimento' && w.cena === 0) p.quebraApos = true;
    if (w.p === 'vez' && w.cena === 1) p.quebraApos = true;
    if (w.p === 'responder.' && w.cena === 1) p.quebraApos = true;
    if (w.p === 'pouco' && w.cena === 1) p.quebraApos = true;
    if (w.p === 'loja.' && w.cena === 1) p.quebraApos = true;
    if (w.p === 'sandália' && w.cena === 2) p.quebraApos = true;
    if (w.p === 'loja' && w.cena === 2) p.quebraApos = true;
    if (w.p === 'modelo' && w.cena === 2) p.quebraApos = true;
    if (w.p === 'hora' && w.cena === 3) p.quebraApos = true;
    if (w.p === 'cliente' && w.cena === 3) p.quebraApos = true;
    if (w.p === 'rápida' && w.cena === 3) p.quebraApos = true;
    return p;
  });

// Controle dinâmico do volume da trilha sonora (~0.10 com fala, ~0.20 em pausas, fade out no fim)
const calcTrilhaVolume = (frame: number): number => {
  // Fade out final nos últimos 40 frames
  if (frame >= 878) {
    return interpolate(frame, [878, 918], [0.18, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }

  // Pausa entre cena 0 e cena 1 (frames 102 a 160 = 3.4s a 5.3s)
  if (frame >= 102 && frame <= 160) {
    return interpolate(frame, [102, 115, 148, 160], [0.1, 0.2, 0.2, 0.1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }

  // Pausa na cena 1 (frames 258 a 290 = 8.6s a 9.7s)
  if (frame >= 258 && frame <= 290) {
    return interpolate(frame, [258, 266, 282, 290], [0.1, 0.18, 0.18, 0.1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }

  // Pausa entre cena 2 e cena 3 (frames 578 a 621 = 19.3s a 20.7s)
  if (frame >= 578 && frame <= 621) {
    return interpolate(frame, [578, 588, 610, 621], [0.1, 0.2, 0.2, 0.1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }

  // Pausa entre cena 3 e cena 4 (frames 771 a 813 = 25.7s a 27.1s)
  if (frame >= 771 && frame <= 813) {
    return interpolate(frame, [771, 782, 802, 813], [0.1, 0.2, 0.2, 0.1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }

  // Cartão final (após a fala final em ~28.6s = frame 858)
  if (frame >= 858) {
    return 0.18;
  }

  // Padrão durante fala
  return 0.1;
};

const Main: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: '#0B0D13',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Áudio: Narração principal (voz de alta qualidade) */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Áudio: Trilha sonora de fundo com ducking e fade */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={() => calcTrilhaVolume(frame)}
      />

      {/* Cena 0: Pergunta / Gancho (0.00s a 4.83s = 0 a 145 frames) */}
      <Sequence from={0} durationInFrames={145}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono relatando o problema (4.48s a 12.67s = 134 a 380 frames) */}
      <Sequence from={134} durationInFrames={246}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa no WhatsApp com o Bot (12.32s a 20.56s = 370 a 617 frames) */}
      <Sequence from={370} durationInFrames={247}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Resultado na prática (20.21s a 26.99s = 606 a 810 frames) */}
      <Sequence from={606} durationInFrames={204}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final com CTA (26.64s a 30.58s = 799 a 918 frames) */}
      <Sequence from={799} durationInFrames={119}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Legenda Karaokê Oficial (apenas até o início do cartão final em frame 799) */}
      {frame < 799 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#A78BFA"
          textoDestaque="#121216"
          tamanho={46}
          base={360}
          maxLetras={44}
        />
      )}

      {/* Barra de Progresso Fina no Topo (y = 150) */}
      <ProgressBar cor="#A78BFA" altura={6} top={150} />
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
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
