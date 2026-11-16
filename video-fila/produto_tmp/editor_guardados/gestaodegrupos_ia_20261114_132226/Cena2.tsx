import React from 'react';
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Smooth continuous push-in on the entire scene (1.0 -> 1.08)
  const sceneScale = interpolate(frame, [0, 246], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  const titleSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  const phoneSpring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 15, mass: 0.8},
  });

  // Checklist items synchronization with voice
  // "O recurso de atas gera um resumo direto no grupo" -> frame 36 (~13.0s)
  const item1Spring = spring({
    frame: frame - 36,
    fps,
    config: {damping: 13, mass: 0.5},
  });

  // "organizando os principais pontos" -> frame 105 (~15.3s)
  const item2Spring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 13, mass: 0.5},
  });

  // "de forma prática" -> frame 156 (~17.0s)
  const item3Spring = spring({
    frame: frame - 156,
    fps,
    config: {damping: 13, mass: 0.5},
  });

  // Subtle 3D floating motion
  const tiltY = Math.sin(frame * 0.05) * 2;
  const floatY = Math.cos(frame * 0.06) * 4;

  // Background ambient animation: pulsing glowing orbs
  const orbScale1 = 1.0 + Math.sin(frame * 0.06) * 0.08;
  const orbScale2 = 1.0 + Math.cos(frame * 0.05) * 0.10;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: '#0F172A',
        fontFamily,
      }}
    >
      {/* Sleek Abstract Motion Graphic Background in Brand Colors (eliminates clashing crypto b-roll) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(ellipse at 50% 30%, #134E4A 0%, #111827 55%, #0B0F19 100%)',
        }}
      />

      {/* Dynamic ambient glowing light orbs */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: '20%',
          width: 600,
          height: 600,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(20, 184, 166, 0.28) 0%, rgba(20, 184, 166, 0) 70%)',
          transform: `translate(-50%, -50%) scale(${orbScale1})`,
          filter: 'blur(40px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 750,
          right: '15%',
          width: 550,
          height: 550,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(45, 212, 191, 0.22) 0%, rgba(45, 212, 191, 0) 70%)',
          transform: `translate(50%, -50%) scale(${orbScale2})`,
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* Subtle tech grid lines representing automation network */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(20, 184, 166, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(20, 184, 166, 0.06) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
          opacity: 0.8,
          pointerEvents: 'none',
        }}
      />

      {/* Upper Area: Badge + Title in Standardized Dark Box with Brand Border (Matches Cenas 1 and 3) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 20,
        }}
      >
        {/* Badge: Como Funciona */}
        <div
          style={{
            opacity: badgeSpring,
            transform: `translateY(${interpolate(badgeSpring, [0, 1], [-15, 0])}px)`,
            padding: '8px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(20, 184, 166, 0.20)',
            border: '1.5px solid rgba(20, 184, 166, 0.65)',
            boxShadow: '0 0 20px rgba(20, 184, 166, 0.3)',
            backdropFilter: 'blur(10px)',
            color: '#14B8A6',
            fontSize: 30,
            fontWeight: 800,
            letterSpacing: 1.5,
            textTransform: 'uppercase',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <span style={{fontSize: 26}}>⚡</span>
          <span>Como Funciona • Atas Automáticas</span>
        </div>

        {/* Title Box: Standardized dark container with brand border (100% readable, zero clash) */}
        <div
          style={{
            opacity: titleSpring,
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.9, 1])})`,
            padding: '14px 32px',
            borderRadius: 20,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: '1.5px solid rgba(20, 184, 166, 0.7)',
            boxShadow:
              '0 12px 30px rgba(0, 0, 0, 0.6), 0 0 25px rgba(20, 184, 166, 0.25)',
            backdropFilter: 'blur(14px)',
            maxWidth: 920,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: 44,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: -0.5,
            }}
          >
            Resumo Direto no Grupo
          </div>
        </div>
      </div>

      {/* Center Frontal Smartphone Mockup (Starts at top: 355, giving 50px of clear space below title) */}
      <div
        style={{
          position: 'absolute',
          top: 355,
          left: 65,
          right: 65,
          display: 'flex',
          justifyContent: 'center',
          perspective: 1200,
          zIndex: 10,
        }}
      >
        <div
          style={{
            width: 890,
            opacity: phoneSpring,
            transform: `scale(${phoneSpring * sceneScale}) translateY(${floatY}px) rotateY(${tiltY}deg)`,
            transformOrigin: 'center center',
            borderRadius: 32,
            backgroundColor: 'rgba(15, 23, 42, 0.97)',
            border: '2.5px solid rgba(20, 184, 166, 0.55)',
            boxShadow:
              '0 30px 60px -10px rgba(0, 0, 0, 0.8), 0 0 40px rgba(20, 184, 166, 0.3)',
            backdropFilter: 'blur(18px)',
            overflow: 'hidden',
          }}
        >
          {/* Mockup WhatsApp Header */}
          <div
            style={{
              padding: '20px 26px',
              backgroundColor: 'rgba(20, 184, 166, 0.20)',
              borderBottom: '1.5px solid rgba(20, 184, 166, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 18,
                  backgroundColor: '#14B8A6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: 32,
                  boxShadow: '0 0 20px rgba(20, 184, 166, 0.6)',
                }}
              >
                🤖
              </div>
              <div>
                <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  Grupo da Empresa
                </div>
                {/* Elevated contrast and font-size for smartphone legibility */}
                <div
                  style={{
                    fontSize: 28,
                    color: '#5EEAD4',
                    fontWeight: 700,
                    letterSpacing: 0.3,
                  }}
                >
                  Gestão de Grupos IA ativo
                </div>
              </div>
            </div>

            {/* Tag Simulação: Clear, high contrast pill */}
            <div
              style={{
                padding: '6px 16px',
                borderRadius: 999,
                backgroundColor: 'rgba(255, 255, 255, 0.18)',
                border: '1px solid rgba(255, 255, 255, 0.4)',
                color: '#FFFFFF',
                fontSize: 24,
                fontWeight: 700,
                letterSpacing: 0.5,
              }}
            >
              Simulação
            </div>
          </div>

          {/* Chat Body & Atas Card */}
          <div
            style={{
              padding: '26px 28px',
              display: 'flex',
              flexDirection: 'column',
              gap: 20,
            }}
          >
            {/* User message in group */}
            <div
              style={{
                alignSelf: 'flex-start',
                maxWidth: '85%',
                padding: '16px 24px',
                borderRadius: '18px 18px 18px 4px',
                backgroundColor: 'rgba(30, 41, 59, 0.95)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#E2E8F0',
                fontSize: 32,
                lineHeight: 1.3,
              }}
            >
              Quem pode resumir o que foi alinhado hoje?
              <div
                style={{
                  fontSize: 22,
                  color: '#94A3B8',
                  textAlign: 'right',
                  marginTop: 4,
                }}
              >
                14:22
              </div>
            </div>

            {/* AI Automated ATA Card */}
            <div
              style={{
                alignSelf: 'stretch',
                padding: '22px 24px',
                borderRadius: 22,
                backgroundColor: 'rgba(17, 24, 39, 0.98)',
                border: '2px solid rgba(20, 184, 166, 0.6)',
                boxShadow: '0 8px 30px rgba(20, 184, 166, 0.22)',
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
              }}
            >
              {/* Header of ATA */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  paddingBottom: 14,
                  borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
                }}
              >
                <div
                  style={{
                    padding: '6px 16px',
                    borderRadius: 10,
                    backgroundColor: '#14B8A6',
                    color: '#FFFFFF',
                    fontSize: 26,
                    fontWeight: 900,
                    letterSpacing: 0.5,
                  }}
                >
                  ATA DO GRUPO
                </div>
                <div style={{fontSize: 28, color: '#94A3B8', fontWeight: 600}}>
                  Gerado automaticamente
                </div>
              </div>

              {/* Checklist Items: Staggered entry synchronized with speech */}
              <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>
                {/* Item 1: enters ~13.4s on 'gera um resumo' */}
                <div
                  style={{
                    opacity: item1Spring,
                    transform: `translateX(${interpolate(item1Spring, [0, 1], [-25, 0])}px)`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: '12px 18px',
                    borderRadius: 14,
                    backgroundColor:
                      frame >= 36
                        ? 'rgba(20, 184, 166, 0.18)'
                        : 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(20, 184, 166, 0.4)',
                  }}
                >
                  <div
                    style={{
                      width: 38,
                      height: 38,
                      borderRadius: 10,
                      backgroundColor: '#14B8A6',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#FFFFFF',
                      fontSize: 24,
                      fontWeight: 900,
                    }}
                  >
                    ✓
                  </div>
                  <div
                    style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}
                  >
                    Alinhamento da reunião concluído
                  </div>
                </div>

                {/* Item 2: enters ~15.3s on 'organizando os principais pontos' */}
                <div
                  style={{
                    opacity: item2Spring,
                    transform: `translateX(${interpolate(item2Spring, [0, 1], [-25, 0])}px)`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: '12px 18px',
                    borderRadius: 14,
                    backgroundColor:
                      frame >= 105
                        ? 'rgba(20, 184, 166, 0.18)'
                        : 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(20, 184, 166, 0.4)',
                  }}
                >
                  <div
                    style={{
                      width: 38,
                      height: 38,
                      borderRadius: 10,
                      backgroundColor: '#14B8A6',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#FFFFFF',
                      fontSize: 24,
                      fontWeight: 900,
                    }}
                  >
                    ✓
                  </div>
                  <div
                    style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}
                  >
                    Principais decisões aprovadas
                  </div>
                </div>

                {/* Item 3: enters ~17.0s on 'de forma prática' */}
                <div
                  style={{
                    opacity: item3Spring,
                    transform: `translateX(${interpolate(item3Spring, [0, 1], [-25, 0])}px)`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: '12px 18px',
                    borderRadius: 14,
                    backgroundColor:
                      frame >= 156
                        ? 'rgba(20, 184, 166, 0.18)'
                        : 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(20, 184, 166, 0.4)',
                  }}
                >
                  <div
                    style={{
                      width: 38,
                      height: 38,
                      borderRadius: 10,
                      backgroundColor: '#14B8A6',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#FFFFFF',
                      fontSize: 24,
                      fontWeight: 900,
                    }}
                  >
                    ✓
                  </div>
                  <div
                    style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}
                  >
                    Próximos passos organizados
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
