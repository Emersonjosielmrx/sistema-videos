import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Scene3_DonoResultado: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Digital Punch-in Close-Up framing (1.28x to 1.36x) - dramatically differentiates Scene 3 from Scene 1
  const videoScale = interpolate(frame, [0, 232], [1.28, 1.36], {
    extrapolateRight: 'clamp',
  });
  // Vertical displacement down (40px) to keep comfortable breathing room above presenter's head
  const videoTranslateY = 40;

  // Dynamic energetic entry punch & emerald flash marking the victory / solution transition
  const entryFlash = interpolate(frame, [0, 6, 16], [0, 0.35, 0], {
    extrapolateRight: 'clamp',
  });
  const entryPunch = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 150},
  });

  // Top header entrance spring
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Steps timing (Strict staggered activation aligned with voice):
  // Step 1: "atende" at frame 53 (~21.9s)
  const step1Active = frame >= 53;
  const step1Spring = spring({
    frame: frame - 53,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Step 2: "recomenda" at frame 86 (~23.0s)
  const step2Active = frame >= 86;
  const step2Spring = spring({
    frame: frame - 86,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Step 3: "vende" at frame 110 (~23.8s)
  const step3Active = frame >= 110;
  const step3Spring = spring({
    frame: frame - 110,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Continuous micro-movement
  const floatY = Math.sin(frame * 0.08) * 3;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
      }}
    >
      {/* Real Owner Video with close-up punch-in scale (1.28x - 1.36x) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: '50% 35%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Dynamic entry flash layer */}
      {entryFlash > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: '#10B981',
            opacity: entryFlash,
            pointerEvents: 'none',
            zIndex: 15,
          }}
        />
      )}

      {/* Top zone protective veil (y=0 to y=360) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 360,
          background:
            'linear-gradient(to bottom, rgba(11, 14, 23, 0.94) 0%, rgba(11, 14, 23, 0.70) 70%, rgba(11, 14, 23, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* COMPACT TOP SAFE ZONE (Strictly y=160 to y=290, preserving >120px completely clean headroom above presenter) */}
      <div
        style={{
          position: 'absolute',
          top: 160,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          zIndex: 20,
        }}
      >
        {/* Rótulo Badge Compacto */}
        <div
          style={{
            opacity: headerSpring,
            transform: `translateY(${(1 - headerSpring) * -15}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '6px 22px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.94)',
            border: '1.5px solid #10B981',
            boxShadow: '0 6px 20px rgba(16, 185, 129, 0.3)',
          }}
        >
          <span style={{fontSize: 24}}>🚀</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#6EE7B7',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>

        {/* 3 Steps Bar (Atende -> Recomenda -> Vende) strictly staggered on spoken words */}
        <div
          style={{
            opacity: headerSpring,
            transform: `translateY(${floatY}px) scale(${0.96 + entryPunch * 0.04})`,
            width: '100%',
            backgroundColor: 'rgba(15, 23, 42, 0.96)',
            border: '1.5px solid rgba(167, 139, 250, 0.35)',
            borderRadius: 22,
            padding: '12px 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 10,
            boxShadow: '0 14px 35px rgba(0, 0, 0, 0.8)',
          }}
        >
          {/* Step 1: Atende - Activates strictly at frame 53 */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '10px 8px',
              borderRadius: 14,
              backgroundColor: step1Active
                ? '#A78BFA'
                : 'rgba(30, 41, 59, 0.85)',
              border: step1Active
                ? '2px solid #FFFFFF'
                : '1px solid rgba(255, 255, 255, 0.15)',
              transform: step1Active
                ? `scale(${0.92 + step1Spring * 0.08})`
                : 'scale(1)',
              boxShadow: step1Active
                ? '0 6px 18px rgba(167, 139, 250, 0.6)'
                : 'none',
              transition: 'background-color 0.2s',
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: step1Active ? '#121216' : '#94A3B8',
                whiteSpace: 'nowrap',
              }}
            >
              {step1Active ? '1. Atende ✓' : '1. Atende'}
            </span>
          </div>

          {/* Step 2: Recomenda - Activates strictly at frame 86 */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '10px 8px',
              borderRadius: 14,
              backgroundColor: step2Active
                ? '#A78BFA'
                : 'rgba(30, 41, 59, 0.85)',
              border: step2Active
                ? '2px solid #FFFFFF'
                : '1px solid rgba(255, 255, 255, 0.15)',
              transform: step2Active
                ? `scale(${0.92 + step2Spring * 0.08})`
                : 'scale(1)',
              boxShadow: step2Active
                ? '0 6px 18px rgba(167, 139, 250, 0.6)'
                : 'none',
              transition: 'background-color 0.2s',
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: step2Active ? '#121216' : '#94A3B8',
                whiteSpace: 'nowrap',
              }}
            >
              {step2Active ? '2. Recomenda ✓' : '2. Recomenda'}
            </span>
          </div>

          {/* Step 3: Vende - Activates strictly at frame 110 */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '10px 8px',
              borderRadius: 14,
              backgroundColor: step3Active
                ? '#10B981'
                : 'rgba(30, 41, 59, 0.85)',
              border: step3Active
                ? '2px solid #FFFFFF'
                : '1px solid rgba(255, 255, 255, 0.15)',
              transform: step3Active
                ? `scale(${0.92 + step3Spring * 0.08})`
                : 'scale(1)',
              boxShadow: step3Active
                ? '0 6px 20px rgba(16, 185, 129, 0.6)'
                : 'none',
              transition: 'background-color 0.2s',
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: step3Active ? '#FFFFFF' : '#94A3B8',
                whiteSpace: 'nowrap',
              }}
            >
              {step3Active ? '3. Vende ✓' : '3. Vende'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
