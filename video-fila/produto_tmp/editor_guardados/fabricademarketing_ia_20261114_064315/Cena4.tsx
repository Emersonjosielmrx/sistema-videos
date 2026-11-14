import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig, Img, staticFile} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background slow zoom
  const bgScale = interpolate(frame, [0, 119], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs (staggered fast so everything is active by frame 15)
  const enterSpring = spring({
    frame: Math.max(0, frame - 1),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const tagsSpring = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  const buttonSpring = spring({
    frame: Math.max(0, frame - 7),
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const handleSpring = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Continuous button pulse (scale 1.0 to 1.045 until the last frame)
  const buttonPulse = 1.02 + Math.sin(frame / 4.0) * 0.025;

  // Dynamic ambient glow behind CTA
  const ctaGlowPulse = 0.45 + 0.25 * Math.sin(frame / 4.0);

  // Shimmer translate across button
  const shimmerX = interpolate(frame % 45, [0, 45], [-200, 850], {
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{position: 'absolute', width: 1080, height: 1920, overflow: 'hidden'}}>
      {/* Background with zoom and blur */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
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
            filter: 'blur(16px)',
          }}
        />
        {/* Dark brand veil */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(17, 24, 39, 0.75) 0%, rgba(17, 24, 39, 0.95) 100%)',
          }}
        />
      </div>

      {/* Floating brand ambient orbs */}
      <div
        style={{
          position: 'absolute',
          width: 650,
          height: 650,
          borderRadius: '50%',
          background: 'rgba(244, 114, 182, 0.22)',
          filter: 'blur(110px)',
          top: 500 + Math.sin(frame / 18) * 35,
          left: 215 + Math.cos(frame / 20) * 35,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: `rgba(244, 114, 182, ${ctaGlowPulse * 0.4})`,
          filter: 'blur(90px)',
          bottom: 380,
          left: 290,
          pointerEvents: 'none',
        }}
      />

      {/* Main Container within Safe Zone (y: 190 - 1560) - well balanced vertically */}
      <div
        style={{
          position: 'absolute',
          top: 205,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${(1 - enterSpring) * -25}px)`,
          opacity: enterSpring,
        }}
      >
        {/* Category Pill */}
        <div
          style={{
            padding: '8px 28px',
            borderRadius: 30,
            background: 'rgba(244, 114, 182, 0.18)',
            border: '1.5px solid rgba(244, 114, 182, 0.55)',
            marginBottom: 24,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#F472B6',
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            Automação de Conteúdo
          </span>
        </div>

        {/* Brand Name */}
        <div
          style={{
            fontFamily,
            fontSize: 64,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.15,
            letterSpacing: -0.5,
            textShadow: '0 4px 24px rgba(0, 0, 0, 0.85)',
            marginBottom: 14,
          }}
        >
          Fábrica de Marketing IA
        </div>

        {/* Product Name - Bright legible luminous pink */}
        <div
          style={{
            fontFamily,
            fontSize: 46,
            fontWeight: 800,
            color: '#F9A8D4',
            textAlign: 'center',
            marginBottom: 50,
            textShadow: '0 2px 14px rgba(244, 114, 182, 0.5)',
          }}
        >
          Fábrica de Conteúdo
        </div>

        {/* Value Proposition Box */}
        <div
          style={{
            width: '100%',
            maxWidth: 900,
            background: 'rgba(17, 24, 39, 0.88)',
            border: '1.5px solid rgba(255, 255, 255, 0.16)',
            borderRadius: 26,
            padding: '32px 30px',
            boxShadow: '0 16px 40px rgba(0, 0, 0, 0.75)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 22,
            marginBottom: 65,
          }}
        >
          <div
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 800,
              color: '#FFFFFF',
              textAlign: 'center',
            }}
          >
            Da ideia à postagem automática
          </div>

          {/* Pillars Row */}
          <div
            style={{
              display: 'flex',
              gap: 14,
              flexWrap: 'wrap',
              justifyContent: 'center',
              transform: `scale(${tagsSpring})`,
              opacity: tagsSpring,
            }}
          >
            <div
              style={{
                padding: '10px 22px',
                borderRadius: 16,
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(244, 114, 182, 0.4)',
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#F1F5F9',
              }}
            >
              ✓ Blog SEO
            </div>
            <div
              style={{
                padding: '10px 22px',
                borderRadius: 16,
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(244, 114, 182, 0.4)',
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#F1F5F9',
              }}
            >
              ✓ Podcast
            </div>
            <div
              style={{
                padding: '10px 22px',
                borderRadius: 16,
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(244, 114, 182, 0.4)',
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#F1F5F9',
              }}
            >
              ✓ Agente de Respostas
            </div>
          </div>
        </div>

        {/* Pulsing Action Button (SAME as convite_voz) positioned right in visual focal zone */}
        <div
          style={{
            position: 'relative',
            width: 840,
            height: 124,
            borderRadius: 62,
            background: 'linear-gradient(135deg, #F472B6 0%, #DB2777 100%)',
            boxShadow: `0 16px 45px rgba(244, 114, 182, ${ctaGlowPulse}), 0 0 35px rgba(244, 114, 182, 0.4)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18,
            transform: `scale(${buttonPulse * buttonSpring})`,
            opacity: buttonSpring,
            overflow: 'hidden',
            marginBottom: 55,
          }}
        >
          {/* Shimmer effect */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: 160,
              transform: `translateX(${shimmerX}px) skewX(-20deg)`,
              background:
                'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)',
            }}
          />

          <span
            style={{
              fontFamily,
              fontSize: 50,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
              textShadow: '0 2px 12px rgba(0, 0, 0, 0.45)',
            }}
          >
            Chame no direct
          </span>
          <span style={{fontSize: 44}}>💬</span>
        </div>

        {/* Handle (@arroba) */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 14,
            padding: '14px 34px',
            borderRadius: 34,
            background: 'rgba(17, 24, 39, 0.92)',
            border: '1.5px solid rgba(255, 255, 255, 0.25)',
            transform: `scale(${handleSpring})`,
            opacity: handleSpring,
            boxShadow: '0 10px 28px rgba(0, 0, 0, 0.75)',
          }}
        >
          <span style={{fontSize: 36}}>📸</span>
          <span
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 0.5,
            }}
          >
            @fabricademarketing.ia
          </span>
        </div>
      </div>
    </div>
  );
};
