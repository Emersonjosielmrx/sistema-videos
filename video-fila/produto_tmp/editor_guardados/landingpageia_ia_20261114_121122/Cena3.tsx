import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';

interface Cena3Props {
  fontFamily: string;
  destaque: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily, destaque}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom contínuo na gravação do dono
  const videoScale = interpolate(frame, [0, 246], [1.0, 1.045], {
    extrapolateRight: 'clamp',
  });

  // Badge "O RESULTADO" entra no frame 6
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Fase 1: "ESTRUTURA PRONTA QUE VENDE" entra no frame 24 (0.8s)
  const cardPhase1Spring = spring({
    frame: frame - 24,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Fase 2: "COMUNICAÇÃO CLARA PARA O NEGÓCIO" no frame 138 (4.6s na cena, ~23.7s)
  const phase2 = frame >= 138;
  const cardPhase2Spring = spring({
    frame: frame - 138,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Flutuação sutil contínua
  const floatY = Math.sin(frame * 0.1) * 2;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono em tela cheia */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 60%',
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

      {/* Degradê superior sutil (y=0 a 310) para contraste - ROSTO 100% PRESERVADO */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 310,
          background:
            'linear-gradient(to bottom, rgba(10, 14, 23, 0.88) 0%, rgba(10, 14, 23, 0.45) 70%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Faixa superior informativa ultra compacta (y=160 a 280) - RESPIRO > 60PX DO CABELO */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* Badge: O RESULTADO */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '6px 20px',
            borderRadius: 20,
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            border: `2px solid ${destaque}`,
            boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#22C55E',
              boxShadow: '0 0 10px #22C55E',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>

        {/* Card Dinâmico no topo */}
        {!phase2 ? (
          <div
            style={{
              padding: '10px 24px',
              borderRadius: 16,
              backgroundColor: 'rgba(17, 24, 39, 0.94)',
              border: `2px solid ${destaque}`,
              boxShadow: `0 8px 24px rgba(0,0,0,0.8), 0 0 16px rgba(245, 158, 11, 0.25)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              transform: `scale(${cardPhase1Spring}) translateY(${(1 - cardPhase1Spring) * 15}px)`,
              opacity: cardPhase1Spring,
            }}
          >
            <span style={{fontSize: 32, color: '#22C55E'}}>✓</span>
            <span
              style={{
                fontSize: 36,
                fontWeight: 800,
                color: '#FFFFFF',
                textAlign: 'center',
                textWrap: 'balance',
              }}
            >
              Estrutura pronta que vende
            </span>
          </div>
        ) : (
          <div
            style={{
              padding: '10px 24px',
              borderRadius: 16,
              backgroundColor: 'rgba(24, 18, 12, 0.95)',
              border: `2px solid ${destaque}`,
              boxShadow: `0 8px 28px rgba(0,0,0,0.8), 0 0 16px rgba(245, 158, 11, 0.35)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              transform: `scale(${cardPhase2Spring}) translateY(${(1 - cardPhase2Spring) * 15}px)`,
              opacity: cardPhase2Spring,
            }}
          >
            <span
              style={{
                fontSize: 36,
                fontWeight: 900,
                color: '#FFFFFF',
                textAlign: 'center',
                textWrap: 'balance',
              }}
            >
              Comunicação clara para o negócio
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
