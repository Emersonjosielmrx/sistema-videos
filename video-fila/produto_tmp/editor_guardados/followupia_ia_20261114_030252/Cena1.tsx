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

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom sutil e contínuo no apresentador (1.08 -> 1.13) ancorado na base
  const videoScale = interpolate(frame, [0, 232], [1.08, 1.14], {
    extrapolateRight: 'clamp',
  });

  // Entrada animada do rótulo
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Transição do título no frame 85
  const isPhase2 = frame >= 85;
  const phaseSpring = spring({
    frame: frame - 85,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Vídeo do apresentador com rebaixamento de 115px para proteger 100% o rosto/cabelo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `translateY(115px) scale(${videoScale})`,
          transformOrigin: '50% 100%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Vinheta superior muito suave apenas para legibilidade do texto no alto, sem tocar no rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 320,
          background:
            'linear-gradient(180deg, rgba(17, 24, 39, 0.92) 0%, rgba(17, 24, 39, 0.4) 65%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Rótulo superior: y=162 (na safe zone) */}
      <div
        style={{
          position: 'absolute',
          top: 162,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${Math.max(0, badgeSpring)})`,
          opacity: Math.min(1, Math.max(0, badgeSpring)),
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 20,
            backgroundColor: 'rgba(17, 24, 39, 0.88)',
            border: '1.5px solid rgba(239, 68, 68, 0.7)',
            backdropFilter: 'blur(8px)',
          }}
        >
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>
      </div>

      {/* Título Forte no alto: estritamente em y=214 (termina em ~y=265, deixando >70px até o topo da cabeça) */}
      <div
        style={{
          position: 'absolute',
          top: 214,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          textAlign: 'center',
          zIndex: 20,
        }}
      >
        {!isPhase2 ? (
          <div
            style={{
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              lineHeight: 1.15,
              textShadow: '0 4px 16px rgba(0,0,0,0.95)',
              padding: '6px 20px',
              borderRadius: 14,
              backgroundColor: 'rgba(17, 24, 39, 0.70)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            VENDAS VALIOSAS PERDIDAS
          </div>
        ) : (
          <div
            style={{
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              lineHeight: 1.15,
              textShadow: '0 4px 16px rgba(0,0,0,0.95)',
              padding: '6px 20px',
              borderRadius: 14,
              backgroundColor: 'rgba(17, 24, 39, 0.70)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              transform: `scale(${Math.max(0, phaseSpring)})`,
              opacity: Math.min(1, Math.max(0, phaseSpring)),
            }}
          >
            EQUIPE{' '}
            <span
              style={{
                color: '#FCA5A5',
                textDecoration: 'underline',
                textDecorationColor: '#EF4444',
              }}
            >
              ESQUECIA DE COBRAR
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
