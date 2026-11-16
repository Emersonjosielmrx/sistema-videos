import React from 'react';
import {
  interpolate,
  OffthreadVideo,
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

  // Distinct tighter close-up framing compared to Scene 1 (1.32 -> 1.42)
  const videoScale = interpolate(frame, [0, 245], [1.32, 1.42], {
    extrapolateRight: 'clamp',
  });

  // Entrance springs
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  const titleSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  // Dynamic Automation Mockup Card sliding in during 'no automático' (relative frame 130)
  const autoCardSpring = spring({
    frame: frame - 130,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  const floatY = Math.sin(frame * 0.08) * 4;
  const autoFloatY = Math.sin(frame * 0.12) * 6;
  const pulse = 1.0 + Math.sin(frame * 0.25) * 0.04;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Presenter Video Fullscreen with Distinct Tight Close-Up Framing */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 36%',
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
        {/* Soft vignette/gradient on top ONLY to ensure contrast without dimming face */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(17, 24, 39, 0.88) 0%, rgba(17, 24, 39, 0.4) 70%, rgba(17, 24, 39, 0) 100%)',
          }}
        />
      </div>

      {/* Dynamic WhatsApp Automation Card on 'no automático' (relative frame 130+, placed in lower open desk area: face 100% free) */}
      {frame >= 130 && (
        <div
          style={{
            position: 'absolute',
            top: 1130 + autoFloatY,
            left: 45,
            opacity: autoCardSpring,
            transform: `scale(${interpolate(autoCardSpring, [0, 1], [0.7, 1]) * pulse}) translateX(${interpolate(autoCardSpring, [0, 1], [-40, 0])}px)`,
            padding: '14px 20px',
            borderRadius: 20,
            backgroundColor: 'rgba(15, 23, 42, 0.96)',
            border: '2px solid rgba(20, 184, 166, 0.75)',
            boxShadow:
              '0 15px 35px rgba(0, 0, 0, 0.8), 0 0 35px rgba(20, 184, 166, 0.45)',
            backdropFilter: 'blur(16px)',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            zIndex: 15,
            maxWidth: 330,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              borderBottom: '1px solid rgba(20, 184, 166, 0.3)',
              paddingBottom: 8,
            }}
          >
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 10,
                backgroundColor: '#14B8A6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20,
                color: '#FFFFFF',
              }}
            >
              🤖
            </div>
            <div style={{fontSize: 26, fontWeight: 900, color: '#FFFFFF'}}>
              WhatsApp no Automático
            </div>
          </div>
          <div style={{display: 'flex', flexDirection: 'column', gap: 8}}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: 24,
                color: '#5EEAD4',
                fontWeight: 700,
              }}
            >
              <span>✓</span>
              <span>Moderação ativa</span>
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: 24,
                color: '#5EEAD4',
                fontWeight: 700,
              }}
            >
              <span>✓</span>
              <span>Resumos automáticos</span>
            </div>
          </div>
        </div>
      )}

      {/* Upper Information Area (strictly between y=165 and y=390 — ROSTO 100% LIVRE) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          transform: `translateY(${floatY}px)`,
          zIndex: 10,
        }}
      >
        {/* Rótulo: O RESULTADO */}
        <div
          style={{
            opacity: badgeSpring,
            transform: `translateY(${interpolate(badgeSpring, [0, 1], [-15, 0])}px)`,
            padding: '8px 24px',
            borderRadius: 999,
            backgroundColor: '#14B8A6',
            color: '#111827',
            fontSize: 32,
            fontWeight: 900,
            letterSpacing: 1.5,
            textTransform: 'uppercase',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: '0 0 25px rgba(20, 184, 166, 0.55)',
          }}
        >
          <span>✓</span>
          <span>O Resultado</span>
        </div>

        {/* Title: GRUPOS DE WHATSAPP NO AUTOMÁTICO */}
        <div
          style={{
            opacity: titleSpring,
            transform: `scale(${interpolate(titleSpring, [0, 1], [0.9, 1])})`,
            padding: '16px 30px',
            borderRadius: 20,
            backgroundColor: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(20, 184, 166, 0.8)',
            boxShadow: '0 0 35px rgba(20, 184, 166, 0.5)',
            backdropFilter: 'blur(14px)',
            maxWidth: 920,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              fontSize: 46,
              fontWeight: 900,
              color: '#FFFFFF',
              textWrap: 'balance',
              lineHeight: 1.2,
              letterSpacing: -0.5,
            }}
          >
            Grupos de WhatsApp
            <span style={{color: '#2DD4BF'}}> no automático</span>
          </div>
        </div>
      </div>
    </div>
  );
};
