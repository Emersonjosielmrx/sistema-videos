import React from 'react';
import {
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const Cena4: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Movimento contínuo de slow zoom no fundo desfocado
  const bgScale = interpolate(frame, [0, 119], [1.08, 1.22], {
    extrapolateRight: 'clamp',
  });

  // Slow zoom contínuo em toda a composição para dinamismo constante
  const cardZoom = interpolate(frame, [0, 119], [1.0, 1.05], {
    extrapolateRight: 'clamp',
  });

  // Entradas escalonadas com spring
  const logoSpring = spring({
    frame: frame - 2,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  const textSpring = spring({
    frame: frame - 6,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Pílulas com stagger de 5 frames cada
  const chip1Spring = spring({
    frame: frame - 9,
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const chip2Spring = spring({
    frame: frame - 14,
    fps,
    config: {damping: 13, stiffness: 140},
  });
  const chip3Spring = spring({
    frame: frame - 19,
    fps,
    config: {damping: 13, stiffness: 140},
  });

  const buttonSpring = spring({
    frame: frame - 16,
    fps,
    config: {damping: 12, stiffness: 140},
  });

  const handleSpring = spring({
    frame: frame - 22,
    fps,
    config: {damping: 13, stiffness: 130},
  });

  // Pulso contínuo de atração do botão CTA (respiro suave de 1.5s entre 1.00 e 1.045)
  const buttonPulse = Math.sin((frame / fps) * 2 * Math.PI / 1.5) * 0.0225 + 1.0225;

  // Brilho/shimmer sweep passando continuamente pelo botão a cada 1.5s (45 frames)
  const shimmerPos = ((frame * 6.5) % 240) - 70; // -70% a 170%

  // Flutuação suave do ícone da logo
  const logoFloat = Math.sin(frame * 0.12) * 5;

  // Micro-deslocamento da seta no CTA
  const arrowShift = Math.sin(frame * 0.22) * 4;

  return (
    <div
      style={{
        position: 'absolute',
        width: 1080,
        height: 1920,
        overflow: 'hidden',
      }}
    >
      {/* Fundo com foto desfocada e zoom contínuo */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          transform: `scale(${bgScale})`,
          filter: 'blur(22px)',
          transformOrigin: 'center center',
        }}
      >
        <Img
          src={staticFile('img_4.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      </div>

      {/* Véu escuro profundo da marca */}
      <div
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          background:
            'radial-gradient(circle at 50% 45%, rgba(17, 24, 39, 0.88) 0%, rgba(11, 15, 23, 0.98) 85%)',
        }}
      />

      {/* Cyber grid tecnológico com pulso de luz */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage:
            'linear-gradient(rgba(14, 165, 233, 0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(14, 165, 233, 0.07) 1px, transparent 1px)',
          backgroundSize: '44px 44px',
          opacity: 0.8 + Math.sin(frame * 0.1) * 0.1,
          pointerEvents: 'none',
        }}
      />

      {/* Conteúdo perfeitamente distribuído verticalmente na Safe Zone (y=250 a y=1340) */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 60,
          right: 60,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pointerEvents: 'none',
          transform: `scale(${cardZoom})`,
          transformOrigin: '50% 50%',
        }}
      >
        {/* Bloco 1: Logo & Marca (y=280 a 455) */}
        {logoSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 280,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              transform: `scale(${Math.max(0, logoSpring)}) translateY(${logoFloat}px)`,
              opacity: Math.min(1, logoSpring),
            }}
          >
            {/* Ícone de Escudo Tecnológico */}
            <div
              style={{
                width: 90,
                height: 90,
                borderRadius: 26,
                background: 'linear-gradient(135deg, #0EA5E9 0%, #0369A1 100%)',
                boxShadow: '0 0 40px rgba(14, 165, 233, 0.75)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 14,
                border: '2px solid rgba(255, 255, 255, 0.55)',
              }}
            >
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2L4 5V11.09C4 16.14 7.41 20.85 12 22C16.59 20.85 20 16.14 20 11.09V5L12 2Z"
                  stroke="#FFFFFF"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  fill="rgba(14, 165, 233, 0.35)"
                />
                <path
                  d="M9 12L11 14L15 10"
                  stroke="#FFFFFF"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            <div
              style={{
                fontSize: 66,
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '2px',
                textTransform: 'uppercase',
                textShadow: '0 4px 22px rgba(0, 0, 0, 0.85)',
              }}
            >
              VPS BLINDADA
            </div>
          </div>
        )}

        {/* Bloco 2: Subtítulo Direto com Espaçamento Amplo (y=530 a 610) */}
        {textSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 530,
              width: 900,
              textAlign: 'center',
              transform: `scale(${Math.max(0, textSpring)})`,
              opacity: Math.min(1, textSpring),
            }}
          >
            <div
              style={{
                fontSize: 42,
                fontWeight: 700,
                color: '#F1F5F9',
                lineHeight: 1.35,
                textWrap: 'balance',
                textShadow: '0 2px 14px rgba(0,0,0,0.85)',
              }}
            >
              Sua VPS configurada, segura e monitorada.
            </div>
          </div>
        )}

        {/* Bloco 3: Pílulas de Tecnologias com Alto Contraste e Entrada Escalonada (y=665 a 765) */}
        <div
          style={{
            position: 'absolute',
            top: 665,
            width: 900,
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: 14,
          }}
        >
          {chip1Spring > 0.01 && (
            <div
              style={{
                transform: `scale(${Math.max(0, chip1Spring)})`,
                opacity: Math.min(1, chip1Spring),
                padding: '12px 26px',
                borderRadius: 999,
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(14, 165, 233, 0.75)',
                fontSize: 34,
                fontWeight: 700,
                color: '#FFFFFF',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.55), 0 0 16px rgba(14, 165, 233, 0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <span style={{color: '#34D399', fontWeight: 800}}>✓</span>
              <span>Docker + Portainer</span>
            </div>
          )}

          {chip2Spring > 0.01 && (
            <div
              style={{
                transform: `scale(${Math.max(0, chip2Spring)})`,
                opacity: Math.min(1, chip2Spring),
                padding: '12px 26px',
                borderRadius: 999,
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(14, 165, 233, 0.75)',
                fontSize: 34,
                fontWeight: 700,
                color: '#FFFFFF',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.55), 0 0 16px rgba(14, 165, 233, 0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <span style={{color: '#34D399', fontWeight: 800}}>✓</span>
              <span>Traefik</span>
            </div>
          )}

          {chip3Spring > 0.01 && (
            <div
              style={{
                transform: `scale(${Math.max(0, chip3Spring)})`,
                opacity: Math.min(1, chip3Spring),
                padding: '12px 26px',
                borderRadius: 999,
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1.5px solid rgba(16, 185, 129, 0.75)',
                fontSize: 34,
                fontWeight: 700,
                color: '#FFFFFF',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.55), 0 0 16px rgba(16, 185, 129, 0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <span style={{color: '#34D399', fontWeight: 800}}>✓</span>
              <span>Bot Sentinela</span>
            </div>
          )}
        </div>

        {/* Bloco 4: Botão CTA Principal Pulsante com Shimmer Contínuo (y=845 a 985) */}
        {buttonSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 845,
              width: 900,
              display: 'flex',
              justifyContent: 'center',
              transform: `scale(${Math.max(0, buttonSpring) * buttonPulse})`,
              opacity: Math.min(1, buttonSpring),
            }}
          >
            <div
              style={{
                position: 'relative',
                width: '100%',
                height: 140,
                borderRadius: 70,
                background: 'linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%)',
                boxShadow:
                  '0 24px 55px rgba(14, 165, 233, 0.7), 0 0 35px rgba(14, 165, 233, 0.45)',
                border: '2px solid rgba(255, 255, 255, 0.7)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 20,
                overflow: 'hidden',
              }}
            >
              {/* Brilho reflexo (sheen/shimmer) passando continuamente a cada 1.5s */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  width: '35%',
                  left: `${shimmerPos}%`,
                  background:
                    'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.55) 50%, transparent 100%)',
                  transform: 'skewX(-25deg)',
                  pointerEvents: 'none',
                }}
              />

              <span
                style={{
                  fontSize: 52,
                  fontWeight: 900,
                  color: '#FFFFFF',
                  textTransform: 'uppercase',
                  letterSpacing: '2px',
                  textShadow: '0 2px 14px rgba(0, 0, 0, 0.45)',
                }}
              >
                Chame No Direct
              </span>

              {/* Seta viva com micro-animação */}
              <div style={{transform: `translateX(${arrowShift}px)`}}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M5 12H19M19 12L12 5M19 12L12 19"
                    stroke="#FFFFFF"
                    strokeWidth="3.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            </div>
          </div>
        )}

        {/* Bloco 5: Rodapé Institucional e @ Equilibrado no Terço Inferior (y=1080 a 1360) */}
        {handleSpring > 0.01 && (
          <div
            style={{
              position: 'absolute',
              top: 1080,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 16,
              transform: `scale(${Math.max(0, handleSpring)})`,
              opacity: Math.min(1, handleSpring),
            }}
          >
            <div
              style={{
                fontSize: 60,
                fontWeight: 900,
                color: '#38BDF8',
                letterSpacing: '1.5px',
                textShadow: '0 2px 20px rgba(14, 165, 233, 0.55)',
              }}
            >
              @vpsblindada.ia
            </div>

            <div
              style={{
                fontSize: 38,
                fontWeight: 700,
                color: '#F1F5F9',
                letterSpacing: '0.5px',
                textAlign: 'center',
              }}
            >
              Setup • Relatórios Claros • Sentinela
            </div>

            <div
              style={{
                padding: '10px 28px',
                borderRadius: 999,
                background: 'rgba(15, 23, 42, 0.90)',
                border: '1.5px solid rgba(14, 165, 233, 0.5)',
                fontSize: 34,
                fontWeight: 600,
                color: '#CBD5E1',
                textAlign: 'center',
                boxShadow: '0 6px 18px rgba(0, 0, 0, 0.4)',
              }}
            >
              Sua infraestrutura segura sem dor de cabeça
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
