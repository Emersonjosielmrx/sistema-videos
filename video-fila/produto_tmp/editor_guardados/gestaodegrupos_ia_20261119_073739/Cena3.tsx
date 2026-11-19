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

interface Cena3Props {
  fontFamily: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração local da cena: ~245 frames (20.26s a 28.44s)
  // Enquadramento equilibrado com respiro confortável de headroom (restaura o padrão da Cena 1):
  // Plano com escala reduzida (1.08x a 1.12x) e punch-in dinâmico (+10% -> 1.18x) na fala clímax "ZERO AJUSTE MANUAL" (frame 140)
  const isPunchIn = frame >= 140;
  const punchImpact =
    isPunchIn && frame < 146 ? (frame % 2 === 0 ? 3 : -3) : 0;
  const videoScale = isPunchIn
    ? interpolate(frame, [140, 245], [1.18, 1.23], {
        extrapolateRight: 'clamp',
      })
    : interpolate(frame, [0, 140], [1.08, 1.12], {
        extrapolateRight: 'clamp',
      });

  // Micro-movimento de respiro no topo
  const floatY = Math.sin(frame / 14) * 3;

  // Entrada do Badge (frame 0 a 15)
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Bloco 1: "Hoje o bot fala com cada comunidade do jeito certo" (fala inicia em ~20.55s -> local 0.29s -> frame 9)
  const part1In = spring({
    frame: frame - 8,
    fps,
    config: {damping: 13, stiffness: 130},
  });
  // Saída do Bloco 1 antes do Bloco 2 (~24.6s -> local 4.34s -> frame 130)
  const part1Out = interpolate(frame, [128, 138], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Bloco 2: "e eu não preciso ajustar nada na mão" (fala inicia em ~24.97s -> local 4.71s -> frame 141)
  const part2In = spring({
    frame: frame - 138,
    fps,
    config: {damping: 12, stiffness: 140},
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
        overflow: 'hidden',
      }}
    >
      {/* Vídeo do dono em tela cheia com headroom ajustado (+60px para baixo e escala equilibrada),
          restaurando o respiro confortável visto na Cena 1 */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale}) translateY(${88 + punchImpact}px)`,
          transformOrigin: '50% 38%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'contrast(1.10) saturate(1.14) brightness(0.96)',
          }}
        />
        {/* Tratamento de cor: Dimming na lateral esquerda para amenizar as altas luzes estouradas da janela */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            bottom: 0,
            width: '45%',
            background:
              'linear-gradient(to right, rgba(17, 24, 39, 0.45) 0%, rgba(17, 24, 39, 0.18) 50%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
        {/* Vinheta sutil superior apenas para contraste do texto no topo, preservando a iluminação do rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 460,
            background:
              'linear-gradient(to bottom, rgba(17, 24, 39, 0.88) 0%, rgba(17, 24, 39, 0.45) 70%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {/* TOPO INFORMATIVO ELEVADO (top: 140 — subido 25px para folga total de headroom sobre o cabelo) */}
      <div
        style={{
          position: 'absolute',
          top: 140,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
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
            padding: '8px 22px',
            borderRadius: 30,
            background: 'rgba(20, 184, 166, 0.18)',
            border: '1.5px solid rgba(20, 184, 166, 0.7)',
            boxShadow: '0 0 20px rgba(20, 184, 166, 0.3)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#14B8A6',
              boxShadow: '0 0 10px #14B8A6',
            }}
          />
          <span
            style={{
              color: '#5EEAD4',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            ETAPA 3/3 • O RESULTADO
          </span>
        </div>

        {/* Card 1: Fala com cada comunidade do jeito certo */}
        {frame < 140 && (
          <div
            style={{
              opacity: part1In * part1Out,
              transform: `translateY(${(1 - part1In) * 25}px) scale(${0.92 + part1In * 0.08})`,
              background: 'rgba(17, 24, 39, 0.94)',
              border: '2px solid rgba(20, 184, 166, 0.5)',
              borderRadius: 22,
              padding: '14px 28px',
              textAlign: 'center',
              boxShadow:
                '0 12px 35px rgba(0, 0, 0, 0.7), 0 0 25px rgba(20, 184, 166, 0.2)',
              maxWidth: 940,
            }}
          >
            <div
              style={{
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textWrap: 'balance',
              }}
            >
              FALA COM CADA COMUNIDADE{' '}
              <span
                style={{
                  color: '#14B8A6',
                  background: 'rgba(20, 184, 166, 0.15)',
                  padding: '2px 14px',
                  borderRadius: 12,
                  border: '1px solid rgba(20, 184, 166, 0.4)',
                }}
              >
                DO JEITO CERTO
              </span>
            </div>
          </div>
        )}

        {/* Card 2: Zero ajuste manual: tudo no automático */}
        {frame >= 134 && (
          <div
            style={{
              opacity: part2In,
              transform: `translateY(${(1 - part2In) * 25}px) scale(${0.92 + part2In * 0.08})`,
              background: 'rgba(17, 24, 39, 0.95)',
              border: '2px solid rgba(20, 184, 166, 0.6)',
              borderRadius: 22,
              padding: '14px 28px',
              textAlign: 'center',
              boxShadow:
                '0 12px 35px rgba(0, 0, 0, 0.7), 0 0 25px rgba(20, 184, 166, 0.25)',
              maxWidth: 940,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 16,
            }}
          >
            <div
              style={{
                width: 42,
                height: 42,
                borderRadius: '50%',
                backgroundColor: 'rgba(20, 184, 166, 0.25)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#14B8A6',
                fontSize: 32,
                fontWeight: 900,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
            <div
              style={{
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textWrap: 'balance',
              }}
            >
              ZERO AJUSTE MANUAL:{' '}
              <span
                style={{
                  background:
                    'linear-gradient(135deg, #14B8A6 0%, #0D9488 100%)',
                  color: '#FFFFFF',
                  padding: '4px 18px',
                  borderRadius: 14,
                  boxShadow: '0 4px 16px rgba(20, 184, 166, 0.4)',
                }}
              >
                TUDO NO AUTOMÁTICO
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
