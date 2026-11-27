import React from 'react';
import {interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena: 5.58s = ~167 frames
  // Ken Burns contínuo e perceptível (escala 1.02 a 1.15 + drift vertical constante)
  const bgScale = interpolate(frame, [0, 167], [1.02, 1.15], {extrapolateRight: 'clamp'});
  const bgY = interpolate(frame, [0, 167], [0, -35], {extrapolateRight: 'clamp'});

  // Ruptura visual no segundo 0: Gancho pop imediato (frame 0 a 3)
  const hookSpring = spring({
    frame: frame - 1,
    fps,
    config: {damping: 10, stiffness: 160},
  });

  // Linha 1: "PASSO AS" entra aos 0.3s (frame 9)
  const l1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Linha 2: "ROTINAS CHATAS" entra aos 0.7s (frame 21)
  const l2Spring = spring({
    frame: frame - 21,
    fps,
    config: {damping: 10, stiffness: 160},
  });

  // Linha 3: "DA SUA EMPRESA" entra aos 1.6s (frame 48)
  const l3Spring = spring({
    frame: frame - 48,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Linha 4: "PARA A IA EXECUTAR?" entra aos 2.3s (frame 69)
  const l4Spring = spring({
    frame: frame - 69,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Microanimação contínua nas cantoneiras e HUD (pulsação de brilho e respiração de escala)
  const cornerPulse = 1 + Math.sin(frame * 0.14) * 0.05;
  const cornerGlow = 8 + Math.sin(frame * 0.16) * 6;
  const borderOpacity = 0.45 + Math.sin(frame * 0.12) * 0.25;

  // Scanner de IA com alta frequência e glow dinâmico
  const scanY = interpolate(frame % 60, [0, 60], [15, 690]);
  const scanOpacity = interpolate(frame % 60, [0, 30, 60], [0.15, 0.65, 0.15]);

  // Floating idle contínuo em todo o bloco de texto para movimento constante (>4%)
  const textIdleY = Math.sin(frame * 0.08) * 4;

  // Transição de saída suave no final da cena (frames 155-167)
  const exitFade = interpolate(frame, [155, 167], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#070A12',
        opacity: exitFade,
      }}
    >
      {/* Imagem de fundo com Ken Burns contínuo */}
      <img
        src={staticFile('img_0.jpg')}
        alt="Escritório"
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          objectFit: 'cover',
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
        }}
      />

      {/* Overlay escuro protetor com iluminação de vinheta tecnológica */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 35%, rgba(15, 23, 42, 0.60) 0%, rgba(10, 14, 26, 0.88) 70%, rgba(5, 7, 14, 0.96) 100%)',
        }}
      />

      {/* Ondas sutis de feixe de luz dinâmico varrendo o fundo */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: interpolate(frame, [0, 167], [-200, 1000]),
          width: 300,
          height: 1920,
          background: 'linear-gradient(90deg, transparent, rgba(124, 58, 237, 0.12), transparent)',
          transform: 'skewX(-20deg)',
          pointerEvents: 'none',
        }}
      />

      {/* Brilho volumétrico roxo no centro */}
      <div
        style={{
          position: 'absolute',
          top: 520,
          left: 140,
          width: 800,
          height: 520,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(124, 58, 237, 0.32) 0%, transparent 70%)',
          filter: 'blur(50px)',
          pointerEvents: 'none',
        }}
      />

      {/* Grade tecnológica de cantos (HUD IA) com respiração e microanimação */}
      <div
        style={{
          position: 'absolute',
          top: 330,
          left: 60,
          width: 960,
          height: 740,
          border: `1px solid rgba(124, 58, 237, ${borderOpacity})`,
          borderRadius: 32,
          pointerEvents: 'none',
        }}
      >
        {/* Cantoneiras estilizadas com pulso contínuo de brilho e escala */}
        <div
          style={{
            position: 'absolute',
            top: -3,
            left: -3,
            width: 28,
            height: 28,
            borderTop: '3.5px solid #A855F7',
            borderLeft: '3.5px solid #A855F7',
            borderTopLeftRadius: 32,
            boxShadow: `0 0 ${cornerGlow}px rgba(168, 85, 247, 0.85)`,
            transform: `scale(${cornerPulse})`,
            transformOrigin: 'top left',
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: -3,
            right: -3,
            width: 28,
            height: 28,
            borderTop: '3.5px solid #A855F7',
            borderRight: '3.5px solid #A855F7',
            borderTopRightRadius: 32,
            boxShadow: `0 0 ${cornerGlow}px rgba(168, 85, 247, 0.85)`,
            transform: `scale(${cornerPulse})`,
            transformOrigin: 'top right',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: -3,
            left: -3,
            width: 28,
            height: 28,
            borderBottom: '3.5px solid #A855F7',
            borderLeft: '3.5px solid #A855F7',
            borderBottomLeftRadius: 32,
            boxShadow: `0 0 ${cornerGlow}px rgba(168, 85, 247, 0.85)`,
            transform: `scale(${cornerPulse})`,
            transformOrigin: 'bottom left',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: -3,
            right: -3,
            width: 28,
            height: 28,
            borderBottom: '3.5px solid #A855F7',
            borderRight: '3.5px solid #A855F7',
            borderBottomRightRadius: 32,
            boxShadow: `0 0 ${cornerGlow}px rgba(168, 85, 247, 0.85)`,
            transform: `scale(${cornerPulse})`,
            transformOrigin: 'bottom right',
          }}
        />

        {/* Linha de varredura (scanner) ativa */}
        <div
          style={{
            position: 'absolute',
            top: scanY,
            left: 20,
            right: 20,
            height: 2.5,
            background: 'linear-gradient(90deg, transparent, #C084FC, transparent)',
            boxShadow: '0 0 20px #A855F7, 0 0 8px #C084FC',
            opacity: scanOpacity,
          }}
        />
      </div>

      {/* Badge Superior: Gancho de Tela com Pop Imediato desde o início (y=175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${Math.max(0.01, hookSpring)})`,
          transformOrigin: 'center center',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 28px',
            borderRadius: 999,
            background: '#0F172A',
            border: '2px solid #7C3AED',
            boxShadow: '0 8px 28px rgba(124, 58, 237, 0.55), 0 0 15px rgba(168, 85, 247, 0.35)',
          }}
        >
          {/* Ponto pulsante neon */}
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#A855F7',
              boxShadow: '0 0 12px #C084FC',
              transform: `scale(${1 + Math.sin(frame * 0.25) * 0.25})`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Rotina chata? Delegue
          </span>
        </div>
      </div>

      {/* Container Principal do Texto Cinético (Pergunta) com respiração contínua */}
      <div
        style={{
          position: 'absolute',
          top: 380,
          left: 70,
          right: 70,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 20,
          transform: `translateY(${textIdleY}px)`,
        }}
      >
        {/* Linha 1: "PASSO AS" */}
        {frame >= 9 && (
          <div
            style={{
              transform: `scale(${l1Spring}) translateY(${interpolate(l1Spring, [0, 1], [30, 0])}px)`,
              opacity: l1Spring,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 48,
                fontWeight: 800,
                color: '#E2E8F0',
                letterSpacing: '0.03em',
                textTransform: 'uppercase',
                textShadow: '0 4px 12px rgba(0,0,0,0.85)',
              }}
            >
              Passo as
            </span>
          </div>
        )}

        {/* Linha 2: "ROTINAS CHATAS" (Elemento com maior impacto visual) */}
        {frame >= 21 && (
          <div
            style={{
              transform: `scale(${l2Spring})`,
              transformOrigin: 'center center',
            }}
          >
            <div
              style={{
                background: 'linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)',
                padding: '14px 38px',
                borderRadius: 24,
                border: '2px solid rgba(255, 255, 255, 0.3)',
                boxShadow: '0 14px 40px rgba(124, 58, 237, 0.75), 0 0 24px rgba(168, 85, 247, 0.5)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 74,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '0.02em',
                  lineHeight: 1.1,
                  display: 'block',
                }}
              >
                ROTINAS CHATAS
              </span>
            </div>
          </div>
        )}

        {/* Linha 3: "DA SUA EMPRESA" */}
        {frame >= 48 && (
          <div
            style={{
              transform: `scale(${l3Spring}) translateY(${interpolate(l3Spring, [0, 1], [25, 0])}px)`,
              opacity: l3Spring,
            }}
          >
            <span
              style={{
                fontFamily,
                fontSize: 52,
                fontWeight: 800,
                color: '#F8FAFC',
                letterSpacing: '0.03em',
                textTransform: 'uppercase',
                textShadow: '0 4px 14px rgba(0,0,0,0.85)',
              }}
            >
              da empresa
            </span>
          </div>
        )}

        {/* Linha 4: "PARA A IA EXECUTAR?" */}
        {frame >= 69 && (
          <div
            style={{
              transform: `scale(${l4Spring})`,
              transformOrigin: 'center center',
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 16,
                background: 'rgba(15, 23, 42, 0.94)',
                border: '2px solid #8B5CF6',
                padding: '16px 36px',
                borderRadius: 24,
                boxShadow: '0 10px 32px rgba(0, 0, 0, 0.8), 0 0 20px rgba(139, 92, 246, 0.3)',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 62,
                  fontWeight: 900,
                  color: '#C084FC',
                  textTransform: 'uppercase',
                  letterSpacing: '0.02em',
                }}
              >
                para a IA executar?
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
