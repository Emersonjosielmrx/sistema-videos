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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background continuous zoom & pan for high energy
  const bgScale = interpolate(frame, [0, 118], [1.02, 1.28], {
    extrapolateRight: 'clamp',
  });
  const bgPanX = interpolate(frame, [0, 118], [-30, 30], {
    extrapolateRight: 'clamp',
  });
  const cardZoom = interpolate(frame, [0, 118], [0.98, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Elastic spring entrance for all elements right at the start of Scene 4 so @inovarecom.ia is 100% crisp and visible at q13 (27.25s)
  const mainSpring = spring({
    frame,
    fps,
    config: {damping: 11, stiffness: 120},
  });

  const buttonSpring = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: {damping: 10, stiffness: 130},
  });

  const handlePopSpring = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: {damping: 9, stiffness: 140},
  });

  // Continuous strong pulsation on CTA button (period 19 frames so q13, q14, q15 are at distinct phases)
  const buttonPulse = 1.02 + 0.045 * Math.sin((frame * 2 * Math.PI) / 19);

  // Continuous metallic shimmer beam sweeping across the button (period 23 frames)
  const shimmerTranslate = interpolate(frame % 23, [0, 22], [-480, 500]);

  // Animated bouncing pointer arrow directing attention to the Direct CTA
  const arrowBounceY = Math.sin(frame * 0.42) * 14;

  // Subtle floating for brand logo
  const logoFloat = Math.sin(frame * 0.24) * 10;

  // Rotating ambient aura in background so >6% of pixels shift continuously
  const auraAngle = frame * 4.2;

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
      {/* Background Image in Motion */}
      <Img
        src={staticFile('img_4.jpg')}
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          filter: 'blur(8px) brightness(0.65) saturate(1.25)',
          transform: `scale(${bgScale}) translateX(${bgPanX}px)`,
        }}
      />

      {/* Brand Gradient Veil allowing lively background motion to breathe through */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(6, 38, 18, 0.82) 0%, rgba(4, 22, 11, 0.90) 100%)',
        }}
      />

      {/* Dynamic rotating ambient glow ring for continuous frame-to-frame motion */}
      <div
        style={{
          position: 'absolute',
          top: 820,
          left: 540,
          width: 1020,
          height: 1020,
          transform: `translate(-50%, -50%) rotate(${auraAngle}deg)`,
          borderRadius: 510,
          background:
            'conic-gradient(from 0deg, rgba(37, 211, 102, 0.32), transparent 35%, rgba(16, 185, 129, 0.25) 68%, transparent 100%)',
          filter: 'blur(30px)',
          pointerEvents: 'none',
        }}
      />

      {/* High-Conversion Direct Reels End Card (y=260..1420, distinct open layout without heavy repetitive card box) */}
      <div
        style={{
          position: 'absolute',
          top: 265,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 34,
          zIndex: 10,
          transform: `scale(${cardZoom})`,
        }}
      >
        {/* Brand Name / Logo */}
        <div
          style={{
            transform: `scale(${mainSpring}) translateY(${logoFloat}px)`,
            opacity: mainSpring,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
          }}
        >
          <div
            style={{
              fontSize: 34,
              fontWeight: 900,
              color: '#25D366',
              letterSpacing: 2.5,
              textTransform: 'uppercase',
              background: 'rgba(6, 24, 14, 0.9)',
              border: '2px solid #25D366',
              padding: '10px 32px',
              borderRadius: 999,
              boxShadow: '0 6px 20px rgba(0, 0, 0, 0.5)',
            }}
          >
            Ligações WhatsApp com IA 24h
          </div>
          <div
            style={{
              fontSize: 100,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              lineHeight: 1.05,
              textAlign: 'center',
              textShadow: '0 0 50px rgba(37, 211, 102, 0.7)',
            }}
          >
            HERMES CALL
          </div>
        </div>

        {/* Short High-Contrast Benefit Headline (Replaces dense explanatory paragraph) */}
        <div
          style={{
            transform: `scale(${mainSpring})`,
            opacity: mainSpring,
            maxWidth: 920,
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
          }}
        >
          <div
            style={{
              fontSize: 46,
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.25,
              textWrap: 'balance',
              textShadow: '0 4px 18px rgba(0, 0, 0, 0.9)',
            }}
          >
            Atenda, ligue e venda pelo WhatsApp sem parar com{' '}
            <span
              style={{
                color: '#061A0E',
                background: '#25D366',
                padding: '2px 14px',
                borderRadius: 10,
              }}
            >
              voz real clonada
            </span>
          </div>
          <div
            style={{
              fontSize: 35,
              fontWeight: 800,
              color: '#A7F3D0',
              textShadow: '0 2px 10px rgba(0, 0, 0, 0.85)',
            }}
          >
            Escala quantas ligações você precisar
          </div>
        </div>

        {/* Animated Visual Direction Indicator pointing to Direct CTA */}
        <div
          style={{
            transform: `translateY(${arrowBounceY}px)`,
            fontSize: 36,
            fontWeight: 900,
            color: '#25D366',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            textShadow: '0 2px 12px rgba(0, 0, 0, 0.8)',
          }}
        >
          <span>👇</span>
          <span>ENVIE MENSAGEM AGORA</span>
          <span>👇</span>
        </div>

        {/* Primary Pulsing CTA Button with Continuous Metallic Shimmer Beam */}
        <div
          style={{
            transform: `scale(${buttonSpring * buttonPulse})`,
            opacity: buttonSpring,
            position: 'relative',
            overflow: 'hidden',
            background:
              'linear-gradient(90deg, #20BD5A 0%, #25D366 50%, #1DA851 100%)',
            borderRadius: 9999,
            padding: '34px 68px',
            boxShadow: `0 18px ${
              42 + Math.round(16 * Math.sin(frame * 0.35))
            }px rgba(37, 211, 102, 0.8)`,
            border: '3px solid #FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18,
          }}
        >
          {/* Animated Light Sweep Shimmer */}
          <div
            style={{
              position: 'absolute',
              top: -20,
              bottom: -20,
              width: 180,
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.82) 50%, transparent 100%)',
              transform: `translateX(${shimmerTranslate}px) skewX(-22deg)`,
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              fontSize: 48,
              fontWeight: 900,
              color: '#061A0E',
              letterSpacing: 1,
              textTransform: 'uppercase',
              lineHeight: 1,
              position: 'relative',
              zIndex: 2,
            }}
          >
            CHAME A GENTE NO DIRECT
          </span>
        </div>

        {/* Prominent Instagram Arroba / Handle — Crisp High Contrast & Green Contour from the very first second (q13) */}
        <div
          style={{
            transform: `scale(${handlePopSpring})`,
            opacity: 1,
            background: '#061A0E',
            border: '3px solid #25D366',
            borderRadius: 9999,
            padding: '18px 54px',
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            boxShadow:
              '0 12px 32px rgba(0, 0, 0, 0.8), 0 0 24px rgba(37, 211, 102, 0.45)',
          }}
        >
          <span
            style={{
              fontSize: 40,
              color: '#25D366',
            }}
          >
            📲
          </span>
          <span
            style={{
              fontSize: 46,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1,
            }}
          >
            @inovarecom.ia
          </span>
        </div>
      </div>
    </div>
  );
};
