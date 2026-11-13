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

export const Cena4Cartao: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps; // 0 to 3.94s (27.84s to 31.78s)

  // Smooth scene entry fade + slide from Scene 3
  const sceneFadeIn = interpolate(t, [0, 0.3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Continuous background camera movement (> 12% motion across scene)
  const bgScale = interpolate(t, [0, 3.94], [1.02, 1.2], {extrapolateRight: 'clamp'});
  const bgPanY = interpolate(t, [0, 3.94], [0, -32], {extrapolateRight: 'clamp'});

  // Staggered cascade springs for authority mockup, central card, CTA button, and @handle
  const mockupSpring = spring({
    frame: Math.max(0, frame - 2),
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const cardSpring = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 14, stiffness: 135},
  });
  const ctaSpring = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: {damping: 12, stiffness: 150},
  });
  const handleSpring = spring({
    frame: Math.max(0, frame - 22),
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Continuous button pulse, light glow pulse, shine sweep & slow card zoom
  const btnPulse = 1 + Math.sin(t * 8.5) * 0.05;
  const glowPulse = 0.25 + Math.sin(t * 5.5) * 0.12;
  const cardSlowZoom = interpolate(t, [0, 3.94], [0.95, 1.03], {extrapolateRight: 'clamp'});
  const shineX = interpolate((frame % 45) / 45, [0, 1], [-220, 1120]);
  const floatY = Math.sin(t * 4.5) * 10;

  return (
    <AbsoluteFill style={{backgroundColor: '#111827', fontFamily, opacity: sceneFadeIn}}>
      {/* Blurred moving background photo + dark brand veil */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
            filter: 'blur(12px) brightness(0.52)',
          }}
        />
      </AbsoluteFill>

      {/* Soft pulsing radial light glow in background */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 48%, rgba(245, 158, 11, ${glowPulse}) 0%, rgba(17, 24, 39, 0.90) 76%)`,
        }}
      />

      {/* Balanced Vertical Safe Zone Container (y: 185 to 1540) */}
      <div
        style={{
          position: 'absolute',
          top: 185,
          bottom: 380,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {/* 1. Visual Authority Element: Miniature Ready Landing Page + Video Demo Mockup Preview */}
        <div
          style={{
            width: '100%',
            background: 'linear-gradient(145deg, rgba(30,41,59,0.96) 0%, rgba(15,23,42,0.96) 100%)',
            border: '2px solid #F59E0B',
            borderRadius: 28,
            padding: '22px 28px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 20,
            transform: `translateY(${interpolate(mockupSpring, [0, 1], [-35, 0]) + floatY * 0.6}px) scale(${interpolate(mockupSpring, [0, 1], [0.92, 1])})`,
            opacity: mockupSpring,
          }}
        >
          {/* Left Mini Browser Preview */}
          <div style={{display: 'flex', flexDirection: 'column', gap: 10, flex: 1.2}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
              <div style={{width: 12, height: 12, borderRadius: 6, background: '#EF4444'}} />
              <div style={{width: 12, height: 12, borderRadius: 6, background: '#F59E0B'}} />
              <div style={{width: 12, height: 12, borderRadius: 6, background: '#10B981'}} />
              <span style={{color: '#F59E0B', fontSize: 32, fontWeight: 900, marginLeft: 6}}>
                Página Pronta ✓
              </span>
            </div>
            <div
              style={{
                background: 'rgba(16, 185, 129, 0.2)',
                border: '2px solid #10B981',
                borderRadius: 14,
                padding: '10px 18px',
                color: '#FFFFFF',
                fontSize: 33,
                fontWeight: 800,
              }}
            >
              Página que Vende
            </div>
          </div>

          {/* Right Mini Video Demo Player Badge */}
          <div
            style={{
              flex: 0.85,
              background: 'rgba(245, 158, 11, 0.18)',
              border: '2px solid #F59E0B',
              borderRadius: 20,
              padding: '14px 18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 14,
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                background: '#F59E0B',
                color: '#121216',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 32,
                fontWeight: 900,
              }}
            >
              ▶
            </div>
            <span style={{color: '#FFFFFF', fontSize: 33, fontWeight: 900}}>
              Vídeo Demo
            </span>
          </div>
        </div>

        {/* 2. Brand & Value Card (Staggered scale spring 0.92 -> 1.0 + continuous float) */}
        <div
          style={{
            width: '100%',
            background: 'rgba(17, 24, 39, 0.95)',
            border: '2px solid rgba(245, 158, 11, 0.7)',
            borderRadius: 34,
            padding: '38px 38px',
            textAlign: 'center',
            boxShadow: '0 24px 60px rgba(0,0,0,0.75)',
            transform: `translateY(${interpolate(cardSpring, [0, 1], [40, 0]) + floatY}px) scale(${interpolate(cardSpring, [0, 1], [0.92, 1]) * cardSlowZoom})`,
            opacity: cardSpring,
          }}
        >
          {/* Brand Name */}
          <div
            style={{
              color: '#FFFFFF',
              fontSize: 56,
              fontWeight: 900,
              lineHeight: 1.12,
              marginBottom: 18,
              textWrap: 'balance',
            }}
          >
            Landing Page e Comunicação
          </div>

          {/* 1-sentence value proposition from briefing facts */}
          <div
            style={{
              color: '#E2E8F0',
              fontSize: 36,
              fontWeight: 700,
              lineHeight: 1.28,
              textWrap: 'balance',
            }}
          >
            Página de vendas pronta e vídeo de demonstração para transformar visita em cliente.
          </div>
        </div>

        {/* 3. Main Pulsing CTA Button + 4. Staggered @handle (strictly between y=1100 and y=1540) */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
          }}
        >
          <div
            style={{
              position: 'relative',
              width: '100%',
              background: '#F59E0B',
              color: '#121216',
              borderRadius: 28,
              padding: '28px 32px',
              textAlign: 'center',
              fontSize: 42,
              fontWeight: 900,
              letterSpacing: 0.8,
              whiteSpace: 'nowrap',
              textTransform: 'uppercase',
              boxShadow: '0 20px 50px rgba(245, 158, 11, 0.45)',
              transform: `scale(${interpolate(ctaSpring, [0, 1], [0.85, 1]) * btnPulse})`,
              opacity: ctaSpring,
              overflow: 'hidden',
            }}
          >
            {/* Moving shine effect across CTA button */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shineX,
                width: 140,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)',
                transform: 'skewX(-20deg)',
              }}
            />
            CHAME A GENTE NO DIRECT
          </div>

          {/* @handle badge with fade + upward slide */}
          <div
            style={{
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid #F59E0B',
              borderRadius: 999,
              padding: '14px 38px',
              color: '#FFFFFF',
              fontSize: 40,
              fontWeight: 800,
              boxShadow: '0 12px 30px rgba(0,0,0,0.55)',
              transform: `translateY(${interpolate(handleSpring, [0, 1], [35, 0])}px)`,
              opacity: handleSpring,
            }}
          >
            @landingpageia.ia
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
