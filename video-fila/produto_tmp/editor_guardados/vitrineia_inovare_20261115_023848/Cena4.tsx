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

export const Cena4: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tRel = frame / fps; // 0 to 3.95s

  // Strong continuous background push-in & pan up to the very last frame
  const bgScale = interpolate(tRel, [0, 3.95], [1.0, 1.28], {
    extrapolateRight: 'clamp',
  });
  const bgX = interpolate(tRel, [0, 3.95], [40, -40], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(tRel, [0, 3.95], [24, -24], {
    extrapolateRight: 'clamp',
  });

  const cardIn = spring({frame, fps, config: {damping: 13, stiffness: 140}});
  const btnIn = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Spoken cue in Cena 4: "Chame" (28.48s -> tRel 0.49s), "no direct" (29.25s -> tRel 1.26s)
  const directAtivo = tRel >= 1.26;

  // Periodic tap cycles (at tRel = 1.3s and tRel = 2.7s) so q13, q14, q15 show unmistakable visual evolution
  const tapWave1 = interpolate(tRel, [1.25, 1.95], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const tapWave2 = interpolate(tRel, [2.55, 3.35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const activeWave = tRel < 2.2 ? tapWave1 : tapWave2;
  const isPressed =
    (tRel >= 1.25 && tRel <= 1.55) || (tRel >= 2.55 && tRel <= 2.85);

  // Continuous pulse, floating & shimmer right up to 31.94s
  const btnPulse = (isPressed ? 0.94 : 1.04) + Math.sin(tRel * 9.0) * 0.065;
  const floatY = Math.sin(tRel * 4.2) * 16;
  const tiltZ = Math.sin(tRel * 3.2) * 1.5;
  const shimmerX = interpolate((tRel * 1.15) % 1, [0, 1], [-25, 125]);
  const orbX = interpolate(tRel, [0, 3.95], [-200, 200]);

  // Touch indicator finger/ripple animation
  const fingerX = interpolate(Math.sin(tRel * 4.5), [-1, 1], [15, -15]);
  const fingerY = isPressed ? -6 : 14 + Math.sin(tRel * 6.0) * 8;

  return (
    <AbsoluteFill style={{backgroundColor: '#111827'}}>
      {/* Background store photo moving continuously */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(2px)',
            transform: `scale(${bgScale}) translate(${bgX}px, ${bgY}px)`,
          }}
        />
      </AbsoluteFill>

      {/* Moving brand light glow + dark veil */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${50 + orbX * 0.14}% 38%, rgba(167,139,250,0.45) 0%, rgba(17,24,39,0.76) 72%)`,
        }}
      />

      {/* Unified End Card inside Safe Zone (y=310..1120, leaving y=1320..1570 clear for Karaoke) */}
      <div
        style={{
          position: 'absolute',
          top: 310,
          left: 60,
          right: 60,
          transform: `translateY(${interpolate(cardIn, [0, 1], [40, 0]) + floatY}px) rotate(${tiltZ}deg) scale(${interpolate(cardIn, [0, 1], [0.92, 1])})`,
          opacity: cardIn,
          backgroundColor: 'rgba(17, 24, 39, 0.93)',
          border: '3px solid #A78BFA',
          borderRadius: 36,
          padding: '42px 38px',
          boxShadow: '0 28px 64px rgba(0,0,0,0.72)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 24,
        }}
      >
        {/* Brand Pill */}
        <div
          style={{
            backgroundColor: 'rgba(167, 139, 250, 0.18)',
            border: '2px solid #A78BFA',
            borderRadius: 999,
            padding: '10px 28px',
            fontFamily,
            fontSize: 32,
            fontWeight: 800,
            color: '#A78BFA',
            letterSpacing: 0.8,
            textTransform: 'uppercase',
          }}
        >
          Atendimento Inteligente
        </div>

        {/* Brand Name */}
        <div
          style={{
            fontFamily,
            fontSize: 74,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.05,
            letterSpacing: -1,
          }}
        >
          Vitrine <span style={{color: '#A78BFA'}}>IA</span>
        </div>

        {/* Exact factual value proposition */}
        <div
          style={{
            fontFamily,
            fontSize: 40,
            fontWeight: 700,
            color: '#F1F5F9',
            lineHeight: 1.26,
            maxWidth: 820,
            textWrap: 'balance',
          }}
        >
          Bot com todo o conhecimento da sua loja. Atende, recomenda e vende.
        </div>

        {/* Main Pulsing CTA Button with Shimmer + Touch Ripple + Tap Badge */}
        <div style={{position: 'relative', marginTop: 8}}>
          {/* Expanding touch ripple ring around CTA button */}
          {activeWave > 0 && activeWave < 1 && (
            <div
              style={{
                position: 'absolute',
                inset: -14,
                borderRadius: 999,
                border: '4px solid #A78BFA',
                transform: `scale(${interpolate(activeWave, [0, 1], [0.95, 1.22])})`,
                opacity: interpolate(activeWave, [0, 1], [0.9, 0]),
                pointerEvents: 'none',
              }}
            />
          )}

          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              backgroundColor: isPressed ? '#C4B5FD' : '#A78BFA',
              borderRadius: 999,
              padding: '24px 82px 24px 52px',
              transform: `scale(${interpolate(btnIn, [0, 1], [0.85, 1]) * btnPulse})`,

              boxShadow: isPressed
                ? '0 22px 55px rgba(167, 139, 250, 0.85)'
                : '0 16px 40px rgba(167, 139, 250, 0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
            }}
          >
            {/* Continuous bright shimmer sweep */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 150,
                left: `${shimmerX}%`,
                background:
                  'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.6) 50%, rgba(255,255,255,0) 100%)',
                transform: 'skewX(-20deg)',
                pointerEvents: 'none',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#121216',
                letterSpacing: 0.5,
              }}
            >
              CHAME NO DIRECT
            </span>
          </div>

          {/* Mobile Tap Indicator Icon (positioned clear of the 'DIRECT' letters) */}
          <div
            style={{
              position: 'absolute',
              right: 16,
              bottom: -18,
              transform: `translate(${fingerX * 0.4}px, ${fingerY * 0.5}px) scale(${isPressed ? 0.88 : 1.05})`,

              backgroundColor: '#111827',
              border: '3px solid #FFFFFF',
              borderRadius: '50%',
              width: 54,
              height: 54,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 20px rgba(0,0,0,0.6)',
            }}
          >
            <div
              style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                backgroundColor: isPressed ? '#22C55E' : '#A78BFA',
              }}
            />
          </div>
        </div>

        {/* Handle @vitrineia_inovare inside safe zone (y ~ 1030) */}
        <div
          style={{
            marginTop: 10,
            backgroundColor: directAtivo
              ? 'rgba(167, 139, 250, 0.28)'
              : 'rgba(255, 255, 255, 0.08)',
            border: directAtivo
              ? '2.5px solid #A78BFA'
              : '2px solid transparent',
            borderRadius: 999,
            padding: '12px 32px',
            fontFamily,
            fontSize: 38,
            fontWeight: 800,
            color: '#FFFFFF',
            transform: `scale(${directAtivo ? 1 + Math.sin(tRel * 7) * 0.03 : 1})`,
          }}
        >
          @vitrineia_inovare
        </div>
      </div>
    </AbsoluteFill>
  );
};
