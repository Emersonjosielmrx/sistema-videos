import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
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

export const Cena3Dono: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Gentle push-in on the speaker video (scale 1.00 to 1.05)
  const videoScale = interpolate(frame, [0, 241], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  const headerSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Evolution of message in the top banner (strictly y: 184 to 420)
  const phase2Spring = spring({
    frame: frame - 45,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const phase3Spring = spring({
    frame: frame - 161,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const exitOpacity = interpolate(frame, [228, 241], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.fundoEscuro, opacity: exitOpacity}}>
      {/* Background Video (The Owner speaking) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 40%',
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
        {/* Soft top gradient to shield the top text without touching the face */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 440,
            background:
              'linear-gradient(180deg, rgba(11,15,25,0.85) 0%, rgba(11,15,25,0.50) 70%, rgba(11,15,25,0) 100%)',
          }}
        />
        {/* Soft bottom gradient to shield the karaoke subtitle */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(0deg, rgba(11,15,25,0.88) 0%, rgba(11,15,25,0.50) 65%, rgba(11,15,25,0) 100%)',
          }}
        />
      </div>

      {/* TOP AREA ONLY (y: 195 to 420) — Face is completely free below y=480! */}
      <div
        style={{
          position: 'absolute',
          top: 195,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
        }}
      >
        {/* Badge: O Resultado */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 28px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.94)',
            border: `1.5px solid ${THEME.colors.fundoCardBorder}`,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            transform: `scale(${headerSpring})`,
            opacity: headerSpring,
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: THEME.colors.destaqueGreen,
              boxShadow: `0 0 10px ${THEME.colors.destaqueGreen}`,
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
            O Resultado
          </span>
        </div>

        {/* Dynamic Highlight Card (Max bottom y <= 410) */}
        <div
          style={{
            width: '100%',
            maxWidth: 900,
            padding: '20px 32px',
            borderRadius: 22,
            background: 'rgba(15, 23, 42, 0.92)',
            border: `2px solid ${THEME.colors.marca}`,
            boxShadow: '0 16px 40px rgba(0,0,0,0.6)',
            textAlign: 'center',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {frame < 45 && (
            <span
              style={{
                fontFamily,
                fontSize: 42,
                fontWeight: 800,
                color: THEME.colors.texto,
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              Com esse apoio direto
            </span>
          )}

          {frame >= 45 && frame < 161 && (
            <span
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: THEME.colors.destaqueCyan,
                textTransform: 'uppercase',
                letterSpacing: 1,
                transform: `scale(${phase2Spring})`,
                display: 'inline-block',
                textShadow: '0 0 20px rgba(56,189,248,0.4)',
              }}
            >
              Automações Próprias com IA
            </span>
          )}

          {frame >= 161 && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 16,
                transform: `scale(${phase3Spring})`,
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  backgroundColor: THEME.colors.destaqueGreen,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: `0 0 14px ${THEME.colors.destaqueGreen}`,
                }}
              >
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                  <path d="M20 6L9 17L4 12" stroke="#FFFFFF" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 1.5,
                }}
              >
                Com Total Segurança
              </span>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
