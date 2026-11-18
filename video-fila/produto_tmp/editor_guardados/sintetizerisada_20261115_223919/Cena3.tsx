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
  const {fps} = useVideoConfig();

  // Corte em punch-out de volta ao enquadramento aberto (1.00x) + push-in contínuo (slow creep zoom 1.00x -> 1.055x)
  const videoScale = interpolate(frame, [0, 246], [1.0, 1.055], {
    extrapolateRight: 'clamp',
  });
  const videoTranslateY = interpolate(frame, [0, 246], [0, -10], {
    extrapolateRight: 'clamp',
  });

  // Transição no frame 160 (~25.56s, quando fala "sem precisar tocar no celular...")
  const isFase2 = frame >= 160;

  const entradaFase1 = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  const saidaFase1 = isFase2
    ? interpolate(frame, [160, 169], [1, 0], {extrapolateRight: 'clamp'})
    : 1;

  const entradaFase2 = spring({
    frame: frame - 160,
    fps,
    config: {damping: 13, mass: 0.75},
  });

  const pulsoSucesso = 1 + Math.sin(frame / 8) * 0.018;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F172A',
      }}
    >
      {/* Vídeo do Dono em tela cheia */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: '50% 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta superior suave */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 380,
            background:
              'linear-gradient(180deg, rgba(15, 23, 42, 0.85) 0%, rgba(15, 23, 42, 0.4) 65%, rgba(15, 23, 42, 0) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Topo Informativo Unificado e Compacto (y=168 a 295) — Respiro > 80px acima da cabeça */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Card Fase 1: Foco Total */}
        {!isFase2 && (
          <div
            style={{
              width: '100%',
              padding: '14px 22px',
              borderRadius: 20,
              backgroundColor: 'rgba(20, 24, 33, 0.92)',
              border: '1.5px solid rgba(16, 185, 129, 0.45)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.55)',
              opacity: entradaFase1 * saidaFase1,
              transform: `translateY(${interpolate(entradaFase1, [0, 1], [-20, 0])}px)`,
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#10B981',
                    boxShadow: '0 0 8px #10B981',
                  }}
                />
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#A7F3D0',
                    textTransform: 'uppercase',
                    letterSpacing: 1.2,
                  }}
                >
                  O Resultado
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                No consultório
              </span>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.15,
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Começo o dia atendendo meus clientes
            </div>
          </div>
        )}

        {/* Card Fase 2: Sem Tocar no Celular */}
        {isFase2 && (
          <div
            style={{
              width: '100%',
              padding: '14px 22px',
              borderRadius: 20,
              backgroundColor: 'rgba(20, 24, 33, 0.94)',
              border: '2px solid #FFA94D',
              boxShadow: '0 8px 28px rgba(255, 169, 77, 0.35)',
              opacity: entradaFase2,
              transform: `translateY(${interpolate(entradaFase2, [0, 1], [20, 0])}px) scale(${pulsoSucesso})`,
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: '#10B981',
                    boxShadow: '0 0 8px #10B981',
                  }}
                />
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
                  O Resultado • Liberdade
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#10B981',
                }}
              >
                ✓ Sem tocar no celular
              </span>
            </div>
            <div
              style={{
                fontFamily,
                fontSize: 44,
                fontWeight: 900,
                color: '#FFA94D',
                lineHeight: 1.15,
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Sem precisar tocar no celular pela manhã
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
