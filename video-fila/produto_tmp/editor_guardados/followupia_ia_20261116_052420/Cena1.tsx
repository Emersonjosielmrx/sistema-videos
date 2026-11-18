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

interface Cena1Props {
  fontFamily: string;
  corMarca: string;
  corFundo: string;
  corTextoMarca: string;
}

export const Cena1: React.FC<Cena1Props> = ({
  fontFamily,
  corMarca,
  corFundo,
  corTextoMarca,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durFrames = Math.round((12.08 - 4.77) * fps);
  const absTime = 4.77 + frame / fps;

  // Entrada em mola combinada com zoom-through contínuo vindo da Cena 0
  const enter = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 150},
  });

  const enterScale = interpolate(enter, [0, 1], [1.1, 1.0]);

  const exit = interpolate(absTime, [11.75, 12.08], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Zoom suave contínuo no vídeo do dono
  const videoScale = interpolate(frame, [0, durFrames], [1.0, 1.04], {
    extrapolateRight: 'clamp',
  });

  // Micro-flutuação do HUD
  const floatY = Math.sin(frame / 9) * 3;

  // Estados sincronizados com a fala
  const isEsfriaram = absTime >= 7.36;
  const isSemBraco = absTime >= 9.4;

  // Punch-in dinâmico de escala (corte para 1.08x com spring ágil) a partir de q05 (7.36s)
  // pontuando com força o momento da dor ("esfriaram semanas atrás")
  const punchSnap = spring({
    frame: frame - Math.round((7.36 - 4.77) * fps),
    fps,
    config: {damping: 13, stiffness: 180},
  });
  const punchScale = isEsfriaram ? interpolate(punchSnap, [0, 1], [1.0, 1.08]) : 1.0;
  const totalVideoScale = videoScale * punchScale;

  // Transição suave de saída com slide direcional para conectar suavemente à demonstração da Cena 2
  const exitSlideX = interpolate(absTime, [11.73, 12.08], [0, -40], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const step3Enter = spring({
    frame: frame - Math.round((9.4 - 4.77) * fps),
    fps,
    config: {damping: 13, stiffness: 170},
  });

  return (
    <AbsoluteFill
      style={{
        opacity: enter * exit,
        backgroundColor: corFundo,
        transform: `translateX(${exitSlideX}px)`,
      }}
    >
      {/* Vídeo do apresentador com punch-in dinâmico em 7.36s e respiro livre acima da cabeça */}
      <AbsoluteFill
        style={{
          transform: `scale(${totalVideoScale * enterScale}) translateY(95px)`,
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>

      {/* Vinheta inferior para isolar e destacar o Karaokê sobre a roupa */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(to top, rgba(17,24,39,0.92) 0%, rgba(17,24,39,0.5) 60%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Top HUD posicionado em y: 175 (com folga limpa de 17px abaixo da barra de progresso em y: 150, eliminando o sliver cortado) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          backgroundColor: 'rgba(17, 24, 39, 0.94)',
          border: '2px solid rgba(239, 68, 68, 0.65)',
          borderRadius: 22,
          padding: '12px 20px',
          boxShadow: '0 18px 40px rgba(0,0,0,0.65)',
          transform: `translateY(${interpolate(enter, [0, 1], [-25, 0]) + floatY}px)`,
          zIndex: 30,
        }}
      >
        {/* Barra superior do HUD */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 10,
          }}
        >
          <span
            style={{
              fontFamily,
              fontSize: 30,
              fontWeight: 900,
              color: '#FFFFFF',
              backgroundColor: '#EF4444',
              padding: '3px 14px',
              borderRadius: 8,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}
          >
            O PROBLEMA
          </span>
          <span
            style={{
              fontFamily,
              fontSize: 32,
              fontWeight: 800,
              color: isSemBraco ? '#FECACA' : '#FFFFFF',
              textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            }}
          >
            {isSemBraco ? 'Capacidade esgotada' : 'Funil de Vendas'}
          </span>
        </div>

        {/* Grade de cartões dinâmicos */}
        <div style={{display: 'flex', gap: 12}}>
          {/* Card 1: Contatos / Esfriamento */}
          <div
            style={{
              flex: 1,
              backgroundColor: isEsfriaram
                ? 'rgba(239, 68, 68, 0.22)'
                : 'rgba(78, 205, 196, 0.16)',
              border: `2px solid ${isEsfriaram ? '#EF4444' : corMarca}`,
              borderRadius: 16,
              padding: '10px 16px',
              transition: 'all 0.2s ease',
            }}
          >
            <div
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1.2,
              }}
            >
              {isEsfriaram ? '❄️ Esfriaram semanas atrás' : 'Muitos contatos interessados'}
            </div>
          </div>

          {/* Card 2: Sem braço para insistir (surge com a fala aos 9.4s) */}
          {isSemBraco ? (
            <div
              style={{
                flex: 1,
                backgroundColor: '#EF4444',
                borderRadius: 16,
                padding: '10px 16px',
                transform: `scale(${interpolate(step3Enter, [0, 1], [0.88, 1])})`,
                opacity: step3Enter,
                boxShadow: '0 6px 20px rgba(239, 68, 68, 0.45)',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  lineHeight: 1.2,
                }}
              >
                Sem braço para insistir
              </div>
            </div>
          ) : (
            <div
              style={{
                flex: 1,
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: '2px dashed rgba(255, 255, 255, 0.35)',
                borderRadius: 16,
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  fontFamily,
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  textShadow: '0 2px 8px rgba(0,0,0,0.7)',
                }}
              >
                Aguardando retorno...
              </div>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
