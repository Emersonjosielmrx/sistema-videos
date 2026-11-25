import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {BRIEFING} from './constants';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de câmera no vídeo (>= 4%)
  const videoScale = interpolate(frame, [0, 232], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge "O RESULTADO"
  const badgeSpring = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Fase 1: "Hoje o pedido chega completo no meu WhatsApp" (21.9s global -> frame 26 da cena)
  const phase1Spring = spring({
    frame: Math.max(0, frame - 24),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  // Fase 2: "e eu consigo cuidar do preparo com mais tranquilidade" (25.4s global -> frame 131 da cena)
  const isPhase2 = frame >= 131;
  const phase2Spring = spring({
    frame: Math.max(0, frame - 131),
    fps,
    config: {damping: 13, stiffness: 110},
  });

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        background: '#0B0D13',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono em tela cheia com push-in sutil contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_3.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Gradiente escuro no topo para contraste do texto sem cobrir o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 380,
          background:
            'linear-gradient(180deg, rgba(11, 13, 19, 0.88) 0%, rgba(11, 13, 19, 0.35) 70%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* TOP ZONE SEGURA: Rótulo "O RESULTADO" (y=175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${badgeSpring})`,
          opacity: badgeSpring,
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 28px',
            borderRadius: 30,
            background: 'rgba(15, 23, 42, 0.94)',
            border: '2px solid #22C55E',
            boxShadow: '0 8px 24px rgba(34, 197, 94, 0.35)',
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 6,
              background: '#22C55E',
              boxShadow: '0 0 10px #22C55E',
            }}
          />
          <span
            style={{
              fontSize: 34,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O RESULTADO
          </span>
        </div>
      </div>

      {/* TOP ZONE SEGURA: Card Cinético de Sucesso (y=245 a y=340) */}
      {/* Respiro amplo: rosto do dono começa abaixo de y=380 */}
      <div
        style={{
          position: 'absolute',
          top: 245,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          zIndex: 30,
        }}
      >
        {!isPhase2 ? (
          <div
            style={{
              transform: `translateY(${(1 - phase1Spring) * 20}px) scale(${phase1Spring})`,
              opacity: phase1Spring,
              background: 'rgba(15, 23, 42, 0.94)',
              border: '2px solid #22C55E',
              padding: '14px 32px',
              borderRadius: 20,
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.75)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{fontSize: 36}}>✅</span>
            <span
              style={{
                fontSize: 40,
                fontWeight: 800,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              PEDIDO COMPLETO NO WHATSAPP
            </span>
          </div>
        ) : (
          <div
            style={{
              transform: `translateY(${(1 - phase2Spring) * 20}px) scale(${phase2Spring})`,
              opacity: phase2Spring,
              background: 'rgba(15, 23, 42, 0.94)',
              border: `2px solid ${BRIEFING.cores.apoio}`,
              padding: '14px 32px',
              borderRadius: 20,
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.75)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{fontSize: 36}}>🍳</span>
            <span
              style={{
                fontSize: 40,
                fontWeight: 800,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              TRANQUILIDADE NO PREPARO
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
