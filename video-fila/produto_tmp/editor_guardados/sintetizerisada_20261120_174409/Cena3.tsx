import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous multi-axis Ken Burns motion (slow push-in + horizontal pan)
  const bgScale = interpolate(frame, [0, 271], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 271], [-25, 25], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 271], [8, -16], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const titleSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Dynamic slot resolution for 09:00 at frame 40 ("a IA resolve sozinha")
  const slotResolveSpring = spring({
    frame: frame - 40,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Staggered slot reveals across the full scene:
  // Slot 0 (09:00): enters frame 10, resolves frame 40
  // Slot 1 (10:30): enters frame 35
  // Slot 2 (14:00): enters frame 80
  // Slot 3 (16:00): enters frame 140 (synchronized with locution "agenda organizada"!)
  const slot0Spring = spring({frame: frame - 10, fps, config: {damping: 14, stiffness: 110}});
  const slot1Spring = spring({frame: frame - 35, fps, config: {damping: 14, stiffness: 110}});
  const slot2Spring = spring({frame: frame - 80, fps, config: {damping: 14, stiffness: 110}});
  const slot3Spring = spring({frame: frame - 140, fps, config: {damping: 14, stiffness: 110}});

  // Highlight pulse at frame 140 when locution says "agenda organizada"
  const pulseOrganizada = frame >= 140 ? 1 + Math.sin((frame - 140) / 4) * 0.035 : 1;
  const glowGreen = frame >= 140 ? interpolate(frame, [140, 160, 200], [0.6, 0.35, 0.15], {extrapolateRight: 'clamp'}) : 0;

  // Continuous micro-movement
  const pulseHighlight = 1 + Math.sin(frame / 9) * 0.02;
  const tabletFloat = Math.sin(frame / 12) * 4;

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Background Image with multi-axis camera motion */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translate(${bgTranslateX}px, ${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_3.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Protective Gradient Overlay keeping salon professional clearly visible in the center */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.88) 0%, rgba(15,23,42,0.6) 16%, rgba(15,23,42,0.15) 32%, rgba(15,23,42,0.2) 58%, rgba(15,23,42,0.85) 75%, rgba(15,23,42,0.96) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Category Badge (y: 165 - 225) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            backgroundColor: '#1F2937',
            border: '2px solid #FFA94D',
            padding: '10px 26px',
            borderRadius: 999,
            boxShadow: '0 8px 25px rgba(255, 169, 77, 0.3)',
          }}
        >
          <span style={{fontSize: 32}}>✨</span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFA94D',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            O Resultado • Rotina Sem Atrito
          </span>
        </div>
      </div>

      {/* Immediate Positive Victory Headline (y: 240 - 355) */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 60,
          right: 60,
          textAlign: 'center',
          zIndex: 20,
          transform: `scale(${titleSpring})`,
          opacity: titleSpring,
        }}
      >
        <div
          style={{
            fontFamily,
            fontSize: 46,
            fontWeight: 900,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            letterSpacing: '-0.5px',
            textShadow: '0 4px 16px rgba(0,0,0,0.85)',
          }}
        >
          Comece o seu dia com a
        </div>
        <div
          style={{
            marginTop: 8,
            display: 'inline-block',
            backgroundColor: '#22C55E',
            color: '#064E3B',
            fontFamily,
            fontSize: 46,
            fontWeight: 900,
            padding: '6px 24px',
            borderRadius: 14,
            textTransform: 'uppercase',
            boxShadow: `0 6px 24px rgba(34,197,94,${glowGreen ? 0.6 : 0.35})`,
            transform: `scale(${pulseOrganizada})`,
          }}
        >
          Agenda Organizada ✓
        </div>
      </div>

      {/* Appointment Schedule Dashboard Mockup in Lower Section (y: 870 - 1280) */}
      <div
        style={{
          position: 'absolute',
          top: 870,
          left: 65,
          right: 65,
          backgroundColor: 'rgba(17, 24, 39, 0.96)',
          border: '2px solid rgba(255, 255, 255, 0.18)',
          borderRadius: 28,
          padding: '18px 22px',
          boxShadow: '0 24px 50px rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(16px)',
          transform: `translateY(${tabletFloat}px)`,
          zIndex: 25,
        }}
      >
        {/* Schedule Header / Browser Top Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
            paddingBottom: 12,
            marginBottom: 14,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <span style={{fontSize: 32}}>📅</span>
            <div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Grade de Atendimentos
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 700,
                  color: '#9CA3AF',
                }}
              >
                Sincronização em tempo real
              </div>
            </div>
          </div>

          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              backgroundColor: 'rgba(34, 197, 94, 0.2)',
              border: '1.5px solid #22C55E',
              padding: '6px 16px',
              borderRadius: 12,
              fontFamily,
              fontSize: 30,
              fontWeight: 800,
              color: '#86EFAC',
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: '#22C55E',
                boxShadow: '0 0 8px #22C55E',
              }}
            />
            Preenchida
          </div>
        </div>

        {/* Schedule Slots */}
        <div style={{display: 'flex', flexDirection: 'column', gap: 10}}>
          {/* Slot 1: 09:00 - Dynamic transition to Vaga Preenchida (Lista de Espera) */}
          {frame < 40 ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                border: '1.5px solid #EF4444',
                borderRadius: 16,
                padding: '10px 16px',
                transform: `scale(${slot0Spring})`,
                opacity: slot0Spring,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#F87171',
                  }}
                >
                  09:00
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FECACA',
                  }}
                >
                  Cancelamento Noturno
                </span>
              </div>
              <div
                style={{
                  backgroundColor: '#7F1D1D',
                  color: '#FECACA',
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 900,
                  padding: '4px 14px',
                  borderRadius: 10,
                  textTransform: 'uppercase',
                }}
              >
                Vaga Livre ⚠️
              </div>
            </div>
          ) : (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                backgroundColor: 'rgba(34, 197, 94, 0.18)',
                border: '2px solid #22C55E',
                borderRadius: 16,
                padding: '10px 16px',
                transform: `scale(${slotResolveSpring})`,
                boxShadow: '0 4px 18px rgba(34, 197, 94, 0.35)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#22C55E',
                  }}
                >
                  09:00
                </span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FFFFFF',
                  }}
                >
                  Vaga Preenchida
                </span>
              </div>
              <div
                style={{
                  backgroundColor: '#22C55E',
                  color: '#064E3B',
                  fontFamily,
                  fontSize: 30,
                  fontWeight: 900,
                  padding: '4px 14px',
                  borderRadius: 10,
                  textTransform: 'uppercase',
                }}
              >
                Preenchida ✓
              </div>
            </div>
          )}

          {/* Slot 2: 10:30 - Confirmado */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'rgba(31, 41, 55, 0.7)',
              border: '1.5px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 16,
              padding: '10px 16px',
              transform: `scale(${slot1Spring})`,
              opacity: slot1Spring,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#9CA3AF',
                }}
              >
                10:30
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#E5E7EB',
                }}
              >
                Horário Confirmado
              </span>
            </div>
            <div
              style={{
                backgroundColor: 'rgba(34, 197, 94, 0.2)',
                color: '#86EFAC',
                fontFamily,
                fontSize: 30,
                fontWeight: 800,
                padding: '4px 14px',
                borderRadius: 10,
                textTransform: 'uppercase',
              }}
            >
              Confirmado ✓
            </div>
          </div>

          {/* Slot 3: 14:00 - Confirmado */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'rgba(31, 41, 55, 0.7)',
              border: '1.5px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 16,
              padding: '10px 16px',
              transform: `scale(${slot2Spring})`,
              opacity: slot2Spring,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#9CA3AF',
                }}
              >
                14:00
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#E5E7EB',
                }}
              >
                Horário Confirmado
              </span>
            </div>
            <div
              style={{
                backgroundColor: 'rgba(34, 197, 94, 0.2)',
                color: '#86EFAC',
                fontFamily,
                fontSize: 30,
                fontWeight: 800,
                padding: '4px 14px',
                borderRadius: 10,
                textTransform: 'uppercase',
              }}
            >
              Confirmado ✓
            </div>
          </div>

          {/* Slot 4: 16:00 - Cliente Reagendado com pulso verde na locução 'agenda organizada' */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor:
                frame >= 140 ? 'rgba(34, 197, 94, 0.25)' : 'rgba(255, 169, 77, 0.12)',
              border: frame >= 140 ? '2px solid #22C55E' : '1.5px solid #FFA94D',
              borderRadius: 16,
              padding: '10px 16px',
              transform: `scale(${slot3Spring * (frame >= 140 ? pulseOrganizada : 1)})`,
              opacity: slot3Spring,
              boxShadow: frame >= 140 ? '0 0 24px rgba(34, 197, 94, 0.45)' : 'none',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: frame >= 140 ? '#22C55E' : '#FFA94D',
                }}
              >
                16:00
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Cliente Reagendado
              </span>
            </div>
            <div
              style={{
                backgroundColor: frame >= 140 ? '#22C55E' : '#FFA94D',
                color: frame >= 140 ? '#064E3B' : '#1F2937',
                fontFamily,
                fontSize: 30,
                fontWeight: 900,
                padding: '4px 14px',
                borderRadius: 10,
                textTransform: 'uppercase',
              }}
            >
              Reagendado ⚡
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
