import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena0PerguntaProps {
  fontFamily: string;
  ganchoTela: string;
}

export const Cena0Pergunta: React.FC<Cena0PerguntaProps> = ({
  fontFamily,
  ganchoTela,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous camera zoom & pan on background
  const bgScale = interpolate(frame, [0, 150], [1.02, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 150], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const pillEntrance = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const part1Entrance = spring({
    frame: frame - 8, // ~0.3s ("Vou parar de...")
    fps,
    config: {damping: 14, stiffness: 140},
  });

  const part2Entrance = spring({
    frame: frame - 28, // ~0.95s ("perder vendas...")
    fps,
    config: {damping: 11, stiffness: 150},
  });

  const part3Entrance = spring({
    frame: frame - 55, // ~1.85s ("por falta de acompanhamento")
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Center focal cards entrance (~1.5s to 2.5s)
  const cardsEntrance = spring({
    frame: frame - 45,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const card2Entrance = spring({
    frame: frame - 65,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const ganchoEntrance = spring({
    frame: frame - 92, // ~3.1s (gancho fixo)
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Continuous micro-movement
  const floatY = Math.sin(frame / 12) * 5;
  const pulseGlow = 0.85 + Math.sin(frame / 8) * 0.15;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#111827',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background image with motion */}
      <img
        src={staticFile('img_0.jpg')}
        alt=""
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
        }}
      />

      {/* Dark Vignette & Brand Gradient Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(17, 24, 39, 0.75) 0%, rgba(10, 14, 23, 0.95) 85%)',
        }}
      />

      {/* Ambient glowing orb */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: '50%',
          transform: 'translateX(-50%)',
          width: 500,
          height: 500,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(78, 205, 196, 0.2) 0%, transparent 70%)',
          filter: 'blur(50px)',
          opacity: pulseGlow,
          pointerEvents: 'none',
        }}
      />

      {/* Content Container (Safe zone: y=165 to 1420) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          bottom: 380,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'flex-start',
        }}
      >
        {/* Top Context Pill: Dúvida de Vendas */}
        {pillEntrance > 0 && (
          <div
            style={{
              opacity: pillEntrance,
              transform: `scale(${pillEntrance})`,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 28px',
              borderRadius: 30,
              backgroundColor: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(78, 205, 196, 0.5)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
              marginBottom: 24,
            }}
          >
            <span style={{fontSize: 32}}>❓</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: '#4ECDC4',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              Dúvida de Vendas
            </span>
          </div>
        )}

        {/* Big Kinetic Question Blocks */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            transform: `translateY(${floatY}px)`,
          }}
        >
          {/* Part 1: "VOU PARAR DE" */}
          {part1Entrance > 0 && (
            <div
              style={{
                opacity: part1Entrance,
                transform: `scale(${0.9 + part1Entrance * 0.1})`,
                fontSize: 52,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 1,
                textAlign: 'center',
                textShadow: '0 4px 16px rgba(0, 0, 0, 0.8)',
              }}
            >
              VOU PARAR DE
            </div>
          )}

          {/* Part 2: "PERDER VENDAS?" */}
          {part2Entrance > 0 && (
            <div
              style={{
                opacity: part2Entrance,
                transform: `scale(${0.85 + part2Entrance * 0.15})`,
                backgroundColor: '#4ECDC4',
                padding: '14px 44px',
                borderRadius: 24,
                boxShadow: '0 12px 36px rgba(78, 205, 196, 0.45)',
              }}
            >
              <span
                style={{
                  fontSize: 72,
                  fontWeight: 900,
                  color: '#111827',
                  letterSpacing: 1,
                  textAlign: 'center',
                  display: 'block',
                }}
              >
                PERDER VENDAS?
              </span>
            </div>
          )}

          {/* Part 3: "por falta de acompanhamento?" */}
          {part3Entrance > 0 && (
            <div
              style={{
                opacity: part3Entrance,
                transform: `translateY(${(1 - part3Entrance) * 15}px)`,
                fontSize: 46,
                fontWeight: 800,
                color: '#F8FAFC',
                textAlign: 'center',
                maxWidth: 880,
                lineHeight: 1.25,
                textWrap: 'balance',
                textShadow: '0 4px 20px rgba(0, 0, 0, 0.9)',
                marginTop: 4,
              }}
            >
              por falta de acompanhamento?
            </div>
          )}
        </div>

        {/* Central Focal Element: Visualizing the Pain Point (Propostas Paradas) */}
        <div
          style={{
            width: '100%',
            marginTop: 36,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            opacity: cardsEntrance,
            transform: `translateY(${(1 - cardsEntrance) * 20}px)`,
          }}
        >
          {/* Proposal Card 1 */}
          <div
            style={{
              backgroundColor: 'rgba(17, 24, 39, 0.88)',
              border: '2px solid rgba(239, 68, 68, 0.35)',
              borderRadius: 20,
              padding: '18px 26px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 36}}>📄</span>
              <div style={{display: 'flex', flexDirection: 'column'}}>
                <span style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                  Proposta Orçamento #104
                </span>
                <span style={{fontSize: 32, fontWeight: 600, color: '#94A3B8'}}>
                  Enviada no WhatsApp
                </span>
              </div>
            </div>
            <div
              style={{
                padding: '6px 16px',
                borderRadius: 12,
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid rgba(239, 68, 68, 0.6)',
              }}
            >
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FCA5A5',
                }}
              >
                Parada há 4 dias ⚠️
              </span>
            </div>
          </div>

          {/* Proposal Card 2 */}
          {card2Entrance > 0 && (
            <div
              style={{
                opacity: card2Entrance,
                transform: `translateY(${(1 - card2Entrance) * 15}px)`,
                backgroundColor: 'rgba(17, 24, 39, 0.88)',
                border: '2px solid rgba(234, 179, 8, 0.35)',
                borderRadius: 20,
                padding: '18px 26px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span style={{fontSize: 36}}>💬</span>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                    Lead Interessado #105
                  </span>
                  <span style={{fontSize: 32, fontWeight: 600, color: '#94A3B8'}}>
                    Cliente não respondeu
                  </span>
                </div>
              </div>
              <div
                style={{
                  padding: '6px 16px',
                  borderRadius: 12,
                  backgroundColor: 'rgba(234, 179, 8, 0.2)',
                  border: '1px solid rgba(234, 179, 8, 0.6)',
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FDE047',
                  }}
                >
                  Sem acompanhamento ⏳
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Gancho de tela pill (appears at ~3.1s) */}
        {ganchoEntrance > 0 && (
          <div
            style={{
              opacity: ganchoEntrance,
              transform: `scale(${0.9 + ganchoEntrance * 0.1})`,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              marginTop: 28,
              padding: '14px 32px',
              borderRadius: 20,
              backgroundColor: 'rgba(78, 205, 196, 0.18)',
              border: '2px solid #4ECDC4',
              boxShadow: '0 8px 28px rgba(78, 205, 196, 0.35)',
            }}
          >
            <span style={{fontSize: 34}}>⚡</span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#4ECDC4',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              {ganchoTela}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
