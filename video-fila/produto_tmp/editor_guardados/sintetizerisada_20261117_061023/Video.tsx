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
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {briefing} from './briefing';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
});

// Palavras onde forçamos quebra de bloco para manter conectivos e preposições (como 'SEM', 'COM', 'PARA')
// sempre juntos do termo regido na mesma linha/bloco, sem palavras órfãs.
const palavrasComQuebraApos = new Set([
  'tecnologia', // Cena 1: "Eu achava que tecnologia" | "para agendar exigia treinamento"
  'treinamento', // Cena 1: "para agendar exigia treinamento" | "demorado e dava dor de cabeça."
  'cabeça.', // Fim da cena 1
  'confirma', // Cena 2: "A IA agenda, confirma" | "e reagenda sozinha pelo WhatsApp"
  'WhatsApp', // Cena 2 e 3: quebra após WhatsApp
  'automáticos', // Cena 2: "com agendamentos automáticos" | "vinte e quatro horas."
  'automáticos,', // Cena 3: "com agendamentos automáticos," | "sem conflito"
  'conflito', // Cena 3: "sem conflito" | "e sem duplo agendamento."
  'horas.', // Fim da cena 2
  'agendamento.', // Fim da cena 3
]);

// Preparação das palavras do Karaokê: apenas cenas com o apresentador (cenas 1, 2 e 3)
const palavrasKaraoke: PalavraK[] = briefing.palavras
  .filter((w) => w.cena >= 1 && w.cena < 4)
  .map((w, i, arr) => {
    const isUltimaDaCena = i < arr.length - 1 && arr[i + 1].cena !== w.cena;
    const deveQuebrar = isUltimaDaCena || palavrasComQuebraApos.has(w.p);
    return {
      p: w.p,
      ini: w.ini,
      fim: w.fim,
      quebraApos: deveQuebrar,
    };
  });

const Video: React.FC = () => {
  const frame = useCurrentFrame();

  // Curva de volume da trilha sonora: ~0.10 com fala, ~0.20 no cartão final, fade in/out
  const getTrilhaVolume = (f: number) => {
    if (f < 15) return (f / 15) * 0.1;
    if (f >= 786 && f < 820) return 0.1 + ((f - 786) / 34) * 0.1;
    if (f >= 820 && f < 880) return 0.2;
    if (f >= 880) return Math.max(0, 0.2 - ((f - 880) / 26) * 0.2);
    return 0.1;
  };

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Áudio principal: Narração oficial montada */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Áudio secundário: Trilha de fundo com mixagem dinâmica */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume(frame)} />

      {/* Sequências de Cenas */}
      <Sequence from={0} durationInFrames={116}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={106} durationInFrames={221}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={316} durationInFrames={246}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={551} durationInFrames={245}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      <Sequence from={786} durationInFrames={120}>
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de progresso contínua no topo em y=150 (Safe Zone superior) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 999,
          background: 'rgba(255, 255, 255, 0.22)',
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${Math.min(100, (frame / 906) * 100)}%`,
            background: 'linear-gradient(90deg, #FFA94D, #FDBA74)',
            borderRadius: 999,
            boxShadow: '0 0 10px #FFA94D',
          }}
        />
      </div>

      {/* Karaokê oficial padronizado (base=360 -> y=1560, seguro) - Oculto na Cena 0 (para não competir com a tipografia do gancho) e no cartão final */}
      {frame >= 106 && frame < 786 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque={briefing.cores.destaque}
          textoDestaque={briefing.cores.texto_sobre_marca}
          base={360}
          tamanho={46}
          maxLetras={40}
        />
      )}
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Video}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
