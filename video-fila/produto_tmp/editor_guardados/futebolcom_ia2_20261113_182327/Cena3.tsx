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

interface Cena3Props {
  fontFamily: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Reenquadramento e movimento de câmera suave no vídeo
  // Desloca o pizzaiolo para esquerda e para baixo, desobstruindo totalmente o rosto
  const vidScale = interpolate(frame, [0, 209], [1.14, 1.22], {
    extrapolateRight: 'clamp',
  });
  const vidTranslateX = interpolate(frame, [0, 209], [-50, -80], {
    extrapolateRight: 'clamp',
  });
  const vidTranslateY = interpolate(frame, [0, 209], [60, 90], {
    extrapolateRight: 'clamp',
  });

  // Fade de entrada e saída
  const sceneOpacity = interpolate(
    frame,
    [0, 10, 196, 209],
    [0, 1, 1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Top Badge
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Fases do Bloco Informativo:
  // Fase 0: frames 12 a 85 (O pedido entra direto pelo WhatsApp)
  // Fase 1: frames 86 a 135 (com o atendimento da IA)
  // Fase 2: frames 136 a 209 (para a sua pizzaria)
  const activePhase = frame < 86 ? 0 : frame < 136 ? 1 : 2;

  const spring0 = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 120},
  });
  const spring1 = spring({
    frame: frame - 86,
    fps,
    config: {damping: 12, stiffness: 120},
  });
  const spring2 = spring({
    frame: frame - 136,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const currentSpring =
    activePhase === 0 ? spring0 : activePhase === 1 ? spring1 : spring2;

  const pulse = Math.sin(frame * 0.14) * 3;

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#1A0307'}}>
      {/* Vídeo Real Reenquadrado com Rosto do Pizzaiolo Totalmente Livre */}
      <AbsoluteFill style={{overflow: 'hidden'}}>
        <div
          style={{
            width: '100%',
            height: '100%',
            transform: `scale(${vidScale}) translate(${vidTranslateX}px, ${vidTranslateY}px)`,
            transformOrigin: 'top left',
          }}
        >
          <OffthreadVideo
            src={staticFile('video_3.mp4')}
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        </div>

        {/* Gradiente sutil no topo para contraste dos textos sem escurecer a pizza */}
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(20, 2, 6, 0.88) 0%, rgba(20, 2, 6, 0.45) 25%, rgba(0, 0, 0, 0) 45%, rgba(15, 2, 4, 0.5) 100%)',
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {/* Rótulo / Top Badge (y=175 a 235) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
          zIndex: 20,
        }}
      >
        <div
          style={{
            fontFamily,
            fontSize: 32,
            fontWeight: 800,
            color: '#FFFFFF',
            backgroundColor: 'rgba(225, 29, 72, 0.88)',
            border: '2px solid rgba(250, 204, 21, 0.7)',
            padding: '10px 28px',
            borderRadius: 50,
            letterSpacing: 1.2,
            textTransform: 'uppercase',
            boxShadow: '0 8px 28px rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <span>🚀</span>
          <span>O RESULTADO: PEDIDO AUTOMATIZADO</span>
        </div>
      </div>

      {/* Card Dinâmico Posicionado em Área Neutra à Direita (y=255 a 415, x=400 a 1020) */}
      {/* Nunca obstrui o rosto do pizzaiolo no lado esquerdo */}
      <div
        style={{
          position: 'absolute',
          top: 255,
          right: 60,
          width: 620,
          display: 'flex',
          justifyContent: 'flex-end',
          zIndex: 20,
        }}
      >
        <div
          style={{
            width: '100%',
            backgroundColor: 'rgba(22, 3, 7, 0.94)',
            border:
              activePhase === 0
                ? '2.5px solid #25D366'
                : activePhase === 1
                ? '2.5px solid rgba(250, 204, 21, 0.7)'
                : '2.5px solid #E11D48',
            borderRadius: 22,
            padding: '18px 24px',
            boxShadow: '0 14px 34px rgba(0,0,0,0.7)',
            transform: `scale(${Math.min(currentSpring, 1)}) translateY(${(1 - currentSpring) * 18 + pulse}px)`,
            opacity: currentSpring,
          }}
        >
          {activePhase === 0 && (
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  backgroundColor: '#25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  color: '#111111',
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Pedido Direto no WhatsApp
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#25D366',
                    marginTop: 3,
                  }}
                >
                  Cliente escolhe e pede sem fila
                </div>
              </div>
            </div>
          )}

          {activePhase === 1 && (
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 40}}>🤖</span>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FACC15',
                    lineHeight: 1.2,
                  }}
                >
                  Atendimento com Inteligência Artificial
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#E2E8F0',
                    marginTop: 3,
                  }}
                >
                  Tira dúvidas de sabores na hora
                </div>
              </div>
            </div>
          )}

          {activePhase === 2 && (
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 40}}>🔥</span>
              <div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 900,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Mais pizzas no forno e agilidade
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 700,
                    color: '#FACC15',
                    marginTop: 3,
                  }}
                >
                  Sua equipe focada no sabor!
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
