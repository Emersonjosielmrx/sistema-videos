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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous background push-in (1.05 -> 1.16)
  const bgScale = interpolate(frame, [0, 120], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 120], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Slow continuous zoom-in on the entire card container to prevent static feel (32.2s - 34.6s)
  const cardScale = interpolate(frame, [0, 120], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });
  const cardTranslateY = interpolate(frame, [0, 120], [0, -12], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const valueSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const btnSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const handleSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Active continuous button pulse (scale 1.00 to 1.08 until the very final frame)
  const btnPulse = 1.0 + Math.sin(frame / 5) * 0.06;

  // Diagonal shimmer streak passing across button every 45 frames
  const shimmerProgress = (frame % 45) / 45;
  const shimmerX = interpolate(shimmerProgress, [0, 1], [-200, 600]);

  // Ambient floating glow particles
  const glowPulse = 0.85 + Math.sin(frame / 8) * 0.15;
  const arrowX = Math.sin(frame / 5) * 8;

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Background Image with continuous slow zoom */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          filter: 'blur(16px)',
          opacity: 0.3,
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Dark Brand Veil with warm radial glow */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 45%, rgba(255, 169, 77, 0.18) 0%, rgba(31, 41, 55, 0.94) 65%, rgba(15, 23, 42, 0.98) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Main Card Container with continuous slow zoom to eliminate static feel */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${cardScale}) translateY(${cardTranslateY}px)`,
          transformOrigin: 'center 60%',
        }}
      >
        {/* Top Brand & Logo Section (y: 280 to 600) */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          transform: `scale(${logoSpring})`,
          opacity: logoSpring,
          zIndex: 20,
        }}
      >
        {/* Mascot Robot AI Icon */}
        <div
          style={{
            width: 110,
            height: 110,
            borderRadius: 34,
            backgroundColor: '#FFA94D',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 60,
            boxShadow: `0 12px 35px rgba(255, 169, 77, ${glowPulse * 0.6})`,
            marginBottom: 20,
            transform: `scale(${1 + Math.sin(frame / 10) * 0.03})`,
          }}
        >
          🤖
        </div>

        {/* Brand Name */}
        <div
          style={{
            fontFamily,
            fontSize: 76,
            fontWeight: 900,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            lineHeight: 1.1,
            textShadow: '0 4px 20px rgba(0,0,0,0.8)',
          }}
        >
          Agenda IA
        </div>

        {/* Brand Value Proposition */}
        <div
          style={{
            marginTop: 14,
            fontFamily,
            fontSize: 38,
            fontWeight: 800,
            color: '#FFA94D',
            letterSpacing: '-0.5px',
            textShadow: '0 2px 10px rgba(0,0,0,0.6)',
          }}
        >
          Agendamentos automáticos com IA 24h
        </div>
      </div>

      {/* Value Fact Card (y: 650 to 860) */}
      <div
        style={{
          position: 'absolute',
          top: 650,
          left: 70,
          right: 70,
          transform: `scale(${valueSpring})`,
          opacity: valueSpring,
          zIndex: 20,
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(31, 41, 55, 0.95)',
            border: '2px solid rgba(255, 255, 255, 0.15)',
            borderRadius: 26,
            padding: '24px 30px',
            textAlign: 'center',
            boxShadow: '0 18px 40px rgba(0, 0, 0, 0.6)',
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 700,
              color: '#F3F4F6',
              lineHeight: 1.35,
            }}
          >
            Agenda, confirma e reagenda sozinha direto no WhatsApp
          </div>
          <div
            style={{
              marginTop: 14,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              backgroundColor: 'rgba(255, 169, 77, 0.18)',
              border: '1.5px solid #FFA94D',
              borderRadius: 999,
              padding: '8px 24px',
            }}
          >
            <span style={{fontSize: 28}}>⚡</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFA94D',
              }}
            >
              Trabalha 24h a partir de R$ 199/mês
            </span>
          </div>
        </div>
      </div>

      {/* Call To Action Button (y: 920 to 1100) */}
      <div
        style={{
          position: 'absolute',
          top: 920,
          left: 70,
          right: 70,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${btnSpring * btnPulse})`,
          opacity: btnSpring,
          zIndex: 30,
        }}
      >
        <div
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: 820,
            backgroundColor: '#FFA94D',
            borderRadius: 28,
            padding: '28px 36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            boxShadow:
              '0 20px 50px rgba(255, 169, 77, 0.45), inset 0 2px 4px rgba(255, 255, 255, 0.4)',
            overflow: 'hidden',
          }}
        >
          {/* Shimmer Light Streak */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 120,
              background:
                'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
              transform: `translateX(${shimmerX}px) skewX(-25deg)`,
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              fontFamily,
              fontSize: 50,
              fontWeight: 900,
              color: '#1F2937',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            Chame no Direct
          </span>

          <span
            style={{
              fontSize: 44,
              color: '#1F2937',
              fontWeight: 900,
              transform: `translateX(${arrowX}px)`,
            }}
          >
            ➔
          </span>
        </div>
      </div>

      {/* Official Handle / Profile (y: 1160 to 1280) */}
      <div
        style={{
          position: 'absolute',
          top: 1160,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${handleSpring})`,
          opacity: handleSpring,
          zIndex: 25,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 14,
            backgroundColor: 'rgba(31, 41, 55, 0.9)',
            border: '1.5px solid rgba(255, 255, 255, 0.2)',
            borderRadius: 999,
            padding: '12px 32px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span style={{fontSize: 34}}>📸</span>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.5px',
            }}
          >
            @sintetizerisada
          </span>
          <span
            style={{
              backgroundColor: '#38BDF8',
              color: '#FFFFFF',
              borderRadius: '50%',
              width: 28,
              height: 28,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              fontWeight: 900,
            }}
          >
            ✓
          </span>
        </div>
      </div>
      </div>
    </AbsoluteFill>
  );
};
