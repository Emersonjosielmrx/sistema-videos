import React from 'react';
import {
  AbsoluteFill,
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

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Jump-cut com punch-in digital (1.15x a 1.18x): intensidade na explicação e quebra de monotonia
  const videoScale = interpolate(frame, [0, 246], [1.15, 1.18], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave nos últimos 10 frames
  const sceneOpacity = interpolate(frame, [236, 246], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Header "02 · COMO FUNCIONA"
  const headerSpring = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Gatilhos de pop escalonados para cada verbo da fala
  // Etapa 1: "AGENDA" (frame 51)
  const step1Spring = spring({
    frame: frame - 51,
    fps,
    config: {damping: 10, stiffness: 180},
  });

  // Etapa 2: "CONFIRMA" (frame 64)
  const step2Spring = spring({
    frame: frame - 64,
    fps,
    config: {damping: 10, stiffness: 180},
  });

  // Etapa 3: "REAGENDA" (frame 97)
  const step3Spring = spring({
    frame: frame - 97,
    fps,
    config: {damping: 10, stiffness: 180},
  });

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, overflow: 'hidden'}}>
      {/* Vídeo do dono em plano mais fechado (punch-in 1.15x para corte de ritmo) */}
      <AbsoluteFill style={{transform: `scale(${videoScale})`}}>
        <OffthreadVideo
          src={staticFile('dono_2.mp4')}
          muted
          style={{width: '1080px', height: '1920px', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Gradiente sutil no topo para contraste absoluto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 360,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.82) 0%, rgba(15, 23, 42, 0.40) 60%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Topo informativo limpo (y=152 a 285) com respiro amplo (>130px) acima da cabeça */}
      <div
        style={{
          position: 'absolute',
          top: 152,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
        }}
      >
        {/* Rótulo da cena */}
        <div
          style={{
            transform: `scale(${Math.max(0, headerSpring)})`,
            opacity: headerSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '7px 20px',
            borderRadius: 999,
            background: 'rgba(31, 41, 55, 0.90)',
            border: '1.5px solid rgba(255, 169, 77, 0.5)',
            boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FFA94D',
              textTransform: 'uppercase',
              letterSpacing: 1.2,
            }}
          >
            02 · Como Funciona
          </span>
        </div>

        {/* Grade sequencial de 3 etapas que acendem uma a uma na fala com alto contraste */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 12,
            width: '100%',
            maxWidth: 960,
          }}
        >
          {/* 1. AGENDA */}
          {(() => {
            const isSpeaking = frame >= 51 && frame < 64;
            const isConfirmed = frame >= 64;
            const scaleBump = frame >= 51 ? 1 + 0.05 * Math.max(0, step1Spring) : 1;
            return (
              <div
                style={{
                  flex: 1,
                  transform: `scale(${scaleBump})`,
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  padding: '12px 8px',
                  borderRadius: 16,
                  background: isSpeaking
                    ? '#FFA94D'
                    : isConfirmed
                    ? 'rgba(31, 41, 55, 0.95)'
                    : 'rgba(31, 41, 55, 0.88)',
                  border: isSpeaking
                    ? '2px solid #FFE8CC'
                    : isConfirmed
                    ? '2px solid #22C55E'
                    : '1.5px solid rgba(255,255,255,0.25)',
                  boxShadow: isSpeaking
                    ? '0 8px 24px rgba(255, 169, 77, 0.65)'
                    : isConfirmed
                    ? '0 4px 16px rgba(34, 197, 94, 0.3)'
                    : 'none',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: isSpeaking
                      ? '#1F2937'
                      : isConfirmed
                      ? '#22C55E'
                      : '#F8FAFC',
                    textTransform: 'uppercase',
                    textAlign: 'center',
                  }}
                >
                  {isConfirmed ? '✓ 1. Agenda' : '1. Agenda'}
                </span>
              </div>
            );
          })()}

          {/* 2. CONFIRMA */}
          {(() => {
            const isSpeaking = frame >= 64 && frame < 97;
            const isConfirmed = frame >= 97;
            const scaleBump = frame >= 64 ? 1 + 0.05 * Math.max(0, step2Spring) : 1;
            return (
              <div
                style={{
                  flex: 1,
                  transform: `scale(${scaleBump})`,
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  padding: '12px 8px',
                  borderRadius: 16,
                  background: isSpeaking
                    ? '#FFA94D'
                    : isConfirmed
                    ? 'rgba(31, 41, 55, 0.95)'
                    : 'rgba(31, 41, 55, 0.88)',
                  border: isSpeaking
                    ? '2px solid #FFE8CC'
                    : isConfirmed
                    ? '2px solid #22C55E'
                    : '1.5px solid rgba(255,255,255,0.25)',
                  boxShadow: isSpeaking
                    ? '0 8px 24px rgba(255, 169, 77, 0.65)'
                    : isConfirmed
                    ? '0 4px 16px rgba(34, 197, 94, 0.3)'
                    : 'none',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: isSpeaking
                      ? '#1F2937'
                      : isConfirmed
                      ? '#22C55E'
                      : '#F8FAFC',
                    textTransform: 'uppercase',
                    textAlign: 'center',
                  }}
                >
                  {isConfirmed ? '✓ 2. Confirma' : '2. Confirma'}
                </span>
              </div>
            );
          })()}

          {/* 3. REAGENDA */}
          {(() => {
            const isSpeaking = frame >= 97 && frame < 130;
            const isConfirmed = frame >= 130;
            const scaleBump = frame >= 97 ? 1 + 0.05 * Math.max(0, step3Spring) : 1;
            return (
              <div
                style={{
                  flex: 1,
                  transform: `scale(${scaleBump})`,
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  padding: '12px 8px',
                  borderRadius: 16,
                  background: isSpeaking
                    ? '#FFA94D'
                    : isConfirmed
                    ? 'rgba(31, 41, 55, 0.95)'
                    : 'rgba(31, 41, 55, 0.88)',
                  border: isSpeaking
                    ? '2px solid #FFE8CC'
                    : isConfirmed
                    ? '2px solid #22C55E'
                    : '1.5px solid rgba(255,255,255,0.25)',
                  boxShadow: isSpeaking
                    ? '0 8px 24px rgba(255, 169, 77, 0.65)'
                    : isConfirmed
                    ? '0 4px 16px rgba(34, 197, 94, 0.3)'
                    : 'none',
                }}
              >
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 900,
                    color: isSpeaking
                      ? '#1F2937'
                      : isConfirmed
                      ? '#22C55E'
                      : '#F8FAFC',
                    textTransform: 'uppercase',
                    textAlign: 'center',
                  }}
                >
                  {isConfirmed ? '✓ 3. Reagenda' : '3. Reagenda'}
                </span>
              </div>
            );
          })()}
        </div>
      </div>
    </AbsoluteFill>
  );
};
