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
}

export const Cena1: React.FC<Cena1Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera sutil no vídeo do dono (1.0 -> 1.06)
  const videoScale = interpolate(frame, [0, 241], [1.0, 1.06], {
    extrapolateRight: 'clamp',
  });

  // Tag superior: "⚠️ O PROBLEMA"
  const tagSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Card de texto 1: "ACHAVA QUE IA TIRAR CLIENTES..."
  const card1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Troca para o texto 2 aos ~4.5s da cena (frame 135): "...DO ATENDIMENTO NO WHATSAPP?"
  const isSegundaParte = frame >= 135;
  const card2Spring = spring({
    frame: frame - 135,
    fps,
    config: {damping: 14, stiffness: 140},
  });

  // Movimento contínuo no card
  const cardFloatY = Math.sin(frame / 15) * 4;

  return (
    <AbsoluteFill style={{backgroundColor: '#000000', overflow: 'hidden'}}>
      {/* Vídeo do Dono com zoom progressivo contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
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
      </div>

      {/* Gradiente sutil no topo para garantir leitura perfeita (y=0 a 440) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(15, 3, 5, 0.90) 0%, rgba(15, 3, 5, 0.65) 60%, rgba(15, 3, 5, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Faixa Superior Livre de Rosto (y=160 a y=370) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily,
          transform: `translateY(${cardFloatY}px)`,
        }}
      >
        {/* Rótulo / Badge Oficial */}
        <div
          style={{
            opacity: Math.max(0, tagSpring),
            transform: `translateY(${(1 - tagSpring) * -18}px)`,
            backgroundColor: 'rgba(225, 29, 72, 0.35)',
            border: '2px solid rgba(225, 29, 72, 0.85)',
            padding: '6px 24px',
            borderRadius: 999,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: '0 4px 18px rgba(0,0,0,0.5)',
            marginBottom: 12,
          }}
        >
          <span style={{fontSize: 34}}>⚠️</span>
          <span
            style={{
              color: '#FFFFFF',
              fontSize: 34,
              fontWeight: 800,
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>

        {/* Card Dinâmico no Alto (Sincronizado com a fala do Dono) */}
        {!isSegundaParte ? (
          <div
            style={{
              opacity: Math.max(0, card1Spring),
              transform: `scale(${interpolate(card1Spring, [0, 1], [0.85, 1])}) translateY(${(1 - card1Spring) * 20}px)`,
              backgroundColor: 'rgba(18, 18, 22, 0.88)',
              border: '2px solid rgba(255, 255, 255, 0.2)',
              borderRadius: 22,
              padding: '14px 28px',
              maxWidth: 920,
              textAlign: 'center',
              boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
            }}
          >
            <span
              style={{
                fontSize: 42,
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1.25,
                textWrap: 'balance',
              }}
            >
              “Achava que o cardápio ia tirar meus clientes...”
            </span>
          </div>
        ) : (
          <div
            style={{
              opacity: Math.max(0, card2Spring),
              transform: `scale(${interpolate(card2Spring, [0, 1], [0.85, 1])}) translateY(${(1 - card2Spring) * 20}px)`,
              backgroundColor: 'rgba(18, 18, 22, 0.92)',
              border: '2px solid #25D366',
              borderRadius: 22,
              padding: '14px 28px',
              maxWidth: 920,
              textAlign: 'center',
              boxShadow: '0 8px 32px rgba(37, 211, 102, 0.35)',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              justifyContent: 'center',
            }}
          >
            <span style={{fontSize: 40}}>💬</span>
            <span
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: '#25D366',
                lineHeight: 1.2,
                textTransform: 'uppercase',
              }}
            >
              ...Do atendimento no WhatsApp?
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
