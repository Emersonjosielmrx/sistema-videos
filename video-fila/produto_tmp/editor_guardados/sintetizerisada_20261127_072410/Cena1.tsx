import React from 'react';
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {FONT_FAMILY, THEME} from './theme';

export const Cena1: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Câmera do apresentador: plano médio dinâmico com punch-in zoom digital em 10.8s (frame 180)
  // Antes do frame 180: slow push-in contínuo (1.00 -> 1.04)
  // No frame 180: corte seco punch-in para 1.12x centrado no rosto, continuando até 1.15x
  const isSecondHalf = frame >= 180;
  const videoScale = isSecondHalf
    ? interpolate(frame, [180, 246], [1.12, 1.15], {extrapolateRight: 'clamp'})
    : interpolate(frame, [0, 180], [1.0, 1.04], {extrapolateRight: 'clamp'});

  // Entrada suave do badge do topo (frame 6)
  const badgeSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 95},
  });

  // Pílula 1: "2 CLIENTES NO WHATSAPP"
  // Entra no frame 12 e permanece 100% visível, sólida e legível durante TODA a primeira metade da fala e a pausa (até frame 180)
  const pill1Spring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 14, stiffness: 110},
  });

  // Pílula 2: "CLIENTE SAÍA CHATEADO"
  // Sincronizada exatamente para o momento em que a palavra é dita (frame 180, 10.84s - q06)
  // Troca rápida sem elemento fantasma nem escala minúscula
  const pill2Spring = spring({
    frame: frame - 180,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const pulse = Math.sin((frame - 180) * 0.25) * 0.025;

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.darkBg, overflow: 'hidden'}}>
      {/* Vídeo do dono em tela cheia com leve zoom contínuo e punch-in digital na segunda metade */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: '50% 38%',
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

        {/* Gradiente superior suave apenas para contraste da faixa superior (y: 0 a 340) */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 350,
            background:
              'linear-gradient(180deg, rgba(11,15,25,0.85) 0%, rgba(11,15,25,0.5) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Gradiente inferior protetor para a legenda (y: 1300 a 1920) */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 480,
            background:
              'linear-gradient(0deg, rgba(11,15,25,0.88) 0%, rgba(11,15,25,0.4) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Conteúdo do Topo: estritamente entre y: 150 e 330 (rosto 100% livre) */}
      <div
        style={{
          position: 'absolute',
          top: THEME.safeZone.top,
          left: THEME.safeZone.left,
          right: THEME.safeZone.left,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          fontFamily: FONT_FAMILY,
          zIndex: 10,
        }}
      >
        {/* Badge superior de contexto */}
        <div
          style={{
            transform: `scale(${badgeSpring})`,
            opacity: badgeSpring,
            background: '#111827EE',
            border: `1.5px solid ${THEME.colors.primary}`,
            borderRadius: 30,
            padding: '8px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
            marginBottom: 14,
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: 6,
              backgroundColor: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: THEME.colors.primary,
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O Problema Real
          </span>
        </div>

        {/* Pílula 1: 2 Clientes no WhatsApp (visível e sólida dos frames 12 a 179) */}
        {!isSecondHalf && frame >= 12 && (
          <div
            style={{
              transform: `scale(${pill1Spring})`,
              opacity: pill1Spring,
              background: '#111827EE',
              border: '2px solid rgba(255,255,255,0.18)',
              borderRadius: 20,
              padding: '12px 30px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              boxShadow: '0 10px 28px rgba(0,0,0,0.7)',
            }}
          >
            <span style={{fontSize: 34}}>💬</span>
            <span
              style={{
                fontSize: 36,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              2 clientes no WhatsApp
            </span>
          </div>
        )}

        {/* Pílula 2: Cliente saía chateado (entra no frame 180 / 10.84s com 100% de opacidade e escala total) */}
        {isSecondHalf && (
          <div
            style={{
              transform: `scale(${pill2Spring + pulse})`,
              opacity: pill2Spring,
              background: '#2A1215EE',
              border: '2px solid #EF4444',
              borderRadius: 20,
              padding: '12px 30px',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              boxShadow: '0 10px 28px rgba(239,68,68,0.5)',
            }}
          >
            <span style={{fontSize: 34}}>❌</span>
            <span
              style={{
                fontSize: 36,
                fontWeight: 900,
                color: '#FFFFFF',
                textTransform: 'uppercase',
                letterSpacing: 0.5,
              }}
            >
              Cliente saía chateado
            </span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
