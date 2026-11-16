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

  // Strong continuous background zoom & pan for noticeable visual delta across q13, q14, q15
  const bgScale = interpolate(frame, [0, 116], [1.0, 1.2], {
    extrapolateRight: 'clamp',
  });
  const bgPanX = interpolate(frame, [0, 116], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Staggered entrance animations:
  // 1. Brand block enters first (frame 0)
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 150},
  });
  const headerSlideY = interpolate(headerSpring, [0, 1], [-60, 0]);

  // 2. Hero CTA Button pops in early with scale bounce (frame 4) so q13 shows conversion action
  const ctaBounceSpring = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: {damping: 9, stiffness: 160},
  });

  // 3. @futebolcom.ia2 signature block rises smoothly (frame 10)
  const handleSpring = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: {damping: 11, stiffness: 130},
  });
  const handleRiseY = interpolate(handleSpring, [0, 1], [70, 0]);

  // Continuous heartbeat scale pulse on CTA button (0.97 <-> 1.065) + sweeping light beam
  const btnPulse = 1.0 + Math.sin(frame * 0.26) * 0.06;
  const floatY = Math.sin(frame * 0.15) * 8;
  const iconFloatY = Math.cos(frame * 0.18) * 6;
  const shimmerX = ((frame * 18) % 960) - 140;
  const handlePulse = 1.0 + Math.cos(frame * 0.22) * 0.03;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#31060F',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background with continuous zoom & pan */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateX(${bgPanX}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(225, 29, 72, 0.32) 0%, rgba(49, 6, 15, 0.84) 70%, rgba(15, 2, 5, 0.94) 100%)',
          }}
        />
      </div>

      {/* Dynamic sweeping spotlight behind content to ensure strong visual motion across q13, q14, q15 */}
      <div
        style={{
          position: 'absolute',
          top: 340 + Math.sin(frame * 0.16) * 120,
          left: 160 + Math.cos(frame * 0.14) * 160,
          width: 720,
          height: 720,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(250, 204, 21, 0.24) 0%, rgba(225, 29, 72, 0.2) 45%, transparent 70%)',
          filter: 'blur(40px)',
          pointerEvents: 'none',
        }}
      />

      {/* Clean, Breathing 3-Part Conversion Layout spanning y=200 to y=1340 (Zero pamphlet clutter!) */}
      <div
        style={{
          position: 'absolute',
          top: 200,
          left: 60,
          right: 60,
          height: 1160,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          zIndex: 10,
          transform: `translateY(${floatY}px)`,
        }}
      >
        {/* 1. UPPER BLOCK (y=230..640): Brand Identity & Core Value Proposition */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 20,
            opacity: headerSpring,
            transform: `translateY(${headerSlideY}px) scale(${0.9 + headerSpring * 0.1})`,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              width: 112,
              height: 112,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #E11D48 0%, #FACC15 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow:
                '0 14px 32px rgba(225, 29, 72, 0.6), 0 0 26px rgba(250, 204, 21, 0.45)',
              border: '3.5px solid rgba(255, 255, 255, 0.65)',
              transform: `translateY(${iconFloatY}px)`,
            }}
          >
            <span style={{fontSize: 54}}>📱</span>
          </div>

          <span
            style={{
              fontSize: 66,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '0.03em',
              textTransform: 'uppercase',
              textShadow: '0 8px 28px rgba(0, 0, 0, 0.9)',
              lineHeight: 1.05,
            }}
          >
            Cardápio Digital
          </span>

          <div
            style={{
              background: 'rgba(15, 3, 6, 0.82)',
              border: '2px solid rgba(250, 204, 21, 0.5)',
              borderRadius: 26,
              padding: '18px 32px',
              maxWidth: 880,
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.65)',
            }}
          >
            <span
              style={{
                fontSize: 38,
                fontWeight: 800,
                color: '#F8FAFC',
                lineHeight: 1.28,
              }}
            >
              O cliente vê o cardápio com{' '}
              <span style={{color: '#FACC15'}}>fotos no celular</span> e faz o
              pedido direto pelo{' '}
              <span style={{color: '#4ADE80'}}>WhatsApp com IA</span>
            </span>
          </div>
        </div>

        {/* 2. CENTER HERO CTA BUTTON (y=730..930): Staggered Pop + Continuous Pulse + Shimmer */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            zIndex: 20,
            opacity: Math.min(1, ctaBounceSpring * 1.15),
            transform: `scale(${(0.75 + ctaBounceSpring * 0.25) * btnPulse})`,
          }}
        >
          <div
            style={{
              position: 'relative',
              width: 880,
              padding: '34px 40px',
              borderRadius: 36,
              background: 'linear-gradient(135deg, #E11D48 0%, #BE123C 100%)',
              boxShadow:
                '0 22px 55px rgba(225, 29, 72, 0.85), 0 0 38px rgba(250, 204, 21, 0.5)',
              border: '4px solid #FACC15',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 20,
              overflow: 'hidden',
            }}
          >
            {/* Bright sweeping light reflection across CTA button */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerX,
                width: 150,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.6) 50%, transparent 100%)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontSize: 54,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                lineHeight: 1,
              }}
            >
              CHAME NO DIRECT
            </span>
            <span
              style={{
                fontSize: 48,
                color: '#FACC15',
                transform: `translateX(${Math.sin(frame * 0.3) * 9}px)`,
              }}
            >
              ➔
            </span>
          </div>
        </div>

        {/* 3. LOWER THIRD ACCOUNT SIGNATURE (y=1040..1360): Clean @futebolcom.ia2 Handle in Safe Zone */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            opacity: handleSpring,
            transform: `translateY(${handleRiseY}px) scale(${(0.88 + handleSpring * 0.12) * handlePulse})`,
          }}
        >
          <span
            style={{
              fontSize: 36,
              fontWeight: 800,
              color: '#FACC15',
              letterSpacing: '0.02em',
              textShadow: '0 4px 14px rgba(0, 0, 0, 0.9)',
            }}
          >
            Dúvidas respondidas na hora no seu delivery
          </span>

          <div
            style={{
              background: 'rgba(15, 3, 6, 0.95)',
              border: '3px solid #FACC15',
              borderRadius: 42,
              padding: '18px 56px',
              boxShadow:
                '0 14px 36px rgba(0, 0, 0, 0.85), 0 0 24px rgba(225, 29, 72, 0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span
              style={{
                width: 16,
                height: 16,
                borderRadius: '50%',
                background: '#22C55E',
                boxShadow: '0 0 12px #22C55E',
              }}
            />
            <span
              style={{
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.04em',
              }}
            >
              @futebolcom.ia2
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
