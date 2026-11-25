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

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transição de fala para a Fase 2 ("Sempre sobrava algum contato sem registro" aos 9.40s / f=146)
  const isFase2 = frame >= 146;

  // Punch-in seco (corte de escala para 1.12x) na transição da fala para 'Sempre sobrava algum contato sem registro'
  // Antes de f=146: zoom suave de 1.05 a 1.08
  // A partir de f=146: salto seco para 1.12x base (escala 1.18 a 1.22)
  const continuousZoom = interpolate(frame, [0, 241], [1.05, 1.12], {
    extrapolateRight: 'clamp',
  });
  const videoScale = (isFase2 ? 1.12 : 1.0) * continuousZoom;

  const springCard1 = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  const springCard2 = spring({
    frame: frame - 146,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Pulso do indicador de alerta
  const pulseScale = 1 + 0.12 * Math.sin((frame / 12) * Math.PI);

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13', overflow: 'hidden'}}>
      {/* Fundo corporativo com luz de fundo e atmosfera de tecnologia séria */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 25%, rgba(91, 108, 255, 0.22) 0%, rgba(17, 24, 39, 0.8) 50%, #0B0D13 100%)',
        }}
      />

      {/* Frame de Apoio Tecnológico: contextualiza o relato prático do comércio com moldura elegante */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 360,
          height: 1100,
          borderRadius: 36,
          overflow: 'hidden',
          border: isFase2
            ? '2px solid rgba(239, 68, 68, 0.65)'
            : '2px solid rgba(255, 255, 255, 0.16)',
          boxShadow: isFase2
            ? '0 25px 60px rgba(0, 0, 0, 0.95), 0 0 35px rgba(239, 68, 68, 0.3)'
            : '0 25px 60px rgba(0, 0, 0, 0.9), 0 0 35px rgba(91, 108, 255, 0.15)',
          transition: 'border 0.2s, box-shadow 0.2s',
        }}
      >
        {/* Vídeo do apresentador com punch-in seco no momento exato e recorte focado */}
        <div
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            transform: `scale(${videoScale})`,
            transformOrigin: 'center 38%',
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

          {/* Vinheta lateral e vertical para focar na mensagem e atenuar ruído do fundo */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'radial-gradient(circle at 50% 40%, transparent 40%, rgba(11, 13, 19, 0.55) 100%)',
              pointerEvents: 'none',
            }}
          />
        </div>

        {/* Selo de Contextualização do Caso Real no canto superior do frame */}
        <div
          style={{
            position: 'absolute',
            top: 20,
            left: 20,
            padding: '6px 18px',
            borderRadius: 9999,
            background: 'rgba(17, 24, 39, 0.92)',
            border: '1px solid rgba(255, 255, 255, 0.18)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            zIndex: 10,
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#CBD5E1',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 26,
              fontWeight: 800,
              color: '#CBD5E1',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Cenário Real • Atendimento no Comércio
          </span>
        </div>
      </div>

      {/* Faixa segura superior: y=160 a y=340 (respiro seguro acima do frame e da cabeça do apresentador) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 162,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Pill fixa de contexto: O PROBLEMA */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 9999,
            background: 'rgba(17, 24, 39, 0.96)',
            border: '1.5px solid rgba(239, 68, 68, 0.65)',
            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.7)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              transform: `scale(${pulseScale})`,
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>

        {/* Card dinâmico sincronizado à fala */}
        {!isFase2 ? (
          <div
            style={{
              marginTop: 14,
              width: '100%',
              maxWidth: 960,
              background: 'rgba(17, 24, 39, 0.96)',
              border: '1.5px solid rgba(255, 255, 255, 0.18)',
              borderRadius: 22,
              padding: '14px 28px',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.8)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              transform: `scale(${Math.max(0, springCard1)})`,
              opacity: Math.min(1, springCard1),
            }}
          >
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                Anotação Manual de Contatos
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#CBD5E1',
                }}
              >
                Vários canais sem registro centralizado
              </span>
            </div>
            <div
              style={{
                padding: '6px 18px',
                borderRadius: 12,
                background: 'rgba(239, 68, 68, 0.18)',
                border: '1px solid rgba(239, 68, 68, 0.5)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#F87171',
                }}
              >
                Manual
              </span>
            </div>
          </div>
        ) : (
          <div
            style={{
              marginTop: 14,
              width: '100%',
              maxWidth: 960,
              background: 'rgba(17, 24, 39, 0.96)',
              border: '2px solid rgba(239, 68, 68, 0.75)',
              borderRadius: 22,
              padding: '14px 28px',
              boxShadow:
                '0 12px 35px rgba(0, 0, 0, 0.85), 0 0 25px rgba(239, 68, 68, 0.35)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              transform: `scale(${Math.max(0, springCard2)})`,
              opacity: Math.min(1, springCard2),
            }}
          >
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <span
                style={{
                  fontFamily,
                  fontSize: 38,
                  fontWeight: 900,
                  color: '#EF4444',
                  lineHeight: 1.2,
                }}
              >
                Contato Sem Registro
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 600,
                  color: '#FFFFFF',
                }}
              >
                Clientes perdidos na rotina
              </span>
            </div>
            <div
              style={{
                padding: '6px 18px',
                borderRadius: 12,
                background: 'rgba(239, 68, 68, 0.3)',
                border: '1px solid rgba(239, 68, 68, 0.85)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FFFFFF',
                }}
              >
                Alerta
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
