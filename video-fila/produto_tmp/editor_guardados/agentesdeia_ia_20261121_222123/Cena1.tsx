import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
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

  // Escala reduzida em 5% (0.95) e rebaixamento de 40px (+120px) garantindo respiro total no cabelo
  // Corte de aproximação digital (punch-in de 0.98x para 1.15x) exatamente no frame 121 (9.12s global)
  // quando pronuncia 'microtarefas acumuladas', quebrando a monotonia
  const punchSpring = spring({
    frame: frame - 121,
    fps,
    config: {damping: 14, stiffness: 220},
  });

  const baseScale = interpolate(frame, [0, 121], [0.95, 0.98], {
    extrapolateRight: 'clamp',
  });
  const videoScale = interpolate(punchSpring, [0, 1], [baseScale, 1.15]);
  const videoTranslateY = interpolate(punchSpring, [0, 1], [120, 135]);

  // Entrada do Badge "O PROBLEMA" aos 0.2s (frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título Fixo: "PRIORIDADES FICAVAM PARA TRÁS" (5.38s global = frame 9 local)
  const titleSpring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Elemento visual de apoio animado aos 9.12s (frame 121) ilustrando 'microtarefas acumuladas'
  const alertSpring = spring({
    frame: frame - 121,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Transições de entrada e saída
  const enterOpacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [228, 241], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0B0F19',
        opacity: Math.min(enterOpacity, exitOpacity),
      }}
    >
      {/* Vídeo do dono em tela cheia com corte de aproximação digital (punch-in) e enquadramento rebaixado (+120px) */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: '50% 38%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta superior suave para legibilidade perfeita do card */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(11, 15, 25, 0.85) 0%, rgba(11, 15, 25, 0.4) 70%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {/* Faixa Superior restrita no topo (y=155): rosto e olhos 100% livres */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 20,
        }}
      >
        {/* Badge do Rótulo "O PROBLEMA" na paleta verde da marca */}
        <div
          style={{
            opacity: badgeSpring,
            transform: `scale(${interpolate(badgeSpring, [0, 1], [0.85, 1], {extrapolateRight: 'clamp'})})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 24px',
            borderRadius: 24,
            background: 'rgba(16, 185, 129, 0.18)',
            border: '1.5px solid rgba(16, 185, 129, 0.55)',
            boxShadow: '0 4px 20px rgba(16, 185, 129, 0.25)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
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
              textTransform: 'uppercase',
              letterSpacing: 2,
            }}
          >
            O Problema
          </span>
        </div>

        {/* Card Superior Fixo com alto contraste (#FFFFFF e #E2E8F0) mantido durante toda a cena */}
        <div
          style={{
            marginTop: 12,
            width: '100%',
            maxWidth: 960,
            borderRadius: 24,
            background: 'rgba(17, 24, 39, 0.94)',
            border: '1.5px solid rgba(16, 185, 129, 0.35)',
            boxShadow: '0 20px 45px rgba(0, 0, 0, 0.75)',
            padding: '20px 28px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            textAlign: 'center',
            gap: 8,
            opacity: titleSpring,
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.92, 1], {extrapolateRight: 'clamp'})})`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 42,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              lineHeight: 1.2,
            }}
          >
            Prioridades ficavam para trás
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 600,
              color: '#E2E8F0',
            }}
          >
            Falta de tempo para o foco principal
          </div>
        </div>

        {/* Elemento de apoio visual quebrando a monotonia no punch-in aos 9.12s (frame 121) */}
        {frame >= 120 && (
          <div
            style={{
              marginTop: 14,
              opacity: alertSpring,
              transform: `scale(${interpolate(alertSpring, [0, 1], [0.85, 1])}) translateY(${interpolate(alertSpring, [0, 1], [15, 0])}px)`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 24px',
              borderRadius: 20,
              background: 'rgba(239, 68, 68, 0.22)',
              border: '1.5px solid #EF4444',
              boxShadow: '0 0 20px rgba(239, 68, 68, 0.4)',
            }}
          >
            <span style={{fontSize: 24}}>⚠️</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FCA5A5',
                textTransform: 'uppercase',
                letterSpacing: 1.5,
              }}
            >
              Microtarefas Acumuladas
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
