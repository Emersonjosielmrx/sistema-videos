import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Cena3: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Enquadramento close-up diferenciado da Cena 1 + Punch-in de impacto na fala de desfecho
  // Bloco 1 (0 a 105): Close-up 1.25x -> 1.30x ("Hoje o cliente tira dúvidas sozinho")
  // Bloco 2 (106 a 216): Punch-in dramático 1.42x -> 1.48x ("e o pedido chega pronto no meu WhatsApp.")
  let videoScale = 1.25;
  if (frame < 106) {
    videoScale = interpolate(frame, [0, 106], [1.25, 1.30], {
      extrapolateRight: 'clamp',
    });
  } else {
    videoScale = interpolate(frame, [106, 216], [1.42, 1.48], {
      extrapolateRight: 'clamp',
    });
  }

  // Entrada do selo "O RESULTADO"
  const tagSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Estágios da fala do dono
  const fase1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const fase2Spring = spring({
    frame: frame - 104,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  const pulseSuccess =
    frame >= 104 ? 1 + Math.sin((frame - 104) * 0.22) * 0.03 : 1;

  // Pop-up gráfico dinâmico simulando a notificação de pedido pronto no WhatsApp
  const orderSpring = spring({
    frame: frame - 106,
    fps,
    config: {damping: 12, stiffness: 150},
  });
  const orderFloatY = Math.sin((frame - 106) * 0.14) * 6;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono com enquadramento close-up e aproximação contínua */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '52% 38%',
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

        {/* Gradiente superior para contraste garantido */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 420,
            background:
              'linear-gradient(to bottom, rgba(10, 2, 4, 0.9) 0%, rgba(10, 2, 4, 0.6) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Gradiente inferior para o karaokê */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(to top, rgba(10, 1, 3, 0.88) 0%, rgba(10, 1, 3, 0.5) 60%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Zona Superior Exclusiva de Grafismos (y: 195 a 330) */}
      {/* Respiro >= 38px abaixo da barra em y=152 */}
      {/* O ROSTO DO APRESENTADOR ESTÁ 100% LIVRE COM RESPIRO >= 75px */}
      <div
        style={{
          position: 'absolute',
          top: 195,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          zIndex: 30,
        }}
      >
        {/* Badge de Vitória: "O RESULTADO NA PRÁTICA" */}
        <div
          style={{
            transform: `scale(${Math.max(0, tagSpring)})`,
            opacity: Math.min(1, tagSpring),
            background: 'rgba(37, 211, 102, 0.22)',
            border: '2px solid #25D366',
            borderRadius: 999,
            padding: '8px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: '0 4px 18px rgba(0,0,0,0.6)',
          }}
        >
          <span style={{fontSize: 30}}>✅</span>
          <span
            style={{
              color: '#86EFAC',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O RESULTADO NA PRÁTICA
          </span>
        </div>

        {/* Card Dinâmico que Acompanha a Fala */}
        <div
          style={{
            minHeight: 75,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
          }}
        >
          {frame < 104 && (
            <div
              style={{
                transform: `scale(${Math.max(0, fase1Spring)})`,
                opacity: Math.min(1, fase1Spring),
                background: 'rgba(15, 23, 42, 0.95)',
                border: '2px solid rgba(56, 189, 248, 0.6)',
                borderRadius: 20,
                padding: '12px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                boxShadow: '0 8px 30px rgba(0,0,0,0.65)',
              }}
            >
              <span style={{fontSize: 32}}>🤖</span>
              <span
                style={{
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 800,
                  textTransform: 'uppercase',
                }}
              >
                CLIENTE TIRA DÚVIDAS SOZINHO COM A IA
              </span>
            </div>
          )}

          {frame >= 104 && (
            <div
              style={{
                transform: `scale(${pulseSuccess * Math.max(0, fase2Spring)})`,
                opacity: Math.min(1, fase2Spring),
                background:
                  'linear-gradient(135deg, rgba(22, 101, 52, 0.96) 0%, rgba(21, 128, 61, 0.96) 100%)',
                border: '2px solid #86EFAC',
                borderRadius: 20,
                padding: '12px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                boxShadow: '0 10px 40px rgba(34, 197, 94, 0.55)',
              }}
            >
              <span style={{fontSize: 32}}>📲</span>
              <span
                style={{
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 900,
                  textTransform: 'uppercase',
                }}
              >
                PEDIDO CHEGA PRONTO NO WHATSAPP
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Pop-up Gráfico Dinâmico simulando Notificação de Pedido Pronto no WhatsApp (y: 1040 a 1280) */}
      {frame >= 106 && (
        <div
          style={{
            position: 'absolute',
            top: 1040,
            left: 70,
            right: 70,
            transform: `translateY(${orderFloatY}px) scale(${Math.max(
              0,
              orderSpring
            )})`,
            opacity: Math.min(1, orderSpring),
            background: 'rgba(11, 20, 26, 0.96)',
            border: '2.5px solid #25D366',
            borderRadius: 26,
            padding: '20px 24px',
            boxShadow:
              '0 20px 50px rgba(0,0,0,0.85), 0 0 35px rgba(37, 211, 102, 0.45)',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            zIndex: 35,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1.5px solid rgba(255,255,255,0.12)',
              paddingBottom: 10,
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 14,
                  background: '#25D366',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 26,
                }}
              >
                💬
              </div>
              <span style={{color: '#94A3B8', fontSize: 32, fontWeight: 600}}>
                WhatsApp Business • Notificação
              </span>
            </div>
            <div
              style={{
                background: 'rgba(37, 211, 102, 0.2)',
                color: '#86EFAC',
                borderRadius: 999,
                padding: '4px 14px',
                fontSize: 32,
                fontWeight: 800,
                textTransform: 'uppercase',
              }}
            >
              Agora 🔔
            </div>
          </div>

          <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
            <div
              style={{
                color: '#FFFFFF',
                fontSize: 34,
                fontWeight: 900,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span>✅</span> Novo Pedido Pronto!
            </div>
            <div style={{color: '#E2E8F0', fontSize: 32, fontWeight: 500}}>
              1x Burger Artesanal com queijo • Recebido direto no WhatsApp
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
