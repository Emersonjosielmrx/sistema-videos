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
import {Karaoke} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {Cena4} from './Cena4';
import {FONT_FAMILY, THEME} from './theme';

// Dados do briefing.json
import briefing from '../../../trabalhos/sintetizerisada_20261127_072410/public/briefing.json';

// Cenas:
// 0: ini: 0.0,  fim: 5.07  (152 frames)
// 1: ini: 4.72, fim: 12.91 (246 frames) -> Sequence from=142, duration=246
// 2: ini: 12.56, fim: 21.18 (259 frames) -> Sequence from=377, duration=259
// 3: ini: 20.83, fim: 29.80 (269 frames) -> Sequence from=625, duration=269
// 4: ini: 29.45, fim: 33.44 (120 frames) -> Sequence from=884, duration=120
// Duração total: 33.44s -> Math.ceil(33.44 * 30) = 1004 frames

const MainComponent: React.FC = () => {
  const frame = useCurrentFrame();
  const totalFrames = 1004;

  // Barra de progresso contínua no topo em y = 150
  const progress = interpolate(frame, [0, totalFrames - 1], [0, 100], {
    extrapolateRight: 'clamp',
  });

  // Trilha sonora: volume 0.10 com fala, fade in nos primeiros 15 frames e fade out nos últimos 20 frames
  const volumeTrilha = interpolate(
    frame,
    [0, 15, totalFrames - 20, totalFrames],
    [0, 0.1, 0.1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Palavras para o Karaokê (apenas até o início do cartão final em 29.45s)
  // No cartão final NÃO se exibe o Karaokê, conforme instrução explícita
  const palavrasKaraoke = briefing.palavras
    .filter((p) => p.cena < 4)
    .map((p) => {
      // Correção q03: Adicionar interrogação no final da pergunta ("DELES?")
      if (p.cena === 0 && p.p.toLowerCase().includes('deles')) {
        return {...p, p: 'deles?'};
      }
      // Correção q11: Quebra harmônica em "noite" para evitar palavra viúva "UMA"
      if (p.cena === 3 && p.p.toLowerCase() === 'noite') {
        return {...p, quebraApos: true};
      }
      return p;
    });

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.darkBg}}>
      {/* 1. Áudio completo da narração */}
      <Audio src={staticFile('narracao.mp3')} />

      {/* 2. Trilha sonora de fundo calibrada */}
      <Audio src={staticFile('trilha.mp3')} volume={volumeTrilha} />

      {/* 3. Sequências de Cenas */}
      {/* Cena 0: Pergunta / Gancho */}
      <Sequence from={0} durationInFrames={152}>
        <Cena0 />
      </Sequence>

      {/* Cena 1: Dono (depoimento real) */}
      <Sequence from={142} durationInFrames={246}>
        <Cena1 />
      </Sequence>

      {/* Cena 2: Conversa WhatsApp (IA bloqueando horário) */}
      <Sequence from={377} durationInFrames={259}>
        <Cena2 />
      </Sequence>

      {/* Cena 3: Veo (vídeo comercial + comparativo e benefícios) */}
      <Sequence from={625} durationInFrames={269}>
        <Cena3 />
      </Sequence>

      {/* Cena 4: Cartão Final */}
      <Sequence from={884} durationInFrames={120}>
        <Cena4 />
      </Sequence>

      {/* 4. Barra de progresso fina na Safe Zone (y = 150) */}
      <div
        style={{
          position: 'absolute',
          top: THEME.safeZone.top,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          height: 6,
          backgroundColor: 'rgba(255, 255, 255, 0.18)',
          borderRadius: 3,
          overflow: 'hidden',
          zIndex: 100,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${progress}%`,
            backgroundColor: THEME.colors.primary,
            boxShadow: `0 0 10px ${THEME.colors.primary}`,
          }}
        />
      </div>

      {/* 5. Karaokê padrão pronto (ativo das cenas 0 a 3, desliga no cartão final frame 884) */}
      {frame < 884 && (
        <Karaoke
          palavras={palavrasKaraoke}
          fontFamily={FONT_FAMILY}
          destaque={THEME.colors.primary}
          textoDestaque={THEME.colors.textOnPrimary}
          tamanho={46}
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
      component={MainComponent}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(briefing.duracao_s * 30)}
    />
  );
};
