import React from 'react';
import {
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CORES} from './types';

export const Cena1: React.FC<{fontFamily: string}> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Cortes de punch-in zoom dinâmico de Reels em 3 escalas:
  // Bloco 1 (0 a 74): 1.00x -> 1.04x ("No sábado à noite")
  // Bloco 2 (75 a 154): punch-in imediato para 1.12x -> 1.17x ("acumulavam muitas mensagens ao mesmo tempo")
  // Bloco 3 (155 a 236): punch-in imediato para 1.25x -> 1.30x ("e eu não vencia responder.")
  let videoScale = 1.0;
  if (frame < 75) {
    videoScale = interpolate(frame, [0, 75], [1.0, 1.04], {
      extrapolateRight: 'clamp',
    });
  } else if (frame < 155) {
    videoScale = interpolate(frame, [75, 155], [1.12, 1.17], {
      extrapolateRight: 'clamp',
    });
  } else {
    videoScale = interpolate(frame, [155, 236], [1.25, 1.30], {
      extrapolateRight: 'clamp',
    });
  }

  // Entrada do selo de contexto
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
    frame: frame - 75,
    fps,
    config: {damping: 12, stiffness: 150},
  });
  const fase3Spring = spring({
    frame: frame - 155,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  // Micro-ícones flutuantes para dinâmica visual
  const iconFloat1 = Math.sin(frame * 0.18) * 8;
  const iconFloat2 = Math.cos(frame * 0.16) * 8;

  const pulseAlert =
    frame >= 155 ? 1 + Math.sin((frame - 155) * 0.25) * 0.04 : 1;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Vídeo do Dono com zoom suave contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${videoScale})`,
          transformOrigin: 'center 45%',
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

        {/* Gradiente superior para contraste garantido */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 420,
            background:
              'linear-gradient(to bottom, rgba(15, 2, 5, 0.9) 0%, rgba(15, 2, 5, 0.6) 65%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Gradiente inferior para leitura do karaokê */}
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

      {/* Micro-ícones flutuantes laterais nas frases de impacto (fora da zona do rosto) */}
      {frame >= 75 && (
        <div
          style={{
            position: 'absolute',
            left: 50,
            top: 460,
            transform: `translateY(${iconFloat1}px) scale(${
              frame >= 155 ? pulseAlert : 1
            })`,
            background:
              frame >= 155
                ? 'rgba(239, 68, 68, 0.92)'
                : 'rgba(225, 29, 72, 0.92)',
            border: frame >= 155 ? '2.5px solid #FCA5A5' : '2.5px solid #FECDD3',
            borderRadius: 999,
            width: 58,
            height: 58,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 32,
            boxShadow: '0 6px 22px rgba(0,0,0,0.7)',
            zIndex: 35,
          }}
        >
          {frame >= 155 ? '⚠️' : '💬'}
        </div>
      )}

      {frame >= 75 && (
        <div
          style={{
            position: 'absolute',
            right: 50,
            top: 460,
            transform: `translateY(${iconFloat2}px) scale(${
              frame >= 155 ? pulseAlert : 1
            })`,
            background:
              frame >= 155
                ? 'rgba(220, 38, 38, 0.92)'
                : 'rgba(37, 211, 102, 0.92)',
            border: frame >= 155 ? '2.5px solid #FCA5A5' : '2.5px solid #86EFAC',
            borderRadius: 999,
            width: 58,
            height: 58,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 32,
            boxShadow: '0 6px 22px rgba(0,0,0,0.7)',
            zIndex: 35,
          }}
        >
          {frame >= 155 ? '⏳' : '📱'}
        </div>
      )}

      {/* Zona Superior Exclusiva de Grafismos (y: 195 a 330) */}
      {/* Respiro >= 38px abaixo da barra em y=152 */}
      {/* O ROSTO DO APRESENTADOR (y: 400 a 1480) ESTÁ 100% LIVRE COM RESPIRO >= 75px */}
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
        {/* Badge de Contexto: "O PROBLEMA REAL" */}
        <div
          style={{
            transform: `scale(${Math.max(0, tagSpring)})`,
            opacity: Math.min(1, tagSpring),
            background: 'rgba(239, 68, 68, 0.22)',
            border: '2px solid #EF4444',
            borderRadius: 999,
            padding: '8px 24px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            boxShadow: '0 4px 18px rgba(0,0,0,0.6)',
          }}
        >
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: 999,
              background: '#EF4444',
              boxShadow: '0 0 10px #EF4444',
            }}
          />
          <span
            style={{
              color: '#FCA5A5',
              fontSize: 32,
              fontWeight: 800,
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            O PROBLEMA REAL
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
          {frame < 75 && (
            <div
              style={{
                transform: `scale(${Math.max(0, fase1Spring)})`,
                opacity: Math.min(1, fase1Spring),
                background: 'rgba(26, 12, 18, 0.94)',
                border: '2px solid rgba(250, 204, 21, 0.45)',
                borderRadius: 20,
                padding: '12px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                boxShadow: '0 8px 30px rgba(0,0,0,0.65)',
              }}
            >
              <span style={{fontSize: 32}}>🕒</span>
              <span
                style={{
                  color: CORES.apoio,
                  fontSize: 34,
                  fontWeight: 800,
                  textTransform: 'uppercase',
                }}
              >
                SÁBADO À NOITE • PICO DE PEDIDOS
              </span>
            </div>
          )}

          {frame >= 75 && frame < 155 && (
            <div
              style={{
                transform: `scale(${Math.max(0, fase2Spring)})`,
                opacity: Math.min(1, fase2Spring),
                background: 'rgba(35, 8, 14, 0.95)',
                border: `2px solid ${CORES.marca}`,
                borderRadius: 20,
                padding: '12px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                boxShadow: `0 8px 30px ${CORES.marca}66`,
              }}
            >
              <span style={{fontSize: 32}}>📱</span>
              <span
                style={{
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 900,
                  textTransform: 'uppercase',
                }}
              >
                MENSAGENS ACUMULADAS NO WHATSAPP
              </span>
            </div>
          )}

          {frame >= 155 && (
            <div
              style={{
                transform: `scale(${pulseAlert * Math.max(0, fase3Spring)})`,
                opacity: Math.min(1, fase3Spring),
                background:
                  'linear-gradient(135deg, rgba(220, 38, 38, 0.96) 0%, rgba(153, 27, 27, 0.96) 100%)',
                border: '2px solid #FCA5A5',
                borderRadius: 20,
                padding: '12px 28px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                boxShadow: '0 8px 35px rgba(220, 38, 38, 0.7)',
              }}
            >
              <span style={{fontSize: 32}}>⏳</span>
              <span
                style={{
                  color: '#FFFFFF',
                  fontSize: 34,
                  fontWeight: 900,
                  textTransform: 'uppercase',
                }}
              >
                NÃO VENCIA RESPONDER OS CLIENTES
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
