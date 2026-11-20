import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena4Cartao: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Scene fade in (frames 0 to 10)
  const sceneOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Continuous background camera push-in
  const bgScale = interpolate(frame, [0, 119], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.7},
  });

  const titleSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  const descSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  const buttonSpring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 180},
  });

  const footerSpring = spring({
    frame: frame - 24,
    fps,
    config: {damping: 14, mass: 0.7},
  });

  // Continuous CTA button pulse (rule: scale 1.0 to 1.08 until final frame)
  const pulseFactor = (Math.sin(frame / 6) * 0.5 + 0.5) * 0.07;
  const btnScale = (0.94 + buttonSpring * 0.06) * (1 + pulseFactor);

  // Shimmer effect moving diagonally across button
  const shimmerPos = interpolate(frame % 45, [0, 45], [-120, 220]);

  // Floating micro-motion for logo
  const logoFloatY = Math.sin(frame / 12) * 6;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* Background Image with Blur & Continuous Scale */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale})`,
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(14px)',
          }}
        />
        {/* Dark brand veil */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(17, 24, 39, 0.72) 0%, rgba(17, 24, 39, 0.96) 100%)',
          }}
        />
      </div>

      {/* Decorative ambient glow behind logo */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: '50%',
          width: 500,
          height: 500,
          transform: 'translate(-50%, -50%)',
          borderRadius: '50%',
          backgroundColor: '#22C55E',
          opacity: 0.16,
          filter: 'blur(80px)',
          pointerEvents: 'none',
        }}
      />

      {/* Center Container strictly in safe zone (y=160 to y=1520) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 60px',
          zIndex: 20,
        }}
      >
        {/* Animated Brand Icon (y ≈ 280) */}
        <div
          style={{
            opacity: logoSpring,
            transform: `translateY(${(1 - logoSpring) * -30 + logoFloatY}px) scale(${0.85 + logoSpring * 0.15})`,
            width: 130,
            height: 130,
            borderRadius: 36,
            background: 'linear-gradient(135deg, #22C55E 0%, #15803D 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 16px 45px rgba(34, 197, 94, 0.5)',
            marginBottom: 28,
          }}
        >
          <span style={{fontSize: 66}}>⚡</span>
        </div>

        {/* Brand Name (y ≈ 430) */}
        <div
          style={{
            opacity: titleSpring,
            transform: `translateY(${(1 - titleSpring) * 25}px)`,
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            marginBottom: 16,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 64,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
              textShadow: '0 4px 20px rgba(0,0,0,0.9)',
            }}
          >
            Disparo em Massa
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 64,
              fontWeight: 900,
              color: '#22C55E',
              letterSpacing: '-0.02em',
              textShadow: '0 0 25px rgba(34, 197, 94, 0.6)',
            }}
          >
            IA
          </span>
        </div>

        {/* 1 Frase do que o produto faz (y ≈ 540) */}
        <div
          style={{
            opacity: descSpring,
            transform: `translateY(${(1 - descSpring) * 20}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 8,
            textAlign: 'center',
            maxWidth: 880,
            marginBottom: 60,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 700,
              color: '#F1F5F9',
              lineHeight: 1.35,
              textShadow: '0 2px 10px rgba(0,0,0,0.8)',
            }}
          >
            Disparo inteligente no WhatsApp
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 500,
              color: '#94A3B8',
              lineHeight: 1.35,
            }}
          >
            Mensagens personalizadas e envio automático.
          </span>
        </div>

        {/* Pulsing Action Button (y ≈ 840) */}
        <div
          style={{
            opacity: buttonSpring,
            transform: `scale(${btnScale})`,
            width: 840,
            height: 114,
            borderRadius: 57,
            background: 'linear-gradient(135deg, #22C55E 0%, #16A34A 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 16px 50px rgba(34, 197, 94, 0.6)',
            position: 'relative',
            overflow: 'hidden',
            marginBottom: 44,
          }}
        >
          {/* Shimmer light bar across button */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `${shimmerPos}%`,
              width: 100,
              background:
                'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.45), transparent)',
              transform: 'skewX(-25deg)',
              pointerEvents: 'none',
            }}
          />

          <span
            style={{
              fontFamily,
              fontSize: 44,
              fontWeight: 900,
              color: '#111827',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Chame no Direct
          </span>
        </div>

        {/* Social Handle @ (y ≈ 1040) */}
        <div
          style={{
            opacity: footerSpring,
            transform: `translateY(${(1 - footerSpring) * 20}px)`,
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '14px 34px',
            borderRadius: 999,
            backgroundColor: 'rgba(255, 255, 255, 0.06)',
            border: '1.5px solid rgba(255, 255, 255, 0.15)',
            marginBottom: 44,
          }}
        >
          <span style={{fontSize: 34}}>💬</span>
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.02em',
            }}
          >
            @disparoemmassa.ia
          </span>
        </div>

        {/* Feature Highlights from Facts (y ≈ 1180) */}
        <div
          style={{
            opacity: footerSpring,
            display: 'flex',
            gap: 16,
            justifyContent: 'center',
            flexWrap: 'wrap',
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(17, 24, 39, 0.85)',
              border: '1px solid rgba(34, 197, 94, 0.35)',
              padding: '10px 22px',
              borderRadius: 999,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#86EFAC',
              }}
            >
              ✓ Rotação de instâncias
            </span>
          </div>

          <div
            style={{
              backgroundColor: 'rgba(17, 24, 39, 0.85)',
              border: '1px solid rgba(34, 197, 94, 0.35)',
              padding: '10px 22px',
              borderRadius: 999,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 700,
                color: '#86EFAC',
              }}
            >
              ✓ Envio automático
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
