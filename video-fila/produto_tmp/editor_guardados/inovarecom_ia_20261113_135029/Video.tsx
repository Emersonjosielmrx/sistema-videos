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
import {briefing} from './briefing';
import {ProgressBar} from './ProgressBar';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';

const {fontFamily} = loadFont();

// Volume ducking helper for background music
const getTrilhaVolume = (frame: number): number => {
  const t = frame / 30;
  // Fade in at start
  const fadeIn = interpolate(t, [0, 0.6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // Fade out at end
  const fadeOut = interpolate(t, [29.2, 30.46], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Speech timing windows
  const isSpeech =
    (t >= 0.25 && t <= 3.5) ||
    (t >= 4.7 && t <= 9.8) ||
    (t >= 10.8 && t <= 18.2) ||
    (t >= 18.8 && t <= 26.2) ||
    (t >= 26.9 && t <= 28.8);

  const baseVol = isSpeech ? 0.10 : 0.22;
  return baseVol * fadeIn * fadeOut;
};

// Filter words for Karaoke: scenes 0 to 3 only (no karaoke on final card)
// Set natural breaks to avoid orphan monosyllables and keep phrases cohesive
const palavrasKaraoke = briefing.palavras
  .filter((p) => p.cena < 4)
  .map((p, idx, arr) => {
    // 1. Cena 0: break before "de" so "Sua equipe não dá conta" and "de ligar para tantos contatos" form 2 balanced lines
    const breakBeforeDeC0 = p.cena === 0 && p.p.toLowerCase() === 'de' && Math.abs(p.ini - 1.579) < 0.1;

    // 2. Cena 1: clean phrase breaks for natural reading flow
    const breakBeforeEC1 = p.cena === 1 && p.p.toLowerCase() === 'e' && Math.abs(p.ini - 6.59) < 0.1;
    const breakBeforeParaC1 = p.cena === 1 && p.p.toLowerCase() === 'para' && Math.abs(p.ini - 8.288) < 0.1;

    // 3. Cena 2: break before "automáticas", "em", "com", and "vinte" so each idea and "vinte e quatro horas" stay grouped
    const breakBeforeAutoC2 = p.cena === 2 && p.p.toLowerCase() === 'automáticas' && Math.abs(p.ini - 12.694) < 0.1;
    const breakBeforeEmC2 = p.cena === 2 && p.p.toLowerCase() === 'em' && Math.abs(p.ini - 14.333) < 0.1;
    const breakBeforeComC2 = p.cena === 2 && p.p.toLowerCase() === 'com' && Math.abs(p.ini - 15.406) < 0.1;
    const breakBeforeVinteC2 = p.cena === 2 && p.p.toLowerCase() === 'vinte' && Math.abs(p.ini - 16.857) < 0.2;

    // 4. Cena 3: break before "precisamos" and "sem" to group "sem sobrecarregar nossa equipe comercial"
    const breakBeforePrecisamosC3 = p.cena === 3 && p.p.toLowerCase() === 'precisamos' && Math.abs(p.ini - 21.6) < 0.1;
    const breakBeforeSemC3 = p.cena === 3 && p.p.toLowerCase() === 'sem' && Math.abs(p.ini - 23.28) < 0.2;

    const quebraAntes =
      breakBeforeDeC0 ||
      breakBeforeEC1 ||
      breakBeforeParaC1 ||
      breakBeforeAutoC2 ||
      breakBeforeEmC2 ||
      breakBeforeComC2 ||
      breakBeforeVinteC2 ||
      breakBeforePrecisamosC3 ||
      breakBeforeSemC3;
    const quebraApos = idx === arr.length - 1 || p.cena !== arr[idx + 1].cena;

    // Extend 'contatos' (cena 0) to 4.35s so the green highlight stays active at 3.77s through the end of scene 0
    // Extend 'comercial' (cena 3) to 26.55s so the highlight stays active through the end of scene 3
    const isContatosC0 = p.cena === 0 && p.p.toLowerCase().includes('contatos');
    const isComercialC3 = p.cena === 3 && p.p.toLowerCase().includes('comercial');
    const fimAjustado = isContatosC0 ? 4.35 : isComercialC3 ? 26.55 : p.fim;

    // Clean word text (e.g. "comercial." -> "comercial" so karaoke displays "COMERCIAL")
    const textoLimpo = isComercialC3 ? 'comercial' : p.p;

    return {
      p: textoLimpo,
      ini: p.ini,
      fim: fimAjustado,
      quebraAntes,
      quebraApos,
    };
  });

const Main: React.FC = () => {
  const totalFrames = Math.ceil(briefing.duracao_s * 30); // 914 frames
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        backgroundColor: '#082E16',
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* 1. Full voiceover audio */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Background music with auto-ducking */}
      <Audio
        src={staticFile('trilha.mp3')}
        volume={(f) => getTrilhaVolume(f)}
      />

      {/* 3. Scene Sequences */}
      {/* Cena 0: Pergunta (0.00s a 4.71s | f 0 a 141) */}
      <Sequence from={0} durationInFrames={141} name="Cena 0 - Pergunta">
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: O Gargalo (4.36s a 10.83s | f 131 a 325) */}
      <Sequence from={131} durationInFrames={194} name="Cena 1 - Gargalo">
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: A Solução (10.48s a 19.25s | f 314 a 577) */}
      <Sequence from={314} durationInFrames={263} name="Cena 2 - Solução">
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: O Dono / Resultado (18.90s a 26.92s | f 567 a 808) */}
      <Sequence from={567} durationInFrames={241} name="Cena 3 - Dono">
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final / CTA (26.57s a 30.46s | f 797 a 914) */}
      <Sequence from={797} durationInFrames={117} name="Cena 4 - CTA">
        <Cena4 fontFamily={fontFamily} />
      </Sequence>

      {/* 4. Top Progress Bar (y=152) */}
      <ProgressBar destaque="#25D366" />

      {/* 5. Synchronized Karaoke (scenes 0 to 3 only, strictly hidden in final card at f >= 797, base raised to safe zone y <= 1500) */}
      {frame < 797 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={fontFamily}
          destaque="#25D366"
          textoDestaque="#121216"
          tamanho={46}
          base={420}
          maxLetras={45}
        />
      )}
    </div>
  );
};

export const Raiz: React.FC = () => {
  const duracaoEmFrames = Math.ceil(briefing.duracao_s * 30); // 914 frames

  return (
    <Composition
      id="Main"
      component={Main}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={duracaoEmFrames}
    />
  );
};
