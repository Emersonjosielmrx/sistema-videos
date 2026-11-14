import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Props = {
  fontFamily: string;
};

export const Cena1: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Background smooth pan and zoom
  const bgScale = interpolate(frame, [0, 230], [1.03, 1.10], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateX = interpolate(frame, [0, 230], [-20, 20], {
    extrapolateRight: 'clamp',
  });

  // Spring animations
  const topPillSpring = spring({
    frame: frame - 4,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  const titleSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  // Card 1 enters when "mexer com inteligência artificial" starts (~frame 26)
  const card1Spring = spring({
    frame: frame - 26,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Card 2 enters when "A rotina já é corrida demais" starts (~frame 140)
  const card2Spring = spring({
    frame: frame - 140,
    fps,
    config: {damping: 12, mass: 0.6},
  });

  // Highlight tip enters at frame 175
  const tipSpring = spring({
    frame: frame - 175,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Background Image with motion */}
      <div
        style={{
          position: 'absolute',
          width: 1080,
          height: 1920,
          transform: `scale(${bgScale}) translateX(${bgTranslateX}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_1.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Dark gradient overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(180deg, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.72) 25%, rgba(15,23,42,0.60) 50%, rgba(15,23,42,0.82) 78%, rgba(15,23,42,0.96) 100%)',
        }}
      />

      {/* Top Badge: O PROBLEMA (y=175) */}
      <div
        style={{
          position: 'absolute',
          top: 175,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          opacity: Math.min(1, Math.max(0, topPillSpring)),
          transform: `scale(${0.9 + 0.1 * Math.min(1, Math.max(0, topPillSpring))})`,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '10px 24px',
            borderRadius: 30,
            background: 'rgba(31, 41, 55, 0.88)',
            border: '2px solid rgba(245, 158, 11, 0.7)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
          }}
        >
          <span style={{fontSize: 34}}>⚠️</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#F59E0B',
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
            }}
          >
            O Problema
          </span>
        </div>
      </div>

      {/* Headline (y=265) */}
      <div
        style={{
          position: 'absolute',
          top: 265,
          left: 60,
          right: 60,
          textAlign: 'center',
          opacity: Math.min(1, Math.max(0, titleSpring)),
          transform: `translateY(${(1 - Math.min(1, Math.max(0, titleSpring))) * 20}px)`,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: 52,
            fontWeight: 800,
            color: '#FFFFFF',
            textShadow: '0 4px 18px rgba(0,0,0,0.95)',
            textWrap: 'balance',
          }}
        >
          A rotina do salão já é corrida demais
        </h2>
      </div>

      {/* Card 1: Medo de complicação com IA (y=430) */}
      <div
        style={{
          position: 'absolute',
          top: 430,
          left: 60,
          right: 60,
          opacity: Math.min(1, Math.max(0, card1Spring)),
          transform: `translateX(${(1 - Math.min(1, Math.max(0, card1Spring))) * -40}px) translateY(${Math.sin(frame * 0.08) * 4}px)`,
        }}
      >
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(245, 158, 11, 0.55)',
            borderRadius: 24,
            padding: '24px 28px',
            boxShadow: '0 12px 35px rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 40}}>🤖</span>
              <span style={{fontSize: 44, fontWeight: 800, color: '#FFFFFF'}}>
                Mexer com IA parecia difícil
              </span>
            </div>
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.25)',
                border: '1px solid #EF4444',
                color: '#FCA5A5',
                fontSize: 32,
                fontWeight: 800,
                padding: '4px 16px',
                borderRadius: 14,
              }}
            >
              MITO
            </div>
          </div>
          <div style={{fontSize: 34, fontWeight: 500, color: '#D1D5DB', lineHeight: 1.3}}>
            Medo de sistemas complicados e perda de tempo no atendimento
          </div>
        </div>
      </div>

      {/* Card 2: Rotina corrida demais (y=720) */}
      <div
        style={{
          position: 'absolute',
          top: 720,
          left: 60,
          right: 60,
          opacity: Math.min(1, Math.max(0, card2Spring)),
          transform: `translateX(${(1 - Math.min(1, Math.max(0, card2Spring))) * 40}px) translateY(${Math.cos(frame * 0.08) * 4}px)`,
        }}
      >
        <div
          style={{
            background: 'rgba(17, 24, 39, 0.90)',
            border: '2px solid rgba(239, 68, 68, 0.65)',
            borderRadius: 24,
            padding: '24px 28px',
            boxShadow: '0 12px 35px rgba(0,0,0,0.7)',
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
              <span style={{fontSize: 40}}>⏳</span>
              <span style={{fontSize: 44, fontWeight: 800, color: '#FFFFFF'}}>
                Rotina corrida no salão
              </span>
            </div>
            <div
              style={{
                background: 'rgba(239, 68, 68, 0.35)',
                border: '1px solid #F87171',
                color: '#FECACA',
                fontSize: 32,
                fontWeight: 800,
                padding: '4px 16px',
                borderRadius: 14,
              }}
            >
              SOBRECARGA
            </div>
          </div>
          <div style={{fontSize: 34, fontWeight: 500, color: '#D1D5DB', lineHeight: 1.3}}>
            Atender clientes, cortar cabelo e ainda responder mensagens no WhatsApp
          </div>
        </div>
      </div>

      {/* Bottom Tip Badge (y=1030) */}
      {frame >= 170 && (
        <div
          style={{
            position: 'absolute',
            top: 1030,
            left: 60,
            right: 60,
            display: 'flex',
            justifyContent: 'center',
            opacity: Math.min(1, Math.max(0, tipSpring)),
            transform: `scale(${0.92 + 0.08 * Math.min(1, Math.max(0, tipSpring))})`,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14,
              padding: '14px 26px',
              borderRadius: 20,
              background: 'rgba(31, 41, 55, 0.92)',
              border: '2px solid rgba(245, 158, 11, 0.5)',
              boxShadow: '0 8px 25px rgba(0,0,0,0.6)',
            }}
          >
            <span style={{fontSize: 34}}>💡</span>
            <span style={{fontSize: 34, fontWeight: 700, color: '#F59E0B'}}>
              Como atender sem parar o trabalho?
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
