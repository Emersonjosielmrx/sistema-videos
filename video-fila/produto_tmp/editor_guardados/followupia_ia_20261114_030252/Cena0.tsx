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

  // Movimento contínuo de push-in na câmera
  const bgScale = interpolate(frame, [0, 159], [1.02, 1.12], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 159], [0, -20], {
    extrapolateRight: 'clamp',
  });

  // Top badge
  const badgeSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Fases da fala cinética:
  // Fase 1: "Cliente sumiu" (0.0s - 1.4s | frames 0 - 42)
  // Fase 2: "após receber o orçamento" (1.4s - 2.8s | frames 43 - 85)
  // Fase 3: "e você perdeu a venda?" (2.8s - 5.29s | frames 86 - 159)
  const isPhase1 = frame < 43;
  const isPhase2 = frame >= 43 && frame < 86;
  const isPhase3 = frame >= 86;

  const p1Spring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const p2Spring = spring({
    frame: frame - 43,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const p3Spring = spring({
    frame: frame - 86,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  // Flutuação sutil de respiração
  const floatY = Math.sin(frame / 14) * 6;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
        backgroundColor: '#111827',
        fontFamily,
      }}
    >
      {/* Imagem de fundo com push de câmera */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
          transformOrigin: '50% 60%',
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
        {/* Camada de escurecimento equilibrada: preserva a foto e garante contraste */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 30%, rgba(17, 24, 39, 0.70) 0%, rgba(17, 24, 39, 0.90) 80%)',
          }}
        />
      </div>

      {/* Topo seguro: Badge de contexto (y=168) */}
      <div
        style={{
          position: 'absolute',
          top: 168,
          left: 60,
          right: 60,
          display: 'flex',
          justifyContent: 'center',
          transform: `scale(${Math.max(0, badgeSpring)})`,
          opacity: Math.min(1, Math.max(0, badgeSpring)),
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 22px',
            borderRadius: 24,
            backgroundColor: 'rgba(239, 68, 68, 0.16)',
            border: '1.5px solid rgba(239, 68, 68, 0.65)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <span style={{fontSize: 26}}>⚠️</span>
          <span
            style={{
              fontSize: 32,
              fontWeight: 800,
              color: '#FCA5A5',
              letterSpacing: 1.2,
              textTransform: 'uppercase',
            }}
          >
            Alerta de Venda
          </span>
        </div>
      </div>

      {/* Bloco Cinético Central Unificado (y=280 a 640) — Deixa 65% da tela livre para a fotografia! */}
      <div
        style={{
          position: 'absolute',
          top: 260,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `translateY(${floatY}px)`,
          zIndex: 20,
        }}
      >
        {/* FASE 1: CLIENTE SUMIU? */}
        {isPhase1 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
              transform: `scale(${Math.max(0, p1Spring)})`,
              opacity: Math.min(1, Math.max(0, p1Spring)),
              textAlign: 'center',
            }}
          >
            <div
              style={{
                fontSize: 60,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1.5,
                textTransform: 'uppercase',
                textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              }}
            >
              CLIENTE
            </div>
            <div
              style={{
                fontSize: 68,
                fontWeight: 900,
                color: '#111827',
                backgroundColor: '#4ECDC4',
                padding: '6px 28px',
                borderRadius: 18,
                boxShadow:
                  '0 12px 30px rgba(78, 205, 196, 0.5), 0 0 20px rgba(78, 205, 196, 0.4)',
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}
            >
              SUMIU?
            </div>
          </div>
        )}

        {/* FASE 2: APÓS RECEBER O ORÇAMENTO? */}
        {isPhase2 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
              transform: `scale(${Math.max(0, p2Spring)})`,
              opacity: Math.min(1, Math.max(0, p2Spring)),
              textAlign: 'center',
            }}
          >
            <div
              style={{
                fontSize: 52,
                fontWeight: 900,
                color: '#E2E8F0',
                letterSpacing: 1,
                textTransform: 'uppercase',
                textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              }}
            >
              APÓS RECEBER
            </div>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 14,
                backgroundColor: 'rgba(17, 24, 39, 0.88)',
                border: '2px solid #4ECDC4',
                padding: '10px 28px',
                borderRadius: 20,
                boxShadow: '0 12px 30px rgba(0,0,0,0.6)',
              }}
            >
              <span style={{fontSize: 38}}>📄</span>
              <span
                style={{
                  fontSize: 52,
                  fontWeight: 900,
                  color: '#4ECDC4',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                O ORÇAMENTO?
              </span>
            </div>
          </div>
        )}

        {/* FASE 3: E VOCÊ PERDEU A VENDA? */}
        {isPhase3 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
              transform: `scale(${Math.max(0, p3Spring)})`,
              opacity: Math.min(1, Math.max(0, p3Spring)),
              textAlign: 'center',
            }}
          >
            <div
              style={{
                fontSize: 52,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: 1,
                textTransform: 'uppercase',
                textShadow: '0 4px 20px rgba(0,0,0,0.9)',
              }}
            >
              E VOCÊ
            </div>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 14,
                backgroundColor: 'rgba(239, 68, 68, 0.22)',
                border: '2px solid #EF4444',
                padding: '10px 28px',
                borderRadius: 20,
                boxShadow: '0 0 35px rgba(239, 68, 68, 0.4)',
              }}
            >
              <span style={{fontSize: 38}}>❌</span>
              <span
                style={{
                  fontSize: 56,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                PERDEU A VENDA?
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
