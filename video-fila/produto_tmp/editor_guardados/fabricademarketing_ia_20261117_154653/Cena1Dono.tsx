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
import {CORES} from './constants';

interface Cena1Props {
  fontFamily: string;
}

export const Cena1Dono: React.FC<Cena1Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Zoom lento e constante no vídeo (1.00 -> 1.05)
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Fade out suave na transição final (frames 232-245)
  const cenaOpacity = interpolate(frame, [232, 245], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Topo: Rótulo "01. A ROTINA" (entra no frame 6)
  const rotuloSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Fase 1: Atendimento presencial (frames 0 a 115)
  const fase1Entrada = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 140},
  });
  const fase1Saida = interpolate(frame, [110, 118], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fase1Visivel = frame < 120;

  // Fase 2: Comentários esperando (entra no frame 118 ~ 9.28s absoluto)
  const fase2Entrada = spring({
    frame: frame - 118,
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const fase2Visivel = frame >= 115;

  return (
    <AbsoluteFill style={{opacity: cenaOpacity, overflow: 'hidden'}}>
      {/* Vídeo do apresentador em tela cheia com push suave */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 45%',
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

      {/* Gradiente sutil estritamente no topo (y=0 a 280) para dar contraste aos badges sem escurecer o rosto (rosto começa em y=490) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 320,
          background:
            'linear-gradient(180deg, rgba(11, 15, 25, 0.8) 0%, rgba(11, 15, 25, 0.4) 70%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOP SAFE ZONE: y = 165 a 340 (respiro de mais de 150 px até o topo do cabelo em y=490) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 50,
        }}
      >
        {/* Rótulo Oficial da Cena: "01. A ROTINA" */}
        <div
          style={{
            opacity: rotuloSpring,
            transform: `translateY(${(1 - rotuloSpring) * -15}px)`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 22px',
            borderRadius: 24,
            backgroundColor: 'rgba(17, 24, 39, 0.94)',
            border: `1.5px solid ${CORES.bordaCard}`,
            boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: CORES.marca,
              boxShadow: `0 0 8px ${CORES.marca}`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: CORES.textoPrincipal,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            01. A ROTINA
          </span>
        </div>

        {/* Bloco Fase 1: Atendendo Cliente na Empresa */}
        {fase1Visivel && (
          <div
            style={{
              opacity: fase1Entrada * fase1Saida,
              transform: `scale(${0.92 + fase1Entrada * 0.08})`,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              backgroundColor: 'rgba(17, 24, 39, 0.95)',
              borderRadius: 20,
              padding: '14px 26px',
              border: '1.5px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            }}
          >
            <span style={{fontSize: 34}}>💼</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 0.5,
              }}
            >
              Atendendo cliente presencial
            </span>
          </div>
        )}

        {/* Bloco Fase 2: Comentários Esperando */}
        {fase2Visivel && (
          <div
            style={{
              opacity: Math.max(0, Math.min(1, fase2Entrada)),
              transform: `scale(${0.92 + fase2Entrada * 0.08})`,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              backgroundColor: 'rgba(31, 20, 28, 0.95)',
              borderRadius: 20,
              padding: '14px 26px',
              border: '1.5px solid rgba(244, 114, 182, 0.6)',
              boxShadow: `0 8px 24px rgba(0,0,0,0.6), 0 0 20px ${CORES.marcaGlow}`,
            }}
          >
            <span style={{fontSize: 34}}>⏳</span>
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
              }}
            >
              Comentários ficavam esperando
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
