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

export const Cena3DonoResultado: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Push-in de câmera suave no vídeo do dono
  const scale = interpolate(frame, [0, 245], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante
  const floatY = Math.sin(frame / 12) * 3;

  // Header superior (frame 4)
  const headerSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Step 1: "escolhe sozinho no celular" (~18.3s) -> frame 20
  const step1Active = frame >= 20;

  // Step 2: "tira dúvida com a IA" (~21.2s) -> frame 115
  const step2Active = frame >= 115;

  // Step 3: "o pedido chega pelo WhatsApp" (~23.7s) -> frame 190
  const step3Active = frame >= 190;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0B0D13',
      }}
    >
      {/* Vídeo do Dono com color grading suave (integração à paleta da marca, sem luz fluorescente crua) */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
            filter: 'brightness(0.96) contrast(1.08) saturate(1.10)',
          }}
        />
      </div>

      {/* Vinheta protetora quente e suave da marca (área do rosto 100% desobstruída e nítida) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(49, 6, 15, 0.78) 0%, rgba(11, 13, 19, 0.35) 18%, rgba(11, 13, 19, 0.0) 34%, rgba(11, 13, 19, 0.0) 65%, rgba(11, 13, 19, 0.75) 88%, rgba(11, 13, 19, 0.95) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo na Safe Zone estritamente no topo (y=160 a y=280: respiro de mais de 100px acima da cabeça) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 160,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 30,
        }}
      >
        {headerSpring > 0 && (
          <div
            style={{
              transform: `scale(${headerSpring}) translateY(${floatY}px)`,
              opacity: headerSpring,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '100%',
              maxWidth: 900,
            }}
          >
            {/* Badge Rótulo Compacto "O RESULTADO" */}
            <div
              style={{
                backgroundColor: '#E11D48',
                padding: '6px 22px',
                borderRadius: 999,
                boxShadow: '0 6px 18px rgba(225, 29, 72, 0.5)',
                border: '1.5px solid rgba(255, 255, 255, 0.3)',
                marginBottom: 10,
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
                O RESULTADO
              </span>
            </div>

            {/* Marcadores em linha única compacta com margem ampla lateral (>120px) e respiro acima da cabeça */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                justifyContent: 'center',
                backgroundColor: 'rgba(15, 23, 42, 0.88)',
                padding: '8px 14px',
                borderRadius: 20,
                border: '1.5px solid rgba(255, 255, 255, 0.12)',
                boxShadow: '0 8px 25px rgba(0, 0, 0, 0.65)',
              }}
            >
              {/* Etapa 1 */}
              <div
                style={{
                  backgroundColor: step1Active
                    ? 'rgba(250, 204, 21, 0.18)'
                    : 'transparent',
                  border: step1Active
                    ? '2px solid #FACC15'
                    : '1.5px solid rgba(255, 255, 255, 0.1)',
                  padding: '8px 14px',
                  borderRadius: 14,
                  boxShadow: step1Active
                    ? '0 4px 14px rgba(250, 204, 21, 0.3)'
                    : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span style={{fontSize: 28}}>📱</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: step1Active ? '#FACC15' : '#94A3B8',
                  }}
                >
                  1. No Celular
                </span>
              </div>

              {/* Etapa 2 */}
              <div
                style={{
                  backgroundColor: step2Active
                    ? 'rgba(225, 29, 72, 0.22)'
                    : 'transparent',
                  border: step2Active
                    ? '2px solid #E11D48'
                    : '1.5px solid rgba(255, 255, 255, 0.1)',
                  padding: '8px 14px',
                  borderRadius: 14,
                  boxShadow: step2Active
                    ? '0 4px 14px rgba(225, 29, 72, 0.3)'
                    : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span style={{fontSize: 28}}>🤖</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: step2Active ? '#FFFFFF' : '#94A3B8',
                  }}
                >
                  2. Com IA
                </span>
              </div>

              {/* Etapa 3 */}
              <div
                style={{
                  backgroundColor: step3Active
                    ? 'rgba(34, 197, 94, 0.22)'
                    : 'transparent',
                  border: step3Active
                    ? '2px solid #22C55E'
                    : '1.5px solid rgba(255, 255, 255, 0.1)',
                  padding: '8px 14px',
                  borderRadius: 14,
                  boxShadow: step3Active
                    ? '0 4px 14px rgba(34, 197, 94, 0.3)'
                    : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span style={{fontSize: 28}}>💬</span>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: step3Active ? '#22C55E' : '#94A3B8',
                  }}
                >
                  3. No WhatsApp
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
