import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena4Props {
  fontFamily: string;
}

export const Cena4: React.FC<Cena4Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background continuous zoom: 1.02 to 1.22
  const bgScale = interpolate(frame, [0, 134], [1.02, 1.22], {
    extrapolateRight: 'clamp',
  });

  // Smooth fade in transition over previous scene
  const sceneFadeIn = interpolate(frame, [0, 14], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Staggered entrances throughout the scene (elimina quadros congelados / idênticos em q13, q14, q15)
  // 1. Logo & Brand Title: frame 2
  const logoSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // 2. Sub-brand pill: frame 14
  const pillSpring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // 3. Central Value Proposition Card: frame 26
  const cardSpring = spring({
    frame: frame - 26,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 4. CTA Button: frame 42
  const btnSpring = spring({
    frame: frame - 42,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 5. Official Profile Handle (@inovaresites): frame 58
  const handleSpring = spring({
    frame: frame - 58,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Button continuous active breath & pulse (1.00 to 1.06)
  const btnPulse = 1.02 + Math.sin(frame * 0.22) * 0.04;
  const btnGlowSpread = 25 + Math.sin(frame * 0.22) * 15;
  const btnGlowPulse = 0.6 + Math.sin(frame * 0.22) * 0.3;

  // Continuous light sweep shimmer animation for button (repeats every 36 frames / 1.2s)
  const shimmerPos = ((frame * 2.8) % 180) - 40; // -40% to 140%

  // Continuous floating and breathing for the central card
  const cardFloatY = Math.sin(frame * 0.1) * 10;
  const cardBreath = 1 + Math.sin(frame * 0.08) * 0.02;

  // Logo dynamic rotation & micro-motion
  const logoFloat = Math.sin(frame * 0.12) * 6;
  const crestRotate = Math.sin(frame * 0.15) * 6;
  const crestScale = 1 + Math.sin(frame * 0.15) * 0.06;

  // Ambient center energy glow
  const glowPulse = 0.25 + Math.sin(frame * 0.1) * 0.1;
  const glowScale = 1 + Math.sin(frame * 0.08) * 0.1;

  // Handle micro-float
  const handleFloat = Math.sin(frame * 0.1 + 1) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F0913',
        fontFamily,
        opacity: sceneFadeIn,
      }}
    >
      {/* Background with continuous push-in zoom */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(12px) brightness(0.60) contrast(1.15)',
          }}
        />
        {/* Dark vignette overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 50%, rgba(15, 9, 19, 0.55) 0%, rgba(11, 13, 19, 0.95) 100%)',
          }}
        />
      </div>

      {/* Ambient pink energy glow in center */}
      <div
        style={{
          position: 'absolute',
          top: 550,
          left: 140,
          width: 800,
          height: 600,
          borderRadius: '50%',
          background: `radial-gradient(circle, rgba(236,72,153,${glowPulse}) 0%, transparent 70%)`,
          filter: 'blur(65px)',
          transform: `scale(${glowScale}) translateY(${Math.sin(frame * 0.07) * 16}px)`,
          pointerEvents: 'none',
        }}
      />

      {/* Brand Header Section (y = 350 to 580) - Stagger 1: frame 2 */}
      <div
        style={{
          position: 'absolute',
          top: 350,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `scale(${Math.max(0, logoSpring)}) translateY(${logoFloat}px)`,
          opacity: Math.max(0, logoSpring),
        }}
      >
        {/* Brand Crest / Icon with continuous rotate & scale */}
        <div
          style={{
            width: 86,
            height: 86,
            borderRadius: 26,
            background: `linear-gradient(135deg, ${CORES.marca}, ${CORES.marcaDark})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: `0 10px 30px ${CORES.marcaGlow}`,
            marginBottom: 18,
            transform: `rotate(${crestRotate}deg) scale(${crestScale})`,
          }}
        >
          <span style={{fontSize: 46, color: '#FFFFFF'}}>⚡</span>
        </div>

        {/* Brand Name */}
        <h1
          style={{
            fontSize: 70,
            fontWeight: 900,
            color: '#FFFFFF',
            letterSpacing: -1,
            margin: 0,
            textTransform: 'uppercase',
            textShadow: '0 4px 24px rgba(0,0,0,0.9)',
          }}
        >
          INOVARE SITES
        </h1>

        {/* Sub-brand Tag - Stagger 2: frame 14 */}
        <div
          style={{
            marginTop: 14,
            padding: '8px 24px',
            borderRadius: 999,
            background: 'rgba(236, 72, 153, 0.18)',
            border: `1.5px solid ${CORES.marca}`,
            transform: `scale(${Math.max(0, pillSpring)})`,
            opacity: Math.max(0, pillSpring),
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#F472B6',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            LANDING PAGES & COMUNICAÇÃO
          </span>
        </div>
      </div>

      {/* Value Proposition Card - Stagger 3: frame 26 (y = 690 to 1020)
          Fonte ampliada para 42px e espaçamento generoso para leitura perfeita em telas móveis */}
      <div
        style={{
          position: 'absolute',
          top: 690,
          left: 60,
          right: 60,
          transform: `scale(${Math.max(0, cardSpring) * cardBreath}) translateY(${cardFloatY}px)`,
          opacity: Math.max(0, cardSpring),
        }}
      >
        <div
          style={{
            background: 'rgba(15, 12, 22, 0.95)',
            border: '2px solid rgba(255, 255, 255, 0.18)',
            borderRadius: 36,
            padding: '36px 36px',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.9)',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            textAlign: 'center',
          }}
        >
          <div style={{display: 'flex', justifyContent: 'center'}}>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: CORES.textoDestaque,
                textTransform: 'uppercase',
                letterSpacing: 1.5,
              }}
            >
              ★ A SOLUÇÃO COMPLETA ★
            </span>
          </div>

          <p
            style={{
              fontSize: 42,
              fontWeight: 700,
              lineHeight: 1.5,
              color: '#F8FAFC',
              margin: 0,
              textWrap: 'balance',
            }}
          >
            <span style={{color: '#FFFFFF', fontWeight: 800}}>
              Página de vendas pronta
            </span>{' '}
            e{' '}
            <span style={{color: '#F472B6', fontWeight: 800}}>
              vídeo de demonstração
            </span>{' '}
            para apresentar seu produto e transformar visita em cliente.
          </p>
        </div>
      </div>

      {/* High-Converting Pulsing CTA Button - Stagger 4: frame 42 (y = 1120)
          Com efeito contínuo de pulso (scale 1.0 a 1.06) e varredura luminosa (shimmer) */}
      <div
        style={{
          position: 'absolute',
          top: 1120,
          left: 70,
          right: 70,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${Math.max(0, btnSpring) * btnPulse})`,
          opacity: Math.max(0, btnSpring),
        }}
      >
        <div
          style={{
            width: '100%',
            height: 120,
            borderRadius: 60,
            background: `linear-gradient(135deg, ${CORES.marca}, #DB2777)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18,
            boxShadow: `0 16px 50px rgba(236, 72, 153, ${btnGlowPulse}), 0 0 ${btnGlowSpread}px ${CORES.marca}`,
            border: '2.5px solid rgba(255, 255, 255, 0.45)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Continuous Light Sweep Shimmer traversing across button */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `${shimmerPos}%`,
              width: '45%',
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.85) 50%, transparent 100%)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />

          <span style={{fontSize: 46, color: '#FFFFFF'}}>💬</span>
          <span
            style={{
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
              textShadow: '0 2px 10px rgba(0,0,0,0.5)',
            }}
          >
            CHAME NO DIRECT
          </span>
        </div>
      </div>

      {/* Official Handle @inovaresites - Stagger 5: frame 58 (y = 1320) */}
      <div
        style={{
          position: 'absolute',
          top: 1320,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          transform: `scale(${Math.max(0, handleSpring)}) translateY(${handleFloat}px)`,
          opacity: Math.max(0, handleSpring),
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 34px',
            borderRadius: 999,
            background: 'rgba(11, 13, 19, 0.94)',
            border: '1.5px solid rgba(255, 255, 255, 0.18)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
          }}
        >
          <span style={{fontSize: 34}}>📸</span>
          <span
            style={{
              fontSize: 36,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 0.5,
            }}
          >
            @inovaresites
          </span>
          <span
            style={{
              fontSize: 32,
              color: '#38BDF8',
              background: 'rgba(56, 189, 248, 0.18)',
              borderRadius: '50%',
              width: 38,
              height: 38,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            ✓
          </span>
        </div>
      </div>
    </div>
  );
};
