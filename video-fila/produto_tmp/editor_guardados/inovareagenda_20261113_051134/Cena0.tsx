import React from 'react';
import {
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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background smooth push-in (1.00 -> 1.08)
  const bgScale = interpolate(frame, [0, 160], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 160], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  const line1Spring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  // "tecnologia" spoken around frame 40 (1.34s)
  const tecSpring = spring({
    frame: frame - 40,
    fps,
    config: {damping: 10, mass: 0.4},
  });

  const line2Spring = spring({
    frame: frame - 68,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  // "no meu negócio" spoken around frame 93 (3.10s)
  const negocioSpring = spring({
    frame: frame - 93,
    fps,
    config: {damping: 11, mass: 0.5},
  });

  // Hook tag appears at frame 105
  const hookSpring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  const hookPulse = 1 + 0.025 * Math.sin(frame * 0.15);

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background image with push-in and subtle pan */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
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
      </div>

      {/* Dark gradient overlay for extreme readability */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.90) 0%, rgba(15,23,42,0.65) 22%, rgba(15,23,42,0.50) 48%, rgba(15,23,42,0.75) 75%, rgba(15,23,42,0.96) 100%)',
        }}
      />

      {/* Subtle floating ambient particles */}
      <div
        style={{
          position: 'absolute',
          top: 300 + Math.sin(frame * 0.05) * 20,
          left: 120 + Math.cos(frame * 0.04) * 15,
          width: 280,
          height: 280,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(245,158,11,0.22) 0%, rgba(245,158,11,0) 70%)',
          filter: 'blur(30px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 850 + Math.cos(frame * 0.06) * 25,
          right: 100 + Math.sin(frame * 0.05) * 20,
          width: 320,
          height: 320,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(245,158,11,0.18) 0%, rgba(245,158,11,0) 70%)',
          filter: 'blur(35px)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Header Badge (y=175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.min(1, Math.max(0, badgeSpring)),
          transform: `scale(${0.9 + 0.1 * Math.min(1, Math.max(0, badgeSpring))})`,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            background: 'rgba(31, 41, 55, 0.88)',
            border: '2px solid rgba(245, 158, 11, 0.7)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6), 0 0 15px rgba(245,158,11,0.25)',
          }}
        >
          <span style={{fontSize: 34}}>❓</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
            }}
          >
            Dúvida Frequente
          </span>
        </div>
      </div>

      {/* Center Kinetic Question Block (y=450 to 920) */}
      <div
        style={{
          position: 'absolute',
          top: 450,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 20,
        }}
      >
        {/* Line 1 */}
        <div
          style={{
            fontSize: 54,
            fontWeight: 800,
            color: '#FFFFFF',
            textShadow: '0 4px 18px rgba(0,0,0,0.95)',
            opacity: Math.min(1, Math.max(0, line1Spring)),
            transform: `translateY(${(1 - Math.min(1, Math.max(0, line1Spring))) * 25}px)`,
          }}
        >
          Preciso entender de
        </div>

        {/* Line 2: TECNOLOGIA? Highlight Pill */}
        <div
          style={{
            opacity: Math.min(1, Math.max(0, tecSpring)),
            transform: `scale(${0.85 + 0.15 * Math.min(1, Math.max(0, tecSpring))})`,
          }}
        >
          <div
            style={{
              display: 'inline-block',
              background: '#F59E0B',
              color: '#121216',
              fontSize: 68,
              fontWeight: 900,
              padding: '6px 32px',
              borderRadius: 18,
              letterSpacing: '2px',
              boxShadow:
                '0 12px 35px rgba(245, 158, 11, 0.55), 0 0 20px rgba(245, 158, 11, 0.4)',
              textTransform: 'uppercase',
            }}
          >
            TECNOLOGIA?
          </div>
        </div>

        {/* Line 3 */}
        <div
          style={{
            fontSize: 48,
            fontWeight: 700,
            color: '#E5E7EB',
            textShadow: '0 4px 16px rgba(0,0,0,0.9)',
            opacity: Math.min(1, Math.max(0, line2Spring)),
            transform: `translateY(${(1 - Math.min(1, Math.max(0, line2Spring))) * 20}px)`,
          }}
        >
          para colocar isso
        </div>

        {/* Line 4 */}
        <div
          style={{
            fontSize: 58,
            fontWeight: 900,
            color: '#FFFFFF',
            textShadow: '0 4px 20px rgba(0,0,0,0.95)',
            opacity: Math.min(1, Math.max(0, negocioSpring)),
            transform: `scale(${0.9 + 0.1 * Math.min(1, Math.max(0, negocioSpring))})`,
          }}
        >
          no meu <span style={{color: '#F59E0B'}}>negócio?</span>
        </div>
      </div>

      {/* Floating Hook Card (y=980) */}
      {frame >= 105 && (
        <div
          style={{
            position: 'absolute',
            top: 980,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(1, Math.max(0, hookSpring)),
            transform: `scale(${hookPulse * (0.9 + 0.1 * Math.min(1, Math.max(0, hookSpring)))})`,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '14px 28px',
              borderRadius: 22,
              background: 'rgba(17, 24, 39, 0.92)',
              border: '2px solid rgba(245, 158, 11, 0.5)',
              boxShadow: '0 10px 30px rgba(0,0,0,0.7)',
            }}
          >
            <span style={{fontSize: 34}}>💡</span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 700,
                color: '#F3F4F6',
              }}
            >
              Tecnologia difícil no salão?
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
