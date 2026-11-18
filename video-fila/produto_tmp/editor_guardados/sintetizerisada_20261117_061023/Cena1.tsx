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

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Plano médio natural (1.00x -> 1.03x) para contrastar com o punch-in da Cena 2
  const videoScale = interpolate(frame, [0, 221], [1.0, 1.03], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave no fim da cena (últimos 10 frames)
  const sceneOpacity = interpolate(frame, [210, 221], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Topo: Entrada da etiqueta de etapa "01 · O RECEIO"
  const stepSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Card 1: "Treinamento demorado?" entra na fala "tecnologia para agendar" (~frame 60)
  const card1Spring = spring({
    frame: frame - 60,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Transição para "Dor de cabeça" aos ~frame 158 ("e dava dor de cabeça")
  const dorSpring = spring({
    frame: frame - 158,
    fps,
    config: {damping: 10, stiffness: 140},
  });

  // Pulso de dor de cabeça
  const dorPulse = 1 + 0.04 * Math.sin((frame - 158) * 0.3);

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, overflow: 'hidden'}}>
      {/* Vídeo do dono em tela cheia com movimento contínuo */}
      <AbsoluteFill style={{transform: `scale(${videoScale})`}}>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{width: '1080px', height: '1920px', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Vinheta superior muito suave para garantir 100% de contraste no texto sem escurecer o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 380,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.75) 0%, rgba(15, 23, 42, 0.35) 60%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo informativo (y=165 a 360, safe zone respeitada, respiro > 70px até o topo da cabeça em y=450) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
        }}
      >
        {/* Etapa 1 */}
        <div
          style={{
            transform: `scale(${Math.max(0, stepSpring)})`,
            opacity: stepSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 20px',
            borderRadius: 999,
            background: 'rgba(31, 41, 55, 0.90)',
            border: '1.5px solid rgba(255, 169, 77, 0.5)',
            boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFA94D',
              textTransform: 'uppercase',
              letterSpacing: 1.2,
            }}
          >
            01 · O Receio
          </span>
        </div>

        {/* Card dinâmico que evolui com a fala */}
        {frame >= 60 && (
          <div
            style={{
              transform: `scale(${Math.max(0, card1Spring)})`,
              opacity: card1Spring,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              maxWidth: 880,
            }}
          >
            {frame < 158 ? (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  padding: '14px 28px',
                  borderRadius: 20,
                  background: 'rgba(31, 41, 55, 0.92)',
                  border: '2px solid rgba(255, 169, 77, 0.5)',
                  boxShadow: '0 10px 30px rgba(0,0,0,0.6)',
                }}
              >
                <svg
                  width="36"
                  height="36"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#FFA94D"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 800,
                    color: '#F8FAFC',
                    textTransform: 'uppercase',
                  }}
                >
                  Treinamento demorado?
                </span>
              </div>
            ) : (
              <div
                style={{
                  transform: `scale(${dorPulse})`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  padding: '14px 28px',
                  borderRadius: 20,
                  background: 'rgba(31, 41, 55, 0.94)',
                  border: '2px solid #FFA94D',
                  boxShadow: '0 10px 30px rgba(255, 169, 77, 0.45)',
                }}
              >
                <svg
                  width="36"
                  height="36"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#FFA94D"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <span
                  style={{
                    fontFamily,
                    fontSize: 36,
                    fontWeight: 900,
                    color: '#FFA94D',
                    textTransform: 'uppercase',
                    letterSpacing: 1,
                  }}
                >
                  Dor de cabeça?
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
