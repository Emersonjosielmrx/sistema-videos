import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';
import {COLORS, SAFE_ZONE} from './types';

interface Cena0Props {
  fontFamily: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo (zoom 1.05 -> 1.16)
  const bgScale = interpolate(frame, [0, 160], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica residual contínua (>4% movimento)
  const floatY = Math.sin(frame / 12) * 5;
  const pulseScale = 1 + Math.sin(frame / 8) * 0.03;

  // Animação de entrada dos elementos
  // 1. Badge de alerta superior (~0.2s / frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Linha 1 de texto: "SEU CLIENTE" (~0.3s / frame 9)
  const title1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // 3. Título principal cinético: "DESISTE DO PEDIDO?" (~0.97s / frame 29)
  const punchSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 10, stiffness: 140},
  });

  // 4. Virada de texto na segunda fala: "QUANDO PRECISA INSTALAR ALGO?" (~2.0s / frame 60)
  const switchPhase = spring({
    frame: frame - 60,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 5. Card ilustrativo de atrito (~frame 72 / 2.4s)
  const cardSpring = spring({
    frame: frame - 72,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // 6. Gancho fixo superior (~frame 92 / 3.0s)
  const hookSpring = spring({
    frame: frame - 92,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Transição de saída suave no final da cena (frames 146 a 160)
  const exitOpacity = interpolate(frame, [146, 160], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const exitSlide = interpolate(frame, [146, 160], [0, -30], {
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
        backgroundColor: '#000000',
        fontFamily,
        opacity: exitOpacity,
        transform: `translateY(${exitSlide}px)`,
      }}
    >
      {/* Imagem de Fundo com Câmera Dinâmica e Cores Vivas (Regra 23) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu protetor moderado e localizado (não escurece a foto inteira - Regra 23) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(15,2,6,0.72) 0%, rgba(20,3,8,0.22) 28%, rgba(20,3,8,0.30) 65%, rgba(10,1,3,0.85) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* CONTEÚDO DENTRO DA SAFE ZONE (y=150 a y=1580, x=60 a 1020) */}

      {/* 1. Badge Superior de Alerta (y=175) */}
      {frame >= 6 && (
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: SAFE_ZONE.left,
            right: SAFE_ZONE.left,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(badgeSpring, 1),
            transform: `scale(${Math.max(0.7, badgeSpring)})`,
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 999,
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              border: `2px solid ${COLORS.primary}`,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
            }}
          >
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: '50%',
                backgroundColor: COLORS.danger,
                boxShadow: `0 0 12px ${COLORS.danger}`,
                transform: `scale(${pulseScale})`,
              }}
            />
            <span
              style={{
                color: COLORS.white,
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              Alerta Delivery
            </span>
          </div>
        </div>
      )}

      {/* 2. Bloco do Título Cinético Sincronizado com a Fala (y=260 a y=530) */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: SAFE_ZONE.left,
          right: SAFE_ZONE.left,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Fase 1: "Seu cliente desiste do pedido?" (0.3s a 2.0s) */}
        {frame < 60 ? (
          <>
            {frame >= 9 && (
              <div
                style={{
                  opacity: Math.min(title1Spring, 1),
                  transform: `translateY(${interpolate(title1Spring, [0, 1], [25, 0])}px)`,
                  marginBottom: 14,
                }}
              >
                <div
                  style={{
                    backgroundColor: 'rgba(18, 4, 9, 0.94)',
                    padding: '8px 24px',
                    borderRadius: 14,
                    border: '1.5px solid rgba(255, 255, 255, 0.16)',
                    boxShadow: '0 6px 18px rgba(0,0,0,0.6)',
                  }}
                >
                  <span
                    style={{
                      fontSize: 48,
                      fontWeight: 800,
                      color: COLORS.white,
                      letterSpacing: 1.5,
                      textTransform: 'uppercase',
                    }}
                  >
                    Seu cliente
                  </span>
                </div>
              </div>
            )}

            {frame >= 28 && (
              <div
                style={{
                  opacity: Math.min(punchSpring, 1),
                  transform: `scale(${Math.max(0.6, punchSpring)})`,
                  display: 'inline-block',
                }}
              >
                <div
                  style={{
                    backgroundColor: COLORS.primary,
                    padding: '16px 36px',
                    borderRadius: 22,
                    boxShadow: '0 16px 40px rgba(225, 29, 72, 0.65)',
                    border: '2px solid rgba(255, 255, 255, 0.35)',
                  }}
                >
                  <h1
                    style={{
                      margin: 0,
                      fontSize: 62,
                      fontWeight: 900,
                      color: COLORS.white,
                      lineHeight: 1.1,
                      letterSpacing: -0.5,
                      textTransform: 'uppercase',
                      textAlign: 'center',
                    }}
                  >
                    DESISTE DO PEDIDO?
                  </h1>
                </div>
              </div>
            )}
          </>
        ) : (
          /* Fase 2: "quando precisa instalar alguma coisa?" (2.0s a 5.0s) */
          <div
            style={{
              opacity: Math.min(switchPhase, 1),
              transform: `scale(${Math.max(0.7, switchPhase)})`,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <div
              style={{
                backgroundColor: 'rgba(18, 4, 9, 0.94)',
                padding: '8px 26px',
                borderRadius: 14,
                border: '1.5px solid rgba(255, 255, 255, 0.16)',
                boxShadow: '0 6px 18px rgba(0,0,0,0.6)',
              }}
            >
              <span
                style={{
                  fontSize: 44,
                  fontWeight: 800,
                  color: COLORS.white,
                  letterSpacing: 1.5,
                  textTransform: 'uppercase',
                }}
              >
                Quando precisa
              </span>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.94)',
                padding: '16px 36px',
                borderRadius: 22,
                boxShadow: '0 16px 40px rgba(239, 68, 68, 0.6)',
                border: '2px solid rgba(255, 255, 255, 0.35)',
              }}
            >
              <h1
                style={{
                  margin: 0,
                  fontSize: 58,
                  fontWeight: 900,
                  color: COLORS.white,
                  lineHeight: 1.1,
                  letterSpacing: -0.5,
                  textTransform: 'uppercase',
                  textAlign: 'center',
                }}
              >
                INSTALAR ALGO? ❌
              </h1>
            </div>
          </div>
        )}
      </div>

      {/* 3. Card Visual de Atrito (y=570 a y=880) — Design Leve, Limpo e Sem Poluição (Regra 10) */}
      {frame >= 72 && (
        <div
          style={{
            position: 'absolute',
            top: 570,
            left: SAFE_ZONE.left,
            right: SAFE_ZONE.left,
            opacity: Math.min(cardSpring, 1),
            transform: `translateY(${interpolate(cardSpring, [0, 1], [40, 0]) + floatY}px)`,
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: '100%',
              backgroundColor: 'rgba(18, 4, 9, 0.92)',
              borderRadius: 30,
              padding: '30px 28px',
              border: '2px solid rgba(255, 255, 255, 0.16)',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.85)',
              display: 'flex',
              alignItems: 'center',
              gap: 22,
            }}
          >
            {/* Ícone animado em squircle com borda branca (aprendizado 188e2265) */}
            <div
              style={{
                width: 90,
                height: 90,
                borderRadius: 26,
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                border: '3px solid #FFFFFF',
                boxShadow: '0 8px 24px rgba(239, 68, 68, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <span style={{fontSize: 46}}>📱❌</span>
            </div>

            {/* Texto de alto contraste e legibilidade */}
            <div>
              <div
                style={{
                  fontSize: 38,
                  fontWeight: 900,
                  color: COLORS.accent,
                  marginBottom: 6,
                  textTransform: 'uppercase',
                }}
              >
                Exigir Aplicativo?
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: COLORS.white,
                  lineHeight: 1.3,
                  maxWidth: 680,
                }}
              >
                Gera desistência imediata no momento do pedido.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Gancho de Tela Fixo no alto (y=920 a y=1020) */}
      {frame >= 92 && (
        <div
          style={{
            position: 'absolute',
            top: 920,
            left: SAFE_ZONE.left,
            right: SAFE_ZONE.left,
            opacity: Math.min(hookSpring, 1),
            transform: `translateY(${interpolate(hookSpring, [0, 1], [30, 0])}px)`,
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
              padding: '14px 32px',
              borderRadius: 20,
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              border: `2px solid ${COLORS.accent}`,
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.8)',
            }}
          >
            <span style={{fontSize: 34}}>💡</span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 800,
                color: COLORS.accent,
                letterSpacing: 0.5,
              }}
            >
              Cliente precisa baixar app?
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
