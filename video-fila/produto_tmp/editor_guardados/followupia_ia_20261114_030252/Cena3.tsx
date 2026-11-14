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

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom contínuo na foto de fundo
  const bgScale = interpolate(frame, [0, 193], [1.03, 1.12], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 193], [0, -22], {
    extrapolateRight: 'clamp',
  });

  // Top badge
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card 1: "Hoje eu parei de perder venda" (frame 14)
  const c1Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Card 2: "recupero clientes" (frame 86)
  const c2Spring = spring({
    frame: frame - 86,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Card 3: "sem esforço manual" (frame 116)
  const c3Spring = spring({
    frame: frame - 116,
    fps,
    config: {damping: 13, stiffness: 130},
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
      {/* Imagem de fundo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
          transformOrigin: '50% 60%',
        }}
      >
        <Img
          src={staticFile('img_3.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(17, 24, 39, 0.76) 0%, rgba(17, 24, 39, 0.94) 85%)',
          }}
        />
      </div>

      {/* Topo: Rótulo "O resultado" (y=162) */}
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
            backgroundColor: 'rgba(78, 205, 196, 0.15)',
            border: '1.5px solid #4ECDC4',
            backdropFilter: 'blur(8px)',
          }}
        >
          <span style={{fontSize: 26}}>🏆</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#4ECDC4',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>
      </div>

      {/* Título da cena (y=214) */}
      <div
        style={{
          position: 'absolute',
          top: 214,
          left: 60,
          right: 60,
          textAlign: 'center',
          zIndex: 20,
        }}
      >
        <div
          style={{
            fontSize: 44,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.15,
            textTransform: 'uppercase',
            textShadow: '0 4px 16px rgba(0,0,0,0.9)',
          }}
        >
          RECUPERAÇÃO SEM ESFORÇO MANUAL
        </div>
      </div>

      {/* Grade de Destaques Distribuição Vertical Equilibrada (y=320 a 1280) */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: 70,
          right: 70,
          display: 'flex',
          flexDirection: 'column',
          gap: 36,
          zIndex: 10,
        }}
      >
        {/* Card 1: Fim das perdas */}
        {frame >= 12 && (
          <div
            style={{
              padding: '30px 32px',
              borderRadius: 28,
              backgroundColor: 'rgba(17, 24, 39, 0.90)',
              border: '2px solid rgba(78, 205, 196, 0.55)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.65)',
              display: 'flex',
              alignItems: 'center',
              gap: 24,
              transform: `scale(${Math.max(0, c1Spring)}) translateY(${(1 - Math.min(1, c1Spring)) * 25 + Math.sin(frame / 16) * 4}px)`,
              opacity: Math.min(1, Math.max(0, c1Spring)),
            }}
          >
            <div
              style={{
                width: 76,
                height: 76,
                borderRadius: 22,
                backgroundColor: 'rgba(78, 205, 196, 0.18)',
                border: '1.5px solid #4ECDC4',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 38,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
            <div>
              <div
                style={{
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                Fim das Vendas Perdidas
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#94A3B8',
                  marginTop: 6,
                }}
              >
                Pare de perder clientes por esquecimento
              </div>
            </div>
          </div>
        )}

        {/* Card 2: Reativação */}
        {frame >= 84 && (
          <div
            style={{
              padding: '30px 32px',
              borderRadius: 28,
              backgroundColor: 'rgba(17, 24, 39, 0.90)',
              border: '2px solid rgba(78, 205, 196, 0.55)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.65)',
              display: 'flex',
              alignItems: 'center',
              gap: 24,
              transform: `scale(${Math.max(0, c2Spring)}) translateY(${(1 - Math.min(1, c2Spring)) * 25 + Math.sin((frame + 10) / 16) * 4}px)`,
              opacity: Math.min(1, Math.max(0, c2Spring)),
            }}
          >
            <div
              style={{
                width: 76,
                height: 76,
                borderRadius: 22,
                backgroundColor: 'rgba(78, 205, 196, 0.18)',
                border: '1.5px solid #4ECDC4',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 38,
                flexShrink: 0,
              }}
            >
              💬
            </div>
            <div>
              <div
                style={{
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                Leads Inativos Reativados
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#94A3B8',
                  marginTop: 6,
                }}
              >
                Follow-ups no WhatsApp que convertem
              </div>
            </div>
          </div>
        )}

        {/* Card 3: Automação completa */}
        {frame >= 114 && (
          <div
            style={{
              padding: '30px 32px',
              borderRadius: 28,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid #4ECDC4',
              backdropFilter: 'blur(16px)',
              boxShadow:
                '0 20px 40px rgba(0, 0, 0, 0.7), 0 0 30px rgba(78,205,196,0.35)',
              display: 'flex',
              alignItems: 'center',
              gap: 24,
              transform: `scale(${Math.max(0, c3Spring)}) translateY(${(1 - Math.min(1, c3Spring)) * 25 + Math.sin((frame + 20) / 16) * 4}px)`,
              opacity: Math.min(1, Math.max(0, c3Spring)),
            }}
          >
            <div
              style={{
                width: 76,
                height: 76,
                borderRadius: 22,
                backgroundColor: 'rgba(78, 205, 196, 0.25)',
                border: '2px solid #4ECDC4',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 38,
                flexShrink: 0,
              }}
            >
              ⚡
            </div>
            <div>
              <div
                style={{
                  fontSize: 40,
                  fontWeight: 900,
                  color: '#4ECDC4',
                  lineHeight: 1.2,
                }}
              >
                Zero Esforço Manual
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#E2E8F0',
                  marginTop: 6,
                }}
              >
                A inteligência artificial conduz o fechamento
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
