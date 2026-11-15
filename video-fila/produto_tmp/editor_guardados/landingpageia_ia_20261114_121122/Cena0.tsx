import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

interface Cena0Props {
  fontFamily: string;
  destaque: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily, destaque}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera do fundo (push-in + pan suave)
  const bgScale = interpolate(frame, [0, 171], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 171], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Badge topo - entra rápido a 0.2s (frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Bloco 1: "SEU SITE ATRAI VISITAS..." entra aos 0.4s (frame 12)
  const card1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Bloco 2: "...MAS NINGUÉM ENTRA EM CONTATO?" entra aos 2.7s (frame 81)
  const card2Spring = spring({
    frame: frame - 81,
    fps,
    config: {damping: 11, stiffness: 110},
  });

  // Pulso contínuo sutil
  const breathe = Math.sin(frame * 0.08) * 4;

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
      {/* Imagem de Fundo com zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: -60,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          filter: 'brightness(0.65) contrast(1.15)',
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
      </div>

      {/* Véu de contraste gradiente escuro */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 40%, rgba(17, 24, 39, 0.45) 0%, rgba(10, 14, 23, 0.88) 85%)',
        }}
      />

      {/* Grafismos de tecnologia / grade animada de tráfego */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          opacity: 0.25,
        }}
      >
        <svg width="1080" height="1920">
          <defs>
            <pattern
              id="grid-c0"
              width="80"
              height="80"
              patternUnits="userSpaceOnUse"
            >
              <circle cx="40" cy="40" r="1.5" fill="#F59E0B" />
              <path
                d="M 80 0 L 0 0 0 80"
                fill="none"
                stroke="rgba(245, 158, 11, 0.15)"
                strokeWidth="1"
              />
            </pattern>
          </defs>
          <rect width="1080" height="1920" fill="url(#grid-c0)" />
        </svg>
      </div>

      {/* Círculos dinâmicos de radar no centro */}
      <div
        style={{
          position: 'absolute',
          top: 750,
          left: 540,
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
        }}
      >
        {[1, 2, 3].map((idx) => {
          const ringProgress = ((frame * 0.02 + idx * 0.33) % 1);
          const ringSize = ringProgress * 700 + 150;
          const ringOpacity = (1 - ringProgress) * 0.35;
          return (
            <div
              key={idx}
              style={{
                position: 'absolute',
                top: -ringSize / 2,
                left: -ringSize / 2,
                width: ringSize,
                height: ringSize,
                borderRadius: '50%',
                border: `2px solid ${destaque}`,
                opacity: ringOpacity,
              }}
            />
          );
        })}
      </div>

      {/* Topo Informativo (y=165 a 260) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 30,
            background: 'rgba(17, 24, 39, 0.88)',
            border: `2px solid ${destaque}`,
            boxShadow: `0 8px 24px rgba(0, 0, 0, 0.6), 0 0 16px rgba(245, 158, 11, 0.25)`,
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: destaque,
              boxShadow: `0 0 10px ${destaque}`,
            }}
          />
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            Site sem vendas?
          </span>
        </div>
      </div>

      {/* Centro Focal Dinâmico (y=300 a 1240) */}
      <div
        style={{
          position: 'absolute',
          top: 290,
          left: 60,
          width: 960,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 28,
          transform: `translateY(${breathe}px)`,
        }}
      >
        {/* Bloco 1: SEU SITE INSTITUCIONAL ATRAI VISITAS */}
        <div
          style={{
            width: '100%',
            padding: '34px 38px',
            borderRadius: 26,
            background: 'rgba(17, 24, 39, 0.94)',
            border: '2px solid rgba(255, 255, 255, 0.14)',
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
            transform: `scale(${card1Spring}) translateY(${(1 - card1Spring) * 35}px)`,
            opacity: card1Spring,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 16,
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 700,
                color: '#94A3B8',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Tráfego do Site
            </span>
            <div
              style={{
                display: 'flex',
                gap: 8,
                alignItems: 'center',
                backgroundColor: 'rgba(34, 197, 94, 0.15)',
                padding: '6px 14px',
                borderRadius: 20,
                border: '1px solid rgba(34, 197, 94, 0.3)',
              }}
            >
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  backgroundColor: '#22C55E',
                }}
              />
              <span style={{fontSize: 32, color: '#22C55E', fontWeight: 800}}>
                Visitas ativas
              </span>
            </div>
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.22,
              textWrap: 'balance',
            }}
          >
            Seu site institucional atrai visitas...
          </h1>

          {/* Gráfico de barras de tráfego com métricas visuais */}
          <div
            style={{
              marginTop: 22,
              padding: '18px 22px',
              backgroundColor: 'rgba(255,255,255,0.05)',
              borderRadius: 18,
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 16,
              }}
            >
              <span style={{fontSize: 32, fontWeight: 700, color: '#CBD5E1'}}>
                Acessos contínuos
              </span>
              <span style={{fontSize: 32, fontWeight: 800, color: '#22C55E'}}>
                ▲ Em crescimento
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'flex-end',
                justifyContent: 'space-between',
                gap: 12,
                height: 110,
                padding: '0 10px',
              }}
            >
              {[42, 60, 78, 55, 88, 72, 98].map((h, i) => {
                const barProgress = spring({
                  frame: frame - (10 + i * 3),
                  fps,
                  config: {damping: 12},
                });
                const isHighlight = i === 6;
                return (
                  <div
                    key={i}
                    style={{
                      width: 90,
                      height: `${h * barProgress}%`,
                      background: isHighlight
                        ? `linear-gradient(to top, #D97706, ${destaque})`
                        : 'linear-gradient(to top, rgba(245, 158, 11, 0.2), rgba(245, 158, 11, 0.55))',
                      borderRadius: '8px 8px 4px 4px',
                      boxShadow: isHighlight
                        ? `0 0 16px ${destaque}`
                        : 'none',
                    }}
                  />
                );
              })}
            </div>
          </div>
        </div>

        {/* Bloco 2: ...MAS NINGUÉM ENTRA EM CONTATO? (entra aos 2.5s) */}
        {frame >= 70 && (
          <div
            style={{
              width: '100%',
              padding: '36px 38px',
              borderRadius: 26,
              background: 'rgba(24, 18, 12, 0.96)',
              border: `3px solid ${destaque}`,
              boxShadow: `0 24px 60px rgba(0,0,0,0.85), 0 0 35px rgba(245, 158, 11, 0.35)`,
              transform: `scale(${card2Spring}) translateY(${(1 - card2Spring) * 40}px)`,
              opacity: card2Spring,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 14,
              }}
            >
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '6px 16px',
                  borderRadius: 12,
                  backgroundColor: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid #EF4444',
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#F87171',
                    textTransform: 'uppercase',
                  }}
                >
                  Gargalo Comercial
                </span>
              </div>

              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#F87171',
                }}
              >
                Sem retorno
              </span>
            </div>

            <h2
              style={{
                margin: 0,
                fontSize: 52,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textWrap: 'balance',
              }}
            >
              ...mas{' '}
              <span
                style={{
                  color: destaque,
                  textDecoration: 'underline',
                  textUnderlineOffset: '8px',
                }}
              >
                ninguém entra em contato?
              </span>
            </h2>
          </div>
        )}
      </div>
    </div>
  );
};
