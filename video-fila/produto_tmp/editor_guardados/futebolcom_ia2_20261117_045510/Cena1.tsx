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

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Push-in suave no vídeo do apresentador (1.00 -> 1.05)
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge do topo (y ~ 170)
  const rotuloSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Card 1: "ENVIAVA ARQUIVO EM PDF PESADO" (~frame 8 ao frame 100)
  const card1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Card 2: "CLIENTE DESISTIA ANTES DE ABRIR" (entra a partir de ~frame 100)
  const card2Spring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  // Movimento sutil para não ficar estático
  const microFloat = Math.sin(frame / 14) * 4;

  return (
    <AbsoluteFill style={{backgroundColor: '#000000', overflow: 'hidden'}}>
      {/* Vídeo do dono em tela cheia com leve push-in */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 40%',
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
        {/* Vinheta superior suave para legibilidade dos cards no topo sem escurecer o rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(180deg, rgba(15, 2, 5, 0.85) 0%, rgba(15, 2, 5, 0.45) 60%, rgba(15, 2, 5, 0) 100%)',
          }}
        />
        {/* Vinheta inferior sutil para a legenda */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 420,
            background:
              'linear-gradient(0deg, rgba(0, 0, 0, 0.75) 0%, rgba(0, 0, 0, 0) 100%)',
          }}
        />
      </div>

      {/* Faixa superior (Safe Zone: y=160 a 420, estritamente acima da cabeça do apresentador) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${microFloat}px)`,
        }}
      >
        {/* Rótulo da cena: O PROBLEMA */}
        {frame >= 5 && (
          <div
            style={{
              transform: `scale(${rotuloSpring})`,
              opacity: rotuloSpring,
              backgroundColor: '#E11D48',
              borderRadius: 12,
              padding: '8px 22px',
              border: '2px solid rgba(255, 255, 255, 0.3)',
              boxShadow: '0 6px 20px rgba(225, 29, 72, 0.6)',
              marginBottom: 14,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              O PROBLEMA
            </span>
          </div>
        )}

        {/* Card Dinâmico 1 (Frame 10 a 105): Fala sobre PDF pesado */}
        {frame >= 10 && frame < 105 && (
          <div
            style={{
              transform: `scale(${card1Spring})`,
              opacity: card1Spring,
              backgroundColor: 'rgba(20, 5, 9, 0.92)',
              border: '2px solid #E11D48',
              borderRadius: 18,
              padding: '14px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.85)',
            }}
          >
            <span style={{fontSize: 38}}>📄❌</span>
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.15,
                }}
              >
                ENVIO EM PDF PESADO
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FACC15',
                  textTransform: 'uppercase',
                }}
              >
                Dificuldade para o cliente abrir
              </span>
            </div>
          </div>
        )}

        {/* Card Dinâmico 2 (Frame 105 em diante): Cliente desistia antes mesmo de abrir */}
        {frame >= 105 && (
          <div
            style={{
              transform: `scale(${card2Spring})`,
              opacity: card2Spring,
              backgroundColor: 'rgba(30, 8, 12, 0.94)',
              border: '2px solid #EF4444',
              borderRadius: 18,
              padding: '14px 28px',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              boxShadow: '0 10px 30px rgba(239, 68, 68, 0.45)',
            }}
          >
            <span style={{fontSize: 38}}>⚠️</span>
            <div style={{display: 'flex', flexDirection: 'column'}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.15,
                }}
              >
                CLIENTE DESISTIA ANTES DE ABRIR
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#F87171',
                  textTransform: 'uppercase',
                }}
              >
                Vendas perdidas no primeiro contato
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
