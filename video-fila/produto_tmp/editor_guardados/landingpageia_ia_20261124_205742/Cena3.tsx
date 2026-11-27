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
  const {fps, durationInFrames} = useVideoConfig();

  // Push-in contínuo no vídeo do dono com offset para proteger respiro da cabeça
  const videoScale = interpolate(frame, [0, durationInFrames], [1.1, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Fade out nos últimos 10 frames
  const opacity = interpolate(
    frame,
    [durationInFrames - 10, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // 1. Badge superior "O RESULTADO" (~frame 6)
  const headerSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Pill "Página de vendas no ar" (~23.62s / frame 52)
  const pill1Spring = spring({
    frame: frame - 52,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // 3. Pill "Vídeo apresentando o produto" (~25.86s / frame 119)
  const pill2Spring = spring({
    frame: frame - 119,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // 4. Card de Conversão "VISITA ➔ CLIENTE" (~27.98s / frame 183)
  const conversionSpring = spring({
    frame: frame - 183,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Pulso do card de conversão
  const convPulse = Math.sin((frame - 183) / 6) * 0.03;

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
      {/* Vídeo do Dono (Resultado) com zoom sutil e offset seguro */}
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
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Degradê superior sutil para proteger contraste sem cobrir o rosto */}
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

      {/* Faixa superior exclusiva em linha única (y: 165 a 225) */}
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
        {/* Fase 1: Rótulo Inicial "O RESULTADO" (frames 0 a 51) */}
        {frame < 52 && (
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
              border: '1.5px solid rgba(16, 185, 129, 0.6)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
            }}
          >
            <span style={{fontSize: 28}}>✨</span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: '#34D399',
                letterSpacing: '1px',
                textTransform: 'uppercase',
              }}
            >
              O RESULTADO
            </span>
          </div>
        )}

        {/* Fase 2: Página Pronta (frames 52 a 118) */}
        {frame >= 52 && frame < 119 && (
          <div
            style={{
              opacity: pill1Spring,
              transform: `scale(${pill1Spring})`,
              padding: '10px 24px',
              borderRadius: 20,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '1.5px solid rgba(245, 158, 11, 0.5)',
              color: '#FFFFFF',
              fontSize: 34,
              fontWeight: 700,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.65)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span style={{fontSize: 28}}>🚀</span>
            <span>Página de Vendas no Ar</span>
          </div>
        )}

        {/* Fase 3: Vídeo Apresenta (frames 119 a 182) */}
        {frame >= 119 && frame < 183 && (
          <div
            style={{
              opacity: pill2Spring,
              transform: `scale(${pill2Spring})`,
              padding: '10px 24px',
              borderRadius: 20,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '1.5px solid rgba(245, 158, 11, 0.5)',
              color: '#FFFFFF',
              fontSize: 34,
              fontWeight: 700,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.65)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span style={{fontSize: 28}}>🎥</span>
            <span>Vídeo Apresenta o Produto</span>
          </div>
        )}

        {/* Fase 4: Conversão Final "Visita ➔ Cliente" (frames 183 a 245) */}
        {frame >= 183 && (
          <div
            style={{
              opacity: conversionSpring,
              transform: `scale(${interpolate(conversionSpring, [0, 1], [0.85, 1]) + convPulse})`,
              padding: '10px 30px',
              borderRadius: 22,
              background: 'rgba(17, 24, 39, 0.96)',
              border: '2px solid rgba(16, 185, 129, 0.85)',
              boxShadow: '0 10px 30px rgba(16, 185, 129, 0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <span
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#F3F4F6',
                textTransform: 'uppercase',
                letterSpacing: '1px',
              }}
            >
              Visita
            </span>
            <span
              style={{
                fontSize: 36,
                color: '#F59E0B',
                fontWeight: 900,
              }}
            >
              ➔
            </span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#34D399',
                textTransform: 'uppercase',
                letterSpacing: '1px',
              }}
            >
              Cliente
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
