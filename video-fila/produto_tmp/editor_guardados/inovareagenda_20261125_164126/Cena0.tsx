import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena0: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Câmera dinâmica contínua: push-in acelerado na abertura para prender atenção no Reels
  const scale = interpolate(frame, [0, 40, 140], [1.06, 1.20, 1.30], {
    extrapolateRight: 'clamp',
  });
  const panY = interpolate(frame, [0, 140], [0, -35], {
    extrapolateRight: 'clamp',
  });

  // Gancho imediato em 0-2s
  // 1. Tag de horário no topo (aparece no frame 0 com pulso)
  const pulse = Math.sin(frame * 0.25) * 0.15 + 0.85;

  // 2. Título principal entra já aos ~0.2s (frame 6)
  const titleSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, mass: 0.5, stiffness: 130},
  });

  // 3. Card WhatsApp Notificação entra antecipadamente nos primeiros 0.33s (frame 10) para retenção imediata
  const notifSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 13, mass: 0.6, stiffness: 120},
  });

  // Transição de saída aos frames 125-139
  const sceneOpacity = interpolate(frame, [125, 139], [1, 0], {
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
        backgroundColor: '#0F172A',
        opacity: sceneOpacity,
      }}
    >
      {/* Background Image com Zoom / Pan */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${scale}) translateY(${panY}px)`,
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
      </div>

      {/* Ambiência noturna dramática e vinheta protetora */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.88) 0%, rgba(15,23,42,0.52) 40%, rgba(15,23,42,0.92) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Safe Zone container: x=60 a 1020, y=150 a 1580 */}
      <div
        style={{
          position: 'absolute',
          top: 170,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Badge temporal no topo */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 999,
            backgroundColor: 'rgba(31, 41, 55, 0.94)',
            border: '1.5px solid rgba(245, 158, 11, 0.5)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
          }}
        >
          <div
            style={{
              width: 14,
              height: 14,
              borderRadius: '50%',
              backgroundColor: '#EF4444',
              boxShadow: `0 0 ${12 * pulse}px #EF4444`,
            }}
          />
          <span
            style={{
              fontFamily,
              fontSize: 34,
              fontWeight: 800,
              color: '#F9FAFB',
              letterSpacing: 1.5,
              textTransform: 'uppercase',
            }}
          >
            02:47 DA MADRUGADA
          </span>
        </div>

        {/* Título Principal com Spring nos primeiros 0.2s */}
        {frame >= 6 && (
          <div
            style={{
              marginTop: 28,
              transform: `scale(${titleSpring})`,
              transformOrigin: 'center center',
              padding: '16px 36px',
              borderRadius: 20,
              backgroundColor: 'rgba(15, 23, 42, 0.96)',
              border: '2px solid rgba(245, 158, 11, 0.85)',
              boxShadow: '0 16px 40px rgba(0,0,0,0.7)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <h1
              style={{
                margin: 0,
                fontFamily,
                fontSize: 60,
                fontWeight: 900,
                color: '#FFFFFF',
                textAlign: 'center',
                letterSpacing: 1,
                lineHeight: 1.15,
                textWrap: 'balance',
              }}
            >
              PERDENDO CLIENTE?
            </h1>
            <span
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 900,
                color: '#F59E0B',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
              }}
            >
              DE MADRUGADA NO WHATSAPP
            </span>
          </div>
        )}

        {/* Mockup Notificação WhatsApp — Entra aos 0.33s (frame 10) para retenção imediata */}
        {frame >= 10 && (
          <div
            style={{
              marginTop: 35,
              width: 860,
              maxWidth: '100%',
              transform: `scale(${notifSpring}) translateY(${interpolate(
                notifSpring,
                [0, 1],
                [35, 0]
              )}px)`,
              padding: '24px 30px',
              borderRadius: 24,
              backgroundColor: 'rgba(30, 41, 59, 0.96)',
              border: '2px solid rgba(37, 211, 102, 0.85)',
              boxShadow:
                '0 20px 45px rgba(0,0,0,0.85), 0 0 25px rgba(37, 211, 102, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
                <div
                  style={{
                    width: 42,
                    height: 42,
                    borderRadius: '50%',
                    backgroundColor: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontWeight: 900,
                    fontSize: 24,
                  }}
                >
                  💬
                </div>
                <span
                  style={{
                    fontFamily,
                    fontSize: 35,
                    fontWeight: 800,
                    color: '#25D366',
                  }}
                >
                  WhatsApp • Novo Cliente
                </span>
              </div>
              <span
                style={{
                  fontFamily,
                  fontSize: 34,
                  fontWeight: 600,
                  color: '#94A3B8',
                }}
              >
                02:47
              </span>
            </div>

            <div
              style={{
                fontFamily,
                fontSize: 38,
                fontWeight: 600,
                color: '#F8FAFC',
                lineHeight: 1.3,
              }}
            >
              &ldquo;Olá! Tem horário disponível para amanhã cedo?&rdquo;
            </div>

            <div
              style={{
                marginTop: 8,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 26px',
                borderRadius: 14,
                backgroundColor: '#DC2626',
                border: '2px solid #EF4444',
                boxShadow: '0 6px 20px rgba(220, 38, 38, 0.55)',
                alignSelf: 'flex-start',
              }}
            >
              <span
                style={{
                  fontFamily,
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  letterSpacing: 0.5,
                }}
              >
                ⚠️ Ninguém respondeu até a manhã
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
