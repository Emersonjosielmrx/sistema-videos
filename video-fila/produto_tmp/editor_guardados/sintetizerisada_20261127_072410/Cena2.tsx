import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {FONT_FAMILY, THEME} from './theme';

export const Cena2: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (>= 4% de movimento)
  const bgScale = interpolate(frame, [0, 259], [1.08, 1.22], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 259], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Top Badge
  const badgeSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Entrada do celular e zoom dinâmico contínuo (push-in suave de produto moderno)
  const phoneSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  const phonePushIn = interpolate(frame, [0, 259], [0.98, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Mensagens com springs individuais
  const msg1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const isTyping = frame >= 38 && frame < 65;

  const msg2Spring = spring({
    frame: frame - 65,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const msg3Spring = spring({
    frame: frame - 125,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const msg4Spring = spring({
    frame: frame - 160,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  const isBloqueado = frame >= 165;
  const lockSpring = spring({
    frame: frame - 165,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const msg5Spring = spring({
    frame: frame - 200,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Scroll sutil e seguro: mantém todas as mensagens inteiras, sem corte ou balão fatiado
  const scrollOffset = interpolate(
    frame,
    [195, 215],
    [0, -25],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.darkBg, overflow: 'hidden'}}>
      {/* Background desfocado com movimento contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
          transformOrigin: 'center center',
          filter: 'blur(12px)',
        }}
      >
        <Img
          src={staticFile('img_2.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11,15,25,0.85) 0%, rgba(11,15,25,0.65) 50%, rgba(11,15,25,0.92) 100%)',
          }}
        />
      </div>

      {/* Conteúdo na Safe Zone */}
      <div
        style={{
          position: 'absolute',
          top: THEME.safeZone.top + 10,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily: FONT_FAMILY,
          zIndex: 10,
        }}
      >
        {/* Top Badge */}
        {frame >= 4 && (
          <div
            style={{
              transform: `translateY(${(1 - badgeSpring) * -15}px)`,
              background: '#111827F5',
              border: `1.5px solid ${THEME.colors.primary}`,
              borderRadius: 24,
              padding: '6px 22px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
              marginBottom: 12,
            }}
          >
            <span style={{fontSize: 28}}>⚡</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: THEME.colors.primary,
                letterSpacing: 1.2,
                textTransform: 'uppercase',
              }}
            >
              Como Funciona • IA no WhatsApp
            </span>
          </div>
        )}

        {/* Indicador de Status IA */}
        {frame >= 8 && (
          <div
            style={{
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              background: isBloqueado ? '#064E3BF5' : '#1E293BF5',
              border: `1.5px solid ${isBloqueado ? '#10B981' : '#60A5FA'}`,
              borderRadius: 18,
              padding: '8px 22px',
              boxShadow: '0 6px 20px rgba(0,0,0,0.5)',
              transform: isBloqueado ? `scale(${1 + lockSpring * 0.04})` : 'scale(1)',
            }}
          >
            <span style={{fontSize: 28}}>{isBloqueado ? '🔒' : '👁️'}</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: isBloqueado ? '#6EE7B7' : '#93C5FD',
                textTransform: 'uppercase',
              }}
            >
              {isBloqueado
                ? 'Vaga bloqueada para o 1º que escolheu'
                : 'Verificando horários em tempo real'}
            </span>
          </div>
        )}

        {/* Mockup Realista de Smartphone Moderno com Proporções Autênticas */}
        {frame >= 6 && (
          <div
            style={{
              width: 840,
              height: 980,
              background: '#0B141B',
              borderRadius: 44,
              border: '10px solid #1E293B',
              boxShadow:
                '0 30px 80px rgba(0,0,0,0.85), 0 0 0 2px rgba(255,255,255,0.15), 0 0 40px rgba(255,169,77,0.15)',
              overflow: 'hidden',
              position: 'relative',
              transform: `scale(${phoneSpring * phonePushIn})`,
            }}
          >
            {/* Notch / Dynamic Island */}
            <div
              style={{
                position: 'absolute',
                top: 8,
                left: '50%',
                transform: 'translateX(-50%)',
                width: 120,
                height: 20,
                backgroundColor: '#000000',
                borderRadius: 10,
                zIndex: 30,
              }}
            />

            {/* Header Fixo do WhatsApp */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 110,
                paddingTop: 16,
                background: '#1F2C34',
                paddingLeft: 22,
                paddingRight: 22,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1.5px solid rgba(255,255,255,0.12)',
                zIndex: 20,
                boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: 26,
                    background: THEME.colors.primary,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 28,
                    fontWeight: 900,
                    color: '#1F2937',
                  }}
                >
                  ⚡
                </div>
                <div>
                  <div style={{fontSize: 34, fontWeight: 800, color: '#FFFFFF'}}>
                    Agenda IA
                  </div>
                  <div style={{fontSize: 32, color: '#25D366', fontWeight: 700}}>
                    Online agora
                  </div>
                </div>
              </div>
              <div
                style={{
                  background: 'rgba(255,255,255,0.12)',
                  padding: '6px 16px',
                  borderRadius: 12,
                  fontSize: 32,
                  color: '#CBD5E1',
                  fontWeight: 700,
                }}
              >
                Simulação
              </div>
            </div>

            {/* Viewport de Mensagens com Máscara Gradiente no Topo (elimina balões fatiados) */}
            <div
              style={{
                position: 'absolute',
                top: 110,
                left: 0,
                right: 0,
                bottom: 0,
                overflow: 'hidden',
                padding: '18px 22px',
                WebkitMaskImage:
                  'linear-gradient(to bottom, transparent 0px, black 35px, black 100%)',
                maskImage:
                  'linear-gradient(to bottom, transparent 0px, black 35px, black 100%)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 14,
                  transform: `translateY(${scrollOffset}px)`,
                }}
              >
                {/* Msg 1: Cliente */}
                {frame >= 12 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      maxWidth: '85%',
                      background: '#202C33',
                      padding: '12px 20px',
                      borderRadius: '16px 16px 16px 4px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                      transform: `translateY(${(1 - msg1Spring) * 15}px)`,
                    }}
                  >
                    <div style={{fontSize: 34, fontWeight: 600, color: '#E9EDEF'}}>
                      Oi! Tem horário amanhã às 15h?
                    </div>
                    <div
                      style={{
                        textAlign: 'right',
                        fontSize: 32,
                        color: '#94A3B8',
                        marginTop: 4,
                      }}
                    >
                      14:32
                    </div>
                  </div>
                )}

                {/* IA Digitando */}
                {isTyping && (
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      background: '#005C4B',
                      padding: '10px 20px',
                      borderRadius: 16,
                      color: '#D9FDD3',
                      fontSize: 32,
                      fontWeight: 700,
                      fontStyle: 'italic',
                    }}
                  >
                    Digitando...
                  </div>
                )}

                {/* Msg 2: IA Responde */}
                {frame >= 65 && (
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      maxWidth: '88%',
                      background: '#005C4B',
                      padding: '12px 20px',
                      borderRadius: '16px 16px 4px 16px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                      transform: `translateY(${(1 - msg2Spring) * 15}px)`,
                    }}
                  >
                    <div style={{fontSize: 34, fontWeight: 600, color: '#E9EDEF'}}>
                      Tenho sim! Às 15h está livre. Posso reservar para você?
                    </div>
                    <div
                      style={{
                        textAlign: 'right',
                        fontSize: 32,
                        color: '#68D391',
                        marginTop: 4,
                      }}
                    >
                      14:32 ✓✓
                    </div>
                  </div>
                )}

                {/* Msg 3: Cliente Confirma */}
                {frame >= 125 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      maxWidth: '85%',
                      background: '#202C33',
                      padding: '12px 20px',
                      borderRadius: '16px 16px 16px 4px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                      transform: `translateY(${(1 - msg3Spring) * 15}px)`,
                    }}
                  >
                    <div style={{fontSize: 34, fontWeight: 600, color: '#E9EDEF'}}>
                      Pode reservar, por favor.
                    </div>
                    <div
                      style={{
                        textAlign: 'right',
                        fontSize: 32,
                        color: '#94A3B8',
                        marginTop: 4,
                      }}
                    >
                      14:33
                    </div>
                  </div>
                )}

                {/* Msg 4: IA Confirma e Bloqueia Vaga */}
                {frame >= 160 && (
                  <div
                    style={{
                      alignSelf: 'flex-end',
                      maxWidth: '90%',
                      background: '#005C4B',
                      padding: '14px 20px',
                      borderRadius: '16px 16px 4px 16px',
                      border: '2px solid #10B981',
                      boxShadow: '0 4px 18px rgba(16,185,129,0.35)',
                      transform: `translateY(${(1 - msg4Spring) * 15}px)`,
                    }}
                  >
                    <div style={{fontSize: 34, fontWeight: 700, color: '#FFFFFF'}}>
                      Pronto, horário confirmado. Vou te lembrar antes.
                    </div>
                    <div
                      style={{
                        marginTop: 8,
                        background: 'rgba(0,0,0,0.3)',
                        padding: '6px 14px',
                        borderRadius: 10,
                        fontSize: 32,
                        fontWeight: 800,
                        color: '#34D399',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                      }}
                    >
                      <span>🔒 Vaga bloqueada no sistema</span>
                    </div>
                    <div
                      style={{
                        textAlign: 'right',
                        fontSize: 32,
                        color: '#68D391',
                        marginTop: 4,
                      }}
                    >
                      14:33 ✓✓
                    </div>
                  </div>
                )}

                {/* Msg 5: Cliente Agradece */}
                {frame >= 200 && (
                  <div
                    style={{
                      alignSelf: 'flex-start',
                      maxWidth: '85%',
                      background: '#202C33',
                      padding: '12px 20px',
                      borderRadius: '16px 16px 16px 4px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                      transform: `translateY(${(1 - msg5Spring) * 15}px)`,
                    }}
                  >
                    <div style={{fontSize: 34, fontWeight: 600, color: '#E9EDEF'}}>
                      Perfeito, obrigada!
                    </div>
                    <div
                      style={{
                        textAlign: 'right',
                        fontSize: 32,
                        color: '#94A3B8',
                        marginTop: 4,
                      }}
                    >
                      14:33
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
