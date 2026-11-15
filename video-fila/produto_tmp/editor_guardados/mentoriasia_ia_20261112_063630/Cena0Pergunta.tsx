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
import {THEME} from './theme';

interface CenaProps {
  fontFamily: string;
}

export const Cena0Pergunta: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background camera motion: continuous push-in and slight tilt
  const bgScale = interpolate(frame, [0, 182], [1.05, 1.2], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 182], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Entry springs
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // "QUER APLICAR IA" (speaks from ~0.3s = 9 frames to 2.1s = 64 frames)
  const title1Spring = spring({
    frame: frame - 8,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const iaBadgeSpring = spring({
    frame: frame - 24,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const rotinaSpring = spring({
    frame: frame - 68,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Second half: "mas não sabe por onde começar?" (starts ~2.98s = frame 89)
  const part2Progress = spring({
    frame: frame - 88,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Exit transition at end of scene
  const exitOpacity = interpolate(frame, [168, 182], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.fundoEscuro, opacity: exitOpacity}}>
      {/* Background Image with motion */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Dark contrast gradients for high readability */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11,15,25,0.85) 0%, rgba(11,15,25,0.72) 40%, rgba(11,15,25,0.92) 100%)',
          }}
        />
      </div>

      {/* Decorative dynamic ambient glow */}
      <div
        style={{
          position: 'absolute',
          top: 300,
          left: 100,
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(37,99,235,0.25) 0%, rgba(37,99,235,0) 70%)',
          transform: `scale(${1 + Math.sin(frame / 20) * 0.08})`,
          filter: 'blur(40px)',
          pointerEvents: 'none',
        }}
      />

      {/* Top Header Badge (Safe zone: y >= 160) */}
      <div
        style={{
          position: 'absolute',
          top: 195,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring}) translateY(${(1 - badgeSpring) * -30}px)`,
          opacity: badgeSpring,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.94)',
            border: `1.5px solid ${THEME.colors.fundoCardBorder}`,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: THEME.colors.destaqueCyan,
              boxShadow: `0 0 12px ${THEME.colors.destaqueCyan}`,
              transform: `scale(${1 + Math.sin(frame / 10) * 0.25})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: THEME.colors.texto,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            Treinamentos e Mentorias IA
          </span>
        </div>
      </div>

      {/* Main Kinetic Typography Block (y: 340 to 1250) */}
      <div
        style={{
          position: 'absolute',
          top: 340,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 28,
        }}
      >
        {/* Phase 1: Question Setup */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            transform: `scale(${title1Spring}) translateY(${(1 - title1Spring) * 40}px)`,
            opacity: title1Spring,
            width: '100%',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 52,
              fontWeight: 800,
              color: THEME.colors.textoSecundario,
              textTransform: 'uppercase',
              letterSpacing: 1.5,
              textShadow: '0 4px 16px rgba(0,0,0,0.8)',
            }}
          >
            Quer aplicar
          </span>

          {/* Glowing IA Banner — Balanced 2 lines, strictly centered with wide safe margins */}
          <div
            style={{
              marginTop: 16,
              transform: `scale(${iaBadgeSpring})`,
              display: 'inline-flex',
              padding: '18px 48px',
              borderRadius: 24,
              background: `linear-gradient(135deg, ${THEME.colors.marca} 0%, #1D4ED8 100%)`,
              border: '2px solid rgba(255,255,255,0.3)',
              boxShadow: '0 12px 36px rgba(37,99,235,0.55)',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 64,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
                textAlign: 'center',
                lineHeight: 1.18,
              }}
            >
              Inteligência <br />
              Artificial
            </span>
          </div>

          {/* "na sua rotina" */}
          <div
            style={{
              marginTop: 20,
              transform: `scale(${rotinaSpring}) translateY(${(1 - rotinaSpring) * 20}px)`,
              opacity: rotinaSpring,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 60,
                fontWeight: 800,
                color: THEME.colors.texto,
                textTransform: 'uppercase',
                letterSpacing: 2,
                textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              }}
            >
              na sua rotina?
            </span>
          </div>
        </div>

        {/* Phase 2: Dilemma Card ("mas não sabe por onde começar?") */}
        {frame >= 86 && (
          <div
            style={{
              width: '100%',
              maxWidth: 920,
              marginTop: 20,
              padding: '36px 36px',
              borderRadius: 30,
              background: 'rgba(15, 23, 42, 0.92)',
              border: '2px solid rgba(239, 68, 68, 0.4)',
              boxShadow: '0 20px 50px rgba(0,0,0,0.7)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
              transform: `scale(${part2Progress}) translateY(${(1 - part2Progress) * 50}px)`,
              opacity: part2Progress,
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 20px',
                borderRadius: 999,
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid rgba(239, 68, 68, 0.5)',
              }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#EF4444" strokeWidth="2.5" />
                <path d="M12 7V13" stroke="#EF4444" strokeWidth="2.5" strokeLinecap="round" />
                <circle cx="12" cy="17" r="1.5" fill="#EF4444" />
              </svg>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FCA5A5',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                O Grande Obstáculo
              </span>
            </div>

            <div
              style={{
                textAlign: 'center',
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: THEME.colors.texto,
                lineHeight: 1.25,
                textTransform: 'uppercase',
              }}
            >
              Mas não sabe <br />
              <span style={{color: THEME.colors.destaqueCyan}}>por onde começar?</span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
