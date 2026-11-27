import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Scene0_Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous background camera push-in (1.08 to 1.18)
  const bgScale = interpolate(frame, [0, 150], [1.08, 1.20], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 150], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Continuous push-in on the cards container (1.0 to 1.05) to eliminate any static moment
  const cardsPushIn = interpolate(frame, [0, 150], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Entrance animations for staggered kinetic text
  // Immediate pop-in at frame 0 (0.0s) -> Immediate hook
  const card1Spring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // 0.33s (frame 10) -> Notification message enters quickly
  const notifSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 1.13s (frame 34) -> The core dilemma "DEMORA A RESPONDER?" enters
  const card2Spring = spring({
    frame: frame - 34,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Scale bounce & glow emphasis on "DEMORA A RESPONDER?" at frame 76 (2.53s, word 'demora')
  const emphasisSpring = spring({
    frame: frame - 76,
    fps,
    config: {damping: 10, stiffness: 170},
  });
  const emphasisScale =
    frame >= 76
      ? interpolate(emphasisSpring, [0, 0.4, 1], [1.0, 1.10, 1.03])
      : 1.0;

  // Micro-floating motion and continuous pulse dynamics (>4% active movement)
  const floatY = Math.sin(frame * 0.09) * 6;
  const pulseAlert = 1 + Math.sin(frame * 0.16) * 0.05;
  const pulseTag =
    emphasisScale * (1.0 + Math.sin(frame * 0.18) * 0.035);
  const glowSpread =
    (frame >= 76 ? 30 : 16) + Math.sin(frame * 0.18) * 14;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
      }}
    >
      {/* Background: Real physical store video with subtle blur & motion + protective veil */}
      <div
        style={{
          position: 'absolute',
          inset: -20,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(10px) brightness(0.50)',
          }}
        />
        {/* Dark radial overlay to guarantee text legibility while keeping store atmosphere */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 35%, rgba(15, 23, 42, 0.65) 0%, rgba(10, 13, 20, 0.92) 100%)',
          }}
        />
      </div>

      {/* Floating luminous bokeh light particles drifting gently */}
      {[
        {top: 280, left: 140, size: 280, color: 'rgba(167, 139, 250, 0.22)', speed: 0.06},
        {top: 650, left: 620, size: 340, color: 'rgba(251, 191, 36, 0.18)', speed: 0.08},
        {top: 1020, left: 180, size: 380, color: 'rgba(167, 139, 250, 0.20)', speed: 0.05},
      ].map((pt, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            top: pt.top + Math.sin(frame * pt.speed + i) * 16,
            left: pt.left + Math.cos(frame * pt.speed + i) * 12,
            width: pt.size,
            height: pt.size,
            borderRadius: '50%',
            background: pt.color,
            filter: 'blur(75px)',
            pointerEvents: 'none',
          }}
        />
      ))}

      {/* Top Badge: Category Context (y=165) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            border: '1.5px solid rgba(167, 139, 250, 0.5)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#A78BFA',
              boxShadow: '0 0 10px #A78BFA',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#F8FAFC',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            Atendimento da Loja
          </span>
        </div>
      </div>

      {/* Main Kinetic Content Container (Vertical coverage centered y=240 to 1250, Push-in contínuo) */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 60,
          right: 60,
          transform: `scale(${cardsPushIn}) translateY(${floatY}px)`,
          transformOrigin: '50% 45%',
          display: 'flex',
          flexDirection: 'column',
          gap: 28,
          zIndex: 10,
        }}
      >
        {/* Card 1: Question Lead (Imediato frame 0, gancho forte) */}
        <div
          style={{
            opacity: card1Spring,
            transform: `translateY(${(1 - card1Spring) * 25}px)`,
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            border: '1.5px solid rgba(167, 139, 250, 0.35)',
            borderRadius: 24,
            padding: '28px 36px',
            boxShadow: '0 20px 45px rgba(0, 0, 0, 0.75)',
          }}
        >
          <div
            style={{
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.2,
              textWrap: 'balance',
            }}
          >
            Cliente pergunta sobre um produto...
          </div>
        </div>

        {/* Central Notification Card: Realistic Direct alert with continuous pulse & alert badge */}
        {frame >= 8 && (
          <div
            style={{
              opacity: notifSpring,
              transform: `scale(${0.95 + notifSpring * 0.05}) translateY(${(1 - notifSpring) * 25}px)`,
              backgroundColor: 'rgba(30, 41, 59, 0.96)',
              border: '2px solid rgba(167, 139, 250, 0.45)',
              borderRadius: 26,
              padding: '28px 32px',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              boxShadow:
                '0 20px 50px rgba(0, 0, 0, 0.75), 0 0 30px rgba(167, 139, 250, 0.25)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: '50%',
                    backgroundColor: '#A78BFA',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 28,
                    color: '#121216',
                    fontWeight: 900,
                    boxShadow: '0 0 16px rgba(167, 139, 250, 0.6)',
                  }}
                >
                  💬
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span style={{fontSize: 36, fontWeight: 800, color: '#FFFFFF'}}>
                    Mensagem no Direct
                  </span>
                  <span style={{fontSize: 28, fontWeight: 600, color: '#A78BFA'}}>
                    Instagram da Loja
                  </span>
                </div>
              </div>
              <span
                style={{
                  fontSize: 30,
                  fontWeight: 600,
                  color: '#94A3B8',
                }}
              >
                Agora
              </span>
            </div>

            <div
              style={{
                fontSize: 38,
                fontWeight: 600,
                color: '#F1F5F9',
                backgroundColor: 'rgba(15, 23, 42, 0.65)',
                padding: '16px 20px',
                borderRadius: 16,
                borderLeft: '4px solid #A78BFA',
              }}
            >
              "Vocês têm esse modelo em outras cores?"
            </div>

            <div
              style={{
                alignSelf: 'flex-start',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                backgroundColor: 'rgba(245, 158, 11, 0.22)',
                border: '1.5px solid rgba(245, 158, 11, 0.75)',
                borderRadius: 999,
                padding: '10px 22px',
                transform: `scale(${pulseAlert})`,
                boxShadow: '0 6px 18px rgba(245, 158, 11, 0.3)',
              }}
            >
              <span style={{fontSize: 26}}>⏳</span>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FBBF24',
                }}
              >
                Aguardando resposta...
              </span>
            </div>
          </div>
        )}

        {/* Card 2: The Core Dilemma with Kinetic Highlight & Scale Bounce at frame 76 */}
        {frame >= 32 && (
          <div
            style={{
              opacity: card2Spring,
              transform: `scale(${0.94 + card2Spring * 0.06}) translateY(${(1 - card2Spring) * 25}px)`,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid #A78BFA',
              borderRadius: 26,
              padding: '30px 36px',
              display: 'flex',
              flexDirection: 'column',
              gap: 18,
              boxShadow: `0 24px 60px rgba(0, 0, 0, 0.8), 0 0 ${glowSpread}px rgba(167, 139, 250, 0.35)`,
            }}
          >
            <div
              style={{
                fontSize: 46,
                fontWeight: 800,
                color: '#F8FAFC',
              }}
            >
              E você...
            </div>

            {/* Kinetic Highlight / Marca-texto with scale bounce on emphasis */}
            <div
              style={{
                display: 'inline-block',
                alignSelf: 'flex-start',
                backgroundColor: '#A78BFA',
                padding: '14px 28px',
                borderRadius: 16,
                transform: `scale(${pulseTag})`,
                boxShadow: `0 10px 28px rgba(167, 139, 250, 0.6), 0 0 ${glowSpread}px rgba(167, 139, 250, 0.7)`,
              }}
            >
              <span
                style={{
                  fontSize: 54,
                  fontWeight: 900,
                  color: '#121216',
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                }}
              >
                Demora a responder?
              </span>
            </div>

            <div
              style={{
                fontSize: 34,
                fontWeight: 600,
                color: '#CBD5E1',
                marginTop: 2,
              }}
            >
              Demora no retorno faz o cliente esfriar
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
