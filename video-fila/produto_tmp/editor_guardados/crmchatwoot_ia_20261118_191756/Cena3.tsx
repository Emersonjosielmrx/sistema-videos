import React from 'react';
import {
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

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no vídeo
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Topo badge aos 0.1s (frame 3)
  const badgeSpring = spring({
    frame: frame - 3,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Título 1: Adaptado ao seu jeito (~0.4s / frame 11)
  const title1Spring = spring({
    frame: frame - 11,
    fps,
    config: {damping: 12, stiffness: 95},
  });

  // Título 2: Clareza e sem complicação (~4.1s / frame 124)
  const turnPoint = 124;
  const isTurn = frame >= turnPoint;

  const title2Spring = spring({
    frame: frame - turnPoint,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  const floatY = Math.sin(frame / 12) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono em Tela Cheia com iluminação natural intacta */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 40%',
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

      {/* Gradiente sutil estritamente no topo para contraste */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 280,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.85) 0%, rgba(15, 23, 42, 0.45) 60%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Grafismos de Topo (Safe Zone: y=165 a 330) */}
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
          transform: `translateY(${floatY}px)`,
          pointerEvents: 'none',
        }}
      >
        {/* Rótulo da Cena (O resultado) */}
        <div
          style={{
            transform: `scale(${Math.max(0, badgeSpring)})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 24px',
              borderRadius: 24,
              background: 'rgba(15, 23, 42, 0.82)',
              border: '1.5px solid rgba(31, 147, 255, 0.4)',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 6px 20px rgba(0, 0, 0, 0.5)',
            }}
          >
            <span style={{fontSize: 30}}>🚀</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#60A5FA',
                textTransform: 'uppercase',
                letterSpacing: 1.1,
              }}
            >
              O Resultado
            </span>
          </div>
        </div>

        {/* Headline Dinâmica Sincronizada */}
        {!isTurn ? (
          <div
            style={{
              transform: `scale(${Math.max(0, title1Spring)})`,
              maxWidth: 920,
              textAlign: 'center',
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.88)',
                border: '2px solid rgba(31, 147, 255, 0.5)',
                borderRadius: 20,
                padding: '12px 28px',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 8px 30px rgba(0, 0, 0, 0.6)',
                display: 'inline-block',
              }}
            >
              <span
                style={{
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.2,
                }}
              >
                ADAPTADO AO SEU{' '}
                <span style={{color: '#38BDF8'}}>FLUXO DE TRABALHO</span>
              </span>
            </div>
          </div>
        ) : (
          <div
            style={{
              transform: `scale(${Math.max(0, title2Spring)})`,
              maxWidth: 920,
              textAlign: 'center',
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.9)',
                border: '2px solid #1F93FF',
                borderRadius: 20,
                padding: '12px 28px',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 10px 32px rgba(31, 147, 255, 0.4)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <span style={{fontSize: 36}}>✨</span>
              <span
                style={{
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.2,
                }}
              >
                CLAREZA E{' '}
                <span style={{color: '#60A5FA'}}>SEM COMPLICAÇÃO</span>
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
