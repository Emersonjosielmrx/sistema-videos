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

export const Cena2: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Corte de escala na transição: punch-in zoom de 1.16x a 1.22x quebrando a monotonia da câmera
  const videoScale = interpolate(frame, [0, 245], [1.16, 1.22], {
    extrapolateRight: 'clamp',
  });
  // Reposicionamento do apresentador para baixo (+42px) garantindo >50px de respiro sobre a cabeça
  const videoTranslateY = interpolate(frame, [0, 245], [42, 32], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante
  const pulseScale = 1 + Math.sin(frame / 12) * 0.012;
  const pulseExecution = 1 + Math.sin(frame / 6) * 0.02;

  // Entrada do badge de rótulo (frame 0)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada da 1ª parte: "O Inovare Claw já vem pronto" (15.109s - 14.07s = 1.039s = frame ~31)
  const part1Spring = spring({
    frame: frame - 31,
    fps,
    config: {damping: 13, stiffness: 125},
  });

  // Entrada do Passo 1: "Eu passo a tarefa" (18.369s - 14.07s = 4.299s = frame ~129)
  const step1Spring = spring({
    frame: frame - 129,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Entrada do Passo 2: "e o agente executa por mim" (19.969s - 14.07s = 5.899s = frame ~177)
  const step2Spring = spring({
    frame: frame - 177,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const showSteps = frame >= 125;

  return (
    <AbsoluteFill style={{backgroundColor: '#0B0D13', overflow: 'hidden'}}>
      {/* Vídeo do apresentador com punch-in zoom (1.16x) e rebaixamento para não colidir no cabelo */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: 'center 38%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_2.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta cinematográfica */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11, 13, 19, 0.85) 0%, rgba(11, 13, 19, 0) 28%, rgba(11, 13, 19, 0) 70%, rgba(11, 13, 19, 0.88) 100%)',
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {/* Faixa superior na Safe Zone (y 160 a 440) com >50px de respiro livre até o cabelo */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 70,
          right: 90,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
        }}
      >
        {/* Badge "02 • COMO FUNCIONA" */}
        <div
          style={{
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(badgeSpring, [0, 1], [-15, 0])}px) scale(${pulseScale})`,
            background: 'rgba(11, 13, 19, 0.95)',
            border: '2px solid rgba(124, 58, 237, 0.65)',
            borderRadius: 999,
            padding: '6px 22px',
            boxShadow: '0 6px 20px rgba(124, 58, 237, 0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: 6,
              background: '#10B981',
              boxShadow: '0 0 10px #10B981',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#A7F3D0',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            02 • Como Funciona
          </span>
        </div>

        {/* Card 1: Introdução ("O Inovare Claw já vem pronto") */}
        {!showSteps ? (
          <div
            style={{
              width: '100%',
              opacity: interpolate(part1Spring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(part1Spring, [0, 1], [25, 0])}px)`,
              background: 'rgba(11, 13, 19, 0.94)',
              borderRadius: 24,
              border: '2px solid rgba(124, 58, 237, 0.5)',
              padding: '18px 24px',
              boxShadow: '0 12px 35px rgba(0, 0, 0, 0.75)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                width: 50,
                height: 50,
                borderRadius: 25,
                background: 'rgba(124, 58, 237, 0.25)',
                border: '1.5px solid #7C3AED',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
                flexShrink: 0,
              }}
            >
              ⚡
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <div
                style={{
                  fontFamily,
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                O Inovare Claw já vem pronto
              </div>
              {/* Subtítulo com contraste elevado em lilás claro (#D4BBFF) */}
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#D4BBFF',
                }}
              >
                ✓ Sem configuração complexa
              </div>
            </div>
          </div>
        ) : (
          /* Mockup de Interface do Agente Autônomo ("Show, Don't Tell" em tempo real) */
          <div
            style={{
              width: '100%',
              background: 'rgba(11, 13, 19, 0.95)',
              borderRadius: 22,
              border: '2px solid rgba(124, 58, 237, 0.6)',
              padding: '12px 18px',
              boxShadow: '0 12px 35px rgba(0, 0, 0, 0.8), 0 0 20px rgba(124, 58, 237, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            {/* Barra superior de terminal do Agente */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                paddingBottom: 6,
              }}
            >
              <div style={{display: 'flex', gap: 6, alignItems: 'center'}}>
                <div style={{width: 10, height: 10, borderRadius: 5, background: '#EF4444'}} />
                <div style={{width: 10, height: 10, borderRadius: 5, background: '#F59E0B'}} />
                <div style={{width: 10, height: 10, borderRadius: 5, background: '#10B981'}} />
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#CBD5E1',
                    marginLeft: 6,
                    letterSpacing: '0.5px',
                  }}
                >
                  INOVARE CLAW • AGENTE
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#34D399',
                  background: 'rgba(16, 185, 129, 0.2)',
                  padding: '2px 8px',
                  borderRadius: 6,
                }}
              >
                ● AUTÔNOMO
              </span>
            </div>

            {/* Passo 1 sincronizado com "Eu passo a tarefa" */}
            <div
              style={{
                opacity: interpolate(step1Spring, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(step1Spring, [0, 1], [-20, 0])}px)`,
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: 14,
                border: '1.5px solid rgba(124, 58, 237, 0.4)',
                padding: '8px 14px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <div
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 17,
                  background: '#7C3AED',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 22,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  flexShrink: 0,
                }}
              >
                1
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                }}
              >
                Eu passo a tarefa
              </span>
            </div>

            {/* Passo 2 sincronizado com "e o agente executa por mim" */}
            <div
              style={{
                opacity: interpolate(step2Spring, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(step2Spring, [0, 1], [20, 0])}px) scale(${frame >= 177 ? pulseExecution : 1})`,
                background: frame >= 177 ? 'rgba(16, 185, 129, 0.16)' : 'rgba(255, 255, 255, 0.04)',
                borderRadius: 14,
                border: frame >= 177 ? '2px solid #10B981' : '1.5px solid rgba(255, 255, 255, 0.1)',
                padding: '8px 14px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                boxShadow: frame >= 177 ? '0 0 15px rgba(16, 185, 129, 0.4)' : 'none',
              }}
            >
              <div
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: 17,
                  background: frame >= 177 ? '#10B981' : '#64748B',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily,
                  fontSize: 22,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  flexShrink: 0,
                }}
              >
                2
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: frame >= 177 ? '#A7F3D0' : '#E2E8F0',
                }}
              >
                O agente executa por mim ⚡
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
