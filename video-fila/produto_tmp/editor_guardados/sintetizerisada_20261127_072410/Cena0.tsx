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

export const Cena0: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo: slow push-in contínuo (escala 1.00 para 1.08 ao longo da cena)
  const bgScale = interpolate(frame, [0, 152], [1.0, 1.08], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 152], [0, -30], {
    extrapolateRight: 'clamp',
  });

  // Top Badge (frame 2)
  const badgeSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Título (frame 4)
  const titleSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, stiffness: 110},
  });

  // Destaque "mesmo horário" em 1.53s (frame 46)
  const isMesmoHorario = frame >= 46;
  const highlightSpring = spring({
    frame: frame - 46,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  // Entrada SIMULTÂNEA de ambos os cards nos primeiros 0.8s (frame 6 a 18)
  const card1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const card2Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  // Alerta imediato de conflito aos 0.75s (frame 22) - Tensão e urgência antes dos 2 segundos
  const isEarlyConflito = frame >= 22;
  const earlyConflitoSpring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  // Conflito / Perda final em 2.60s (frame 78) "perde um deles"
  const isConflito = frame >= 78;
  const conflitoSpring = spring({
    frame: frame - 78,
    fps,
    config: {damping: 12, stiffness: 130},
  });

  const pulse = isConflito ? Math.sin((frame - 78) * 0.25) * 0.035 : isEarlyConflito ? Math.sin((frame - 22) * 0.2) * 0.02 : 0;

  return (
    <AbsoluteFill style={{backgroundColor: THEME.colors.darkBg, overflow: 'hidden'}}>
      {/* Imagem de fundo com zoom dinâmico */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_0.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(180deg, rgba(11,15,25,0.88) 0%, rgba(11,15,25,0.65) 45%, rgba(11,15,25,0.92) 100%)',
          }}
        />
      </div>

      {/* Container compacto no topo garantindo respiro total dos rostos */}
      <div
        style={{
          position: 'absolute',
          top: THEME.safeZone.top + 15,
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
              background: '#1F2937F5',
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
            <span style={{fontSize: 28}}>⚠️</span>
            <span
              style={{
                fontSize: 32,
                fontWeight: 800,
                color: THEME.colors.primary,
                letterSpacing: 1.2,
                textTransform: 'uppercase',
              }}
            >
              Conflito de Horário
            </span>
          </div>
        )}

        {/* Título Gancho Cinético */}
        {frame >= 8 && (
          <div
            style={{
              textAlign: 'center',
              transform: `translateY(${(1 - titleSpring) * -15}px)`,
              marginBottom: 16,
            }}
          >
            <div
              style={{
                fontSize: 50,
                fontWeight: 900,
                color: THEME.colors.textPrimary,
                lineHeight: 1.15,
                textShadow: '0 4px 16px rgba(0,0,0,0.9)',
                textTransform: 'uppercase',
              }}
            >
              Dois clientes pedem
            </div>
            <div
              style={{
                marginTop: 6,
                display: 'inline-block',
                transform: isMesmoHorario
                  ? `scale(${1 + highlightSpring * 0.04})`
                  : 'scale(1)',
                background: isMesmoHorario ? THEME.colors.primary : 'transparent',
                color: isMesmoHorario ? THEME.colors.textOnPrimary : THEME.colors.primary,
                padding: '4px 20px',
                borderRadius: 14,
                fontSize: 52,
                fontWeight: 900,
                textTransform: 'uppercase',
                boxShadow: isMesmoHorario
                  ? '0 0 30px rgba(255,169,77,0.65)'
                  : 'none',
              }}
            >
              o mesmo horário?
            </div>
          </div>
        )}

        {/* Cards de Colisão Compactos */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            alignItems: 'center',
          }}
        >
          {/* Card 1: Mariana Costa (entra no frame 6) */}
          {frame >= 6 && (
            <div
              style={{
                width: 820,
                background: '#131B2EF5',
                borderRadius: 20,
                border: '2px solid rgba(255,255,255,0.15)',
                padding: '14px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: '0 10px 28px rgba(0,0,0,0.7)',
                transform: `translateX(${(1 - card1Spring) * -60}px)`,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 29,
                    background: 'linear-gradient(135deg, #3B82F6, #1D4ED8)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  MC
                </div>
                <div>
                  <div style={{fontSize: 36, fontWeight: 800, color: '#FFFFFF'}}>
                    Mariana Costa
                  </div>
                  <div style={{fontSize: 32, fontWeight: 600, color: THEME.colors.textMuted}}>
                    Pediu: Amanhã às 15:00
                  </div>
                </div>
              </div>
              <div
                style={{
                  background: '#064E3BCC',
                  border: '1.5px solid #10B981',
                  borderRadius: 12,
                  padding: '6px 16px',
                  fontSize: 32,
                  fontWeight: 800,
                  color: '#6EE7B7',
                }}
              >
                15:00
              </div>
            </div>
          )}

          {/* Card 2: Juliana Silva (entra simultaneamente no frame 6) */}
          {frame >= 6 && (
            <div
              style={{
                width: 820,
                background: (isConflito || isEarlyConflito) ? '#2A1215F8' : '#131B2EF5',
                borderRadius: 20,
                border: `2px solid ${(isConflito || isEarlyConflito) ? '#EF4444' : 'rgba(255,255,255,0.15)'}`,
                padding: '14px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: (isConflito || isEarlyConflito)
                  ? '0 10px 30px rgba(239,68,68,0.55)'
                  : '0 10px 28px rgba(0,0,0,0.7)',
                transform: isConflito
                  ? `scale(${1 + pulse})`
                  : `translateX(${(1 - card2Spring) * 60}px)`,
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div
                  style={{
                    width: 58,
                    height: 58,
                    borderRadius: 29,
                    background: (isConflito || isEarlyConflito)
                      ? 'linear-gradient(135deg, #EF4444, #991B1B)'
                      : 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 32,
                    fontWeight: 900,
                    color: '#FFFFFF',
                  }}
                >
                  JS
                </div>
                <div>
                  <div style={{fontSize: 36, fontWeight: 800, color: '#FFFFFF'}}>
                    Juliana Silva
                  </div>
                  <div
                    style={{
                      fontSize: 32,
                      fontWeight: 600,
                      color: (isConflito || isEarlyConflito) ? '#FCA5A5' : THEME.colors.textMuted,
                    }}
                  >
                    Pediu: Amanhã às 15:00
                  </div>
                </div>
              </div>
              <div
                style={{
                  background: (isConflito || isEarlyConflito) ? '#7F1D1D' : '#064E3BCC',
                  border: `1.5px solid ${(isConflito || isEarlyConflito) ? '#EF4444' : '#10B981'}`,
                  borderRadius: 12,
                  padding: '6px 16px',
                  fontSize: 32,
                  fontWeight: 800,
                  color: (isConflito || isEarlyConflito) ? '#FECACA' : '#6EE7B7',
                }}
              >
                15:00
              </div>
            </div>
          )}

          {/* Alerta de conflito imediato antes dos 2 segundos (frame 22 / 0.73s) */}
          {isEarlyConflito && !isConflito && (
            <div
              style={{
                transform: `scale(${earlyConflitoSpring + pulse})`,
                background: '#EF4444',
                color: '#FFFFFF',
                padding: '8px 26px',
                borderRadius: 16,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                boxShadow: '0 8px 24px rgba(239,68,68,0.7)',
                marginTop: 4,
              }}
            >
              <span style={{fontSize: 32}}>⚠️</span>
              <span style={{fontSize: 34, fontWeight: 900, textTransform: 'uppercase', letterSpacing: 1}}>
                CONFLITO: 15:00
              </span>
            </div>
          )}

          {/* Banner de alerta dramático */}
          {isConflito && (
            <div
              style={{
                transform: `scale(${conflitoSpring + pulse})`,
                background: '#EF4444',
                color: '#FFFFFF',
                padding: '10px 28px',
                borderRadius: 16,
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                boxShadow: '0 8px 24px rgba(239,68,68,0.65)',
                marginTop: 6,
              }}
            >
              <span style={{fontSize: 32}}>❌</span>
              <span style={{fontSize: 34, fontWeight: 900, textTransform: 'uppercase'}}>
                Você perde um deles!
              </span>
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
