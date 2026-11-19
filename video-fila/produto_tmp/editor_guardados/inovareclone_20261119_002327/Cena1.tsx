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

  // Movimento de câmera contínuo no vídeo do dono
  const videoScale = interpolate(frame, [0, 245], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada (início da cena 1 sobre o fim da cena 0)
  const entryOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Fade de saída antes da cena 2
  const exitOpacity = interpolate(frame, [235, 245], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Animação do HUD superior (faixa estrita y=150 a 420)
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Fase 1: Horas perdidas (entra frame 12, ~0.4s)
  const fase1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Chip 1: Cenário demorado (entra frame 50)
  const chip1Spring = spring({
    frame: frame - 50,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Chip 2: Refazendo falas (entra frame 90)
  const chip2Spring = spring({
    frame: frame - 90,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Transição da Fase 1 para Fase 2 aos ~5.2s (frame 155)
  // Fase 2: Conteúdo não saía no dia certo
  const isFase2 = frame >= 155;
  const fase2Spring = spring({
    frame: frame - 155,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        backgroundColor: CORES.fundoEscuro,
        opacity: entryOpacity * exitOpacity,
        fontFamily,
      }}
    >
      {/* Vídeo do dono em tela cheia com push-in sutil */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
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
        {/* Sombra sutil apenas no topo (y=0 a 350) para garantir leitura do HUD sem escurecer o rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 380,
            background:
              'linear-gradient(180deg, rgba(15, 23, 42, 0.75) 0%, rgba(15, 23, 42, 0.4) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* HUD SUPERIOR: FAIXA RESTRITA y=165 a 420 (Rosto do dono começa em y ~480) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Tag da Etapa: 01 • O PROBLEMA */}
        <div
          style={{
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `scale(${badgeSpring})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 999,
            backgroundColor: 'rgba(15, 23, 42, 0.88)',
            border: '1.5px solid rgba(239, 68, 68, 0.6)',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.5)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            01 • O Problema
          </span>
        </div>

        {/* Card Dinâmico no Topo */}
        <div
          style={{
            marginTop: 14,
            width: '100%',
            maxWidth: 920,
            backgroundColor: 'rgba(15, 23, 42, 0.88)',
            backdropFilter: 'blur(10px)',
            borderRadius: 20,
            padding: '16px 24px',
            border: `1.5px solid ${isFase2 ? 'rgba(239, 68, 68, 0.5)' : 'rgba(139, 92, 246, 0.35)'}`,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
            minHeight: 145,
            justifyContent: 'center',
          }}
        >
          {!isFase2 ? (
            // Momento 1: Horas perdidas arrumando cenário e refazendo falas
            <div
              style={{
                opacity: interpolate(fase1Spring, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(fase1Spring, [0, 1], [15, 0])}px)`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                width: '100%',
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  textAlign: 'center',
                  letterSpacing: '-0.5px',
                }}
              >
                Horas Perdidas com Gravação
              </div>
              <div
                style={{
                  display: 'flex',
                  gap: 12,
                  justifyContent: 'center',
                  flexWrap: 'wrap',
                }}
              >
                {frame >= 50 && (
                  <div
                    style={{
                      opacity: interpolate(chip1Spring, [0, 1], [0, 1]),
                      transform: `scale(${chip1Spring})`,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '4px 14px',
                      borderRadius: 10,
                      backgroundColor: 'rgba(239, 68, 68, 0.25)',
                      border: '1px solid rgba(239, 68, 68, 0.5)',
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#FCA5A5',
                    }}
                  >
                    <span>⏰</span>
                    <span>Cenário Demorado</span>
                  </div>
                )}
                {frame >= 90 && (
                  <div
                    style={{
                      opacity: interpolate(chip2Spring, [0, 1], [0, 1]),
                      transform: `scale(${chip2Spring})`,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '4px 14px',
                      borderRadius: 10,
                      backgroundColor: 'rgba(239, 68, 68, 0.25)',
                      border: '1px solid rgba(239, 68, 68, 0.5)',
                      fontSize: 32,
                      fontWeight: 700,
                      color: '#FCA5A5',
                    }}
                  >
                    <span>🔁</span>
                    <span>Refazendo Falas</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            // Momento 2: No fim, o conteúdo quase nunca saía no dia certo
            <div
              style={{
                opacity: interpolate(fase2Spring, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(fase2Spring, [0, 1], [15, 0])}px)`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 10,
                width: '100%',
              }}
            >
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FCA5A5',
                  textTransform: 'uppercase',
                  textAlign: 'center',
                  letterSpacing: '-0.5px',
                }}
              >
                Conteúdo Não Saía no Dia Certo
              </div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '4px 16px',
                  borderRadius: 10,
                  backgroundColor: 'rgba(239, 68, 68, 0.35)',
                  border: '1px solid #EF4444',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                }}
              >
                <span>📅</span>
                <span>Cronograma Atrasado</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
