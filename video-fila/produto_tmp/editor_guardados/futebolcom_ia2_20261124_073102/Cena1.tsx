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

interface Cena1Props {
  fontFamily: string;
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera: zoom e pan lateral suave (scale 1.05 -> 1.18, panX 0 -> -35px)
  const bgScale = interpolate(frame, [0, 195], [1.05, 1.18], {
    extrapolateRight: 'clamp',
  });
  const bgPanX = interpolate(frame, [0, 195], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Micro-dinâmica residual contínua (>4% movimento)
  const floatCard1 = Math.sin(frame / 14) * 5;
  const floatCard2 = Math.cos(frame / 14) * 5;

  // Entrada dos elementos
  // 1. Rótulo superior "O PROBLEMA" (~frame 6)
  const rotuloSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 2. Título da cena (~frame 16)
  const titleSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // 3. Simulação visual do download travado / atrito (~frame 42 / fala "desistisse")
  const downloadSimSpring = spring({
    frame: frame - 40,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // 4. Revelação do que o cliente realmente quer (~frame 110 / fala "só para ver o meu cardápio")
  const menuCardSpring = spring({
    frame: frame - 108,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Progresso do download simulado (trava em 18% para ilustrar o atrito)
  const downloadProgress = interpolate(frame, [45, 95], [0, 18], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Transições de entrada e saída
  const enterOpacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const exitOpacity = interpolate(frame, [180, 195], [1, 0], {
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
        opacity: Math.min(enterOpacity, exitOpacity),
      }}
    >
      {/* Imagem de Fundo com Pan e Zoom Contínuos (Vibrante - Regra 23) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateX(${bgPanX}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_1.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu protetor moderado (preserva as cores do restaurante - Regra 23) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(20,3,8,0.78) 0%, rgba(25,4,10,0.25) 28%, rgba(20,3,8,0.30) 65%, rgba(10,1,3,0.88) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* 1. Rótulo Obrigatório da Cena (y=175) */}
      {frame >= 6 && (
        <div
          style={{
            position: 'absolute',
            top: 175,
            left: SAFE_ZONE.left,
            right: SAFE_ZONE.left,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(rotuloSpring, 1),
            transform: `scale(${Math.max(0.7, rotuloSpring)})`,
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
              border: `2px solid ${COLORS.danger}`,
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.75)',
            }}
          >
            <span style={{fontSize: 26}}>⚠️</span>
            <span
              style={{
                color: COLORS.white,
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              O Problema
            </span>
          </div>
        </div>
      )}

      {/* 2. Título Superior com Box Protetor Opaco (y=255) - Regras 5 e 6 */}
      {frame >= 16 && (
        <div
          style={{
            position: 'absolute',
            top: 255,
            left: SAFE_ZONE.left,
            right: SAFE_ZONE.left,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(titleSpring, 1),
            transform: `translateY(${interpolate(titleSpring, [0, 1], [25, 0])}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(20, 4, 10, 0.94)',
              padding: '14px 34px',
              borderRadius: 22,
              border: '2px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 12px 32px rgba(0,0,0,0.8)',
              textAlign: 'center',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 48,
                fontWeight: 900,
                color: COLORS.white,
                lineHeight: 1.15,
                textTransform: 'uppercase',
                letterSpacing: -0.5,
              }}
            >
              O ATRITO DE{' '}
              <span
                style={{
                  color: COLORS.accent,
                  backgroundColor: 'rgba(250, 204, 21, 0.15)',
                  padding: '2px 12px',
                  borderRadius: 10,
                  border: '1.5px solid rgba(250, 204, 21, 0.4)',
                }}
              >
                BAIXAR APP
              </span>
            </h2>
          </div>
        </div>
      )}

      {/* 3. Composição Visual Fluida Nativa de Reels (y=375 a y=1100) — SEM SLIDES CORPORATIVOS (Regra 11) */}
      <div
        style={{
          position: 'absolute',
          top: 375,
          left: SAFE_ZONE.left,
          right: SAFE_ZONE.left,
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
        }}
      >
        {/* Card 1: Simulação da Barreira do App no Celular do Cliente */}
        {frame >= 40 && (
          <div
            style={{
              opacity: Math.min(downloadSimSpring, 1),
              transform: `translateY(${interpolate(downloadSimSpring, [0, 1], [40, 0]) + floatCard1}px)`,
              backgroundColor: 'rgba(24, 4, 10, 0.94)',
              borderRadius: 28,
              padding: '28px 30px',
              border: `2px solid rgba(239, 68, 68, 0.65)`,
              boxShadow: '0 18px 45px rgba(0, 0, 0, 0.85)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 18,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: 18,
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    border: '2px solid rgba(239, 68, 68, 0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 30,
                  }}
                >
                  📱
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 36,
                      fontWeight: 900,
                      color: COLORS.white,
                      textTransform: 'uppercase',
                    }}
                  >
                    Exigir Download
                  </div>
                  <div
                    style={{
                      fontSize: 30,
                      fontWeight: 600,
                      color: '#F87171',
                    }}
                  >
                    Memória cheia • Espera demorada
                  </div>
                </div>
              </div>

              <div
                style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.25)',
                  padding: '6px 14px',
                  borderRadius: 8,
                  color: COLORS.danger,
                  fontWeight: 800,
                  fontSize: 26,
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                }}
              >
                DESISTÊNCIA
              </div>
            </div>

            {/* Barra simulada de download travado */}
            <div
              style={{
                width: '100%',
                height: 14,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: 999,
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <div
                style={{
                  width: `${downloadProgress}%`,
                  height: '100%',
                  backgroundColor: COLORS.danger,
                  boxShadow: `0 0 10px ${COLORS.danger}`,
                }}
              />
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginTop: 10,
                fontSize: 26,
                fontWeight: 700,
                color: COLORS.textMuted,
              }}
            >
              <span>Baixando pacote...</span>
              <span style={{color: COLORS.danger}}>Travado em 18% ❌</span>
            </div>
          </div>
        )}

        {/* Card 2: O Contraste — O Cliente Só Quer Ver o Cardápio (Entra na fala "só para ver o meu cardápio") */}
        {frame >= 108 && (
          <div
            style={{
              opacity: Math.min(menuCardSpring, 1),
              transform: `translateY(${interpolate(menuCardSpring, [0, 1], [40, 0]) + floatCard2}px)`,
              backgroundColor: 'rgba(18, 4, 9, 0.94)',
              borderRadius: 28,
              padding: '28px 30px',
              border: `2px solid ${COLORS.accent}`,
              boxShadow: '0 18px 45px rgba(0, 0, 0, 0.85)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 18,
              }}
            >
              <div
                style={{
                  width: 68,
                  height: 68,
                  borderRadius: 20,
                  backgroundColor: 'rgba(250, 204, 21, 0.2)',
                  border: `2px solid ${COLORS.accent}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 36,
                  flexShrink: 0,
                }}
              >
                🍔
              </div>
              <div>
                <div
                  style={{
                    fontSize: 38,
                    fontWeight: 900,
                    color: COLORS.accent,
                    textTransform: 'uppercase',
                    marginBottom: 4,
                  }}
                >
                  Só Quer Ver o Cardápio!
                </div>
                <div
                  style={{
                    fontSize: 32,
                    fontWeight: 600,
                    color: COLORS.white,
                    lineHeight: 1.3,
                  }}
                >
                  Sem baixar nada, direto no celular com fotos.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
