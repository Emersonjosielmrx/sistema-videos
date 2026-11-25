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

interface Cena0Props {
  fontFamily: string;
}

export const Cena0: React.FC<Cena0Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo (>= 4% de escala ao longo da cena)
  const bgScale = interpolate(frame, [0, 160], [1.02, 1.14], {
    extrapolateRight: 'clamp',
  });
  const bgPanY = interpolate(frame, [0, 160], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Entrada do Badge superior (aos 0.25s)
  const badgeSpring = spring({
    frame: frame - 7,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Título Principal (aos 0.4s)
  const title1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 15, stiffness: 130},
  });

  // Destaque da palavra "DESISTE" (aos 1.0s = frame 30)
  const desisteSpring = spring({
    frame: frame - 30,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Segunda linha do título (aos 1.6s = frame 48)
  const title2Spring = spring({
    frame: frame - 48,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Entrada do Card Central de Alerta/Rejeição do App (aos 0.4s = frame 12)
  const cardSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 100},
  });

  // Gancho inferior "Cliente não precisa baixar nada" (aos 3.6s = frame 108)
  const ganchoSpring = spring({
    frame: frame - 108,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Microdinâmica constante
  const floatY = Math.sin(frame / 12) * 6;
  const pulseScale = 1 + Math.sin(frame / 8) * 0.02;

  return (
    <AbsoluteFill style={{backgroundColor: '#0F172A', overflow: 'hidden'}}>
      {/* Fundo com foto em zoom e pan dinâmicos */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgPanY}px)`,
          transformOrigin: 'center center',
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
        {/* Camada protetora escura para garantir contraste >= 4.5:1 */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(15,23,42,0.88) 0%, rgba(15,23,42,0.75) 45%, rgba(11,13,19,0.94) 100%)',
          }}
        />
      </div>

      {/* Conteúdo na Safe Zone (y: 150 a 1580, x: 60 a 1020) */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Badge da Dor */}
        {frame >= 7 && (
          <div
            style={{
              transform: `scale(${Math.max(0, badgeSpring)})`,
              opacity: Math.min(1, badgeSpring),
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 24px',
              borderRadius: 30,
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              border: '2px solid #EF4444',
              boxShadow: '0 8px 24px rgba(239, 68, 68, 0.25)',
              marginBottom: 20,
            }}
          >
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: '50%',
                backgroundColor: '#EF4444',
                boxShadow: '0 0 10px #EF4444',
              }}
            />
            <span
              style={{
                fontFamily,
                fontSize: 34,
                fontWeight: 800,
                color: '#FEE2E2',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              BARREIRA DE AGENDAMENTO
            </span>
          </div>
        )}

        {/* Título Cinético Gigante */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 12,
            marginTop: 10,
          }}
        >
          {frame >= 12 && (
            <div
              style={{
                transform: `scale(${Math.max(0, title1Spring)})`,
                opacity: Math.min(1, title1Spring),
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                flexWrap: 'wrap',
                justifyContent: 'center',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 56,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textShadow: '0 4px 16px rgba(0,0,0,0.9)',
                }}
              >
                SEU CLIENTE
              </span>
              <span
                style={{
                  fontFamily,
                  fontSize: 56,
                  fontWeight: 900,
                  color: '#0F172A',
                  backgroundColor: '#FFA94D',
                  padding: '4px 18px',
                  borderRadius: 14,
                  transform: `scale(${frame >= 30 ? Math.max(0, desisteSpring) : 1})`,
                  boxShadow: '0 6px 20px rgba(255,169,77,0.4)',
                }}
              >
                DESISTE
              </span>
            </div>
          )}

          {frame >= 48 && (
            <div
              style={{
                transform: `scale(${Math.max(0, title2Spring)})`,
                opacity: Math.min(1, title2Spring),
                fontFamily,
                fontSize: 46,
                fontWeight: 900,
                color: '#F8FAFC',
                textShadow: '0 4px 16px rgba(0,0,0,0.9)',
                maxWidth: 920,
                lineHeight: 1.2,
                textWrap: 'balance',
              }}
            >
              DE MARCAR POR CAUSA DE APLICATIVO?
            </div>
          )}
        </div>

        {/* Card Central Visual: Simulação do Problema do App */}
        {frame >= 12 && (
          <div
            style={{
              marginTop: 40,
              width: 860,
              transform: `scale(${Math.max(0, cardSpring)}) translateY(${floatY}px)`,
              opacity: Math.min(1, cardSpring),
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              borderRadius: 32,
              border: '2px solid rgba(255, 255, 255, 0.14)',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.85)',
              padding: '36px 40px',
              display: 'flex',
              flexDirection: 'column',
              gap: 24,
            }}
          >
            {/* Cabeçalho do Card */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1.5px solid rgba(255,255,255,0.1)',
                paddingBottom: 20,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 16,
                    backgroundColor: '#EF4444',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 32,
                    color: '#FFFFFF',
                    fontWeight: 900,
                  }}
                >
                  ✕
                </div>
                <div style={{display: 'flex', flexDirection: 'column'}}>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 38,
                      fontWeight: 800,
                      color: '#FFFFFF',
                    }}
                  >
                    Instalar Aplicativo (180 MB)
                  </span>
                  <span
                    style={{
                      fontFamily,
                      fontSize: 34,
                      fontWeight: 600,
                      color: '#94A3B8',
                    }}
                  >
                    Exigido para agendar horário
                  </span>
                </div>
              </div>
              <div
                style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid #EF4444',
                  padding: '8px 16px',
                  borderRadius: 12,
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#F87171',
                }}
              >
                Fricção alta
              </div>
            </div>

            {/* Barra de desistência simulada */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#CBD5E1',
                }}
              >
                <span>Download cancelado pelo cliente</span>
                <span style={{color: '#EF4444'}}>Desistiu</span>
              </div>
              <div
                style={{
                  width: '100%',
                  height: 16,
                  borderRadius: 10,
                  backgroundColor: 'rgba(255,255,255,0.08)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${interpolate(frame, [45, 90], [20, 65], {
                      extrapolateRight: 'clamp',
                    })}%`,
                    height: '100%',
                    backgroundColor: '#EF4444',
                    borderRadius: 10,
                  }}
                />
              </div>
            </div>

            {/* Alerta de Perda */}
            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.12)',
                borderRadius: 18,
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                border: '1px solid rgba(239, 68, 68, 0.3)',
              }}
            >
              <span style={{fontSize: 36}}>⚠️</span>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 700,
                  color: '#FCA5A5',
                  lineHeight: 1.3,
                }}
              >
                Cliente fecha a loja e não volta para marcar.
              </span>
            </div>
          </div>
        )}

        {/* Gancho fixo (aos 3.6s) */}
        {frame >= 108 && (
          <div
            style={{
              marginTop: 36,
              transform: `scale(${Math.max(0, ganchoSpring) * pulseScale})`,
              opacity: Math.min(1, ganchoSpring),
              backgroundColor: '#FFA94D',
              padding: '16px 36px',
              borderRadius: 24,
              boxShadow: '0 12px 32px rgba(255, 169, 77, 0.45)',
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            <span style={{fontSize: 36, color: '#0F172A'}}>⚡</span>
            <span
              style={{
                fontFamily,
                fontSize: 36,
                fontWeight: 900,
                color: '#0F172A',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Cliente não precisa baixar nada
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
