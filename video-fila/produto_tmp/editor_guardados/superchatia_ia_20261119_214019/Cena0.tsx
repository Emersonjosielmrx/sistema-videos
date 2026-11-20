import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena0Props {
  fontFamily: string;
  destaque: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily, destaque}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Push-in ágil de câmera logo nos primeiros 2 segundos (0s a 2s) para prender no feed
  const cameraScale = interpolate(frame, [0, 60, 147], [1.0, 1.07, 1.12], {
    extrapolateRight: 'clamp',
  });

  // Slow scale contínuo do sticker de pergunta
  const stickerScale = interpolate(frame, [0, 147], [0.98, 1.02], {
    extrapolateRight: 'clamp',
  });

  // Entrada ágil do sticker via spring
  const stickerEntrance = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Acendimento neon imediato de 'SEM COMPLICAÇÃO?' aos 0.5s (frame 15) conforme exigência de gancho
  const punchSpring = spring({
    frame: frame - 15,
    fps,
    config: {damping: 12, stiffness: 190},
  });

  // Micro-animações contínuas: flutuação suave e pulsação de glow para dinamismo constante
  const floatY = Math.sin(frame * 0.12) * 5;
  const glowPulse = 18 + Math.sin(frame * 0.16) * 10;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#070A12',
        fontFamily,
      }}
    >
      {/* Apresentador nítido e iluminado, reposicionado com respiro generoso entre cabeça e cartão */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(42px) scale(${cameraScale})`,
          transformOrigin: '50% 35%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />

        {/* Gradiente sutil no topo para contraste do sticker superior */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 440,
            background:
              'linear-gradient(180deg, rgba(7, 10, 18, 0.85) 0%, rgba(7, 10, 18, 0.35) 60%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Gradiente sutil na base para a legenda karaokê */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 520,
            background:
              'linear-gradient(0deg, rgba(7, 10, 18, 0.9) 0%, rgba(7, 10, 18, 0.3) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Terço superior: Sticker flutuante compacto e bem encaixado (top: 155, altura reduzida) */}
      {/* Mais de 80px de respiro livre acima do cabelo do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `translateY(${floatY}px) scale(${Math.max(0, stickerEntrance) * stickerScale})`,
          opacity: Math.min(1, Math.max(0, stickerEntrance)),
          zIndex: 20,
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            backgroundColor: '#0F172A',
            border: '2px solid rgba(91, 108, 255, 0.65)',
            borderRadius: 24,
            padding: '16px 28px 18px',
            boxShadow: `0 16px 40px rgba(0, 0, 0, 0.85), 0 0 ${glowPulse}px rgba(91, 108, 255, 0.4)`,
            boxSizing: 'border-box',
            textAlign: 'center',
          }}
        >
          {/* Header do sticker estilo Stories/Reels */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '4px 18px',
              backgroundColor: 'rgba(91, 108, 255, 0.18)',
              border: '1px solid rgba(91, 108, 255, 0.4)',
              borderRadius: 999,
              marginBottom: 10,
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: destaque,
                boxShadow: `0 0 8px ${destaque}`,
              }}
            />
            <span
              style={{
                color: '#E0E7FF',
                fontSize: 32,
                fontWeight: 800,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              Pergunta do Cliente
            </span>
          </div>

          {/* Texto principal da pergunta */}
          <h1
            style={{
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              lineHeight: 1.2,
              margin: '0 0 10px 0',
              textWrap: 'balance',
            }}
          >
            Minha equipe vai conseguir usar o sistema...
          </h1>

          {/* Slot de destaque SEM COMPLICAÇÃO? com entrada imediata aos 0.5s (frame 15) e neon glow */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: 58,
            }}
          >
            {frame >= 15 ? (
              <div
                style={{
                  transform: `scale(${Math.max(0, punchSpring)}) rotate(-1deg)`,
                  opacity: Math.min(1, Math.max(0, punchSpring)),
                  backgroundColor: destaque,
                  borderRadius: 14,
                  padding: '8px 30px',
                  boxShadow: `0 8px 24px rgba(91, 108, 255, 0.8), 0 0 ${glowPulse}px ${destaque}`,
                  border: '2px solid rgba(255, 255, 255, 0.65)',
                }}
              >
                <span
                  style={{
                    fontSize: 44,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    letterSpacing: '0.03em',
                    textTransform: 'uppercase',
                    textShadow: '0 3px 10px rgba(0,0,0,0.4)',
                  }}
                >
                  SEM COMPLICAÇÃO?
                </span>
              </div>
            ) : (
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#F1F5F9',
                }}
              >
                sem complicação?
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
