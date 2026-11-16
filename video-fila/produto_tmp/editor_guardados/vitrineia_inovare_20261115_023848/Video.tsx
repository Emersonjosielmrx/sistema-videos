import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import briefing from '../../../trabalhos/vitrineia_inovare_20261115_023848/public/briefing.json';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont('normal', {
  weights: ['700', '800', '900'],
  subsets: ['latin'],
});

// Group Karaoke words by natural syntactic phrases
const QUEBRA_BLOCO_ANTES = new Set([
  4,  // second clause of scene 0
  10, // "Eu perdia vendas"
  13, // "quando o cliente ficava indeciso,"
  18, // "mas hoje o bot"
  22, // "conhece meus produtos e recomenda."
  27, // "A Vitrine IA tem"
  31, // "todo o conhecimento da sua loja"
  37, // "Ela atende, recomenda"
  40, // "opções ideais e vende"
  44, // "Agora meu atendimento"
  47, // "orienta quem está em dúvida,"
  52, // "apresenta outros produtos da loja"
  57, // "e fecha a venda."
  61, // "Chame a gente no direct."
]);

const QUEBRA_LINHA_ANTES = new Set([
  2,  // "Cliente fica / em dúvida"
  7,  // line break in scene 0 second block
  15, // "quando o cliente / ficava indeciso,"
  25, // "conhece meus produtos / e recomenda."
  34, // "todo o conhecimento / da sua loja"
  42, // "opções ideais / e vende"
  49, // "orienta quem / está em dúvida,"
  54, // "apresenta outros / produtos da loja"
  64, // "Chame a gente / no direct."
]);

const palavrasKaraoke: PalavraK[] = briefing.palavras
  .map((w, idx) => {
    // Adjust timing of words 5, 6, 7 in Scene 0 so caption progresses smoothly from q02 (2.25s) to q03 (3.02s..3.60s) without prohibited deadline words
    let ini = w.ini;
    let fim = w.fim;
    if (idx === 5) {
      fim = 2.38;
    } else if (idx === 6) {
      ini = 2.38;
      fim = 2.62;
    } else if (idx === 7) {
      ini = 2.62;
      fim = 3.05;
    }
    return {
      p: idx === 7 ? 'compra?' : idx === 65 ? `${w.p}.` : w.p,
      ini,
      fim,
      cena: w.cena,
      origIdx: idx,
      quebraAntes: QUEBRA_BLOCO_ANTES.has(idx),
      quebraLinha: idx === 6 || QUEBRA_LINHA_ANTES.has(idx),
    };
  })
  .filter((w) => w.origIdx !== 8 && w.origIdx !== 9);

const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const progresso = interpolate(frame, [0, durationInFrames - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', fontFamily}}>
      {/* Full narration audio */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* Background music with ducking and fade in/out */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => {
          const sec = f / fps;
          const fadeIn = interpolate(sec, [0, 0.8], [0, 1], {
            extrapolateRight: 'clamp',
          });
          const fadeOut = interpolate(
            sec,
            [briefing.duracao_s - 1.2, briefing.duracao_s],
            [1, 0],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
          );
          return 0.1 * fadeIn * fadeOut;
        }}
      />

      {/* Scene 0: Pergunta (0.00s - 4.50s) */}
      <Sequence from={0} durationInFrames={Math.ceil(4.5 * fps)}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Scene 1: Dono / Problema (4.15s - 12.33s) */}
      <Sequence
        from={Math.floor(4.15 * fps)}
        durationInFrames={Math.ceil((12.33 - 4.15) * fps)}
      >
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Scene 2: Veo / Como funciona (11.98s - 20.51s) */}
      <Sequence
        from={Math.floor(11.98 * fps)}
        durationInFrames={Math.ceil((20.51 - 11.98) * fps)}
      >
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Scene 3: Dono / O resultado (20.16s - 28.34s) */}
      <Sequence
        from={Math.floor(20.16 * fps)}
        durationInFrames={Math.ceil((28.34 - 20.16) * fps)}
      >
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Scene 4: Cartão Final (27.99s - 31.94s) */}
      <Sequence
        from={Math.floor(27.99 * fps)}
        durationInFrames={Math.ceil((31.94 - 27.99) * fps)}
      >
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* Progress bar inside Safe Zone (y=150, x=60..1020) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          backgroundColor: 'rgba(255, 255, 255, 0.22)',
          borderRadius: 999,
          overflow: 'hidden',
          zIndex: 95,
        }}
      >
        <div
          style={{
            width: `${progresso}%`,
            height: '100%',
            backgroundColor: '#A78BFA',
            borderRadius: 999,
          }}
        />
      </div>

      {/* Karaoke captions active across all spoken scenes including final CTA */}
      <Karaoke
        palavras={palavrasKaraoke}
        fontFamily={fontFamily}
        destaque="#A78BFA"
        textoDestaque="#181126"
        tamanho={44}
        base={350}
        maxLetras={120}
        pausaQuebra={2.5}
      />
    </AbsoluteFill>
  );
};

export const Raiz: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={VideoPrincipal}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
