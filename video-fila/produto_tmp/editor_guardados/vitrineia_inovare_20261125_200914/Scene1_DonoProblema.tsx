import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Scene1_DonoProblema: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Camera Dynamics:
  // Phase 1 (0 to 127): Medium shot with gradual zoom (1.02x to 1.09x)
  // Frame 128: Clear digital punch-in cut (zoom snaps to 1.25x focado no rosto) na virada da gravidade ('...e eu não conseguia...')
  // Phase 2 (128 to 245): Punch-in close-up continuing slow push-in from 1.25x to 1.32x
  const videoScale =
    frame < 128
      ? interpolate(frame, [0, 128], [1.02, 1.09], {extrapolateRight: 'clamp'})
      : interpolate(frame, [128, 245], [1.25, 1.32], {extrapolateRight: 'clamp'});

  // Visual impact flash on the digital punch-in cut at frame 128
  const punchFlash = interpolate(frame, [128, 131, 142], [0, 0.28, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top header entrance spring
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Intermediate dynamic evolution in Phase 1 at frame 56 (~1.8s, "sobre os produtos da loja")
  // Breaks the 5s static freeze and introduces visual momentum before the punch-in
  const phase1b = frame >= 56;
  const phase1bSpring = spring({
    frame: frame - 56,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Phase 2 transition at frame 128 (~8.9s into video, "e eu não conseguia...")
  const isPhase2 = frame >= 128;
  const phase2Spring = spring({
    frame: frame - 128,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Micro-floating motion to ensure >4% continuous dynamics
  const floatY = Math.sin(frame * 0.08) * 4;
  const alertPulse = 1 + Math.sin(frame * 0.14) * 0.04;
  const badgePulse = 1 + Math.sin(frame * 0.12) * 0.03;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
      }}
    >
      {/* Real Owner Video with slow push-in + punch-in digital at frame 128 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 36%',
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
      </div>

      {/* Dramatic punch-in impact flash at frame 128 */}
      {punchFlash > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: '#EF4444',
            opacity: punchFlash,
            pointerEvents: 'none',
            zIndex: 10,
          }}
        />
      )}

      {/* Top zone soft protective gradient (y=0 to y=430) - ROSTO PRESERVADO */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 440,
          background:
            'linear-gradient(to bottom, rgba(11, 14, 23, 0.90) 0%, rgba(11, 14, 23, 0.65) 70%, rgba(11, 14, 23, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOP SAFE ZONE ELEMENTS (Strictly y=160 to y=410, ROSTO 100% LIVRE) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 70,
          right: 70,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
          zIndex: 20,
        }}
      >
        {/* Rótulo Badge */}
        <div
          style={{
            opacity: headerSpring,
            transform: `translateY(${(1 - headerSpring) * -20}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 22px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            border: '1.5px solid #EF4444',
            boxShadow: '0 8px 24px rgba(239, 68, 68, 0.3)',
          }}
        >
          <span style={{fontSize: 26}}>⚠️</span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>

        {/* Narrative Card (Changes dynamically across the scene: Phase 1a -> Phase 1b -> Phase 2 Alert) */}
        {!isPhase2 ? (
          <div
            style={{
              opacity: headerSpring,
              transform: `translateY(${floatY}px)`,
              width: '100%',
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid rgba(167, 139, 250, 0.3)',
              borderRadius: 22,
              padding: '18px 28px',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              boxShadow: '0 18px 40px rgba(0, 0, 0, 0.7)',
            }}
          >
            <div
              style={{
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textAlign: 'center',
                textWrap: 'balance',
              }}
            >
              {!phase1b
                ? 'Perguntas acumulando na loja'
                : 'Muitas mensagens chegando'}
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                transform: `scale(${phase1b ? badgePulse : 1})`,
              }}
            >
              <span style={{fontSize: 26}}>{!phase1b ? '📥' : '💬'}</span>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: phase1b ? '#DDD6FE' : '#CBD5E1',
                }}
              >
                {!phase1b
                  ? 'Dúvidas sobre produtos o dia todo'
                  : 'Fila de clientes aguardando resposta'}
              </span>
            </div>
          </div>
        ) : (
          <div
            style={{
              opacity: phase2Spring,
              transform: `scale(${0.94 + phase2Spring * 0.06}) translateY(${floatY}px)`,
              width: '100%',
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid #EF4444',
              borderRadius: 22,
              padding: '18px 28px',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              boxShadow: '0 18px 40px rgba(239, 68, 68, 0.35)',
            }}
          >
            <div
              style={{
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textAlign: 'center',
                textWrap: 'balance',
              }}
            >
              Impossível responder todas a tempo
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                transform: `scale(${alertPulse})`,
              }}
            >
              <span style={{fontSize: 26}}>⏱️</span>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FBBF24',
                }}
              >
                Falta de tempo para atender a todos
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
