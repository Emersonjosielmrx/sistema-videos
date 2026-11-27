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

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Transição de entrada suave com slide lateral direcional para quebrar o corte seco
  const slideInX = interpolate(frame, [0, 9], [60, 0], {
    extrapolateRight: 'clamp',
  });

  // Push-in contínuo da câmera (1.14 a 1.20) enquadrando mais no apresentador e atenuando as prateleiras
  const videoScale = interpolate(frame, [0, 235], [1.14, 1.20], {
    extrapolateRight: 'clamp',
  });
  const videoTranslateY = interpolate(frame, [0, 235], [20, 10], {
    extrapolateRight: 'clamp',
  });

  // Microdinâmica constante
  const pulseScale = 1 + Math.sin(frame / 12) * 0.012;

  // Entrada do badge de rótulo (frame 0)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada da 1ª parte: "Eu não precisei aprender nada técnico" (22.783s - 21.90s = 0.883s = frame ~26)
  const part1Spring = spring({
    frame: frame - 26,
    fps,
    config: {damping: 13, stiffness: 125},
  });

  // Entrada da 2ª parte: "Hoje o agente trabalha sozinho e eu cuido do meu negócio" (26.143s - 21.90s = 4.243s = frame ~127)
  const part2Spring = spring({
    frame: frame - 127,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const isPart2 = frame >= 127;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0B0D13',
        overflow: 'hidden',
        transform: `translateX(${slideInX}px)`,
      }}
    >
      {/* Vídeo do apresentador com enquadramento mais próximo e push-in */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: 'center 40%',
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
        {/* Vinheta corporativa profunda para unificar a direção de arte com a identidade escura da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 40%, rgba(11, 13, 19, 0.3) 0%, rgba(11, 13, 19, 0.82) 65%, rgba(11, 13, 19, 0.98) 100%)',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11, 13, 19, 0.85) 0%, rgba(11, 13, 19, 0) 25%, rgba(11, 13, 19, 0) 70%, rgba(11, 13, 19, 0.92) 100%)',
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {/* Faixa superior na Safe Zone (y 160 a 430), livre da cabeça do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 70,
          right: 90,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
        }}
      >
        {/* Badge "03 • O RESULTADO NO NEGÓCIO" */}
        <div
          style={{
            opacity: interpolate(badgeSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(badgeSpring, [0, 1], [-15, 0])}px) scale(${pulseScale})`,
            background: 'rgba(11, 13, 19, 0.95)',
            border: '2px solid rgba(124, 58, 237, 0.65)',
            borderRadius: 999,
            padding: '8px 24px',
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
              background: '#8B5CF6',
              boxShadow: '0 0 10px #8B5CF6',
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#EDE9FE',
              letterSpacing: '1px',
              textTransform: 'uppercase',
            }}
          >
            03 • O Resultado
          </span>
        </div>

        {/* Card Dinâmico no Topo */}
        {!isPart2 ? (
          <div
            style={{
              width: '100%',
              opacity: interpolate(part1Spring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(part1Spring, [0, 1], [25, 0])}px)`,
              background: 'rgba(11, 13, 19, 0.94)',
              borderRadius: 24,
              border: '2px solid rgba(255, 255, 255, 0.15)',
              padding: '20px 28px',
              boxShadow: '0 12px 35px rgba(0, 0, 0, 0.75)',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
            }}
          >
            {/* Ícone de verificação com alto contraste: fundo verde brilhante e traço em branco puro */}
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 26,
                background: '#10B981',
                border: '2px solid #34D399',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                boxShadow: '0 0 16px rgba(16, 185, 129, 0.6)',
                flexShrink: 0,
              }}
            >
              ✓
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
                Sem aprender nada técnico
              </div>
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#A7F3D0',
                }}
              >
                Pronto para uso imediato
              </div>
            </div>
          </div>
        ) : (
          <div
            style={{
              width: '100%',
              opacity: interpolate(part2Spring, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(part2Spring, [0, 1], [25, 0])}px)`,
              background: 'rgba(11, 13, 19, 0.94)',
              borderRadius: 24,
              border: '2px solid rgba(124, 58, 237, 0.6)',
              padding: '20px 28px',
              boxShadow: '0 12px 35px rgba(124, 58, 237, 0.35)',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 26,
                background: 'rgba(124, 58, 237, 0.35)',
                border: '1.5px solid #7C3AED',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 28,
                flexShrink: 0,
              }}
            >
              🚀
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
              <div
                style={{
                  fontFamily,
                  fontSize: 42,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                O agente trabalha sozinho
              </div>
              {/* Alinhado em 1ª pessoa com a locução do dono ('...e eu cuido do meu negócio') */}
              <div
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#DDD6FE',
                }}
              >
                E eu cuido do meu negócio 💼
              </div>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
