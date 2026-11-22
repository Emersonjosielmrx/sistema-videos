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

  // Movimento de câmera contínuo (> 4% variação)
  // Enquadramento que posiciona o rosto no terço superior e a boca livre da legenda karaokê
  const videoScale = interpolate(frame, [0, 241], [1.14, 1.22], {
    extrapolateRight: 'clamp',
  });
  const videoTranslateY = interpolate(frame, [0, 241], [50, 80], {
    extrapolateRight: 'clamp',
  });

  // Entrada do badge e título aos 0.2s (frame 6)
  const headerSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Mudança para "ATENDIMENTO ÁGIL" aos 5.8s (frame 175)
  const isAgil = frame >= 175;
  const agilSpring = spring({
    frame: frame - 175,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  // Transições de opacidade da cena
  const sceneOpacity = interpolate(
    frame,
    [0, 10, 230, 241],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{opacity: sceneOpacity, backgroundColor: '#0B0D13'}}>
      {/* Vídeo do dono falando em tela cheia com enquadramento perfeito protegendo o rosto */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${videoScale}) translateY(${videoTranslateY}px)`,
          transformOrigin: 'top center',
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
        {/* Camada suave no topo para assegurar contraste sem escurecer o rosto */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 280,
            background:
              'linear-gradient(180deg, rgba(11,13,19,0.95) 0%, rgba(11,13,19,0.65) 60%, rgba(11,13,19,0) 100%)',
          }}
        />
      </div>

      {/* Elementos textuais EXCLUSIVAMENTE no topo (y=155 a y=275), com respiro > 150px do topo da cabeça */}
      <div
        style={{
          position: 'absolute',
          top: 155,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          transform: `scale(${headerSpring})`,
          transformOrigin: 'top center',
        }}
      >
        {/* Badge "O RESULTADO" */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '6px 20px',
            borderRadius: 20,
            background: '#5B6CFF',
            boxShadow: '0 8px 24px rgba(91, 108, 255, 0.5)',
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Resultado
          </span>
        </div>

        {/* Título de alto contraste posicionado com segurança no alto */}
        <div
          style={{
            width: '100%',
            padding: '12px 22px',
            borderRadius: 18,
            background: 'rgba(17, 24, 39, 0.96)',
            border: '2px solid rgba(255, 255, 255, 0.16)',
            boxShadow: '0 12px 35px rgba(0, 0, 0, 0.85)',
            textAlign: 'center',
          }}
        >
          {!isAgil ? (
            <div
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textWrap: 'balance',
              }}
            >
              Organização em um só lugar
            </div>
          ) : (
            <div
              style={{
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
                textWrap: 'balance',
                transform: `scale(${agilSpring})`,
              }}
            >
              Atendimento ágil para todo cliente
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
