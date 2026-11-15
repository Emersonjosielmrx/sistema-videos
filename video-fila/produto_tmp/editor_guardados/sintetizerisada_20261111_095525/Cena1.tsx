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
  cores: {
    marca: string;
    destaque: string;
    apoio: string;
    fundo_escuro: string;
  };
};

export const Cena1: React.FC<Props> = ({fontFamily, cores}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom suave e contínuo no vídeo do dono (1.0 -> 1.06)
  const videoScale = interpolate(frame, [0, 230], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Badge fixo "O PROBLEMA" no topo
  const badgeAnim = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // FASE 1: 0 a 70 frames (~4.82s a 7.18s) - "Remarcações de última hora"
  const fase1Entrada = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const fase1Saida = interpolate(frame, [65, 71], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fase1Visivel = frame < 72;

  // FASE 2: 72 a 122 frames (~7.22s a 8.88s) - "Tomavam meu tempo"
  const fase2Entrada = spring({
    frame: frame - 73,
    fps,
    config: {damping: 12, stiffness: 140},
  });
  const fase2Saida = interpolate(frame, [117, 123], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fase2Visivel = frame >= 72 && frame < 124;

  // FASE 3: 124 a 230 frames (~8.95s a 12.48s) - "Vários horários vagos no meu dia"
  const fase3Entrada = spring({
    frame: frame - 124,
    fps,
    config: {damping: 12, stiffness: 130},
  });
  const fase3Visivel = frame >= 124;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: cores.fundo_escuro,
        overflow: 'hidden',
      }}
    >
      {/* Vídeo do Dono com zoom suave contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 35%',
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

      {/* Gradiente sutil no topo para máxima legibilidade sem tocar no rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.92) 0%, rgba(15, 23, 42, 0.75) 60%, rgba(15, 23, 42, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo estritamente no topo: y=160 a y=420 (rosto do apresentador totalmente livre) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          zIndex: 10,
        }}
      >
        {/* Badge do Rótulo "O PROBLEMA" */}
        <div
          style={{
            opacity: badgeAnim,
            transform: `scale(${badgeAnim})`,
            backgroundColor: 'rgba(17, 24, 39, 0.92)',
            border: `2px solid ${cores.destaque}`,
            borderRadius: 24,
            padding: '8px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            boxShadow: `0 4px 16px rgba(0,0,0,0.6), 0 0 12px rgba(255, 169, 77, 0.3)`,
            marginBottom: 16,
          }}
        >
          <span style={{fontSize: 34}}>⚠️</span>
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: cores.destaque,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            O Problema Real
          </span>
        </div>

        {/* Título Fase 1: Remarcações de Última Hora */}
        {fase1Visivel && (
          <div
            style={{
              opacity: fase1Entrada * fase1Saida,
              transform: `translateY(${interpolate(fase1Entrada, [0, 1], [25, 0])}px) scale(${interpolate(fase1Saida, [0, 1], [0.94, 1])})`,
              backgroundColor: 'rgba(17, 24, 39, 0.88)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: 18,
              padding: '12px 28px',
              textAlign: 'center',
              boxShadow: '0 8px 25px rgba(0,0,0,0.5)',
            }}
          >
            <span
              style={{
                fontSize: 50,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                lineHeight: 1.2,
                textShadow: '0 3px 10px rgba(0,0,0,0.9)',
              }}
            >
              Remarcações de Última Hora
            </span>
          </div>
        )}

        {/* Título Fase 2: Tomavam Meu Tempo */}
        {fase2Visivel && (
          <div
            style={{
              opacity: fase2Entrada * fase2Saida,
              transform: `translateY(${interpolate(fase2Entrada, [0, 1], [25, 0])}px) scale(${interpolate(fase2Saida, [0, 1], [0.94, 1])})`,
              backgroundColor: 'rgba(17, 24, 39, 0.88)',
              border: `2px solid ${cores.destaque}`,
              borderRadius: 18,
              padding: '12px 28px',
              textAlign: 'center',
              boxShadow: `0 8px 25px rgba(0,0,0,0.5), 0 0 15px rgba(255, 169, 77, 0.25)`,
            }}
          >
            <span
              style={{
                fontSize: 52,
                fontWeight: 900,
                color: cores.destaque,
                textTransform: 'uppercase',
                lineHeight: 1.2,
              }}
            >
              Tomavam Todo o Meu Tempo
            </span>
          </div>
        )}

        {/* Título Fase 3: Vários Horários Vagos */}
        {fase3Visivel && (
          <div
            style={{
              opacity: fase3Entrada,
              transform: `translateY(${interpolate(fase3Entrada, [0, 1], [25, 0])}px)`,
              backgroundColor: 'rgba(17, 24, 39, 0.9)',
              border: '2px solid rgba(239, 68, 68, 0.7)',
              borderRadius: 18,
              padding: '12px 28px',
              textAlign: 'center',
              boxShadow: '0 8px 25px rgba(0,0,0,0.6), 0 0 15px rgba(239, 68, 68, 0.2)',
            }}
          >
            <span
              style={{
                fontSize: 48,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                lineHeight: 1.2,
                whiteSpace: 'nowrap',
              }}
            >
              Vários Horários Vagos no Dia
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
