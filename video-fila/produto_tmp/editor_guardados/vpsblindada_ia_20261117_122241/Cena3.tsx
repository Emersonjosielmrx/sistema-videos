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
import {BotIcon, CheckIcon, ShieldIcon} from './Icons';

interface Cena3Props {
  fontFamily: string;
}

export const Cena3: React.FC<Cena3Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Duração da cena 3: 18.57s a 25.37s = 6.80s (204 frames a 30 fps)
  // Variação de corte em relação à Cena 1: punch-in digital (+12%) com enquadramento
  // deslocado para a esquerda (translateX: -160px), liberando totalmente a lateral direita (ar livre)
  const baseScale = interpolate(frame, [0, 204], [1.06, 1.12], {
    extrapolateRight: 'clamp',
  });

  // Entrada do card flutuante do Bot Sentinela sincronizado com a locução ("o robô vigiando", ~frame 130)
  // Entra com slide lateral com overshoot e scale spring ágil
  const holoCardSpring = spring({
    frame: frame - 130,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 140},
  });
  const holoSlideX = interpolate(holoCardSpring, [0, 1], [80, 0]);
  const holoFloat = Math.sin((frame / 30) * Math.PI * 2) * 4;

  // Efeito contínuo de radar/ping pulsando no ponto verde de 'Monitoramento Ativo'
  const pingScale = interpolate((frame % 30) / 30, [0, 1], [1, 2.8]);
  const pingOpacity = interpolate((frame % 30) / 30, [0, 1], [0.8, 0]);

  // Entrada do Badge "O RESULTADO" aos ~0.15s (frame 5)
  const badgeSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, mass: 0.6, stiffness: 130},
  });

  // Título 1: "NÃO FICO MAIS NO ESCURO" entra aos ~0.3s (frame 9) e sai aos ~2.8s (frame 85)
  const title1In = spring({
    frame: frame - 9,
    fps,
    config: {damping: 14, mass: 0.7, stiffness: 130},
  });
  const title1Out = interpolate(frame, [80, 88], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Título 2: "SERVIDOR SEGURO + ROBÔ VIGIANDO" entra aos ~3.0s (frame 88)
  const title2In = spring({
    frame: frame - 88,
    fps,
    config: {damping: 14, mass: 0.7, stiffness: 130},
  });

  // Pulso sutil no indicador de sucesso
  const successPulse = interpolate(
    Math.sin((frame / 30) * Math.PI * 3.5),
    [-1, 1],
    [0.95, 1.05]
  );

  return (
    <AbsoluteFill style={{backgroundColor: '#0B1120'}}>
      {/* Fundo com vídeo desfocado para preenchimento de bordas do punch-in */}
      <AbsoluteFill>
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
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
              'radial-gradient(circle at 65% 45%, rgba(14, 165, 233, 0.15) 0%, rgba(11, 17, 32, 0.75) 80%)',
          }}
        />
      </AbsoluteFill>

      {/* Vídeo do apresentador com punch-in (+12%) e deslocado à esquerda (-220px), liberando amplo respiro na lateral direita */}
      <AbsoluteFill
        style={{
          transform: `translateX(-220px) translateY(40px) scale(${baseScale})`,
          transformOrigin: '50% 50%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
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

      {/* Card Flutuante Oficial do BOT SENTINELA:
          Entra sincronizado no frame 130 quando a locução cita "o robô vigiando",
          posicionado na lateral direita com folga total do apresentador (zero sobreposição) */}
      {frame >= 130 && (
        <div
          style={{
            position: 'absolute',
            top: 580,
            right: 50,
            width: 300,
            padding: '16px 20px',
            borderRadius: 22,
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            border: '2px solid rgba(16, 185, 129, 0.85)',
            boxShadow:
              '0 14px 40px rgba(0, 0, 0, 0.85), 0 0 25px rgba(16, 185, 129, 0.4)',
            backdropFilter: 'blur(10px)',
            transform: `translateX(${holoSlideX}px) translateY(${holoFloat}px) scale(${holoCardSpring})`,
            opacity: holoCardSpring,
            zIndex: 45,
            fontFamily,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginBottom: 12,
            }}
          >
            <div
              style={{
                width: 46,
                height: 46,
                borderRadius: 23,
                backgroundColor: 'rgba(16, 185, 129, 0.25)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1.5px solid #10B981',
                boxShadow: '0 0 12px rgba(16, 185, 129, 0.5)',
              }}
            >
              <BotIcon size={30} color="#34D399" />
            </div>
            <div>
              <div style={{fontSize: 28, fontWeight: 900, color: '#34D399', letterSpacing: 1}}>
                BOT SENTINELA
              </div>
            </div>
          </div>

          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 10,
              backgroundColor: 'rgba(16, 185, 129, 0.2)',
              border: '1px solid rgba(16, 185, 129, 0.5)',
              padding: '6px 14px',
              borderRadius: 12,
            }}
          >
            <div style={{position: 'relative', width: 12, height: 12}}>
              {/* Ponto fixo verde */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: 6,
                  backgroundColor: '#10B981',
                  boxShadow: '0 0 8px #10B981',
                }}
              />
              {/* Radar / Ping wave em looping contínuo */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: 6,
                  border: '1.5px solid #34D399',
                  transform: `scale(${pingScale})`,
                  opacity: pingOpacity,
                  pointerEvents: 'none',
                }}
              />
            </div>
            <span style={{fontSize: 24, fontWeight: 800, color: '#ECFDF5'}}>
              Monitoramento Ativo
            </span>
          </div>
        </div>
      )}

      {/* Vinheta sutil superior APENAS na faixa y 0-320 para garantir contraste sem escurecer o rosto */}
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
              transform: `scale(${Math.max(0, badgeSpring * successPulse)})`,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '6px 22px',
              borderRadius: 20,
              backgroundColor: 'rgba(14, 165, 233, 0.22)',
              border: '2px solid #0EA5E9',
              boxShadow: '0 0 20px rgba(14, 165, 233, 0.45)',
              backdropFilter: 'blur(8px)',
            }}
          >
            <ShieldIcon size={26} color="#38BDF8" />
            <span
              style={{
                fontSize: 32,
                fontWeight: 900,
                color: '#38BDF8',
                letterSpacing: 2,
                textTransform: 'uppercase',
              }}
            >
              O RESULTADO
            </span>
          </div>
        )}

        {/* Título Superior 1: NÃO FICO MAIS NO ESCURO (Frame 9 a 88) */}
        {frame >= 9 && frame < 88 && (
          <div
            style={{
              marginTop: 12,
              textAlign: 'center',
              transform: `translateY(${(1 - title1In) * 15}px)`,
              opacity: title1In * title1Out,
              backgroundColor: 'rgba(11, 17, 32, 0.92)',
              padding: '8px 22px',
              borderRadius: 16,
              border: '1.5px solid rgba(14, 165, 233, 0.5)',
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
              NÃO FICO MAIS NO{' '}
              <span
                style={{
                  color: '#FFFFFF',
                  backgroundColor: '#0284C7',
                  padding: '2px 10px',
                  borderRadius: 8,
                }}
              >
                ESCURO
              </span>
            </div>
          </div>
        )}

        {/* Título Superior 2: SERVIDOR SEGURO + ROBÔ VIGIANDO */}
        {frame >= 88 && (
          <div
            style={{
              marginTop: 12,
              textAlign: 'center',
              transform: `translateY(${(1 - title2In) * 15}px)`,
              opacity: title2In,
              backgroundColor: 'rgba(11, 17, 32, 0.92)',
              padding: '8px 22px',
              borderRadius: 16,
              border: '1.5px solid rgba(16, 185, 129, 0.6)',
              boxShadow: '0 8px 25px rgba(0,0,0,0.7)',
            }}
          >
            <div
              style={{
                fontSize: 40,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textTransform: 'uppercase',
              }}
            >
              SERVIDOR SEGURO +{' '}
              <span
                style={{
                  color: '#0B1120',
                  backgroundColor: '#10B981',
                  padding: '3px 12px',
                  borderRadius: 8,
                  fontWeight: 900,
                }}
              >
                ROBÔ VIGIANDO
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
