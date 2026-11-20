import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena1Props {
  fontFamily: string;
  destaque: string;
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily, destaque}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Punch-in de 15% (escala 1.15x) logo no corte inicial da Cena 1, eliminando jump-cut com a Cena 0
  const isSecondPhase = frame >= 134;
  const videoScale = !isSecondPhase
    ? interpolate(frame, [0, 134], [1.15, 1.22], {extrapolateRight: 'clamp'})
    : interpolate(frame, [134, 245], [1.25, 1.34], {extrapolateRight: 'clamp'});

  // Badge superior "O PROBLEMA"
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada inicial do cartão superior
  const cardSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Pattern interrupt: B-roll gráfico de aplicativos desconectados entrando aos ~6.0s (frame 42)
  // rompe o plano contínuo e ilustra "cada atendente abria um aplicativo diferente"
  const appsInterruptSpring = spring({
    frame: frame - 42,
    fps,
    config: {damping: 14, stiffness: 150},
  });

  // Transição ágil com mola para a fase 2 (frame 134)
  const phase2Spring = spring({
    frame: frame - 134,
    fps,
    config: {damping: 14, stiffness: 160},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#000000',
        fontFamily,
      }}
    >
      {/* Vídeo do apresentador (Dono) com punch-in zoom digital na virada da fala e enquadramento seguro */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(65px) scale(${videoScale})`,
          transformOrigin: '50% 28%',
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

      {/* Gradiente escuro no topo para dar destaque e contraste à tipografia */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(7, 10, 18, 0.85) 0%, rgba(7, 10, 18, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Rótulo superior "O PROBLEMA" elevado para y = 155 garantindo respiro limpo */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${Math.max(0, badgeSpring)})`,
          opacity: Math.max(0, badgeSpring),
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            backgroundColor: '#0F172A',
            border: '1.5px solid rgba(239, 68, 68, 0.55)',
            borderRadius: 999,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              color: '#F8FAFC',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>
      </div>

      {/* Cartão Superior Compacto e OPACO (top: 198px, altura reduzida sem tags redundantes restaurando >15% de headroom) */}
      <div
        style={{
          position: 'absolute',
          top: 198,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${Math.max(0, cardSpring)})`,
          opacity: Math.min(1, Math.max(0, cardSpring)),
          zIndex: 15,
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            backgroundColor: '#0F172A',
            border: isSecondPhase
              ? '2px solid rgba(245, 158, 11, 0.65)'
              : '2px solid rgba(239, 68, 68, 0.55)',
            borderRadius: 20,
            padding: '16px 24px',
            boxShadow: '0 16px 36px rgba(0, 0, 0, 0.85)',
            boxSizing: 'border-box',
          }}
        >
          {/* Tópico 1 (4.56s até 9.03s = frames 0 a 133): Título direto sem tags redundantes para respiro livre */}
          {!isSecondPhase ? (
            <div style={{textAlign: 'center'}}>
              <h2
                style={{
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  margin: 0,
                  lineHeight: 1.25,
                  textWrap: 'balance',
                }}
              >
                Cada atendente em um aplicativo diferente
              </h2>
            </div>
          ) : (
            /* Tópico 2 (9.03s até 12.74s = frame 134+): "Fácil se perder no atendimento" com entrada elástica rápida */
            <div
              style={{
                textAlign: 'center',
                transform: `translateY(${interpolate(phase2Spring, [0, 1], [12, 0])}px)`,
                opacity: Math.min(1, phase2Spring),
              }}
            >
              <h2
                style={{
                  fontSize: 36,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  margin: 0,
                  lineHeight: 1.25,
                  textWrap: 'balance',
                }}
              >
                Fácil se perder no atendimento
              </h2>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  marginTop: 10,
                  width: '100%',
                }}
              >
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FDE047',
                    backgroundColor: 'rgba(245, 158, 11, 0.22)',
                    padding: '4px 18px',
                    borderRadius: 10,
                    border: '1.5px solid rgba(253, 224, 71, 0.55)',
                    textShadow: '0 2px 8px rgba(0,0,0,0.6)',
                  }}
                >
                  Cliente esperando mais tempo
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Pattern Interrupt (frames 42 a 133): Ilustração dinâmica de múltiplos aplicativos desconectados */}
      {/* Quebra a monotonia do plano, cobre o corte de fala aos 6.2s e ilustra 'cada atendente em um app' */}
      {frame >= 42 && !isSecondPhase && (
        <div
          style={{
            position: 'absolute',
            top: 310,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            gap: 16,
            transform: `translateY(${interpolate(appsInterruptSpring, [0, 1], [20, 0])}px) scale(${Math.max(0, appsInterruptSpring)})`,
            opacity: Math.min(1, Math.max(0, appsInterruptSpring)),
            zIndex: 25,
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              padding: '8px 18px',
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid rgba(239, 68, 68, 0.7)',
              borderRadius: 14,
              color: '#FCA5A5',
              fontSize: 32,
              fontWeight: 800,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.8)',
              transform: 'rotate(-2deg)',
            }}
          >
            ✕ WhatsApp separado
          </div>
          <div
            style={{
              padding: '8px 18px',
              backgroundColor: 'rgba(15, 23, 42, 0.94)',
              border: '1.5px solid rgba(239, 68, 68, 0.7)',
              borderRadius: 14,
              color: '#FCA5A5',
              fontSize: 32,
              fontWeight: 800,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.8)',
              transform: 'rotate(2deg)',
            }}
          >
            ✕ Instagram separado
          </div>
        </div>
      )}
    </div>
  );
};
