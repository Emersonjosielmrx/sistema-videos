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

interface StepItem {
  num: string;
  title: string;
  badge: string;
  frameIn: number;
}

export const Cena2ComoFunciona: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Gentle camera zoom
  const videoScale = interpolate(frame, [0, 259], [1.08, 1.14], {
    extrapolateRight: 'clamp',
  });

  const headerSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const steps: StepItem[] = [
    {
      num: '1/4',
      title: 'Treinamento Vibe Coding',
      badge: 'Código & IA',
      frameIn: 36, // ~13.84s (local: 1.25s)
    },
    {
      num: '2/4',
      title: 'Consultoria de Otimização',
      badge: 'Processos',
      frameIn: 82, // ~15.38s (local: 2.79s)
    },
    {
      num: '3/4',
      title: 'Pack de Prompts Validados',
      badge: 'Testados',
      frameIn: 135, // ~17.16s (local: 4.57s)
    },
    {
      num: '4/4',
      title: 'Mapa Mental Completo',
      badge: 'Direção',
      frameIn: 177, // ~18.55s (local: 5.96s)
    },
  ];

  const exitOpacity = interpolate(frame, [246, 259], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.fundoEscuro, opacity: exitOpacity}}>
      {/* Background B-Roll Video — Shifted left to keep the person's face/body safely on the left */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `translateX(-110px) scale(${videoScale})`,
          transformOrigin: 'left center',
        }}
      >
        <OffthreadVideo
          src={staticFile('video_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Contrast gradient: darkens right side for the card stack while preserving the man on the left */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(90deg, rgba(11,15,25,0.25) 0%, rgba(11,15,25,0.65) 42%, rgba(11,15,25,0.94) 75%, rgba(11,15,25,0.98) 100%)',
          }}
        />
        {/* Soft top gradient */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 280,
            background: 'linear-gradient(180deg, rgba(11,15,25,0.85) 0%, rgba(11,15,25,0) 100%)',
          }}
        />
      </div>

      {/* Top Header Badge — Aligned with right-docked content to preserve free space on left */}
      <div
        style={{
          position: 'absolute',
          top: 184,
          left: 450,
          right: THEME.safeZone.left,
          display: 'flex',
          justifyContent: 'flex-start',
          transform: `scale(${headerSpring}) translateY(${(1 - headerSpring) * -30}px)`,
          opacity: headerSpring,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            background: 'rgba(17, 24, 39, 0.94)',
            border: `1.5px solid ${THEME.colors.fundoCardBorder}`,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: THEME.colors.destaqueCyan,
              boxShadow: `0 0 10px ${THEME.colors.destaqueCyan}`,
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
            Como Funciona
          </span>
        </div>
      </div>

      {/* Title above cards (y: 260) */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: 450,
          right: THEME.safeZone.left,
          transform: `scale(${headerSpring})`,
          opacity: headerSpring,
        }}
      >
        <span
          style={{
            fontFamily,
            fontSize: 44,
            fontWeight: 900,
            color: THEME.colors.texto,
            textTransform: 'uppercase',
            letterSpacing: 1,
            lineHeight: 1.15,
            textShadow: '0 4px 16px rgba(0,0,0,0.9)',
          }}
        >
          O Método Traz:
        </span>
      </div>

      {/* 4 Sequential Step Cards — Positioned in the right column (x: 450 to 1020), 0% overlap with face */}
      <div
        style={{
          position: 'absolute',
          top: 340,
          left: 450,
          right: THEME.safeZone.left,
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        {steps.map((step, idx) => {
          const isEntered = frame >= step.frameIn;
          const cardSpring = spring({
            frame: frame - step.frameIn,
            fps,
            config: {damping: 14, stiffness: 130},
          });

          const nextStep = steps[idx + 1];
          const isCurrentlyActive =
            isEntered && (!nextStep || frame < nextStep.frameIn);

          if (!isEntered) return null;

          return (
            <div
              key={idx}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '20px 22px',
                borderRadius: 20,
                background: isCurrentlyActive
                  ? 'rgba(15, 23, 42, 0.96)'
                  : 'rgba(15, 23, 42, 0.82)',
                border: isCurrentlyActive
                  ? `2px solid ${THEME.colors.destaqueCyan}`
                  : '1.5px solid rgba(255, 255, 255, 0.1)',
                boxShadow: isCurrentlyActive
                  ? '0 12px 36px rgba(37,99,235,0.45)'
                  : '0 8px 24px rgba(0,0,0,0.5)',
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                transform: `scale(${cardSpring}) translateX(${(1 - cardSpring) * 60}px)`,
                opacity: cardSpring,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <div
                  style={{
                    padding: '4px 12px',
                    borderRadius: 8,
                    background: isCurrentlyActive
                      ? THEME.colors.marca
                      : 'rgba(255, 255, 255, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 900,
                      color: '#FFFFFF',
                    }}
                  >
                    {step.num}
                  </span>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '4px 12px',
                    borderRadius: 8,
                    background: isCurrentlyActive
                      ? 'rgba(56, 189, 248, 0.2)'
                      : 'rgba(255, 255, 255, 0.06)',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 32,
                      fontWeight: 700,
                      color: isCurrentlyActive ? THEME.colors.destaqueCyan : THEME.colors.textoMuted,
                    }}
                  >
                    {step.badge}
                  </span>
                </div>
              </div>

              {/* Step Title */}
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: isCurrentlyActive ? '#FFFFFF' : THEME.colors.textoSecundario,
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                  lineHeight: 1.2,
                }}
              >
                {step.title}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
