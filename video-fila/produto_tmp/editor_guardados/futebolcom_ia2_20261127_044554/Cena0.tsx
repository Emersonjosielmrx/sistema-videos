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

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no fundo dinâmico de restaurante (push contínuo de 1.05 a 1.14)
  const bgScale = interpolate(frame, [0, 128], [1.05, 1.14], {
    extrapolateRight: 'clamp',
  });

  // Título 1: entra aos 0.27s (frame 8)
  const sprTitulo1 = spring({
    frame: frame - 8,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Título 2: entra com overshoot elástico aos 1.4s (frame 42)
  const sprTitulo2 = spring({
    frame: frame - 42,
    fps,
    config: {damping: 9, stiffness: 150},
  });

  // Card do WhatsApp: ENTRA NO SEGUNDO ZERO (frame 1) com pop suave e overshoot
  const sprChat = spring({
    frame: frame - 1,
    fps,
    config: {damping: 10, stiffness: 160, mass: 0.8},
  });

  // Micro-vibração de notificação nos primeiros 16 frames
  const vibrateRot =
    frame < 18
      ? Math.sin(frame * 1.8) *
        interpolate(frame, [0, 18], [2.2, 0], {extrapolateRight: 'clamp'})
      : 0;

  // Flutuação contínua suave no mockup
  const floatY = Math.sin(frame / 12) * 6;

  // Alerta de desistência: entra aos 1.25s (frame 38) com alta legibilidade imediata
  const sprAlerta = spring({
    frame: frame - 38,
    fps,
    config: {damping: 11, stiffness: 160},
  });

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
      {/* Fundo de B-Roll Dinâmico de Restaurante com Desfoque Bokeh e Movimento */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale})`,
          transformOrigin: 'center center',
        }}
      >
        <OffthreadVideo
          src={staticFile('dono_1.mp4')}
          muted
          style={{
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
            filter: 'blur(14px) brightness(0.62)',
          }}
        />
        {/* Overlay escuro em vinheta para alto contraste e foco */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at center, rgba(49, 6, 15, 0.55) 0%, rgba(11, 13, 19, 0.92) 100%)',
          }}
        />
      </div>

      {/* Partículas de luz / bokeh quentes subindo sutilmente no fundo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          overflow: 'hidden',
        }}
      >
        {[0, 1, 2, 3].map((i) => {
          const pY = interpolate((frame * 1.5 + i * 80) % 360, [0, 360], [1200, 300]);
          const pX = 180 + i * 220;
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: pX,
                top: pY,
                width: 18 + i * 8,
                height: 18 + i * 8,
                borderRadius: '50%',
                background: 'radial-gradient(circle, rgba(250, 204, 21, 0.28) 0%, transparent 70%)',
              }}
            />
          );
        })}
      </div>

      {/* Faixa Superior (Safe Zone y = 160 a 440) — Foco exclusivo na dor, sem caixas concorrentes */}
      <div
        style={{
          position: 'absolute',
          top: 165,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
          zIndex: 20,
        }}
      >
        {/* Pill Badge de Contexto */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '8px 24px',
            borderRadius: 30,
            background: 'rgba(49, 6, 15, 0.94)',
            border: '1.5px solid #E11D48',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.75)',
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              background: '#22C55E',
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
            ATENDIMENTO NO WHATSAPP
          </span>
        </div>

        {/* Título Principal Cinético (Pergunta do Gancho) */}
        <div
          style={{
            width: '100%',
            maxWidth: 960,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          {frame >= 8 && (
            <div
              style={{
                transform: `scale(${sprTitulo1})`,
                opacity: sprTitulo1,
                background: 'rgba(11, 13, 19, 0.94)',
                padding: '12px 28px',
                borderRadius: 18,
                border: '1.5px solid rgba(255, 255, 255, 0.15)',
                boxShadow: '0 12px 30px rgba(0,0,0,0.85)',
              }}
            >
              <span
                style={{
                  fontSize: 50,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.2,
                  textAlign: 'center',
                  display: 'block',
                }}
              >
                CLIENTE MANDA UM OI...
              </span>
            </div>
          )}

          {frame >= 42 && (
            <div
              style={{
                transform: `scale(${sprTitulo2})`,
                opacity: Math.min(sprTitulo2, 1),
                background: '#E11D48',
                padding: '12px 28px',
                borderRadius: 18,
                boxShadow: '0 14px 35px rgba(225, 29, 72, 0.65)',
              }}
            >
              <span
                style={{
                  fontSize: 50,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  lineHeight: 1.2,
                  textAlign: 'center',
                  display: 'block',
                }}
              >
                ...E SOME SEM FAZER O PEDIDO?
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Centro: Balão / Mockup Ampliado do WhatsApp com Pop Imediato no Segundo 0 */}
      <div
        style={{
          position: 'absolute',
          top: 560,
          left: 60,
          right: 60,
          transform: `scale(${sprChat}) translateY(${floatY}px) rotate(${vibrateRot}deg)`,
          transformOrigin: 'center center',
          opacity: Math.min(sprChat, 1),
          background: 'rgba(15, 20, 30, 0.96)',
          borderRadius: 32,
          border: '2px solid rgba(255, 255, 255, 0.16)',
          padding: 34,
          boxShadow: '0 25px 65px rgba(0, 0, 0, 0.95)',
          zIndex: 15,
        }}
      >
        {/* Topo do Chat Simulado */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingBottom: 20,
            borderBottom: '1.5px solid rgba(255, 255, 255, 0.12)',
            marginBottom: 24,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <div
              style={{
                width: 60,
                height: 60,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #22C55E, #15803D)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 32,
                fontWeight: 900,
                color: '#FFFFFF',
                boxShadow: '0 4px 15px rgba(34, 197, 94, 0.4)',
              }}
            >
              C
            </div>
            <div>
              <div style={{fontSize: 38, fontWeight: 800, color: '#FFFFFF'}}>
                Cliente Delivery
              </div>
              <div style={{fontSize: 32, fontWeight: 500, color: '#94A3B8'}}>
                Aguardando resposta...
              </div>
            </div>
          </div>

          {/* Selo Simulação Obrigatório */}
          <div
            style={{
              padding: '6px 16px',
              borderRadius: 14,
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.18)',
              fontSize: 32,
              fontWeight: 700,
              color: '#CBD5E1',
            }}
          >
            Simulação
          </div>
        </div>

        {/* Mensagem 1: Cliente manda Oi */}
        <div
          style={{
            alignSelf: 'flex-start',
            maxWidth: 720,
            background: '#1F2937',
            padding: '22px 28px',
            borderRadius: '24px 24px 24px 4px',
            marginBottom: 22,
            boxShadow: '0 8px 20px rgba(0, 0, 0, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <div
            style={{
              fontSize: 38,
              fontWeight: 600,
              color: '#F9FAFB',
              lineHeight: 1.35,
            }}
          >
            &quot;Oi, boa noite! Queria ver o cardápio e fazer um pedido...&quot;
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
              gap: 8,
              marginTop: 12,
              fontSize: 32,
              color: '#9CA3AF',
            }}
          >
            <span>19:42</span>
            <span style={{color: '#60A5FA', fontWeight: 900}}>✓✓</span>
          </div>
        </div>

        {/* Notificação de Demora / Desistência com Contraste Definitivo Imediato */}
        {frame >= 38 && (
          <div
            style={{
              transform: `scale(${sprAlerta})`,
              opacity: Math.min(sprAlerta, 1),
              background: 'linear-gradient(135deg, rgba(190, 18, 60, 0.95), rgba(76, 5, 25, 0.98))',
              border: '2px solid #E11D48',
              borderRadius: 22,
              padding: '20px 26px',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
              boxShadow: '0 12px 35px rgba(225, 29, 72, 0.55)',
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                background: '#E11D48',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 32,
                color: '#FFFFFF',
                flexShrink: 0,
                boxShadow: '0 0 15px rgba(225, 29, 72, 0.8)',
              }}
            >
              ⏳
            </div>
            <div>
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textShadow: '0 2px 6px rgba(0,0,0,0.8)',
                }}
              >
                Demora no atendimento manual
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 700,
                  color: '#FECDD3',
                  marginTop: 4,
                  textShadow: '0 2px 6px rgba(0,0,0,0.8)',
                }}
              >
                Cliente desiste antes de escolher o que pedir
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
