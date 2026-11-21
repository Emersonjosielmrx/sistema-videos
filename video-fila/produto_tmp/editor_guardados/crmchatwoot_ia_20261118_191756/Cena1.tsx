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
  const {fps} = useVideoConfig();

  // Movimento de câmera com enquadramento perfeito (espaço de respiro garantido acima da cabeça)
  const videoScale = interpolate(frame, [0, 245], [1.07, 1.12], {
    extrapolateRight: 'clamp',
  });

  // Topo badge aos 0.15s (frame 5)
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Entrada do primeiro título aos 0.8s (frame 25)
  const title1Spring = spring({
    frame: frame - 25,
    fps,
    config: {damping: 12, stiffness: 90},
  });

  // Ponto de virada aos 5.3s (frame 160)
  const turnPoint = 160;
  const isTurn = frame >= turnPoint;

  const title2Spring = spring({
    frame: frame - turnPoint,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  const floatY = Math.sin(frame / 12) * 3;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#0F172A',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono com enquadramento rebaixado em 120px para garantir mais de 50px de respiro acima da cabeça */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(120px) scale(${videoScale})`,
          transformOrigin: '50% 30%',
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

      {/* Vinheta ultra suave exclusivamente no topo para leitura cristalina dos grafismos */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 270,
          background:
            'linear-gradient(180deg, rgba(15, 23, 42, 0.88) 0%, rgba(15, 23, 42, 0.4) 65%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Grafismos de Topo (Safe Zone: y=190 a 310 — respiro de >55px até o topo da cabeça do apresentador) */}
      <div
        style={{
          position: 'absolute',
          top: 190,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          transform: `translateY(${floatY}px)`,
          pointerEvents: 'none',
        }}
      >
        {/* Rótulo da Cena (O problema) */}
        <div
          style={{
            transform: `scale(${Math.max(0, badgeSpring)})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              padding: '6px 22px',
              borderRadius: 22,
              background: 'rgba(15, 23, 42, 0.85)',
              border: '1.5px solid rgba(255, 255, 255, 0.25)',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 6px 18px rgba(0, 0, 0, 0.5)',
            }}
          >
            <span style={{fontSize: 28}}>🏢</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#E2E8F0',
                textTransform: 'uppercase',
                letterSpacing: 1.1,
              }}
            >
              O Problema
            </span>
          </div>
        </div>

        {/* Headline Sincronizada com a Fala */}
        {!isTurn ? (
          <div
            style={{
              transform: `scale(${Math.max(0, title1Spring)})`,
              maxWidth: 920,
              textAlign: 'center',
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.9)',
                border: '2px solid rgba(239, 68, 68, 0.45)',
                borderRadius: 18,
                padding: '10px 24px',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
                display: 'inline-block',
              }}
            >
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.2,
                }}
              >
                ERA SÓ PRA{' '}
                <span style={{color: '#F87171'}}>EMPRESA GRANDE?</span>
              </span>
            </div>
          </div>
        ) : (
          <div
            style={{
              transform: `scale(${Math.max(0, title2Spring)})`,
              maxWidth: 920,
              textAlign: 'center',
            }}
          >
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.92)',
                border: '2px solid #1F93FF',
                borderRadius: 18,
                padding: '10px 24px',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 10px 28px rgba(31, 147, 255, 0.4)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <span style={{fontSize: 32}}>✅</span>
              <span
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.2,
                }}
              >
                HOJE:{' '}
                <span style={{color: '#60A5FA'}}>ATENDIMENTO ORGANIZADO</span>
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
