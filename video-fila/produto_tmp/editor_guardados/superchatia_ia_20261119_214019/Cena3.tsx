import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Cena3Props {
  fontFamily: string;
  destaque: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily, destaque}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Slow push-in contínuo de aproximação de câmera (1.10x a 1.22x) quebrando a tomada estática
  const videoScale = interpolate(frame, [0, 235], [1.10, 1.22], {
    extrapolateRight: 'clamp',
  });

  // Badge superior "O RESULTADO"
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada inicial do cartão
  const cardSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Entrada escalonada dos mini-ícones flutuantes dos aplicativos ilustrando 'tudo em um só lugar'
  const appIcon1Spring = spring({frame: frame - 15, fps, config: {damping: 14, stiffness: 140}});
  const appIcon2Spring = spring({frame: frame - 28, fps, config: {damping: 14, stiffness: 140}});
  const appIcon3Spring = spring({frame: frame - 42, fps, config: {damping: 14, stiffness: 140}});

  // Fase 2 entra aos ~28.0s (frame relativo 135)
  const isSecondPhase = frame >= 135;
  const phase2Spring = spring({
    frame: frame - 135,
    fps,
    config: {damping: 14, stiffness: 160},
  });

  // Pulso do indicador IA 24h
  const livePulse = 1 + Math.sin(frame * 0.25) * 0.08;

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
      {/* Vídeo do dono falando em plano mais fechado (close-up) desde o frame 0 com respiro livre */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(60px) scale(${videoScale})`,
          transformOrigin: '50% 30%',
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
      </div>

      {/* Gradiente suave apenas no topo para contraste do card */}
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

      {/* Rótulo superior "O RESULTADO" em y = 155 */}
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
            border: '1.5px solid rgba(34, 197, 94, 0.55)',
            borderRadius: 999,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: '#22C55E',
              boxShadow: '0 0 10px #22C55E',
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
            O Resultado
          </span>
        </div>
      </div>

      {/* Cartão Superior Compacto e OPACO (top: 198px, restaurando >15% de headroom acima do apresentador) */}
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
              ? '2px solid rgba(91, 108, 255, 0.65)'
              : '2px solid rgba(34, 197, 94, 0.55)',
            borderRadius: 20,
            padding: '16px 24px',
            boxShadow: '0 16px 36px rgba(0, 0, 0, 0.85)',
            boxSizing: 'border-box',
          }}
        >
          {/* Bloco 1 (23.59s a 28.0s): "Hoje minha equipe atende tudo em um só lugar" */}
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
                Equipe atendendo tudo em um só lugar
              </h2>
            </div>
          ) : (
            /* Bloco 2 (28.0s a 31.78s): "com a IA no WhatsApp ajudando o dia inteiro" */
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
                IA no WhatsApp ajudando o dia inteiro
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
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#4ADE80',
                    backgroundColor: 'rgba(34, 197, 94, 0.18)',
                    padding: '4px 18px',
                    borderRadius: 10,
                    border: '1.5px solid rgba(34, 197, 94, 0.45)',
                  }}
                >
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      backgroundColor: '#22C55E',
                      boxShadow: '0 0 10px #22C55E',
                      transform: `scale(${livePulse})`,
                    }}
                  />
                  Atendimento IA 24h
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mini-ícones flutuantes dos aplicativos ilustrando 'tudo em um só lugar' */}
      {/* Entrada dinâmica escalonada com leve flutuação contínua e respiro livre acima do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 310,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          gap: 16,
          zIndex: 25,
          pointerEvents: 'none',
        }}
      >
        {/* WhatsApp */}
        {frame >= 15 && (
          <div
            style={{
              transform: `translateY(${Math.sin(frame * 0.12) * 5}px) scale(${Math.max(0, appIcon1Spring)})`,
              opacity: Math.min(1, Math.max(0, appIcon1Spring)),
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 18px',
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '1.5px solid rgba(34, 197, 94, 0.6)',
              borderRadius: 14,
              boxShadow: '0 8px 20px rgba(0,0,0,0.7), 0 0 12px rgba(34, 197, 94, 0.35)',
              color: '#4ADE80',
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            <span>●</span> WhatsApp
          </div>
        )}

        {/* Telegram */}
        {frame >= 28 && (
          <div
            style={{
              transform: `translateY(${Math.sin(frame * 0.12 + 1.2) * 5}px) scale(${Math.max(0, appIcon2Spring)})`,
              opacity: Math.min(1, Math.max(0, appIcon2Spring)),
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 18px',
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '1.5px solid rgba(56, 189, 248, 0.6)',
              borderRadius: 14,
              boxShadow: '0 8px 20px rgba(0,0,0,0.7), 0 0 12px rgba(56, 189, 248, 0.35)',
              color: '#38BDF8',
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            <span>●</span> Telegram
          </div>
        )}

        {/* Instagram */}
        {frame >= 42 && (
          <div
            style={{
              transform: `translateY(${Math.sin(frame * 0.12 + 2.4) * 5}px) scale(${Math.max(0, appIcon3Spring)})`,
              opacity: Math.min(1, Math.max(0, appIcon3Spring)),
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 18px',
              backgroundColor: 'rgba(15, 23, 42, 0.92)',
              border: '1.5px solid rgba(225, 48, 108, 0.6)',
              borderRadius: 14,
              boxShadow: '0 8px 20px rgba(0,0,0,0.7), 0 0 12px rgba(225, 48, 108, 0.35)',
              color: '#FFA0D0',
              fontSize: 32,
              fontWeight: 800,
            }}
          >
            <span>●</span> Instagram
          </div>
        )}
      </div>
    </div>
  );
};
