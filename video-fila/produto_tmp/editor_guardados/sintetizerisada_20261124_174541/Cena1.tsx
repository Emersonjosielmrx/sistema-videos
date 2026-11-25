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

interface Cena1Props {
  fontFamily: string;
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no vídeo do apresentador (zoom 1.00 -> 1.06)
  const videoScale = interpolate(frame, [0, 241], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge superior (aos 0.2s = frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título 1 (de 0s a 3.5s / 4.94s a 8.5s do vídeo total)
  const title1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título 2 (a partir de 3.5s = frame 105, sincronizado com "ninguém queria instalar mais um aplicativo")
  const title2Spring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Microdinâmica constante nos textos
  const pulseScale = 1 + Math.sin(frame / 10) * 0.015;

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Vídeo do apresentador mudo em tela cheia com leve zoom dinâmico */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
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
        {/* Vinheta superior muito suave para garantir contraste do texto sem escurecer o rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 380,
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.4) 65%, transparent 100%)',
          }}
        />
      </div>

      {/* Conteúdo Superior na Safe Zone (y: 156 a 250) — Rosto 100% livre com >80px de respiro */}
      <div
        style={{
          position: 'absolute',
          top: 156,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 8,
          zIndex: 50,
        }}
      >
        {/* Badge de Contexto: O Problema */}
        {frame >= 6 && (
          <div
            style={{
              transform: `scale(${Math.max(0, badgeSpring)})`,
              opacity: Math.min(1, badgeSpring),
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '4px 16px',
              borderRadius: 20,
              backgroundColor: '#0B0D13',
              border: '1.5px solid #EF4444',
              boxShadow: '0 4px 14px rgba(0,0,0,0.8)',
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: '#EF4444',
                boxShadow: '0 0 8px #EF4444',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 28,
                fontWeight: 800,
                color: '#FFFFFF',
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              O PROBLEMA
            </span>
          </div>
        )}

        {/* Bloco 1 de Título (Frame 10 até 105) */}
        {frame >= 10 && frame < 105 && (
          <div
            style={{
              transform: `scale(${Math.max(0, title1Spring) * pulseScale})`,
              opacity: Math.min(1, title1Spring),
              backgroundColor: 'rgba(11, 13, 19, 0.94)',
              border: '1.5px solid rgba(255, 255, 255, 0.15)',
              padding: '8px 24px',
              borderRadius: 14,
              boxShadow: '0 8px 24px rgba(0,0,0,0.85)',
              textAlign: 'center',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.1,
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
              }}
            >
              PERDENDO CLIENTES POR APLICATIVO
            </span>
          </div>
        )}

        {/* Bloco 2 de Título (Frame 105 em diante — sincronizado com "ninguém queria instalar mais um aplicativo") */}
        {frame >= 105 && (
          <div
            style={{
              transform: `scale(${Math.max(0, title2Spring) * pulseScale})`,
              opacity: Math.min(1, title2Spring),
              backgroundColor: 'rgba(11, 13, 19, 0.94)',
              border: '1.5px solid #FFA94D',
              padding: '8px 24px',
              borderRadius: 14,
              boxShadow: '0 8px 24px rgba(0,0,0,0.85)',
              textAlign: 'center',
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#FFA94D',
                lineHeight: 1.1,
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
              }}
            >
              NINGUÉM QUER INSTALAR MAIS UM APP
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
