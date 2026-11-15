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

  // Zoom sutil e contínuo no vídeo do dono (1.00 -> 1.06)
  const videoScale = interpolate(frame, [0, 230], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Card Superior (frame 5)
  const cardSpring = spring({
    frame: frame - 5,
    fps,
    config: {damping: 12, stiffness: 100},
  });

  // Ponto de virada na fala: ~9.0s (frame 124 no contexto da cena)
  // "até organizar tudo em um só lugar"
  const isSolucao = frame >= 124;
  const solucaoSpring = spring({
    frame: frame - 124,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Brilho pulsante sutil na borda
  const borderPulse = Math.sin(frame / 10) * 0.2 + 0.8;

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Vídeo do Dono em tela cheia com leve zoom contínuo */}
      <AbsoluteFill
        style={{
          transform: `scale(${videoScale})`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Leve vinheta no topo para dar destaque e leitura máxima ao card */}
        <AbsoluteFill
          style={{
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.3) 22%, rgba(15,23,42,0) 40%, rgba(15,23,42,0.55) 85%, rgba(15,23,42,0.92) 100%)',
            pointerEvents: 'none',
          }}
        />
      </AbsoluteFill>

      {/* Conteúdo EXCLUSIVAMENTE na faixa do topo (y: 165 a 330) para proteger 100% o rosto do dono */}
      <AbsoluteFill style={{padding: '0 60px', pointerEvents: 'none'}}>
        <div
          style={{
            position: 'absolute',
            top: 170,
            left: 60,
            right: 60,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            opacity: interpolate(cardSpring, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(cardSpring, [0, 1], [-25, 0])}px)`,
          }}
        >
          {!isSolucao ? (
            /* Fase 1: O Problema Relatado */
            <div
              style={{
                width: '100%',
                maxWidth: 920,
                padding: '14px 24px',
                borderRadius: 22,
                background: 'rgba(17, 24, 39, 0.92)',
                border: `2px solid rgba(239, 68, 68, ${borderPulse})`,
                boxShadow:
                  '0 12px 30px rgba(0,0,0,0.65), 0 0 20px rgba(239, 68, 68, 0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
              }}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 14,
                  background: 'rgba(239, 68, 68, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                ⚠️
              </div>
              <div style={{flex: 1}}>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#F87171',
                    textTransform: 'uppercase',
                    letterSpacing: 1.5,
                  }}
                >
                  O PROBLEMA: MISTURA TOTAL
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Pedidos de compra e suporte misturados no WhatsApp
                </div>
              </div>
            </div>
          ) : (
            /* Fase 2: A Virada / Organização */
            <div
              style={{
                width: '100%',
                maxWidth: 920,
                padding: '14px 24px',
                borderRadius: 22,
                background: 'rgba(17, 24, 39, 0.94)',
                border: `2px solid rgba(31, 147, 255, ${borderPulse})`,
                boxShadow:
                  '0 12px 35px rgba(0,0,0,0.7), 0 0 25px rgba(31, 147, 255, 0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                transform: `scale(${interpolate(solucaoSpring, [0, 1], [0.92, 1])})`,
                opacity: interpolate(solucaoSpring, [0, 1], [0, 1]),
              }}
            >
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 14,
                  background: 'rgba(31, 147, 255, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                  flexShrink: 0,
                }}
              >
                ⚡
              </div>
              <div style={{flex: 1}}>
                <div
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#60A5FA',
                    textTransform: 'uppercase',
                    letterSpacing: 1.5,
                  }}
                >
                  A SOLUÇÃO: TUDO CENTRALIZADO
                </div>
                <div
                  style={{
                    fontFamily,
                    fontSize: 34,
                    fontWeight: 700,
                    color: '#FFFFFF',
                    lineHeight: 1.2,
                  }}
                >
                  Atendimento organizado em um só lugar
                </div>
              </div>
            </div>
          )}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
