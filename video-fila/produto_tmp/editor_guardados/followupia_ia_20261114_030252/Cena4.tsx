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

export const Cena4: React.FC<Props> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera contínuo no fundo
  const bgScale = interpolate(frame, [0, 119], [1.02, 1.12], {
    extrapolateRight: 'clamp',
  });
  const bgY = interpolate(frame, [0, 119], [0, -18], {
    extrapolateRight: 'clamp',
  });

  // Entrada dos elementos
  const logoSpring = spring({
    frame,
    fps,
    config: {damping: 13, stiffness: 120},
  });

  const buttonSpring = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const handleSpring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  const trustSpring = spring({
    frame: frame - 28,
    fps,
    config: {damping: 14, stiffness: 120},
  });

  // Pulso contínuo do botão CTA (1.00 -> 1.06) até o último frame
  const pulse = 1.0 + Math.sin(frame / 7) * 0.035;

  // Efeito shimmer passando pelo botão
  const shimmerProgress = (frame % 45) / 45;
  const shimmerX = interpolate(shimmerProgress, [0, 1], [-200, 900]);

  // Brilho pulsante no logo
  const glowOpacity = 0.5 + Math.sin(frame / 8) * 0.25;

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
      {/* Imagem de fundo desfocada com push contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale}) translateY(${bgY}px)`,
          transformOrigin: 'center center',
          filter: 'blur(22px)',
          opacity: 0.45,
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </div>

      {/* Véu escuro da marca para contraste total */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at 50% 50%, rgba(17, 24, 39, 0.82) 0%, rgba(17, 24, 39, 0.96) 90%)',
        }}
      />

      {/* Luz ambiente ciano ao fundo que respira */}
      <div
        style={{
          position: 'absolute',
          top: 650,
          left: 190,
          width: 700,
          height: 700,
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(78, 205, 196, 0.25) 0%, transparent 70%)',
          transform: `scale(${1 + Math.sin(frame / 10) * 0.1})`,
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo Central Unificado e Perfeitamente Distribuído (y=360 a 1280) */}
      <div
        style={{
          position: 'absolute',
          top: 360,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          zIndex: 10,
        }}
      >
        {/* Bloco 1: Ícone + Marca + Proposta (y=360 a 720) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 18,
            transform: `scale(${Math.max(0, logoSpring)})`,
            opacity: Math.min(1, Math.max(0, logoSpring)),
          }}
        >
          {/* Ícone de IA */}
          <div
            style={{
              width: 104,
              height: 104,
              borderRadius: 32,
              backgroundColor: '#1F2937',
              border: '2.5px solid #4ECDC4',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 54,
              boxShadow: `0 0 35px rgba(78, 205, 196, ${glowOpacity})`,
            }}
          >
            ⚡
          </div>

          <div
            style={{
              fontSize: 68,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: 0.5,
              textTransform: 'uppercase',
              textShadow:
                '0 4px 20px rgba(0,0,0,0.8), 0 0 30px rgba(78,205,196,0.4)',
            }}
          >
            Follow-up IA
          </div>

          <div
            style={{
              fontSize: 34,
              fontWeight: 600,
              color: '#94A3B8',
              maxWidth: 820,
              lineHeight: 1.35,
            }}
          >
            Follow-ups com IA que recuperam vendas
          </div>
        </div>

        {/* Bloco 2: Botão Principal de Conversão Pulsante (y=840 a 980) */}
        {frame >= 10 && (
          <div
            style={{
              marginTop: 64,
              width: '100%',
              maxWidth: 860,
              transform: `scale(${Math.max(0, buttonSpring) * pulse})`,
              opacity: Math.min(1, Math.max(0, buttonSpring)),
            }}
          >
            <div
              style={{
                position: 'relative',
                height: 116,
                borderRadius: 30,
                background: 'linear-gradient(135deg, #4ECDC4 0%, #2DD4BF 100%)',
                boxShadow:
                  '0 18px 44px rgba(78, 205, 196, 0.5), 0 0 25px rgba(78, 205, 196, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 16,
                overflow: 'hidden',
              }}
            >
              {/* Shimmer sweep */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: shimmerX,
                  width: 90,
                  height: '100%',
                  background:
                    'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.65), transparent)',
                  transform: 'skewX(-20deg)',
                  pointerEvents: 'none',
                }}
              />

              <span style={{fontSize: 42}}>💬</span>
              <span
                style={{
                  fontSize: 44,
                  fontWeight: 900,
                  color: '#111827',
                  letterSpacing: 1.2,
                  textTransform: 'uppercase',
                }}
              >
                CHAME NO DIRECT
              </span>
            </div>
          </div>
        )}

        {/* Bloco 3: Arroba Oficial (y=1040 a 1120) */}
        {frame >= 20 && (
          <div
            style={{
              marginTop: 36,
              transform: `scale(${Math.max(0, handleSpring)})`,
              opacity: Math.min(1, Math.max(0, handleSpring)),
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 32px',
                borderRadius: 24,
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                border: '1.5px solid rgba(78, 205, 196, 0.4)',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              }}
            >
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#4ECDC4',
                }}
              >
                @
              </span>
              <span
                style={{
                  fontSize: 34,
                  fontWeight: 800,
                  color: '#FFFFFF',
                  letterSpacing: 0.8,
                }}
              >
                followupia.ia
              </span>
            </div>
          </div>
        )}

        {/* Bloco 4: Selo de Confiança / Proposta de Valor (y=1160 a 1220) */}
        {frame >= 28 && (
          <div
            style={{
              marginTop: 28,
              transform: `scale(${Math.max(0, trustSpring)})`,
              opacity: Math.min(1, Math.max(0, trustSpring)),
            }}
          >
            <div
              style={{
                fontSize: 32,
                fontWeight: 600,
                color: '#94A3B8',
                letterSpacing: 0.5,
              }}
            >
              Automação inteligente no WhatsApp
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
