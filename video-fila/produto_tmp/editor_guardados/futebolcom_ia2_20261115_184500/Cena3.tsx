import React from 'react';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // 116% -> 120% Punch-In Zoom (differentiating Scene 3 "O Resultado" from Scene 1 "O Problema"),
  // with transformOrigin center and videoShiftY=240, ensuring >180px of headroom between presenter's hair and top badges!
  const punch2Spring =
    frame >= 104
      ? spring({
          frame: frame - 104,
          fps,
          config: {damping: 14, stiffness: 170},
        })
      : 0;
  const baseZoom = interpolate(frame, [0, 241], [1.15, 1.18], {
    extrapolateRight: 'clamp',
  });
  const videoScale = baseZoom + punch2Spring * 0.04; // 1.15..1.18 in Phase 1 -> 1.19..1.22 in Phase 2
  const videoShiftX = interpolate(frame, [0, 241], [-20, 0], {
    extrapolateRight: 'clamp',
  });
  const videoShiftY = interpolate(frame, [0, 241], [265, 280], {
    extrapolateRight: 'clamp',
  });

  // Smooth zoom-in entrance from Cena 2
  const enterSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 150},
  });

  // Fade out transition at the end (last 12 frames)
  const sceneOpacity = interpolate(frame, [228, 241], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Top notification bar spring
  const badgeProgress = spring({
    frame: frame - 2,
    fps,
    config: {damping: 13, stiffness: 135},
  });

  // Step 1: Pedido Direto no WhatsApp (local frames 0 to 104)
  const card1Progress = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Step 2: Cliente Seguro da Escolha no Cardápio (local frames 104 to 241)
  const card2Progress = spring({
    frame: frame - 104,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Step 2B: Sub-badge pop at frame 160 ("que fez no cardápio") so q11 -> q12 has strong secondary evolution
  const subBadgePop = spring({
    frame: Math.max(0, frame - 160),
    fps,
    config: {damping: 11, stiffness: 160},
  });

  // Continuous shimmer and pulse on the top badge
  const pulseY = Math.sin(frame * 0.16) * 4;
  const badgeScalePulse = 1.0 + Math.sin(frame * 0.24) * 0.03;
  const shimmerX = ((frame * 16) % 900) - 140;

  return (
    <AbsoluteFill
      style={{
        opacity: sceneOpacity,
        backgroundColor: '#000000',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Owner Video in Close-Up Punch-In (Head safely clear with >180px headroom below badge!) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `translate(${videoShiftX}px, ${videoShiftY}px) scale(${videoScale})`,
          transformOrigin: 'center center',
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

      {/* Warm emerald/gold solution ambient vignette to visually contrast with Cena 1 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 55%, transparent 52%, rgba(6, 48, 28, 0.42) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top gradient overlay ONLY for text contrast (y 0 to 360) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 360,
          background:
            'linear-gradient(180deg, rgba(6, 24, 16, 0.96) 0%, rgba(6, 24, 16, 0.78) 62%, rgba(6, 24, 16, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Distinct Top Solution Notification Bar (y=158 to y=335) — Keeps >135px of headroom above presenter's hair! */}
      <div
        style={{
          position: 'absolute',
          top: 158,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          opacity: enterSpring,
          transform: `translateY(${pulseY}px)`,
          zIndex: 20,
        }}
      >
        {/* Top Row: Step Indicator Pills (1. Pedido no WhatsApp | 2. Cliente Seguro) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            opacity: badgeProgress,
          }}
        >
          <div
            style={{
              padding: '6px 20px',
              borderRadius: 18,
              background:
                frame < 104
                  ? 'linear-gradient(135deg, #22C55E 0%, #15803D 100%)'
                  : 'rgba(34, 197, 94, 0.28)',
              border: '2px solid #4ADE80',
              boxShadow: '0 4px 14px rgba(0,0,0,0.5)',
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
              }}
            >
              ✓ O Resultado
            </span>
          </div>
          <div
            style={{
              padding: '6px 20px',
              borderRadius: 18,
              background:
                frame >= 104
                  ? 'linear-gradient(135deg, #FACC15 0%, #CA8A04 100%)'
                  : 'rgba(250, 204, 21, 0.22)',
              border: '2px solid #FACC15',
              boxShadow: '0 4px 14px rgba(0,0,0,0.5)',
            }}
          >
            <span
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: frame >= 104 ? '#111827' : '#FACC15',
                textTransform: 'uppercase',
              }}
            >
              ★ Cardápio + IA
            </span>
          </div>
        </div>

        {/* Phase 1 (frames 0 to 104): Live WhatsApp Order Notification Card */}
        {frame < 104 && (
          <div
            style={{
              opacity: card1Progress,
              transform: `scale(${0.92 + card1Progress * 0.08}) translateY(${(1 - card1Progress) * 12}px)`,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              padding: '10px 24px',
              borderRadius: 22,
              background: 'rgba(11, 28, 20, 0.95)',
              border: '2.5px solid #22C55E',
              boxShadow:
                '0 12px 28px rgba(0, 0, 0, 0.85), 0 0 20px rgba(34, 197, 94, 0.35)',
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 14,
                background: '#22C55E',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
                color: '#FFFFFF',
                fontWeight: 900,
              }}
            >
              📲
            </div>
            <span
              style={{
                fontSize: 35,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
                whiteSpace: 'nowrap',
              }}
            >
              Pedido Direto no WhatsApp
            </span>
          </div>
        )}

        {/* Phase 2 (frames 104 to 241): Verified Customer Choice Card with Shimmer & Progressive Badge */}
        {frame >= 104 && (
          <div
            style={{
              position: 'relative',
              overflow: 'hidden',
              opacity: card2Progress,
              transform: `scale(${(0.92 + card2Progress * 0.08) * badgeScalePulse}) translateY(${(1 - card2Progress) * 12}px)`,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              padding: '10px 26px',
              borderRadius: 22,
              background: '#0B1324',
              border: '3px solid #FACC15',
              boxShadow:
                '0 12px 28px rgba(0, 0, 0, 0.9), 0 0 22px rgba(250, 204, 21, 0.42)',
            }}
          >
            {/* Sweeping Shimmer Beam across the badge */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: shimmerX,
                width: 120,
                background:
                  'linear-gradient(90deg, transparent 0%, rgba(250, 204, 21, 0.45) 50%, transparent 100%)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />
            <Img
              src={staticFile('prato_executivo.jpg')}
              style={{
                width: 52,
                height: 52,
                borderRadius: 12,
                objectFit: 'cover',
                border: '2px solid #22C55E',
              }}
            />
            <span
              style={{
                fontSize: 35,
                fontWeight: 900,
                color: '#FACC15',
                textTransform: 'uppercase',
                letterSpacing: '0.02em',
                whiteSpace: 'nowrap',
              }}
            >
              ✓ Cliente Seguro da Escolha
            </span>
            {frame >= 160 && (
              <div
                style={{
                  opacity: subBadgePop,
                  transform: `scale(${0.8 + subBadgePop * 0.2})`,
                  background: 'linear-gradient(135deg, #22C55E 0%, #16A34A 100%)',
                  borderRadius: 14,
                  padding: '5px 14px',
                  boxShadow: '0 4px 12px rgba(34, 197, 94, 0.45)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span style={{fontSize: 24, color: '#FFFFFF'}}>★</span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    whiteSpace: 'nowrap',
                  }}
                >
                  No Cardápio
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
