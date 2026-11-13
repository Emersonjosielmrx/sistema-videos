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

export const Cena4Cartao: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Continuous background push-in
  const bgScale = interpolate(frame, [0, 119], [1.1, 1.25], {
    extrapolateRight: 'clamp',
  });

  // Entry animations — quick entrance so elements are fully present immediately
  const logoSpring = spring({
    frame: frame - 1,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const textSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const buttonSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const handleSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Alive micro-interactions:
  // Button pulse
  const buttonPulse = 1 + Math.sin(frame / 6) * 0.035;

  // Floating icon
  const floatOffset = Math.sin(frame / 9) * 8;

  // Moving sheen beam across the button
  const sheenCycle = frame % 36;
  const sheenPos = interpolate(sheenCycle, [0, 22], [-120, 220], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.fundoEscuro}}>
      {/* Blurred background image with slow zoom */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          filter: 'blur(16px)',
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
      </div>

      {/* Deep brand veil for contrast */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at center, rgba(15,23,42,0.85) 0%, rgba(11,15,25,0.96) 100%)',
        }}
      />

      {/* Animated ambient pulse circles */}
      <div
        style={{
          position: 'absolute',
          top: 450,
          left: 540,
          width: 500,
          height: 500,
          marginLeft: -250,
          marginTop: -250,
          borderRadius: '50%',
          border: '1.5px solid rgba(37,99,235,0.25)',
          transform: `scale(${1 + Math.sin(frame / 14) * 0.12})`,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 450,
          left: 540,
          width: 660,
          height: 660,
          marginLeft: -330,
          marginTop: -330,
          borderRadius: '50%',
          border: '1px solid rgba(56,189,248,0.15)',
          transform: `scale(${1 + Math.sin((frame + 10) / 14) * 0.08})`,
          pointerEvents: 'none',
        }}
      />

      {/* Main Content Layout (Strict Safe Zone y: 160 to 1560) */}
      <div
        style={{
          position: 'absolute',
          top: 300,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        {/* Floating Brand Icon */}
        <div
          style={{
            transform: `scale(${logoSpring}) translateY(${floatOffset}px)`,
            opacity: logoSpring,
            width: 108,
            height: 108,
            borderRadius: 32,
            background: `linear-gradient(135deg, ${THEME.colors.marca} 0%, #1E40AF 100%)`,
            border: '2px solid rgba(255, 255, 255, 0.25)',
            boxShadow: '0 16px 40px rgba(37, 99, 235, 0.55)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 26,
          }}
        >
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2L2 7L12 12L22 7L12 2Z"
              stroke="#FFFFFF"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M2 17L12 22L22 17"
              stroke="#38BDF8"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M2 12L12 17L22 12"
              stroke="#93C5FD"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* Brand Name */}
        <div
          style={{
            transform: `scale(${logoSpring}) translateY(${(1 - logoSpring) * 20}px)`,
            opacity: logoSpring,
            marginBottom: 16,
          }}
        >
          <h1
            style={{
              fontFamily,
              fontSize: 54,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 2,
              lineHeight: 1.18,
              textTransform: 'uppercase',
              margin: 0,
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
            }}
          >
            Treinamentos e <br />
            <span style={{color: THEME.colors.destaqueCyan}}>Mentorias IA</span>
          </h1>
        </div>

        {/* Product Value Phrase */}
        <div
          style={{
            transform: `scale(${textSpring}) translateY(${(1 - textSpring) * 15}px)`,
            opacity: textSpring,
            maxWidth: 840,
            marginBottom: 70,
          }}
        >
          <p
            style={{
              fontFamily,
              fontSize: 40,
              fontWeight: 700,
              color: THEME.colors.textoSecundario,
              lineHeight: 1.35,
              margin: 0,
            }}
          >
            Aprenda a criar automações com IA
          </p>
        </div>

        {/* Pulsing CTA Button with Sheen Effect (Centered around y: 920-1040) */}
        <div
          style={{
            width: '100%',
            maxWidth: 880,
            transform: `scale(${buttonSpring * buttonPulse}) translateY(${(1 - buttonSpring) * 30}px)`,
            opacity: buttonSpring,
            position: 'relative',
            marginBottom: 44,
          }}
        >
          <div
            style={{
              position: 'relative',
              width: '100%',
              boxSizing: 'border-box',
              padding: '30px 40px',
              borderRadius: 30,
              background: `linear-gradient(135deg, ${THEME.colors.marca} 0%, #1D4ED8 100%)`,
              border: '2px solid rgba(255, 255, 255, 0.4)',
              boxShadow:
                '0 20px 50px rgba(37,99,235,0.6), inset 0 2px 4px rgba(255,255,255,0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 20,
              overflow: 'hidden',
            }}
          >
            {/* Moving light beam / sheen */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: `${sheenPos}%`,
                width: 140,
                background:
                  'linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)',
                transform: 'skewX(-25deg)',
                pointerEvents: 'none',
              }}
            />

            {/* Direct Airplane Icon */}
            <svg width="44" height="44" viewBox="0 0 24 24" fill="none">
              <path
                d="M22 2L11 13"
                stroke="#FFFFFF"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M22 2L15 22L11 13L2 9L22 2Z"
                stroke="#FFFFFF"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>

            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              Chame no Direct
            </span>
          </div>
        </div>

        {/* Handle @mentoriasia.ia */}
        <div
          style={{
            transform: `scale(${handleSpring})`,
            opacity: handleSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '14px 36px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.94)',
            border: `1.5px solid ${THEME.colors.fundoCardBorder}`,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: THEME.colors.destaqueCyan,
              letterSpacing: 1.5,
            }}
          >
            @mentoriasia.ia
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
