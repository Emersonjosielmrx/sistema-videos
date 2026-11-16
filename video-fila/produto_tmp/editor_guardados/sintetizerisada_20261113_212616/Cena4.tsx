import React from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Img,
} from 'remotion';
import {CORES} from './constants';

interface CenaProps {
  fontFamily: string;
}

export const Cena4: React.FC<CenaProps> = ({fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento de câmera no fundo: zoom contínuo expressivo até o fim
  const bgScale = interpolate(frame, [0, 120], [1.02, 1.15], {
    extrapolateRight: 'clamp',
  });
  const bgTranslateY = interpolate(frame, [0, 120], [0, -25], {
    extrapolateRight: 'clamp',
  });

  // Molas ágeis dos elementos para impacto imediato
  const logoSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const offerSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  const btnSpring = spring({
    frame: frame - 10,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  const subtextSpring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 14, stiffness: 130},
  });

  // Microanimações contínuas no botão de conversão:
  // 1. Pulso suave contínuo (escala de 1.0 para 1.04)
  const btnPulse = 1.0 + 0.038 * Math.sin(frame * 0.18);
  // 2. Passagem de brilho / shimmer sweep de ponta a ponta
  const shimmerPos = interpolate(frame % 32, [0, 32], [-280, 960], {
    extrapolateRight: 'clamp',
  });
  // 3. Deslocamento animado da seta indicativa (bounce suave para a direita)
  const arrowOffset = Math.sin(frame * 0.22) * 8;
  // 4. Glow pulsante contínuo
  const glowIntensity = 18 + 10 * Math.sin(frame * 0.18);

  // Leve flutuação do logo
  const logoFloat = Math.sin(frame * 0.1) * 5;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: CORES.fundo_escuro,
        overflow: 'hidden',
        fontFamily,
      }}
    >
      {/* Imagem de Fundo Desfocada com Movimento Contínuo */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `scale(${bgScale}) translateY(${bgTranslateY}px)`,
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'blur(16px)',
          }}
        />
        {/* Véu escuro com gradiente da marca */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(circle at 50% 50%, rgba(31, 41, 55, 0.82) 0%, rgba(17, 24, 39, 0.98) 100%)',
          }}
        />
      </div>

      {/* Conteúdo Centralizado e Harmonioso em torno de y ~ 960 (eliminando o vazio central) */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: 60,
          right: 60,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        {/* Elemento 1: Marca Agenda IA (y ~ 320 a 540) */}
        <div
          style={{
            opacity: logoSpring,
            transform: `translateY(${(1 - logoSpring) * 30 + logoFloat}px)`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <div
            style={{
              width: 108,
              height: 108,
              borderRadius: 32,
              backgroundColor: CORES.marca,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 14px 40px rgba(255, 169, 77, 0.55)`,
              fontSize: 50,
              fontWeight: 900,
              color: '#111827',
            }}
          >
            IA
          </div>

          <div
            style={{
              fontSize: 66,
              fontWeight: 900,
              color: '#FFFFFF',
              letterSpacing: '-1px',
              textShadow: '0 4px 22px rgba(0,0,0,0.85)',
            }}
          >
            AGENDA IA
          </div>
        </div>

        {/* Elemento 2: Cartão de Oferta e Proposta de Valor (y ~ 570 a 820) */}
        <div
          style={{
            marginTop: 40,
            opacity: offerSpring,
            transform: `translateY(${(1 - offerSpring) * 25}px)`,
            backgroundColor: 'rgba(31, 41, 55, 0.96)',
            border: `2px solid ${CORES.marca}`,
            borderRadius: 28,
            padding: '30px 48px',
            boxShadow:
              '0 18px 45px rgba(255, 169, 77, 0.3), 0 20px 45px rgba(0, 0, 0, 0.7)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
            width: '100%',
            maxWidth: 900,
          }}
        >
          <div
            style={{
              fontSize: 52,
              fontWeight: 900,
              color: CORES.marca,
              letterSpacing: '-0.5px',
              textShadow: '0 2px 12px rgba(255, 169, 77, 0.35)',
            }}
          >
            A partir de R$ 199 / mês
          </div>
          <div
            style={{
              fontSize: 34,
              fontWeight: 700,
              color: '#F3F4F6',
              lineHeight: 1.3,
            }}
          >
            Agendamentos automáticos 24h no WhatsApp
          </div>
        </div>

        {/* Elemento 3: Botão Principal Centralizado no Meio da Tela (y ~ 890 a 1020) com Microanimações */}
        <div
          style={{
            marginTop: 46,
            opacity: btnSpring,
            transform: `scale(${Math.max(0.7, btnSpring) * btnPulse})`,
            position: 'relative',
          }}
        >
          <div
            style={{
              width: 900,
              height: 120,
              borderRadius: 60,
              backgroundColor: CORES.marca,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 18,
              boxShadow: `0 16px 50px rgba(255, 169, 77, 0.65), 0 0 ${glowIntensity}px rgba(255, 169, 77, 0.8)`,
              overflow: 'hidden',
              position: 'relative',
              padding: '0 28px',
            }}
          >
            {/* Shimmer sweep animado contínuo */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                width: 160,
                transform: `translateX(${shimmerPos}px) skewX(-25deg)`,
                background:
                  'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.7) 50%, rgba(255,255,255,0) 100%)',
                pointerEvents: 'none',
              }}
            />

            <span
              style={{
                fontSize: 36,
                fontWeight: 900,
                color: '#111827',
                letterSpacing: '0.5px',
                whiteSpace: 'nowrap',
              }}
            >
              @sintetizerisada — CHAME NO DIRECT
            </span>
            <span
              style={{
                fontSize: 38,
                fontWeight: 900,
                color: '#111827',
                transform: `translateX(${arrowOffset}px)`,
                display: 'inline-block',
                transition: 'transform 0.05s ease',
              }}
            >
              ➔
            </span>
          </div>
        </div>

        {/* Elemento 4: Linha de Confiança Reafirmando os Fatos (y ~ 1080 a 1160) */}
        <div
          style={{
            marginTop: 40,
            opacity: subtextSpring,
            transform: `translateY(${(1 - subtextSpring) * 20}px)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              padding: '8px 24px',
              borderRadius: 20,
              backgroundColor: 'rgba(31, 41, 55, 0.85)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              fontSize: 32,
              fontWeight: 700,
              color: '#D1D5DB',
            }}
          >
            Sem conflito e sem duplo agendamento
          </div>
        </div>
      </div>
    </div>
  );
};
