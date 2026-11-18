import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena3Props {
  fontFamily: string;
}

export const Cena3Dono: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom lento e constante no vídeo (1.00 -> 1.05)
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave na transição para o cartão final (frames 232-245)
  const cenaOpacity = interpolate(frame, [232, 245], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Topo: Rótulo "03. O RESULTADO" (entra no frame 6)
  const rotuloSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Fase 1: Foco no trabalho (frames 0 a 105)
  const fase1Entrada = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const fase1Saida = interpolate(frame, [100, 108], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fase1Visivel = frame < 110;

  // Fase 2: Comentários com tudo automatizado (entra no frame 108 ~ 24.6s)
  const fase2Entrada = spring({
    frame: frame - 108,
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const fase2Visivel = frame >= 105;

  return (
    <AbsoluteFill style={{opacity: cenaOpacity, overflow: 'hidden'}}>
      {/* Vídeo do apresentador em tela cheia com push suave */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 45%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Gradiente sutil estritamente no topo (y=0 a 280) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 320,
          background:
            'linear-gradient(180deg, rgba(11, 15, 25, 0.8) 0%, rgba(11, 15, 25, 0.4) 70%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOP SAFE ZONE: y = 165 a 340 (respiro de mais de 150 px até o topo do cabelo em y=490) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 50,
        }}
      >
        {/* Rótulo Oficial da Cena: "03. O RESULTADO" */}
        <div
          style={{
            opacity: rotuloSpring,
            transform: `translateY(${(1 - rotuloSpring) * -15}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 22px',
            borderRadius: 24,
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            border: '1.5px solid rgba(16, 185, 129, 0.5)',
            boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: '0 0 8px #10B981',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#34D399',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            03. O RESULTADO
          </span>
        </div>

        {/* Bloco Fase 1: Foco no Trabalho */}
        {fase1Visivel && (
          <div
            style={{
              opacity: fase1Entrada * fase1Saida,
              transform: `scale(${0.92 + fase1Entrada * 0.08})`,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              backgroundColor: 'rgba(17, 24, 39, 0.95)',
              borderRadius: 20,
              padding: '14px 26px',
              border: '1.5px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          >
            <span style={{fontSize: 34}}>🎯</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 0.5,
              }}
            >
              Focado no meu trabalho
            </span>
          </div>
        )}

        {/* Bloco Fase 2: Atenção com Tudo Automatizado (Sem números inventados, sem 100%) */}
        {fase2Visivel && (
          <div
            style={{
              opacity: Math.max(0, Math.min(1, fase2Entrada)),
              transform: `scale(${0.92 + fase2Entrada * 0.08})`,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              backgroundColor: 'rgba(15, 33, 27, 0.95)',
              borderRadius: 20,
              padding: '14px 26px',
              border: '1.5px solid rgba(16, 185, 129, 0.6)',
              boxShadow: `0 8px 24px rgba(0,0,0,0.6), 0 0 20px ${CORES.verdeGlow}`,
            }}
          >
            <span style={{fontSize: 34}}>⚡</span>
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                }}
              >
                Quem comenta recebe atenção
              </span>
              <span
                style={{
                  padding: '4px 12px',
                  borderRadius: 14,
                  backgroundColor: 'rgba(16, 185, 129, 0.25)',
                  border: '1px solid #10B981',
                  fontFamily,
                  fontSize: 24,
                  fontWeight: 800,
                  color: '#6EE7B7',
                }}
              >
                Automatizado 🟢
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
