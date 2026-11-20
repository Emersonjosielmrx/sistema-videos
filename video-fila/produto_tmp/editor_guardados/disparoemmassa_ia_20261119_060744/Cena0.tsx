import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Fundo com zoom contínuo e movimento suave (1.05 -> 1.15)
  const bgScale = interpolate(frame, [0, 148], [1.05, 1.15], {
    extrapolateRight: 'clamp',
  });

  // Entrada do selo superior (0.0s -> frame 0-10)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Gancho aos 1.8s (frame 54)
  const ganchoSpring = spring({
    frame: frame - 54,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Card central (surge aos 0.3s / frame 10)
  const cardSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 15, stiffness: 90},
  });

  // Palavra "bloqueado" dita aos 2.12s (frame 64)
  const alertSpring = spring({
    frame: frame - 64,
    fps,
    config: {damping: 16, stiffness: 100},
  });

  // Palavra "campanha" dita aos 2.89s (frame 87)
  const highlightSpring = spring({
    frame: frame - 87,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Micro-animação contínua (flutuação suave do card)
  const floatY = Math.sin(frame * 0.08) * 6;
  const pulseScale = 1 + Math.sin(frame * 0.12) * 0.015;

  // Transição de saída nos últimos 8 frames
  const exitOpacity = interpolate(frame, [140, 148], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: exitOpacity,
      }}
    >
      {/* Imagem de Fundo com Zoom Contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
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
        {/* Véu gradiente escuro de marca para contraste perfeito */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(17, 24, 39, 0.4) 0%, rgba(17, 24, 39, 0.85) 100%)',
          }}
        />
      </div>

      {/* Grafismos de alta tecnologia: anéis cibernéticos em rotação contínua */}
      <svg
        width="1080"
        height="1920"
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          opacity: 0.22,
        }}
      >
        <circle
          cx="540"
          cy="850"
          r="420"
          fill="none"
          stroke="#22C55E"
          strokeWidth="2"
          strokeDasharray="16 24"
          style={{
            transform: `rotate(${frame * 0.4}deg)`,
            transformOrigin: '540px 850px',
          }}
        />
        <circle
          cx="540"
          cy="850"
          r="480"
          fill="none"
          stroke="#10B981"
          strokeWidth="1.5"
          strokeDasharray="8 32"
          style={{
            transform: `rotate(-${frame * 0.25}deg)`,
            transformOrigin: '540px 850px',
          }}
        />
      </svg>

      {/* Topo Informativo (y = 175 a 360) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
          zIndex: 30,
        }}
      >
        {/* Selo Categoria */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.92)',
            border: '1.5px solid rgba(34, 197, 94, 0.5)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            transform: `translateY(${(1 - badgeSpring) * -30}px) scale(${badgeSpring})`,
            opacity: badgeSpring,
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              background: '#22C55E',
              boxShadow: '0 0 10px #22C55E',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Dúvida Frequente
          </span>
        </div>

        {/* Gancho da Tela (aos 1.8s) */}
        {frame >= 54 && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
              padding: '14px 32px',
              borderRadius: 20,
              background: 'rgba(239, 68, 68, 0.18)',
              border: '2px solid rgba(239, 68, 68, 0.7)',
              backdropFilter: 'blur(10px)',
              transform: `scale(${ganchoSpring})`,
              opacity: ganchoSpring,
              boxShadow: '0 8px 30px rgba(239, 68, 68, 0.3)',
            }}
          >
            <span style={{fontSize: 36}}>⚠️</span>
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 800,
                color: '#FECACA',
                letterSpacing: 0.5,
              }}
            >
              Medo de perder o número?
            </span>
          </div>
        )}
      </div>

      {/* Card Focal Central (y = 500 a 1250) */}
      <div
        style={{
          position: 'absolute',
          top: 490,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${floatY}px) scale(${pulseScale * cardSpring})`,
          opacity: cardSpring,
          zIndex: 20,
        }}
      >
        <div
          style={{
            width: '100%',
            boxSizing: 'border-box',
            background: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(255, 255, 255, 0.12)',
            borderRadius: 36,
            padding: '48px 40px',
            boxShadow:
              '0 30px 80px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(20px)',
            display: 'flex',
            flexDirection: 'column',
            gap: 26,
            alignItems: 'center',
            textAlign: 'center',
          }}
        >
          {/* Ícone de Perigo / Alerta WhatsApp */}
          <div
            style={{
              width: 100,
              height: 100,
              borderRadius: 28,
              background: 'linear-gradient(135deg, #1F2937, #111827)',
              border: '2px solid rgba(34, 197, 94, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.4)',
            }}
          >
            <svg
              width="56"
              height="56"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#22C55E"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>

          {/* Pergunta do Cliente */}
          <div
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 800,
              color: '#F8FAFC',
              lineHeight: 1.25,
              textWrap: 'balance',
            }}
          >
            E se o meu WhatsApp principal...
          </div>

          {/* Destaque dramático da palavra "bloqueado" (aos 2.12s) */}
          {frame >= 64 && (
            <div
              style={{
                width: '92%',
                boxSizing: 'border-box',
                padding: '20px 24px',
                borderRadius: 24,
                background:
                  'linear-gradient(135deg, rgba(239, 68, 68, 0.28), rgba(185, 28, 28, 0.38))',
                border: '2.5px solid #EF4444',
                boxShadow:
                  '0 12px 35px rgba(239, 68, 68, 0.4), inset 0 0 20px rgba(239, 68, 68, 0.2)',
                transform: `scale(${alertSpring})`,
                opacity: alertSpring,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 16,
              }}
            >
              <span style={{fontSize: 44}}>🔒</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 54,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: 2,
                  textTransform: 'uppercase',
                  textShadow: '0 4px 14px rgba(0, 0, 0, 0.8)',
                }}
              >
                For Bloqueado?
              </span>
            </div>
          )}

          {/* Destaque "numa campanha" (aos 2.89s) */}
          {frame >= 87 && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 28px',
                borderRadius: 16,
                background: 'rgba(34, 197, 94, 0.15)',
                border: '1.5px solid #22C55E',
                transform: `scale(${highlightSpring})`,
                opacity: highlightSpring,
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#22C55E',
                  letterSpacing: 1,
                  textTransform: 'uppercase',
                }}
              >
                Numa Campanha em Massa
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
