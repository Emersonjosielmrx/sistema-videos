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

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  // Push-in suave com compensação para manter cabeça livre de qualquer elemento
  const videoScale = interpolate(frame, [0, durationInFrames], [1.1, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Fade out nos últimos 10 frames para transição fluida com Cena 2
  const opacity = interpolate(
    frame,
    [durationInFrames - 10, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // 1. Badge superior "O PROBLEMA"
  const headerSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Badges escalonados sincronizados com a fala dos profissionais
  // 8.13s -> frame 94 ("designer")
  const designerSpring = spring({
    frame: frame - 94,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 8.99s -> frame 119 ("redator")
  const redatorSpring = spring({
    frame: frame - 119,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 9.81s -> frame 144 ("editor de vídeo")
  const editorSpring = spring({
    frame: frame - 144,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // 11.29s -> frame 188 ("Cada um num canto, tudo desencontrado")
  const desencontradoSpring = spring({
    frame: frame - 188,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        opacity,
      }}
    >
      {/* Vídeo do Dono com zoom suave e offset seguro para liberar o topo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translateY(85px)`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Degradê sutil no topo para proteger contraste */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 320,
          background:
            'linear-gradient(180deg, rgba(17, 24, 39, 0.8) 0%, rgba(17, 24, 39, 0.4) 70%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Faixa superior segura exclusiva em linha única (y: 165 a 225) */}
      {/* Cabeça do apresentador inicia em y~300, garantindo > 70px de respiro absoluto */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          fontFamily,
          pointerEvents: 'none',
          height: 60,
        }}
      >
        {/* Fase 1: Rótulo Inicial "O PROBLEMA" (frames 0 a 93) */}
        {frame < 94 && (
          <div
            style={{
              opacity: headerSpring,
              transform: `scale(${headerSpring})`,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 28px',
              borderRadius: 24,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '1.5px solid rgba(245, 158, 11, 0.55)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
            }}
          >
            <span style={{fontSize: 28}}>⚠️</span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#F59E0B',
                letterSpacing: '1px',
                textTransform: 'uppercase',
              }}
            >
              O PROBLEMA
            </span>
          </div>
        )}

        {/* Fase 2: Profissionais na mesma linha única (frames 94 a 187) */}
        {frame >= 94 && frame < 188 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: 10,
              maxWidth: 960,
            }}
          >
            {frame >= 94 && (
              <div
                style={{
                  opacity: designerSpring,
                  transform: `scale(${designerSpring})`,
                  padding: '8px 18px',
                  borderRadius: 16,
                  background: 'rgba(17, 24, 39, 0.95)',
                  border: '1.5px solid rgba(255, 255, 255, 0.25)',
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 700,
                  boxShadow: '0 6px 18px rgba(0, 0, 0, 0.6)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span>🎨</span>
                <span>Designer</span>
              </div>
            )}

            {frame >= 119 && (
              <div
                style={{
                  opacity: redatorSpring,
                  transform: `scale(${redatorSpring})`,
                  padding: '8px 18px',
                  borderRadius: 16,
                  background: 'rgba(17, 24, 39, 0.95)',
                  border: '1.5px solid rgba(255, 255, 255, 0.25)',
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 700,
                  boxShadow: '0 6px 18px rgba(0, 0, 0, 0.6)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span>✍️</span>
                <span>Redator</span>
              </div>
            )}

            {frame >= 144 && (
              <div
                style={{
                  opacity: editorSpring,
                  transform: `scale(${editorSpring})`,
                  padding: '8px 18px',
                  borderRadius: 16,
                  background: 'rgba(17, 24, 39, 0.95)',
                  border: '1.5px solid rgba(255, 255, 255, 0.25)',
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 700,
                  boxShadow: '0 6px 18px rgba(0, 0, 0, 0.6)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <span>🎬</span>
                <span>Editor</span>
              </div>
            )}
          </div>
        )}

        {/* Fase 3: Conclusão dramática em linha única (frames 188 a 246) */}
        {frame >= 188 && (
          <div
            style={{
              opacity: desencontradoSpring,
              transform: `scale(${interpolate(desencontradoSpring, [0, 1], [0.85, 1])})`,
              padding: '10px 28px',
              borderRadius: 20,
              background: 'rgba(17, 24, 39, 0.96)',
              border: '2px solid rgba(239, 68, 68, 0.8)',
              boxShadow: '0 10px 28px rgba(239, 68, 68, 0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span style={{fontSize: 28}}>✕</span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#F87171',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              Cada um num canto • Desencontrado
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
