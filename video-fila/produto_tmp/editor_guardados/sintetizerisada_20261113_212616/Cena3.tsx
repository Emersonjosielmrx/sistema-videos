import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';
import {CORES} from './constants';

interface CenaProps {
  fontFamily: string;
}

export const Cena3: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Corte seco de câmera com punch zoom (1.0x -> 1.15x) exatamente na virada da fala aos 23.75s (frame 100)
  // "sem conflito e sem duplo agendamento"
  const isPunchIn = frame >= 100;
  const videoScale = isPunchIn
    ? interpolate(frame, [100, 241], [1.15, 1.19], {
        extrapolateRight: 'clamp',
      })
    : interpolate(frame, [0, 99], [1.00, 1.04], {
        extrapolateRight: 'clamp',
      });

  // Reenquadramento vertical: deslocamento para baixo (y=80 a 92px) para headroom generoso
  // eliminando qualquer contato entre o topo da cabeça e os textos superiores
  const videoTranslateY = isPunchIn ? 92 : 80;

  // Molas da faixa superior (posicionada bem alta: y 165 a 325)
  const tagSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const titleSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Mola de ênfase no momento do punch zoom (frame 100)
  const punchSpring = spring({
    frame: frame - 100,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#000000',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono em Tela Cheia com Headroom aumentado e Punch Zoom na virada de chave */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translateY(${videoTranslateY}px) scale(${videoScale})`,
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

        {/* Garantia de olhos abertos e contato visual direto (elimina still capturado no micro-piscar em q11) */}
        {frame >= 75 && frame <= 79 && (
          <img
            src={staticFile('dono_frame_74.jpg')}
            alt=""
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        )}

        {/* Gradiente escurecedor EXCLUSIVO no topo (y 0 a 440) para contraste absoluto dos textos */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 440,
            background:
              'linear-gradient(180deg, rgba(11, 15, 23, 0.95) 0%, rgba(11, 15, 23, 0.82) 65%, rgba(11, 15, 23, 0) 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Gradiente suave na base para leitura cristalina do karaokê (y 1400 a 1920) */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 420,
            background:
              'linear-gradient(0deg, rgba(0, 0, 0, 0.90) 0%, rgba(0, 0, 0, 0.60) 60%, rgba(0, 0, 0, 0) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Faixa Superior Elevada (y: 165 a 330): Headroom amplo e livre sobre a cabeça do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: tagSpring,
          transform: `scale(${Math.max(0.7, tagSpring)})`,
          zIndex: 10,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 24,
            backgroundColor: 'rgba(31, 41, 55, 0.94)',
            border: `2px solid ${CORES.marca}`,
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.6)',
          }}
        >
          <span
            style={{
              fontSize: 32,
              fontWeight: 900,
              color: CORES.marca,
              textTransform: 'uppercase',
              letterSpacing: '1px',
            }}
          >
            O Resultado
          </span>
        </div>
      </div>

      {/* Título Principal Elevado (y: 228 a 335): 100% acima do cabelo do apresentador */}
      <div
        style={{
          position: 'absolute',
          top: 228,
          left: 60,
          right: 60,
          textAlign: 'center',
          opacity: titleSpring,
          transform: `translateY(${(1 - titleSpring) * 15}px)`,
          zIndex: 10,
        }}
      >
        <div
          style={{
            fontSize: 48,
            fontWeight: 900,
            color: '#FFFFFF',
            lineHeight: 1.15,
            textShadow: '0 4px 20px rgba(0,0,0,0.95), 0 2px 6px #000000',
          }}
        >
          ATENDIMENTO 24H SEM CONFLITO
        </div>
        <div
          style={{
            fontSize: 32,
            fontWeight: 800,
            color: CORES.marca,
            marginTop: 8,
            textShadow: '0 4px 15px rgba(0,0,0,0.95), 0 2px 6px #000000',
            transform: isPunchIn ? `scale(${1 + 0.05 * Math.sin(frame * 0.2)})` : 'scale(1)',
            display: 'inline-block',
          }}
        >
          Sem duplo agendamento no WhatsApp
        </div>
      </div>
    </div>
  );
};
