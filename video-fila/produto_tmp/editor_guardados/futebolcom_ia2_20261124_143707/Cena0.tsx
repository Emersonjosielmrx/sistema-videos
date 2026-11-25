import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig, staticFile, Img} from 'remotion';

interface Props {
  fontFamily: string;
}

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo cinematográfico (Ken Burns focado na cozinha/restaurante ativo, sem banana)
  const cameraScale = interpolate(frame, [0, 153], [1.38, 1.55], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cameraTranslateY = interpolate(frame, [0, 153], [-110, -70], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Notificação WhatsApp entra com impacto IMEDIATO no 1º frame (0 a 200ms)
  const notifSpring = spring({
    frame: frame - 1,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Animação de entrada da badge inicial (frame 2)
  const badgeSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Título principal entra em 0.25s (frame 7 - "Perdendo pedido")
  const titleSpring = spring({
    frame: frame - 7,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Alerta vermelho na notificação em 2.0s (frame 60 - urgência da espera)
  const alertProgress = interpolate(frame, [60, 75], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const alertPulse = Math.sin((frame - 60) * 0.3) * 0.08;

  // Gancho de tela selo fixo entra em 3.6s (frame 108)
  const hookSpring = spring({
    frame: frame - 108,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: '#0F0205',
        fontFamily,
      }}
    >
      {/* Foto de fundo viva com push-in cinematográfico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${cameraScale}) translateY(${cameraTranslateY}px)`,
          transformOrigin: 'center 10%',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        {/* Camada de contraste e vinheta para legibilidade absoluta */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15,2,5,0.85) 0%, rgba(15,2,5,0.55) 40%, rgba(15,2,5,0.92) 85%, #0F0205 100%)',
          }}
        />
      </div>

      {/* ZONA SEGURA: Conteúdo entre y=180 e y=1300 */}
      <div
        style={{
          position: 'absolute',
          top: 180,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 24,
        }}
      >
        {/* Tag de Contexto no topo */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 24px',
              borderRadius: 50,
              backgroundColor: '#0B0D13F2',
              border: '2px solid #E11D48',
              boxShadow: '0 8px 24px rgba(225, 29, 72, 0.35)',
            }}
          >
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: '50%',
                backgroundColor: '#E11D48',
                boxShadow: '0 0 12px #E11D48',
              }}
            />
            <span
              style={{
                color: '#FFFFFF',
                fontSize: 34,
                fontWeight: 800,
                letterSpacing: '1px',
                textTransform: 'uppercase',
              }}
            >
              ALERTA NO ATENDIMENTO
            </span>
          </div>
        )}

        {/* Título Forte Cinético: Fala da cena (y ~ 280) */}
        {titleSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${titleSpring}) translateY(${(1 - titleSpring) * 30}px)`,
              opacity: titleSpring,
              width: '100%',
              backgroundColor: '#0B0D13F5',
              padding: '30px 36px',
              borderRadius: 28,
              border: '2px solid rgba(255, 255, 255, 0.15)',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.85)',
              textAlign: 'center',
            }}
          >
            <div
              style={{
                fontSize: 56,
                fontWeight: 900,
                lineHeight: 1.15,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                textWrap: 'balance',
              }}
            >
              PERDENDO PEDIDO?{' '}
              <span
                style={{
                  color: '#FACC15',
                  backgroundColor: '#E11D48',
                  padding: '4px 14px',
                  borderRadius: 14,
                  display: 'inline-block',
                }}
              >
                POR QUE O CLIENTE
              </span>
            </div>
            <div
              style={{
                marginTop: 14,
                fontSize: 38,
                fontWeight: 800,
                color: '#FFFFFF',
                lineHeight: 1.25,
                textTransform: 'uppercase',
              }}
            >
              Manda um oi e ninguém responde?
            </div>
          </div>
        )}

        {/* Mockup Notificação Mobile Viva WhatsApp (y ~ 540) */}
        {notifSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${notifSpring + (alertProgress > 0 ? alertPulse : 0)}) translateY(${
                (1 - notifSpring) * 40
              }px)`,
              opacity: notifSpring,
              width: '100%',
              backgroundColor: alertProgress > 0 ? '#1F0A10F8' : '#0B0D13F8',
              borderRadius: 26,
              border: `2.5px solid ${alertProgress > 0 ? '#E11D48' : 'rgba(255, 255, 255, 0.18)'}`,
              padding: '24px 28px',
              boxShadow:
                alertProgress > 0
                  ? '0 18px 45px rgba(225, 29, 72, 0.45)'
                  : '0 18px 45px rgba(0, 0, 0, 0.9)',
              transition: 'border 0.2s ease',
            }}
          >
            {/* Header da Notificação */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 16,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 14,
                    backgroundColor: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 26,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  💬
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span
                    style={{
                      fontSize: 34,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    WhatsApp Business
                  </span>
                  <span style={{fontSize: 32, color: '#CBD5E1', fontWeight: 700}}>
                    Novo Cliente
                  </span>
                </div>
              </div>
              <span
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: alertProgress > 0 ? '#FFA4B4' : '#CBD5E1',
                }}
              >
                {alertProgress > 0 ? 'Aguardando resposta...' : 'agora'}
              </span>
            </div>

            {/* Mensagem enviada pelo cliente */}
            <div
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                padding: '18px 22px',
                borderRadius: 18,
                fontSize: 38,
                fontWeight: 700,
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>"Oi, queria fazer um pedido..."</span>
              <span style={{fontSize: 30, color: '#FACC15'}}>⏳</span>
            </div>

            {/* Alerta de Desistência em 2.68s */}
            {alertProgress > 0.05 && (
              <div
                style={{
                  marginTop: 18,
                  padding: '12px 18px',
                  borderRadius: 14,
                  backgroundColor: 'rgba(225, 29, 72, 0.25)',
                  border: '1.5px solid #E11D48',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  opacity: alertProgress,
                }}
              >
                <span style={{fontSize: 30}}>⚠️</span>
                <span
                  style={{
                    fontSize: 32,
                    fontWeight: 800,
                    color: '#FFA4B4',
                    textTransform: 'uppercase',
                  }}
                >
                  Demora na resposta = Venda perdida
                </span>
              </div>
            )}
          </div>
        )}

        {/* Selo Fixo: Gancho de Tela (3.8s) */}
        {hookSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${hookSpring})`,
              opacity: hookSpring,
              backgroundColor: '#E11D48',
              padding: '14px 28px',
              borderRadius: 50,
              boxShadow: '0 10px 30px rgba(225, 29, 72, 0.5)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{fontSize: 32}}>🚨</span>
            <span
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              Cliente some no WhatsApp?
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
