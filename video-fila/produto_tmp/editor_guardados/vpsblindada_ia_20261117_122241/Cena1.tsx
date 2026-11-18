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
import {AlertIcon} from './Icons';

interface Cena1Props {
  fontFamily: string;
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena 1: 4.51s a 12.21s = 7.70s (231 frames a 30 fps)
  // Enquadramento aberto no plano médio (busto/peito):
  // Redução suave de escala (0.92) com leve push-in (0.92 -> 0.95), liberando headroom no topo
  // e garantindo que o peito/camisa fique na faixa da legenda (y=1400-1550) com o rosto livre
  const baseScale = interpolate(frame, [0, 231], [0.92, 0.95], {
    extrapolateRight: 'clamp',
  });

  // Punch-in digital dinâmico sutil (+5%) aos ~3.3s (frame 98) sincronizado com "TUDO JÁ ESTAVA PARADO"
  const punchInSpring =
    frame >= 98
      ? spring({
          frame: frame - 98,
          fps,
          config: {damping: 15, mass: 0.5, stiffness: 150},
        }) * 0.05
      : 0;
  const videoScale = baseScale + punchInSpring;

  // Transição suave de corte de luminosidade entre cena 0 e cena 1 (frames 0 a 5)
  const enterFade = interpolate(frame, [0, 5], [0.65, 0], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge "O PROBLEMA" aos ~0.15s (frame 5)
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 130},
  });

  // Título 1: "ERRO INESPERADO NA OPERAÇÃO" entra aos ~0.3s (frame 10) e sai aos ~3.1s (frame 95)
  const title1In = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, mass: 0.7, stiffness: 130},
  });
  const title1Out = interpolate(frame, [88, 98], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Título 2: "TUDO JÁ ESTAVA PARADO" entra aos ~3.3s (frame 98) com punch-in sincronizado
  const title2In = spring({
    frame: frame - 98,
    fps,
    config: {damping: 14, mass: 0.7, stiffness: 130},
  });

  // Leve pulso contínuo para manter movimento gráfico ativo
  const alertPulse = interpolate(
    Math.sin((frame / 30) * Math.PI * 3.5),
    [-1, 1],
    [0.96, 1.04]
  );

  return (
    <AbsoluteFill style={{backgroundColor: '#0B1120'}}>
      {/* Fundo com desfoque controlado para transmitir solidez e autoridade técnica B2B */}
      <AbsoluteFill>
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(35px) brightness(0.35) saturate(1.2)',
            transform: 'scale(1.1)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 45%, rgba(14, 165, 233, 0.12) 0%, rgba(11, 17, 32, 0.7) 80%)',
          }}
        />
      </AbsoluteFill>

      {/* Vídeo do apresentador com enquadramento aberto (plano médio/busto), respiro no topo e peito livre para a legenda */}
      <AbsoluteFill
        style={{
          transform: `translateY(40px) scale(${videoScale})`,
          transformOrigin: '50% 50%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            borderRadius: 32,
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6)',
          }}
        />
      </AbsoluteFill>

      {/* Suavização da transição de luminosidade entre o fundo escuro da cena 0 e a cena 1 */}
      {enterFade > 0 && (
        <AbsoluteFill
          style={{
            backgroundColor: '#0B1120',
            opacity: enterFade,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Vinheta sutil superior APENAS na faixa y 0-320 para garantir contraste das letras */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 320,
          background:
            'linear-gradient(to bottom, rgba(11, 17, 32, 0.9) 0%, rgba(11, 17, 32, 0.6) 60%, rgba(11, 17, 32, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Gráficos SUPERIORES estritamente na faixa Safe Zone y 155 a 270 */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          zIndex: 50,
        }}
      >
        {/* Rótulo de contexto oficial do briefing */}
        {frame >= 5 && (
          <div
            style={{
              transform: `scale(${Math.max(0, badgeSpring * alertPulse)})`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '6px 20px',
              borderRadius: 20,
              backgroundColor: 'rgba(239, 68, 68, 0.25)',
              border: '2px solid rgba(239, 68, 68, 0.9)',
              boxShadow: '0 0 20px rgba(239, 68, 68, 0.45)',
              backdropFilter: 'blur(8px)',
            }}
          >
            <AlertIcon size={26} color="#EF4444" />
            <span
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: '#FECACA',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              O PROBLEMA
            </span>
          </div>
        )}

        {/* Título Superior 1: ERRO INESPERADO NA OPERAÇÃO (Frame 10 a 98) */}
        {frame >= 10 && frame < 98 && (
          <div
            style={{
              marginTop: 12,
              textAlign: 'center',
              transform: `translateY(${(1 - title1In) * 15}px)`,
              opacity: title1In * title1Out,
              backgroundColor: 'rgba(11, 17, 32, 0.92)',
              padding: '8px 22px',
              borderRadius: 16,
              border: '1.5px solid rgba(239, 68, 68, 0.6)',
              boxShadow: '0 8px 25px rgba(0,0,0,0.7)',
            }}
          >
            <div
              style={{
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textTransform: 'uppercase',
              }}
            >
              ERRO{' '}
              <span
                style={{
                  color: '#FFFFFF',
                  backgroundColor: '#EF4444',
                  padding: '2px 10px',
                  borderRadius: 8,
                }}
              >
                INESPERADO
              </span>{' '}
              NA OPERAÇÃO
            </div>
          </div>
        )}

        {/* Título Superior 2: TUDO JÁ ESTAVA PARADO (Frame 100 adiante) */}
        {frame >= 98 && (
          <div
            style={{
              marginTop: 12,
              textAlign: 'center',
              transform: `translateY(${(1 - title2In) * 15}px)`,
              opacity: title2In,
              backgroundColor: 'rgba(11, 17, 32, 0.92)',
              padding: '8px 22px',
              borderRadius: 16,
              border: '1.5px solid rgba(239, 68, 68, 0.6)',
              boxShadow: '0 8px 25px rgba(0,0,0,0.7)',
            }}
          >
            <div
              style={{
                fontSize: 42,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textTransform: 'uppercase',
              }}
            >
              TUDO JÁ ESTAVA{' '}
              <span
                style={{
                  color: '#FFFFFF',
                  backgroundColor: '#EF4444',
                  padding: '2px 10px',
                  borderRadius: 8,
                }}
              >
                PARADO
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
