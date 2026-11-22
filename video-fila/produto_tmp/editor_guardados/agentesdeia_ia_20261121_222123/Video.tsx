import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Composition,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Karaoke, PalavraK} from '../../lib/karaoke';
import {Cena0} from './Cena0';
import {Cena1} from './Cena1';
import {Cena2} from './Cena2';
import {Cena3} from './Cena3';
import {CenaCartao} from './CenaCartao';
import briefing from '../../../trabalhos/agentesdeia_ia_20261121_222123/public/briefing.json';

const {fontFamily} = loadFont();

// Preparar palavras do Karaokê com quebras estritas por cena (evita misturar falas)
// E remove palavras da cena 4 (cartão final não tem legenda)
const rawPalavras = (briefing.palavras || []) as Array<{
  p: string;
  ini: number;
  fim: number;
  cena: number;
}>;

const karaokePalavras: PalavraK[] = rawPalavras
  .filter((w) => w.cena !== 4)
  .map((w, idx, arr) => {
    const isLastOfScene = idx < arr.length - 1 && arr[idx + 1].cena !== w.cena;
    // Em cena 0: quebra de linha antes de "do" para manter "do dia" junto na 2ª linha
    const isQuebraLinha = w.cena === 0 && w.p.toLowerCase() === 'do';
    return {
      p: w.p,
      ini: w.ini,
      fim: w.fim,
      quebraApos: isLastOfScene,
      quebraLinha: isQuebraLinha,
    };
  });

export const VideoPrincipal: React.FC = () => {
  const frame = useCurrentFrame();
  const totalFrames = 935; // Math.ceil(31.14 * 30)

  // Curva de volume da trilha musical:
  // Volume ~0.10 durante narração, fade-in inicial, sobe para ~0.20 no cartão final e fade-out
  const getTrilhaVolume = (f: number) => {
    if (f < 15) {
      return interpolate(f, [0, 15], [0, 0.1], {extrapolateRight: 'clamp'});
    }
    if (f >= 885 && f < 915) {
      return interpolate(f, [885, 915], [0.1, 0.22], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
    }
    if (f >= 915) {
      return interpolate(f, [915, 935], [0.22, 0], {
        extrapolateRight: 'clamp',
      });
    }
    return 0.1;
  };

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0F19', overflow: 'hidden'}}>
      {/* Áudio: Narração completa (voz principal e fala do dono) */}
      <Audio src={staticFile('narracao.mp3')} volume={1} />

      {/* Áudio: Trilha sonora de fundo */}
      <Audio src={staticFile('trilha.mp3')} volume={getTrilhaVolume} />

      {/* Cenas Sequenciadas com transições de sobreposição suave */}
      {/* Cena 0: Pergunta (0.00s a 5.43s -> frames 0 a 163) */}
      <Sequence from={0} durationInFrames={163}>
        <Cena0 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 1: Dono - O Problema (5.08s a 13.10s -> frames 152 a 393) */}
      <Sequence from={152} durationInFrames={241}>
        <Cena1 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 2: Conversa - Como Funciona (12.75s a 19.87s -> frames 383 a 596) */}
      <Sequence from={383} durationInFrames={214}>
        <Cena2 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 3: Dono - O Resultado (19.52s a 27.55s -> frames 586 a 826) */}
      <Sequence from={586} durationInFrames={241}>
        <Cena3 fontFamily={fontFamily} />
      </Sequence>

      {/* Cena 4: Cartão Final (27.20s a 31.14s -> frames 816 a 935) */}
      <Sequence from={816} durationInFrames={119}>
        <CenaCartao fontFamily={fontFamily} />
      </Sequence>

      {/* Barra de Progresso Fina no Topo (y = 150) */}
      <div
        style={{
          position: 'absolute',
          top: 150,
          left: 60,
          right: 60,
          height: 6,
          borderRadius: 3,
          background: 'rgba(255, 255, 255, 0.15)',
          zIndex: 100,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${Math.min(100, (frame / totalFrames) * 100)}%`,
            height: '100%',
            borderRadius: 3,
            background: 'linear-gradient(90deg, #10B981 0%, #34D399 100%)',
            boxShadow: '0 0 10px #10B981',
          }}
        />
      </div>

      {/* Legenda Karaokê Pronta (apenas durante as cenas 0 a 3, oculta no cartão final) */}
      {frame < 816 && (
        <Karaoke
          palavras={karaokePalavras}
          fontFamily={fontFamily}
          destaque="#10B981"
          textoDestaque="#0B0F19"
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
      component={VideoPrincipal}
      fps={30}
      width={1080}
      height={1920}
      durationInFrames={Math.ceil(31.14 * 30)}
    />
  );
};
