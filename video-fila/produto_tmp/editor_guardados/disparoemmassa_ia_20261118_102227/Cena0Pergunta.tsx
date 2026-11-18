import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0Pergunta: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous background camera movement
  const bgScale = interpolate(frame, [0, 126], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 126], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Fade out transition at the end (frames 116 to 126)
  const sceneOpacity = interpolate(frame, [114, 126], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top pill entrance (y=175)
  const pillEntrance = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.7},
  });

  // Kinetic text 1: "SEU CLIENTE COMPRA" (starts at frame 8 = ~0.27s)
  const text1Spring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 180},
  });

  // Highlight "UMA VEZ" (speech at ~1.37s = frame 41)
  const umaVezSpring = spring({
    frame: frame - 40,
    fps,
    config: {damping: 11, mass: 0.5, stiffness: 220},
  });

  // Kinetic text 2: "...E SOME DA LOJA?" (speech at ~1.75s = frame 52)
  const text2Spring = spring({
    frame: frame - 52,
    fps,
    config: {damping: 11, mass: 0.6, stiffness: 200},
  });

  // Disappearance / Pain alert trigger (speech at ~1.87s = frame 56)
  const alertProgress = spring({
    frame: frame - 56,
    fps,
    config: {damping: 13, mass: 0.7},
  });

  // Ambient floating micro-movement
  const floatY = Math.sin(frame / 14) * 8;
  const pulseScale = 1 + Math.sin(frame / 8) * 0.04;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* Background Image with continuous cinematic push-in */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Dark Vignette Overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(17, 24, 39, 0.45) 0%, rgba(17, 24, 39, 0.92) 100%)',
          }}
        />
      </div>

      {/* Decorative tech grid particles */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          opacity: 0.18,
          backgroundImage:
            'radial-gradient(#22C55E 1.5px, transparent 1.5px)',
          backgroundSize: '48px 48px',
          transform: `translateY(${frame * 0.6}px)`,
        }}
      />

      {/* Top Header Tag (y=190, respiro 40px da barra em y=150) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: pillEntrance,
          transform: `translateY(${(1 - pillEntrance) * -20}px)`,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 999,
            backgroundColor: 'rgba(17, 24, 39, 0.85)',
            border: '1.5px solid rgba(34, 197, 94, 0.4)',
            boxShadow: '0 8px 30px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#22C55E',
              boxShadow: '0 0 12px #22C55E',
              transform: `scale(${pulseScale})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            Pós-Venda Inteligente
          </span>
        </div>
      </div>

      {/* Kinetic Typography Section (y=440 to y=800) */}
      <div
        style={{
          position: 'absolute',
          top: 420,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 22,
          zIndex: 20,
        }}
      >
        {/* Line 1: SEU CLIENTE COMPRA */}
        <div
          style={{
            opacity: Math.max(0, text1Spring),
            transform: `translateY(${(1 - text1Spring) * 35}px) scale(${0.9 + text1Spring * 0.1})`,
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 56,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              textTransform: 'uppercase',
            }}
          >
            Seu cliente compra
          </span>

          {/* UMA VEZ pill highlight */}
          <div
            style={{
              opacity: Math.max(0, umaVezSpring),
              transform: `scale(${Math.max(0, umaVezSpring)})`,
              backgroundColor: '#22C55E',
              padding: '6px 20px',
              borderRadius: 16,
              boxShadow: '0 0 30px rgba(34, 197, 94, 0.5)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 56,
                fontWeight: 900,
                color: '#111827',
                letterSpacing: '-0.01em',
                textTransform: 'uppercase',
              }}
            >
              Uma vez
            </span>
          </div>
        </div>

        {/* Line 2: ...E SOME DA LOJA? */}
        <div
          style={{
            opacity: Math.max(0, text2Spring),
            transform: `translateY(${(1 - text2Spring) * 35}px) scale(${0.92 + text2Spring * 0.08})`,
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              textTransform: 'uppercase',
            }}
          >
            ...e
          </span>

          {/* SOME pill in warning red */}
          <div
            style={{
              backgroundColor: '#EF4444',
              padding: '6px 22px',
              borderRadius: 16,
              boxShadow: '0 0 35px rgba(239, 68, 68, 0.65)',
              transform: `scale(${1 + Math.sin(frame / 6) * 0.03})`,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.02em',
                textTransform: 'uppercase',
              }}
            >
              some
            </span>
          </div>

          <span
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              textTransform: 'uppercase',
            }}
          >
            da loja?
          </span>
        </div>
      </div>

      {/* Center Interactive Visual Card (y=800 to y=1240) */}
      <div
        style={{
          position: 'absolute',
          top: 800,
          left: 80,
          right: 80,
          transform: `translateY(${floatY}px)`,
          zIndex: 15,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(17, 24, 39, 0.88)',
            border: '2px solid rgba(255, 255, 255, 0.12)',
            borderRadius: 32,
            padding: '36px 40px',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.75)',
            display: 'flex',
            flexDirection: 'column',
            gap: 24,
            backdropFilter: 'blur(16px)',
          }}
        >
          {/* Customer status header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1.5px solid rgba(255, 255, 255, 0.08)',
              paddingBottom: 20,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 18,
                  backgroundColor: alertProgress > 0.5 ? '#7F1D1D' : '#14532D',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background-color 0.3s ease',
                }}
              >
                {alertProgress > 0.5 ? (
                  <span style={{fontSize: 34}}>⚠️</span>
                ) : (
                  <span style={{fontSize: 34}}>🛍️</span>
                )}
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                  }}
                >
                  {alertProgress > 0.5 ? 'Cliente Desconectado' : 'Pedido Realizado'}
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 500,
                    color: '#94A3B8',
                  }}
                >
                  Última compra: há semanas
                </span>
              </div>
            </div>

            {/* Status badge */}
            <div
              style={{
                backgroundColor:
                  alertProgress > 0.5 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                border: `1.5px solid ${alertProgress > 0.5 ? '#EF4444' : '#22C55E'}`,
                padding: '8px 18px',
                borderRadius: 999,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: alertProgress > 0.5 ? '#FCA5A5' : '#86EFAC',
                }}
              >
                {alertProgress > 0.5 ? 'SEM RETORNO' : 'VENDA AVULSA'}
              </span>
            </div>
          </div>

          {/* Action insight row */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              padding: '18px 24px',
              borderRadius: 20,
            }}
          >
            <span style={{fontSize: 34}}>💬</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 600,
                color: '#E2E8F0',
                lineHeight: 1.35,
              }}
            >
              {alertProgress > 0.5
                ? 'Sem mensagem de pós-venda, o cliente não volta.'
                : 'O cliente comprou, mas o contato parou por aí.'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
