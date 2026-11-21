import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './constants';

interface Cena1Props {
  fontFamily: string;
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Whip-zoom settle transition from Cena 0 (frames 0 to 18)
  const settleScale = interpolate(frame, [0, 18], [1.14, 1.0], {
    extrapolateRight: 'clamp',
  });

  // Presenter video continuous subtle zoom
  const videoScale = interpolate(frame, [0, 241], [1.05, 1.09], {
    extrapolateRight: 'clamp',
  });

  // Top Bar entrance
  const barSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Stage transitions sincronizadas com a fala:
  // Stage 0: 0 to 54 (antes do áudio)
  // Stage 1: 55 to 117 ("Muitas pessoas chegam na página")
  // Stage 2: 118 to 154 ("não leem o texto")
  // Stage 3: 155 to 241 ("e saem sem comprar nada.")
  const currentStage = frame < 55 ? 0 : frame < 118 ? 1 : frame < 155 ? 2 : 3;

  // Micro-float for top bar
  const barFloatY = Math.sin(frame * 0.08) * 3;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0B0D13',
        fontFamily,
        transform: `scale(${settleScale})`,
        transformOrigin: 'center 40%',
      }}
    >
      {/* Fullscreen Presenter Video - shifted down to keep head comfortably below y=360 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(40px) scale(${videoScale})`,
          transformOrigin: 'center 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: 1080,
            height: 1920,
            objectFit: 'cover',
          }}
        />
        {/* Subtle top darkening exclusively under the top bar for maximum contrast */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 300,
            background:
              'linear-gradient(180deg, rgba(11, 13, 19, 0.85) 0%, rgba(11, 13, 19, 0.35) 75%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Unified Sleek Top Bar (y = 172, height = 76px, ends at y = 248) -> Head at y=360+ gives >110px respiro */}
      <div
        style={{
          position: 'absolute',
          top: 172,
          left: 60,
          right: 60,
          height: 76,
          borderRadius: 22,
          background: 'rgba(11, 13, 19, 0.95)',
          border: '2px solid rgba(255, 255, 255, 0.18)',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.85)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 20px',
          transform: `scale(${Math.max(0, barSpring)}) translateY(${barFloatY}px)`,
          opacity: Math.max(0, barSpring),
          zIndex: 40,
        }}
      >
        {/* Left Badge: 01 • O PROBLEMA */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 18px',
            borderRadius: 14,
            background: 'rgba(239, 68, 68, 0.25)',
            border: '1.5px solid #EF4444',
            flexShrink: 0,
            whiteSpace: 'nowrap',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              textTransform: 'uppercase',
              letterSpacing: 1,
              whiteSpace: 'nowrap',
            }}
          >
            01 • O PROBLEMA
          </span>
        </div>

        {/* Right Content: Topico Ativo sempre em 100% contraste branco sobre container */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            minWidth: 420,
            height: 52,
            flexShrink: 0,
            whiteSpace: 'nowrap',
          }}
        >
          {currentStage === 0 && (
            <span
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
                whiteSpace: 'nowrap',
              }}
            >
              VISITANTES NA PÁGINA
            </span>
          )}

          {currentStage === 1 && (
            <div style={{display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0}}>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}
              >
                CHEGAM NA PÁGINA
              </span>
            </div>
          )}

          {/* Stage 2: NÃO LEEM O TEXTO - Garantido 100% branco nítido com badge contrastante (corrige q05) */}
          {currentStage === 2 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                flexShrink: 0,
                background: 'rgba(239, 68, 68, 0.3)',
                border: '1.5px solid #EF4444',
                padding: '6px 16px',
                borderRadius: 12,
              }}
            >
              <span style={{fontSize: 28}}>⚠️</span>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                  textShadow: '0 2px 8px rgba(0,0,0,0.8)',
                }}
              >
                NÃO LEEM O TEXTO
              </span>
            </div>
          )}

          {currentStage === 3 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                flexShrink: 0,
                background: 'rgba(239, 68, 68, 0.25)',
                border: '1.5px solid #EF4444',
                padding: '6px 16px',
                borderRadius: 12,
              }}
            >
              <span style={{fontSize: 28}}>❌</span>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}
              >
                SAEM SEM COMPRAR
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
