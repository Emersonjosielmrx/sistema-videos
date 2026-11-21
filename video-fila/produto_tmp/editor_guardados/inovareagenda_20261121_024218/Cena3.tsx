import React from 'react';
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  staticFile,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena3: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const totalFrames = 240;

  // Câmera dinâmica contínua: zoom 1.05 -> 1.16 e pan vertical
  const bgScale = interpolate(frame, [0, totalFrames], [1.05, 1.16], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, totalFrames], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge superior no frame 6
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Título no frame 10
  const titleSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Entrada escalonada precisa alinhada com as deixas de voz:
  // Card 1: entra aos 0.3s (frame 10, fala "Hoje o cliente remarca sozinho...")
  const b1Spring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 14, stiffness: 95},
  });

  // Card 2: entra aos 3.6s (frame 108, na fala "a agenda não tem conflito")
  const b2Spring = spring({
    frame: frame - 108,
    fps,
    config: {damping: 13, stiffness: 95},
  });

  // Card 3: entra aos 5.1s (frame 154, na fala "e eu nem preciso intervir")
  const b3Spring = spring({
    frame: frame - 154,
    fps,
    config: {damping: 13, stiffness: 95},
  });

  // Ativação precisa e pop sincronizados com a locução:
  const b1Active = frame < 118;
  const b2Active = frame >= 118;
  const b2Pop = spring({
    frame: frame - 118,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const b3Active = frame >= 162;
  const b3Pop = spring({
    frame: frame - 162,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Pulso contínuo
  const pulse = Math.sin(frame * 0.16) * 0.035 + 1.0;

  // Saída suave
  const exitOpacity = interpolate(frame, [totalFrames - 10, totalFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#0B0D13',
        opacity: exitOpacity,
      }}
    >
      {/* Imagem de Fundo Clara e Vibrante (Regra 19) */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_3.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Vinheta Suave Apenas para Contraste */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(11, 13, 19, 0.82) 0%, rgba(11, 13, 19, 0.30) 35%, rgba(11, 13, 19, 0.42) 65%, rgba(11, 13, 19, 0.85) 100%)',
        }}
      />

      {/* Conteúdo Seguro (y: 170 a 1380) */}
      <div
        style={{
          position: 'absolute',
          left: 60,
          right: 60,
          top: 170,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Rótulo Oficial da Cena */}
        {badgeSpring > 0.01 && (
          <div
            style={{
              transform: `scale(${badgeSpring})`,
              opacity: badgeSpring,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 26px',
              borderRadius: 24,
              background: 'rgba(16, 185, 129, 0.22)',
              border: '2px solid #10B981',
              boxShadow: '0 8px 24px rgba(16, 185, 129, 0.3)',
              marginBottom: 16,
            }}
          >
            <span style={{fontSize: 32}}>✨</span>
            <span
              style={{
                fontFamily,
                fontSize: 32,
                fontWeight: 800,
                color: '#34D399',
                textTransform: 'uppercase',
                letterSpacing: 1.2,
              }}
            >
              O Resultado
            </span>
          </div>
        )}

        {/* Título Principal */}
        {titleSpring > 0.01 && (
          <div
            style={{
              transform: `translateY(${(1 - titleSpring) * 20}px)`,
              opacity: titleSpring,
              width: '100%',
              background: 'rgba(15, 23, 42, 0.88)',
              padding: '18px 24px',
              borderRadius: 24,
              border: '1.5px solid rgba(255, 255, 255, 0.12)',
              fontFamily,
              fontSize: 48,
              fontWeight: 900,
              color: '#FFFFFF',
              textAlign: 'center',
              lineHeight: 1.2,
              textTransform: 'uppercase',
              textShadow: '0 3px 14px rgba(0, 0, 0, 0.9)',
              marginBottom: 24,
              backdropFilter: 'blur(12px)',
            }}
          >
            Agenda automatizada com{' '}
            <span style={{color: '#F59E0B'}}>três certezas</span>
          </div>
        )}

        {/* Checklist dos 3 Benefícios Escalonados */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            alignItems: 'center',
          }}
        >
          {/* Benefício 1 */}
          {b1Spring > 0.01 && (
            <div
              style={{
                transform: `translateX(${(1 - b1Spring) * -35}px) scale(${b1Active ? 1.02 : 1.0})`,
                opacity: b1Spring,
                width: 880,
                background: 'rgba(17, 24, 39, 0.96)',
                border: b1Active
                  ? '2.5px solid #10B981'
                  : '1.5px solid rgba(16, 185, 129, 0.45)',
                borderRadius: 24,
                padding: '22px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                boxShadow: b1Active
                  ? '0 16px 40px rgba(0, 0, 0, 0.8), 0 0 25px rgba(16, 185, 129, 0.35)'
                  : '0 12px 30px rgba(0, 0, 0, 0.7)',
              }}
            >
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: '50%',
                  background: '#10B981',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 900,
                  transform: `scale(${b1Active ? pulse : 1.0})`,
                  boxShadow: '0 0 16px rgba(16, 185, 129, 0.6)',
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 6}}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 36,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      textTransform: 'uppercase',
                    }}
                  >
                    Cliente Remarca Sozinho
                  </span>
                  <span
                    style={{
                      background: 'rgba(16, 185, 129, 0.22)',
                      color: '#34D399',
                      fontFamily,
                      fontSize: 28,
                      fontWeight: 800,
                      padding: '4px 14px',
                      borderRadius: 10,
                      letterSpacing: 0.8,
                    }}
                  >
                    100% AUTOMÁTICO
                  </span>
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#CBD5E1',
                    lineHeight: 1.25,
                  }}
                >
                  O cliente escolhe o novo horário livre no WhatsApp.
                </span>
              </div>
            </div>
          )}

          {/* Benefício 2 */}
          {b2Spring > 0.01 && (
            <div
              style={{
                transform: `translateX(${(1 - b2Spring) * 35}px) scale(${b2Active ? 1.0 + b2Pop * 0.02 : 1.0})`,
                opacity: b2Spring,
                width: 880,
                background: 'rgba(17, 24, 39, 0.96)',
                border: b2Active
                  ? '2.5px solid #10B981'
                  : '1.5px solid rgba(255, 255, 255, 0.15)',
                borderRadius: 24,
                padding: '22px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                boxShadow: b2Active
                  ? '0 16px 40px rgba(0, 0, 0, 0.8), 0 0 25px rgba(16, 185, 129, 0.3)'
                  : '0 10px 25px rgba(0, 0, 0, 0.6)',
                transition: 'border 0.3s ease, box-shadow 0.3s ease',
              }}
            >
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: '50%',
                  background: b2Active ? '#10B981' : 'rgba(255, 255, 255, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: b2Active ? '#FFFFFF' : '#94A3B8',
                  fontSize: 34,
                  fontWeight: 900,
                  boxShadow: b2Active ? '0 0 16px rgba(16, 185, 129, 0.6)' : 'none',
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 6}}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 36,
                      fontWeight: 900,
                      color: b2Active ? '#FFFFFF' : '#CBD5E1',
                      textTransform: 'uppercase',
                    }}
                  >
                    Agenda Sem Conflito
                  </span>
                  <span
                    style={{
                      background: 'rgba(16, 185, 129, 0.22)',
                      color: '#34D399',
                      fontFamily,
                      fontSize: 28,
                      fontWeight: 800,
                      padding: '4px 14px',
                      borderRadius: 10,
                      letterSpacing: 0.8,
                    }}
                  >
                    ZERO CONFLITO
                  </span>
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#94A3B8',
                    lineHeight: 1.25,
                  }}
                >
                  Sem sobreposição e sem duplo agendamento.
                </span>
              </div>
            </div>
          )}

          {/* Benefício 3 */}
          {b3Spring > 0.01 && (
            <div
              style={{
                transform: `translateX(${(1 - b3Spring) * -35}px) scale(${b3Active ? 1.0 + b3Pop * 0.02 : 1.0})`,
                opacity: b3Spring,
                width: 880,
                background: 'rgba(17, 24, 39, 0.96)',
                border: b3Active
                  ? '2.5px solid #F59E0B'
                  : '1.5px solid rgba(255, 255, 255, 0.15)',
                borderRadius: 24,
                padding: '22px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                boxShadow: b3Active
                  ? '0 16px 40px rgba(0, 0, 0, 0.8), 0 0 25px rgba(245, 158, 11, 0.35)'
                  : '0 10px 25px rgba(0, 0, 0, 0.6)',
                transition: 'border 0.3s ease, box-shadow 0.3s ease',
              }}
            >
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: '50%',
                  background: b3Active ? '#F59E0B' : 'rgba(255, 255, 255, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: b3Active ? '#121216' : '#94A3B8',
                  fontSize: 34,
                  fontWeight: 900,
                  boxShadow: b3Active ? '0 0 20px rgba(245, 158, 11, 0.6)' : 'none',
                  flexShrink: 0,
                }}
              >
                ✓
              </div>
              <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 6}}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span
                    style={{
                      fontFamily,
                      fontSize: 36,
                      fontWeight: 900,
                      color: b3Active ? '#F59E0B' : '#CBD5E1',
                      textTransform: 'uppercase',
                    }}
                  >
                    Zero Intervenção Manual
                  </span>
                  <span
                    style={{
                      background: 'rgba(245, 158, 11, 0.22)',
                      color: '#FBBF24',
                      fontFamily,
                      fontSize: 28,
                      fontWeight: 800,
                      padding: '4px 14px',
                      borderRadius: 10,
                      letterSpacing: 0.8,
                    }}
                  >
                    AUTÔNOMO
                  </span>
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 32,
                    fontWeight: 600,
                    color: '#94A3B8',
                    lineHeight: 1.25,
                  }}
                >
                  Você não precisa pausar o trabalho para responder.
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
