import React from 'react';
import {
  Img,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena1Dono: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Dinâmica de Câmera:
  // - Frames 0 a 103: slow push-in suave (1.00 -> 1.05)
  // - Frame 104 em diante: Punch-in zoom de corte digital (+13%, 1.18 -> 1.22) na ênfase "o dia inteiro"
  const isPunchIn = frame >= 104;
  const videoScale = isPunchIn
    ? interpolate(frame, [104, 232], [1.18, 1.23], {extrapolateRight: 'clamp'})
    : interpolate(frame, [0, 103], [1.0, 1.05], {extrapolateRight: 'clamp'});

  // Entrada inicial da cena
  const enterSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Ponto de virada da fala na cena:
  // "o dia inteiro só para validar mensagens de horário" começa por volta de 8.53s (abs)
  // Como a cena começou em 5.08s, 8.53s - 5.08s = 3.45s = ~104 frames
  const switchProgress = interpolate(frame, [100, 112], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Micro-movimento contínuo para evitar elementos estáticos
  const microFloat = Math.sin(frame / 11) * 3;

  // Prevenção de piscada no final do take: o frame 213 mantém contato visual direto e sorriso firme
  const isEndFreeze = frame >= 213;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do dono em tela cheia (MUTED: áudio está na narracao.mp3) */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${videoScale})`,
          transformOrigin: isPunchIn ? '50% 36%' : '50% 40%',
        }}
      >
        {isEndFreeze ? (
          <Img
            src={staticFile('dono_1_freeze.jpg')}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        ) : (
          <OffthreadVideo
            src={staticFile('dono_1.mp4')}
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        )}
        {/* Vinheta escura muito leve nas bordas para destacar textos sem escurecer o apresentador */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.78) 0%, rgba(15,23,42,0.15) 24%, rgba(15,23,42,0.0) 50%, rgba(15,23,42,0.45) 85%, rgba(15,23,42,0.85) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Faixa superior informativa (y=200 a 430) - Acima da cabeça dele */}
      <div
        style={{
          position: 'absolute',
          top: 200,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
          transform: `translateY(${microFloat}px)`,
        }}
      >
        {/* Badge / Rótulo da cena */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 24,
            background: 'rgba(31, 41, 55, 0.92)',
            border: '1.5px solid rgba(255, 169, 77, 0.7)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            transform: `scale(${enterSpring})`,
            opacity: enterSpring,
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#FFA94D',
              boxShadow: '0 0 8px #FFA94D',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: '#FFA94D',
            }}
          >
            A Rotina Presa
          </span>
        </div>

        {/* Bloco de Título Cinético (Fase 1 e Fase 2 da fala) */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            height: 130,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {/* Fase 1 (frames 0 a ~105): "Interrompia atendimentos no estúdio o dia inteiro" */}
          <div
            style={{
              position: 'absolute',
              width: '100%',
              textAlign: 'center',
              opacity: (1 - switchProgress) * enterSpring,
              transform: `translateY(${switchProgress * -15}px)`,
              pointerEvents: 'none',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 46,
                fontWeight: 900,
                lineHeight: 1.25,
                color: '#FFFFFF',
                textShadow: '0 4px 18px rgba(0,0,0,0.9)',
                textWrap: 'balance',
              }}
            >
              Interrompia atendimentos <br />
              <span
                style={{
                  background: '#FFA94D',
                  color: '#1F2937',
                  padding: '2px 14px',
                  borderRadius: 10,
                  display: 'inline-block',
                  marginTop: 4,
                  fontWeight: 900,
                }}
              >
                no estúdio o dia inteiro
              </span>
            </h2>
          </div>

          {/* Fase 2 (frames 105 em diante): "O dia inteiro só para validar horários" */}
          <div
            style={{
              position: 'absolute',
              width: '100%',
              textAlign: 'center',
              opacity: switchProgress,
              transform: `translateY(${(1 - switchProgress) * 15}px)`,
              pointerEvents: 'none',
            }}
          >
            <h2
              style={{
                margin: 0,
                fontSize: 46,
                fontWeight: 900,
                lineHeight: 1.25,
                color: '#FFFFFF',
                textShadow: '0 4px 18px rgba(0,0,0,0.9)',
                textWrap: 'balance',
              }}
            >
              Só para ficar validando <br />
              <span
                style={{
                  background: '#FFA94D',
                  color: '#1F2937',
                  padding: '2px 14px',
                  borderRadius: 10,
                  display: 'inline-block',
                  marginTop: 4,
                  fontWeight: 900,
                }}
              >
                mensagens de horário
              </span>
            </h2>
          </div>
        </div>
      </div>
    </div>
  );
};
