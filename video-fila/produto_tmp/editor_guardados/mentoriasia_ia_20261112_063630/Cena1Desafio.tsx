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

export const Cena1Desafio: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background camera motion
  const bgScale = interpolate(frame, [0, 216], [1.08, 1.22], {
    extrapolateRight: 'clamp',
  });
  const bgPanX = interpolate(frame, [0, 216], [-30, 30], {
    extrapolateRight: 'clamp',
  });

  // Top header spring
  const headerSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Card 1: "Tentava usar IA sem direção" (voice: "Eu tentava usar inteligência artificial...", starts ~frame 15)
  const card1Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Scanner wave / transition trigger at ~frame 88 ("mas faltava método e direção prática...")
  const scanSweep = interpolate(frame, [85, 110], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Card 2: "Faltava método e direção"
  const card2Spring = spring({
    frame: frame - 88,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Fade out transition at the end
  const exitOpacity = interpolate(frame, [204, 216], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.fundoEscuro, opacity: exitOpacity}}>
      {/* Background with motion */}
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
          src={staticFile('img_1.jpg')}
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
              'linear-gradient(180deg, rgba(11,15,25,0.88) 0%, rgba(11,15,25,0.80) 50%, rgba(11,15,25,0.94) 100%)',
          }}
        />
      </div>

      {/* Top Header Badge */}
      <div
        style={{
          position: 'absolute',
          top: 195,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${headerSpring}) translateY(${(1 - headerSpring) * -30}px)`,
          opacity: headerSpring,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 28px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.92)',
            border: `1.5px solid ${THEME.colors.fundoCardBorder}`,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: THEME.colors.destaqueAmber,
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
            O Desafio
          </span>
        </div>
      </div>

      {/* Scene Title (y: 240) */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          textAlign: 'center',
          transform: `scale(${headerSpring})`,
          opacity: headerSpring,
        }}
      >
        <span
          style={{
            fontFamily,
            fontSize: 50,
            fontWeight: 900,
            color: THEME.colors.texto,
            textTransform: 'uppercase',
            letterSpacing: 1.5,
            lineHeight: 1.2,
            textShadow: '0 4px 16px rgba(0,0,0,0.9)',
          }}
        >
          O Grande Gargalo <br />
          <span style={{color: THEME.colors.destaqueCyan}}>Na Rotina Prática</span>
        </span>
      </div>

      {/* Central Split Cards (Antes x Depois / Sem Método x Solução) */}
      <div
        style={{
          position: 'absolute',
          top: 400,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          display: 'flex',
          flexDirection: 'column',
          gap: 26,
        }}
      >
        {/* Card 1: Sem Método (Tentar usar IA sozinho) */}
        <div
          style={{
            width: '100%',
            padding: '30px 32px',
            borderRadius: 24,
            background: 'rgba(15, 23, 42, 0.88)',
            border: '2px solid rgba(239, 68, 68, 0.35)',
            boxShadow: '0 16px 40px rgba(0,0,0,0.6)',
            transform: `scale(${card1Spring}) translateY(${(1 - card1Spring) * 40}px)`,
            opacity: card1Spring,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16}}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                border: '1.5px solid rgba(239, 68, 68, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6L18 18" stroke="#EF4444" strokeWidth="3" strokeLinecap="round" />
              </svg>
            </div>
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#F87171',
                textTransform: 'uppercase',
                letterSpacing: 1,
              }}
            >
              Tentativa sem Método
            </span>
          </div>

          <div style={{display: 'flex', flexDirection: 'column', gap: 12}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <span style={{color: '#EF4444', fontSize: 34, fontWeight: 900}}>•</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: THEME.colors.textoSecundario,
                }}
              >
                Tentava usar inteligência artificial
              </span>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <span style={{color: '#EF4444', fontSize: 34, fontWeight: 900}}>•</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: THEME.colors.textoSecundario,
                }}
              >
                Prompts soltos sem direção real
              </span>
            </div>
          </div>
        </div>

        {/* Divider / Scanning line */}
        {frame >= 85 && (
          <div
            style={{
              position: 'relative',
              height: 4,
              width: '100%',
              background: 'rgba(255,255,255,0.1)',
              borderRadius: 2,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: 0,
                width: `${scanSweep * 100}%`,
                background: `linear-gradient(90deg, transparent, ${THEME.colors.destaqueCyan}, #FFFFFF)`,
                boxShadow: `0 0 16px ${THEME.colors.destaqueCyan}`,
              }}
            />
          </div>
        )}

        {/* Card 2: A Necessidade Real ("Faltava método e direção prática...") */}
        {frame >= 88 && (
          <div
            style={{
              width: '100%',
              padding: '30px 32px',
              borderRadius: 24,
              background: 'rgba(15, 23, 42, 0.92)',
              border: `2px solid ${THEME.colors.marca}`,
              boxShadow: '0 20px 50px rgba(37,99,235,0.3)',
              transform: `scale(${card2Spring}) translateY(${(1 - card2Spring) * 40}px)`,
              opacity: card2Spring,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16}}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 12,
                  backgroundColor: 'rgba(37, 99, 235, 0.25)',
                  border: `1.5px solid ${THEME.colors.marca}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M20 6L9 17L4 12" stroke="#38BDF8" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: THEME.colors.destaqueCyan,
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                O Que Faltava
              </span>
            </div>

            <div style={{display: 'flex', flexDirection: 'column', gap: 12}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <span style={{color: THEME.colors.destaqueCyan, fontSize: 34, fontWeight: 900}}>✓</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Método e direção prática
                </span>
              </div>
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <span style={{color: THEME.colors.destaqueCyan, fontSize: 34, fontWeight: 900}}>✓</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 800,
                    color: '#FFFFFF',
                  }}
                >
                  Aplicação direta na rotina
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
