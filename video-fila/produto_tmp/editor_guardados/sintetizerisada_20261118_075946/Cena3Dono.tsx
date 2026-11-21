import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena3Dono: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Composição diferenciada da Cena 1:
  // Plano mais fechado (close-up 1.15 -> 1.22) com o apresentador rebaixado e levemente deslocado
  // para dar variedade visual e respiro entre o topo do cabelo e os títulos
  const videoScale = interpolate(frame, [0, 236], [1.15, 1.22], {
    extrapolateRight: 'clamp',
  });
  const videoTranslateY = 38;
  const videoTranslateX = -28;

  // Entrada inicial da cena
  const enterSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Ponto de virada da fala:
  // "enquanto os agendamentos automáticos rodam" começa em ~frame 140
  const switchProgress = interpolate(frame, [136, 148], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Entrada do card/gráfico flutuante de agendamento automático
  const autoCardSpring = spring({
    frame: frame - 140,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Micro-movimento contínuo para evitar elementos estáticos
  const microFloat = Math.sin(frame / 10) * 3;
  const cardFloatY = Math.sin(frame / 7) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do dono em plano fechado (close-up) rebaixado e deslocado */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${videoScale}) translate(${videoTranslateX}px, ${videoTranslateY}px)`,
          transformOrigin: '50% 36%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta escura protetora */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.82) 0%, rgba(15,23,42,0.18) 22%, rgba(15,23,42,0.0) 48%, rgba(15,23,42,0.48) 84%, rgba(15,23,42,0.88) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Faixa superior informativa com amplo respiro sobre a cabeça do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 200,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          transform: `translateY(${microFloat}px)`,
        }}
      >
        {/* Badge da cena com transição temática nítida */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 24,
            background:
              switchProgress > 0.5 ? 'rgba(15, 23, 42, 0.94)' : 'rgba(31, 41, 55, 0.92)',
            border:
              switchProgress > 0.5
                ? '1.5px solid rgba(16, 185, 129, 0.75)'
                : '1.5px solid rgba(255, 169, 77, 0.75)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            transform: `scale(${enterSpring})`,
            opacity: enterSpring,
            whiteSpace: 'nowrap',
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: '0 0 10px #10B981',
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: switchProgress > 0.5 ? '#34D399' : '#FFA94D',
              whiteSpace: 'nowrap',
            }}
          >
            {switchProgress > 0.5 ? 'IA Ativa no WhatsApp 24h' : 'Foco no Serviço'}
          </span>
        </div>
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#10B981',
                boxShadow: '0 0 10px #10B981',
              }}
            />
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                color: '#34D399',
                whiteSpace: 'nowrap',
              }}
            >
              IA Ativa no WhatsApp 24h
            </span>
          </div>
        </div>

        {/* Título Dinâmico */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            height: 125,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {/* Fase 1: "Atenção inteira no cliente presencial" */}
          <div
            style={{
              position: 'absolute',
              width: '100%',
              textAlign: 'center',
              opacity: (1 - switchProgress) * enterSpring,
              transform: `translateY(${switchProgress * -15}px)`,
              pointerEvents: 'none',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 46,
                fontWeight: 900,
                lineHeight: 1.25,
                color: '#FFFFFF',
                textShadow: '0 4px 18px rgba(0,0,0,0.9)',
                textWrap: 'balance',
              }}
            >
              Atenção inteira <br />
              <span
                style={{
                  background: '#FFA94D',
                  color: '#1F2937',
                  padding: '2px 14px',
                  borderRadius: 10,
                  display: 'inline-block',
                  marginTop: 4,
                  fontWeight: 900,
                }}
              >
                no cliente presencial
              </span>
            </h2>
          </div>

          {/* Fase 2: "Enquanto os agendamentos automáticos rodam" com tarja protetora sólida */}
          <div
            style={{
              position: 'absolute',
              width: '100%',
              textAlign: 'center',
              opacity: switchProgress,
              transform: `translateY(${(1 - switchProgress) * 15}px)`,
              pointerEvents: 'none',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 46,
                fontWeight: 900,
                lineHeight: 1.25,
                color: '#FFFFFF',
                textShadow: '0 4px 18px rgba(0,0,0,0.9)',
                textWrap: 'balance',
              }}
            >
              Enquanto os agendamentos <br />
              <span
                style={{
                  background: '#FFA94D',
                  color: '#1F2937',
                  padding: '2px 14px',
                  borderRadius: 10,
                  display: 'inline-block',
                  marginTop: 4,
                  fontWeight: 900,
                }}
              >
                automáticos rodam
              </span>
            </h2>
          </div>
        </div>
      </div>

      {/* Gráfico/Widget Flutuante de Agendamento Automático (reforçando a ideia da fala) */}
      {frame >= 136 && (
        <div
          style={{
            position: 'absolute',
            top: 470,
            right: 50,
            padding: '16px 24px',
            borderRadius: 22,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '2px solid rgba(255, 169, 77, 0.75)',
            boxShadow:
              '0 16px 36px rgba(0, 0, 0, 0.65), 0 0 20px rgba(255, 169, 77, 0.25)',
            transform: `scale(${autoCardSpring}) translateY(${cardFloatY}px)`,
            opacity: Math.max(0, autoCardSpring),
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            zIndex: 30,
            maxWidth: 380,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#10B981',
                boxShadow: '0 0 10px #10B981',
              }}
            />
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: '#10B981',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              WhatsApp IA
            </span>
          </div>
          <div
            style={{
              fontSize: 32,
              fontWeight: 700,
              color: '#FFFFFF',
              lineHeight: 1.25,
            }}
          >
            📅 Novo horário agendado com sucesso!
          </div>
        </div>
      )}
    </div>
  );
};
