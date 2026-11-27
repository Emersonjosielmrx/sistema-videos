import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no vídeo do dono em PLANO FECHADO / CLOSE-UP (scale 1.40 a 1.46)
  // Deslocado suavemente à esquerda (translateX -130px) garantindo cobertura total (sem faixa preta)
  // e rosto do apresentador totalmente livre do card PiP
  const videoScale = interpolate(frame, [0, 246], [1.4, 1.46], {
    extrapolateRight: 'clamp',
  });

  // Transição direta sem flash preto no corte da cena 2
  // Badge do topo entra no primeiro frame
  const sprBadge = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 180},
  });

  // Fase 1: entra com pop fluido desde o frame zero
  const sprFase1 = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 180},
  });

  // Transição para a Fase 2: entra aos frame 105 local (quando a fala cita 'eu deixo de perder venda')
  const sprFase2 = spring({
    frame: frame - 105,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const isFase2 = frame >= 105;

  // Entrada do card PiP (entra no frame 2)
  const sprPip = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 170},
  });

  // Pulso contínuo de status
  const pulseScale = 1 + 0.12 * Math.sin((frame * Math.PI) / 14);
  const pipFloatY = Math.sin(frame / 12) * 5;

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono em PLANO FECHADO / CLOSE-UP detalhe com enquadramento cinematográfico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale}) translateX(-130px) translateY(-25px)`,
          transformOrigin: 'center center',
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
        {/* Vinheta escura no topo */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(to bottom, rgba(11, 13, 19, 0.94) 0%, rgba(11, 13, 19, 0.55) 75%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
        {/* Vinheta escura na base para resguardar a legenda */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 450,
            background:
              'linear-gradient(to top, rgba(11, 13, 19, 0.95) 0%, rgba(11, 13, 19, 0.5) 70%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Faixa Superior (Safe Zone y = 160 a 420) */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
          zIndex: 30,
        }}
      >
        {/* Pill Badge: O RESULTADO */}
        <div
          style={{
            transform: `scale(${sprBadge})`,
            opacity: sprBadge,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 30,
            background: '#31060F',
            border: '1.5px solid #E11D48',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.75)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              background: '#22C55E',
              transform: `scale(${pulseScale})`,
              boxShadow: '0 0 10px #22C55E',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FFFFFF',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            O RESULTADO
          </span>
        </div>

        {/* Card Dinâmico Superior (sem transição vazia ou preta) */}
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            background: 'rgba(11, 13, 19, 0.94)',
            borderRadius: 22,
            border: '1.5px solid rgba(34, 197, 94, 0.5)',
            padding: '16px 28px',
            boxShadow: '0 15px 35px rgba(0, 0, 0, 0.85)',
            minHeight: 110,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `scale(${Math.min(sprFase1, 1)})`,
            opacity: Math.min(sprFase1, 1),
          }}
        >
          {!isFase2 ? (
            <div
              style={{
                transform: `scale(${sprFase1})`,
                opacity: Math.min(sprFase1, 1),
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.15,
                }}
              >
                PEDIDO CONFIRMADO NO WHATSAPP
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FACC15',
                  marginTop: 6,
                }}
              >
                Atendimento com IA direto no WhatsApp
              </div>
            </div>
          ) : (
            <div
              style={{
                transform: `scale(${sprFase2})`,
                opacity: Math.min(sprFase2, 1),
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: 48,
                  fontWeight: 900,
                  color: '#86EFAC',
                  textTransform: 'uppercase',
                  lineHeight: 1.15,
                }}
              >
                COZINHA TRABALHANDO SEM PERDER VENDA
              </div>
              <div
                style={{
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#FFFFFF',
                  marginTop: 6,
                }}
              >
                Pedidos organizados e cozinha em produção
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sobreposição em Picture-in-Picture (PiP) com Mockup Animado do Pedido e Cozinha (y = 520 a 1300, x = 680 a 1050) */}
      <div
        style={{
          position: 'absolute',
          top: 520,
          right: 30,
          width: 380,
          transform: `scale(${sprPip}) translateY(${pipFloatY}px)`,
          opacity: Math.min(sprPip, 1),
          borderRadius: 34,
          background: 'rgba(15, 23, 42, 0.96)',
          border: '2.5px solid rgba(34, 197, 94, 0.55)',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.95), 0 0 35px rgba(34, 197, 94, 0.25)',
          padding: 22,
          zIndex: 25,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        {!isFase2 ? (
          /* FASE 1: PEDIDO CONFIRMADO NO WHATSAPP */
          <>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 4,
                borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
                paddingBottom: 12,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <span style={{fontSize: 34, color: '#22C55E'}}>✓</span>
                <span style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  WhatsApp
                </span>
              </div>
              <div style={{fontSize: 32, fontWeight: 800, color: '#86EFAC'}}>
                Pedido Confirmado
              </div>
            </div>

            <div
              style={{
                background: '#1F2937',
                borderRadius: 18,
                padding: '16px 18px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                Pedido #1042
              </div>
              <div style={{fontSize: 32, fontWeight: 700, color: '#FACC15', marginTop: 6}}>
                1x Combo Artesanal
              </div>
              <div style={{fontSize: 32, color: '#CBD5E1', marginTop: 4}}>
                Pedido no WhatsApp
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                background: 'rgba(34, 197, 94, 0.12)',
                padding: '12px 14px',
                borderRadius: 16,
                border: '1px solid #22C55E',
              }}
            >
              <span style={{fontSize: 32}}>🔔</span>
              <span style={{fontSize: 32, fontWeight: 800, color: '#86EFAC'}}>
                Notificação direta
              </span>
            </div>
          </>
        ) : (
          /* FASE 2: COZINHA TRABALHANDO SEM PERDER VENDA */
          <div
            style={{
              transform: `scale(${Math.min(sprFase2, 1)})`,
              opacity: Math.min(sprFase2, 1),
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 4,
                borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
                paddingBottom: 12,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <span style={{fontSize: 34}}>👨‍🍳</span>
                <span style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                  Cozinha
                </span>
              </div>
              <div style={{fontSize: 32, fontWeight: 800, color: '#FACC15'}}>
                Em Produção
              </div>
            </div>

            <div
              style={{
                background: '#1F2937',
                borderRadius: 18,
                padding: '16px 18px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <div style={{fontSize: 34, fontWeight: 900, color: '#FFFFFF'}}>
                Fila de Pedidos
              </div>
              <div style={{fontSize: 32, fontWeight: 700, color: '#86EFAC', marginTop: 6}}>
                ✓ Pedido no WhatsApp
              </div>
              <div style={{fontSize: 32, color: '#CBD5E1', marginTop: 4}}>
                Cozinha em produção
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                background: 'rgba(225, 29, 72, 0.15)',
                padding: '12px 14px',
                borderRadius: 16,
                border: '1px solid #E11D48',
              }}
            >
              <span style={{fontSize: 32}}>⚡</span>
              <span style={{fontSize: 32, fontWeight: 800, color: '#FDA4AF'}}>
                Sem perder venda
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
