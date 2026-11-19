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

interface Cena1Props {
  fontFamily: string;
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração local da cena: ~245 frames (5.35s a 13.53s)
  // Transição de entrada dinâmica (Whip Pan lateral da direita para esquerda, frames 0 a 12)
  const whipInX = interpolate(frame, [0, 12], [1080, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const whipBlur = interpolate(frame, [0, 6, 12], [8, 4, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Dinamismo de câmera:
  // Plano inicial (frames 0 a 153): push-in contínuo de 1.02x para 1.06x
  // Punch-in dinâmico (+9% zoom -> 1.15x) exatamente no momento em que a fala muda para "e uma resposta padrão não serve" (frame 154)
  const isPunchIn = frame >= 154;
  const punchImpact =
    isPunchIn && frame < 160 ? (frame % 2 === 0 ? 3 : -3) : 0;
  const videoScale = isPunchIn
    ? interpolate(frame, [154, 245], [1.15, 1.20], {
        extrapolateRight: 'clamp',
      })
    : interpolate(frame, [0, 154], [1.02, 1.06], {
        extrapolateRight: 'clamp',
      });

  // Micro-movimento de respiro no topo
  const floatY = Math.sin(frame / 14) * 4;

  // Entrada do Badge (frame 10 a 25)
  const badgeSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Bloco 1: "Cada comunidade tem seu jeito de falar" (fala inicia em ~6.38s -> local 1.03s -> frame 31)
  const part1In = spring({
    frame: frame - 28,
    fps,
    config: {damping: 13, stiffness: 130},
  });
  // Saída do Bloco 1 antes do Bloco 2 (~9.8s -> local frame 136 a 145)
  const part1Out = interpolate(frame, [136, 145], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Bloco 2: "Resposta padrão não serve para todo mundo" (entra no frame 146 e está pleno na fala em frame 154)
  const part2In = spring({
    frame: frame - 146,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Ênfase pop no "NÃO SERVE" durante o punch-in (frame 154)
  const naoServeSpring = spring({
    frame: frame - 154,
    fps,
    config: {damping: 10, stiffness: 160},
  });

  // Saída sutil da cena nos últimos 10 frames
  const exitOpacity = interpolate(frame, [235, 245], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#111827',
        fontFamily,
        opacity: exitOpacity,
        transform: `translateX(${whipInX}px)`,
        filter: whipBlur > 0 ? `blur(${whipBlur}px)` : 'none',
        overflow: 'hidden',
      }}
    >
      {/* Vídeo do dono em tela cheia com zoom contínuo e punch-in dramático
          startFrom={5} ajusta o ponto de corte para evitar o piscar de olhos semicerrados em q04 (frame 210) */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${punchImpact}px)`,
          transformOrigin: '50% 45%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          startFrom={5}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Vinheta sutil superior apenas para contraste do texto no topo, preservando a iluminação do rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(to bottom, rgba(17, 24, 39, 0.88) 0%, rgba(17, 24, 39, 0.45) 70%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {/* TOPO INFORMATIVO (y=160 a 450) — ROSTO 100% PROTEGIDO ABAIXO DE y=480 */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
          transform: `translateY(${floatY}px)`,
          zIndex: 30,
        }}
      >
        {/* Badge da Etapa */}
        <div
          style={{
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            background: 'rgba(239, 68, 68, 0.18)',
            border: '1.5px solid rgba(239, 68, 68, 0.7)',
            boxShadow: '0 0 20px rgba(239, 68, 68, 0.25)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              color: '#FCA5A5',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            ETAPA 1/3 • O PROBLEMA
          </span>
        </div>

        {/* Card 1: Cada comunidade tem o seu jeito de falar */}
        {frame < 156 && (
          <div
            style={{
              opacity: part1In * part1Out,
              transform: `translateY(${(1 - part1In) * 25}px) scale(${0.92 + part1In * 0.08})`,
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid rgba(20, 184, 166, 0.5)',
              borderRadius: 24,
              padding: '18px 32px',
              textAlign: 'center',
              boxShadow:
                '0 12px 35px rgba(0, 0, 0, 0.7), 0 0 25px rgba(20, 184, 166, 0.2)',
              maxWidth: 940,
            }}
          >
            <div
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textWrap: 'balance',
              }}
            >
              CADA COMUNIDADE TEM O SEU{' '}
              <span
                style={{
                  color: '#14B8A6',
                  textDecoration: 'underline',
                  textUnderlineOffset: 6,
                }}
              >
                JEITO DE FALAR
              </span>
            </div>
          </div>
        )}

        {/* Card 2: Resposta padrão não serve para todo mundo */}
        {frame >= 150 && (
          <div
            style={{
              opacity: part2In,
              transform: `translateY(${(1 - part2In) * 25}px) scale(${0.92 + part2In * 0.08})`,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '2px solid rgba(239, 68, 68, 0.6)',
              borderRadius: 24,
              padding: '18px 32px',
              textAlign: 'center',
              boxShadow:
                '0 12px 35px rgba(0, 0, 0, 0.7), 0 0 25px rgba(239, 68, 68, 0.25)',
              maxWidth: 940,
            }}
          >
            <div
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textWrap: 'balance',
              }}
            >
              RESPOSTA PADRÃO{' '}
              <span
                style={{
                  display: 'inline-block',
                  transform: isPunchIn
                    ? `scale(${1 + naoServeSpring * 0.12})`
                    : 'none',
                  background: 'rgba(239, 68, 68, 0.25)',
                  color: '#F87171',
                  padding: '2px 14px',
                  borderRadius: 12,
                  border: '1.5px solid rgba(239, 68, 68, 0.7)',
                  boxShadow: isPunchIn
                    ? '0 0 20px rgba(239, 68, 68, 0.6)'
                    : 'none',
                }}
              >
                NÃO SERVE
              </span>{' '}
              PARA TODO MUNDO
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
