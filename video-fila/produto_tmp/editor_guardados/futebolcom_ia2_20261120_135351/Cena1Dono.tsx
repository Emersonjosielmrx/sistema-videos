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

export const Cena1Dono: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Corte de escala digital (punch-in de 14%) aos ~3.5s (frame 105: 'e eu precisava parar a produção')
  const videoScale =
    frame < 105
      ? interpolate(frame, [0, 105], [1.05, 1.09], {
          extrapolateRight: 'clamp',
        })
      : interpolate(frame, [105, 241], [1.22, 1.28], {
          extrapolateRight: 'clamp',
        });

  // Entrada inicial do Card de Topo
  const cardSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 15, mass: 0.8},
  });

  // Notificações animadas de mensagens acumulando (quebrando monotonia do talking head)
  const msg1Spring = spring({
    frame: frame - 18,
    fps,
    config: {damping: 13, mass: 0.6},
  });
  const msg2Spring = spring({
    frame: frame - 46,
    fps,
    config: {damping: 13, mass: 0.6},
  });
  const alertSpring = spring({
    frame: frame - 72,
    fps,
    config: {damping: 13, mass: 0.6},
  });

  // Alerta de parada de produção na virada da frase (frame 105)
  const pararSpring = spring({
    frame: frame - 105,
    fps,
    config: {damping: 13, mass: 0.7},
  });

  // Microflutuação contínua do HUD para dinamismo sutil sem poluição
  const hudFloat = Math.sin(frame * 0.12) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#000000',
      }}
    >
      {/* Vídeo do dono em tela cheia com corte dinâmico de punch-in zoom na virada da fala */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 45%',
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

      {/* Leve vinheta superior para destacar o HUD sem encobrir o rosto */}
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

      {/* Topo Exclusivo Informativo com RÓTULO CONCEITUAL FIXO (Safe Zone: y = 165 a 300) — Rosto 100% livre (y > 420) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          transform: `translateY(${hudFloat}px) scale(${Math.max(0, cardSpring)})`,
          opacity: interpolate(cardSpring, [0, 0.2, 1], [0, 0.8, 1]),
          zIndex: 30,
        }}
      >
        <div
          style={{
            background: 'rgba(20, 5, 10, 0.94)',
            border: frame < 105 ? '2px solid rgba(225, 29, 72, 0.6)' : '2.5px solid #FACC15',
            borderRadius: 26,
            padding: '20px 28px',
            boxShadow:
              frame < 105
                ? '0 16px 36px rgba(0, 0, 0, 0.85), 0 0 25px rgba(225, 29, 72, 0.25)'
                : '0 16px 36px rgba(0, 0, 0, 0.85), 0 0 30px rgba(250, 204, 21, 0.35)',
            display: 'flex',
            alignItems: 'center',
            gap: 20,
          }}
        >
          <div
            style={{
              padding: '10px 18px',
              borderRadius: 14,
              background: frame < 105 ? '#E11D48' : '#FACC15',
              color: frame < 105 ? '#FFFFFF' : '#111827',
              fontFamily,
              fontSize: 32,
              fontWeight: 900,
              textTransform: 'uppercase',
              letterSpacing: 1.1,
              whiteSpace: 'nowrap',
              transition: 'background 0.3s ease',
            }}
          >
            {frame < 105 ? 'O Problema' : '⚠️ Parar Produção'}
          </div>
          <div
            style={{
              fontFamily,
              fontSize: 38,
              fontWeight: 800,
              color: '#FFFFFF',
              lineHeight: 1.25,
              textWrap: 'balance',
            }}
          >
            {frame < 105
              ? 'Muitos clientes indecisos no WhatsApp'
              : 'Cozinha parada para descrever opções'}
          </div>
        </div>
      </div>

      {/* Notificações animadas ilustrando mensagens acumuladas (frames 18 a 104 - Rosto livre) */}
      {frame >= 18 && frame < 105 && (
        <div
          style={{
            position: 'absolute',
            top: 310,
            right: 60,
            maxWidth: 380,
            transform: `scale(${Math.max(0, msg1Spring)})`,
            opacity: interpolate(msg1Spring, [0, 0.3, 1], [0, 0.7, 1]),
            zIndex: 35,
          }}
        >
          <div
            style={{
              background: 'rgba(20, 5, 10, 0.94)',
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
              Tem como mandar fotos?
            </span>
          </div>
        </div>
      )}

      {frame >= 46 && frame < 105 && (
        <div
          style={{
            position: 'absolute',
            top: 395,
            left: 60,
            maxWidth: 380,
            transform: `scale(${Math.max(0, msg2Spring)})`,
            opacity: interpolate(msg2Spring, [0, 0.3, 1], [0, 0.7, 1]),
            zIndex: 35,
          }}
        >
          <div
            style={{
              background: 'rgba(20, 5, 10, 0.94)',
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
              O que vem no combo?
            </span>
          </div>
        </div>
      )}

      {frame >= 72 && frame < 105 && (
        <div
          style={{
            position: 'absolute',
            top: 395,
            right: 60,
            maxWidth: 380,
            transform: `scale(${Math.max(0, alertSpring)})`,
            opacity: interpolate(alertSpring, [0, 0.3, 1], [0, 0.7, 1]),
            zIndex: 35,
          }}
        >
          <div
            style={{
              background: 'rgba(49, 6, 15, 0.96)',
              border: '2px solid #E11D48',
              borderRadius: 18,
              padding: '10px 18px',
              boxShadow: '0 8px 24px rgba(225, 29, 72, 0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span style={{fontSize: 32}}>🔴</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                lineHeight: 1.2,
              }}
            >
              +15 mensagens em aberto
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
