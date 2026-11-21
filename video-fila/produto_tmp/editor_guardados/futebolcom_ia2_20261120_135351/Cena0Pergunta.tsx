import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0Pergunta: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera com punch-in dinâmico aos ~1.0s (frame 30) para quebra de padrão (pattern interrupt)
  const bgScale =
    frame < 30
      ? interpolate(frame, [0, 30], [1.05, 1.08], {
          extrapolateRight: 'clamp',
        })
      : interpolate(frame, [30, 138], [1.18, 1.25], {
          extrapolateRight: 'clamp',
        });

  // Entrada do Card Principal da Pergunta (frame 2)
  const cardSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  // Notificações pipocando nos primeiros 1.5s (estímulo visual da dor / pattern interrupt)
  const notif1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, mass: 0.6},
  });
  const notif2Spring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 13, mass: 0.6},
  });
  const notif3Spring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Microflutuação contínua suave do card
  const floatY = Math.sin(frame * 0.1) * 4;

  // Destaque, pop e glow dinâmico da palavra 'TRAVA' sincronizado com ~1.0s (frame 28-52)
  const isTravaActive = frame >= 28;
  const travaScale = isTravaActive
    ? interpolate(frame, [28, 34, 42, 54], [1.0, 1.2, 1.1, 1.04], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1.0;
  const travaGlow = isTravaActive
    ? interpolate(frame, [28, 34, 46, 70], [0, 24, 14, 6], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0F0205',
      }}
    >
      {/* Vídeo do apresentador no balcão 100% iluminado e nítido desde o frame 0 (sem blackout) */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale})`,
          transformOrigin: '50% 40%',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(1.02) saturate(1.06)',
          }}
        />
      </div>

      {/* Vinheta superior suave para contraste do card informativo sem cobrir o rosto */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 480,
          background:
            'linear-gradient(180deg, rgba(15, 2, 5, 0.85) 0%, rgba(15, 2, 5, 0.4) 65%, rgba(0, 0, 0, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Vinheta inferior suave para dar contraste perfeito à legenda karaokê */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 460,
          background:
            'linear-gradient(0deg, rgba(15, 2, 5, 0.85) 0%, rgba(15, 2, 5, 0.35) 65%, rgba(0, 0, 0, 0) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Pergunta Central em Card Superior Limpo e Integrado (Safe Zone: y = 175 a 410) — Rosto livre (y > 420) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          transform: `translateY(${floatY}px) scale(${Math.max(0, cardSpring)})`,
          opacity: interpolate(cardSpring, [0, 0.2, 1], [0, 0.8, 1]),
          zIndex: 30,
        }}
      >
        <div
          style={{
            background: 'rgba(20, 4, 8, 0.92)',
            border: '2px solid rgba(225, 29, 72, 0.65)',
            borderRadius: 26,
            padding: '24px 30px',
            boxShadow:
              '0 18px 40px rgba(0, 0, 0, 0.85), 0 0 25px rgba(225, 29, 72, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
          }}
        >
          {/* Tag de Contexto Institucional */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginBottom: 14,
            }}
          >
            <div
              style={{
                padding: '6px 18px',
                borderRadius: 14,
                background: '#E11D48',
                color: '#FFFFFF',
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                textTransform: 'uppercase',
                letterSpacing: 1.1,
              }}
            >
              Atendimento WhatsApp
            </div>
          </div>

          {/* Pergunta Central com Palavra-Chave Cinética em Destaque */}
          <div
            style={{
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              lineHeight: 1.25,
              color: '#FFFFFF',
              textWrap: 'balance',
            }}
          >
            Seu cliente{' '}
            <span
              style={{
                display: 'inline-block',
                transform: `scale(${travaScale})`,
                background: isTravaActive ? '#FACC15' : 'rgba(255, 255, 255, 0.12)',
                color: isTravaActive ? '#111827' : '#FFFFFF',
                padding: '2px 16px',
                borderRadius: 14,
                boxShadow: isTravaActive
                  ? `0 0 ${travaGlow}px #FACC15, 0 6px 18px rgba(250, 204, 21, 0.5)`
                  : 'none',
                margin: '0 4px',
              }}
            >
              TRAVA
            </span>{' '}
            na hora de escolher pelo WhatsApp?
          </div>
        </div>
      </div>

      {/* Notificações dinâmicas pipocando nos primeiros 1.5s (Pattern Interrupt nas laterais - Rosto 100% livre) */}
      {frame >= 6 && (
        <div
          style={{
            position: 'absolute',
            top: 410,
            left: 60,
            maxWidth: 380,
            transform: `scale(${Math.max(0, notif1Spring)})`,
            opacity: interpolate(notif1Spring, [0, 0.3, 1], [0, 0.7, 1]),
            zIndex: 35,
          }}
        >
          <div
            style={{
              background: 'rgba(20, 4, 8, 0.94)',
              border: '2px solid rgba(225, 29, 72, 0.65)',
              borderRadius: 18,
              padding: '10px 18px',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.85)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span style={{fontSize: 32}}>💬</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1.2,
              }}
            >
              Tem fotos do cardápio?
            </span>
          </div>
        </div>
      )}

      {frame >= 18 && (
        <div
          style={{
            position: 'absolute',
            top: 410,
            right: 60,
            maxWidth: 380,
            transform: `scale(${Math.max(0, notif2Spring)})`,
            opacity: interpolate(notif2Spring, [0, 0.3, 1], [0, 0.7, 1]),
            zIndex: 35,
          }}
        >
          <div
            style={{
              background: 'rgba(20, 4, 8, 0.94)',
              border: '2px solid rgba(225, 29, 72, 0.65)',
              borderRadius: 18,
              padding: '10px 18px',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.85)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span style={{fontSize: 32}}>💬</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1.2,
              }}
            >
              Qual o molho desse?
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
