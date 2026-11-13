import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  interpolate,
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
import {ProgressBar} from './ProgressBar';

const {fontFamily} = loadFont();

// Carregando briefing oficial
import briefing from '../../../trabalhos/futebolcom_ia2_20261110_045334/public/briefing.json';

// Índices exatos para quebra sintática perfeita das legendas (sem viúvas, sem preposições isoladas):
const quebrasSintaticas = new Set([
  2, // "recebendo os pedidos"
  5, // "no meu WhatsApp"
  8, // "Eu achava que usar"
  12, // "um cardápio digital"
  15, // "ia tirar os meus clientes"
  20, // "do atendimento no WhatsApp."
  24, // "Mas a conversa"
  27, // "continua lá dentro"
  30, // "a IA tira dúvidas"
  34, // "sobre a pizza"
  37, // "enquanto o cliente"
  40, // "escolhe pela foto."
  43, // "Você mantém o canal"
  47, // "que seu cliente já conhece"
  52, // "mas recebe o pedido"
  56, // "organizado direto"
  58, // "na tela do celular"
]);

const palavrasKaraoke: PalavraK[] = briefing.palavras
  .filter((w) => w.cena < 4)
  .map((w, idx) => ({
    p: w.p,
    ini: w.ini,
    fim: w.fim,
    quebraAntes: quebrasSintaticas.has(idx) ? true : undefined,
  }));

const MainVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Curva de volume inteligente da trilha sonora:
  // ~0.10 durante a fala, ~0.20 em pausas e no cartão final, com fade in e out suaves
  const trilhaVolume = (f: number): number => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.12], {extrapolateRight: 'clamp'});
    }
    if (f > 895) {
      return interpolate(f, [895, 914], [0.18, 0], {extrapolateRight: 'clamp'});
    }
    // Pausa entre fala do gancho (fim 3.0s, frame 90) e fala do dono (ini 5.0s, frame 150)
    if (f >= 95 && f <= 145) {
      return interpolate(f, [95, 115, 135, 145], [0.12, 0.22, 0.22, 0.10], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    // Cartão final (a partir de 28.5s / frame 855)
    if (f >= 855) {
      return 0.20;
    }
    return 0.10;
  };

  // Transição suave de entrada das cenas
  const getSceneOpacity = (sceneStartFrame: number, duration = 10) => {
    return interpolate(frame, [sceneStartFrame, sceneStartFrame + duration], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  };

  return (
    <AbsoluteFill style={{backgroundColor: '#0A0103'}}>
      {/* 1. Trilha Sonora de Fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={trilhaVolume(frame)} />

      {/* 2. Narração Completa do Vídeo */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 3. Camadas de Cenas com Overlap Suave */}
      {/* Cena 0: Pergunta (0.0s – 4.43s | frames 0 – 133) */}
      <Sequence from={0} durationInFrames={133}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono (4.08s – 12.11s | frames 122 – 363) */}
      <Sequence from={122} durationInFrames={241}>
        <div style={{width: '100%', height: '100%', opacity: getSceneOpacity(122)}}>
          <Cena1 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 2: Conversa WhatsApp (11.76s – 19.97s | frames 353 – 599) */}
      <Sequence from={353} durationInFrames={246}>
        <div style={{width: '100%', height: '100%', opacity: getSceneOpacity(353)}}>
          <Cena2 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 3: Veo / Resultado (19.62s – 26.95s | frames 589 – 808) */}
      <Sequence from={589} durationInFrames={220}>
        <div style={{width: '100%', height: '100%', opacity: getSceneOpacity(589)}}>
          <Cena3 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* Cena 4: Cartão Final CTA (26.6s – 30.45s | frames 798 – 914) */}
      <Sequence from={798} durationInFrames={116}>
        <div style={{width: '100%', height: '100%', opacity: getSceneOpacity(798)}}>
          <Cena4 fontFamily={fontFamily} />
        </div>
      </Sequence>

      {/* 4. Barra de Progresso no Topo (y=150, visível durante todo o vídeo) */}
      <ProgressBar corPrimaria="#E11D48" corSecundaria="#FACC15" />

      {/* 5. Legenda Karaokê Oficial (visível apenas até o início do cartão final, frame < 798) */}
      {frame < 798 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#E11D48"
          textoDestaque="#FFFFFF"
          tamanho={46}
          base={360}
          maxLetras={28}
          pausaQuebra={0.6}
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
